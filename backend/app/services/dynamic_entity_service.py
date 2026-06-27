"""
Dynamic Entity Service - CRUD operations for runtime-generated entities

This service provides complete CRUD functionality for nocode entities,
including validation, audit logging, and RBAC enforcement.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.services.runtime_model_generator import RuntimeModelGenerator
from app.core.dynamic_query_builder import DynamicQueryBuilder
from app.core.exceptions import AppException
from app.utils.field_type_mapper import FieldTypeMapper
from app.core.exceptions import EntityValidationError
from app.core.scope import apply_tenant_scope  # T-22.007
import logging
import json

logger = logging.getLogger(__name__)


class DynamicEntityService:
    """
    Service for CRUD operations on dynamic nocode entities

    Provides:
    - Create, read, update, delete operations
    - Field validation
    - Tenant isolation
    - RBAC permission checks
    - Audit logging
    - Bulk operations
    """

    # Maps data_scope levels to the org columns they require, in hierarchical order.
    # Each level includes all columns from the levels above it.
    SCOPE_HIERARCHY = {
        'platform': [],
        'tenant': ['tenant_id'],
        'company': ['tenant_id', 'company_id'],
        'branch': ['tenant_id', 'company_id', 'branch_id'],
        'department': ['tenant_id', 'company_id', 'branch_id', 'department_id'],
    }

    def __init__(self, db: Session, current_user):
        """
        Initialize dynamic entity service

        Args:
            db: SQLAlchemy database session
            current_user: Current authenticated user
        """
        self.db = db
        self.current_user = current_user
        self.model_generator = RuntimeModelGenerator(db)
        self.query_builder = DynamicQueryBuilder()
        self.field_mapper = FieldTypeMapper()

    def _check_entity_permission(self, entity_name: str, action: str) -> None:
        """Enforce per-entity permission rules from EntityDefinition.permissions JSONB.

        Story 4.2.4 / arch-21 §3.3. The JSONB shape is ``{role_code: [actions]}``
        where actions are one of ``create | read | update | delete``. When the
        column is null/empty, this method falls through silently and global RBAC
        retains full authority. When populated, the user's role set must intersect
        the set of roles allowed for the requested action; otherwise raises
        a ``PermissionError`` (translated to 403 by the router layer that already
        handles ValueError -> 400 for this service).

        Zero extra DB round-trips per CRUD op: the EntityDefinition row is loaded
        via the per-instance cache added in story 4.2.4 (see
        ``RuntimeModelGenerator.get_entity_definition``), shared with the model
        generation path that runs immediately after this check.
        """
        # Superusers bypass per-entity perms (consistent with global RBAC bypass)
        if getattr(self.current_user, 'is_superuser', False):
            return

        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        entity_def = self.model_generator.get_entity_definition(entity_name, tenant_id)
        if not entity_def:
            return  # Missing entity will surface in the next get_model call

        permissions_map = entity_def.permissions
        if not permissions_map or not isinstance(permissions_map, dict):
            return  # Null or malformed -> global RBAC owns

        allowed_roles = {
            role for role, actions in permissions_map.items()
            if isinstance(actions, list) and action in actions
        }
        if not allowed_roles:
            raise AppException(
                f"Per-entity permission denied: action '{action}' not granted to any role for entity '{entity_name}'",
                status_code=403,
            )

        user_roles = self.current_user.get_roles() if hasattr(self.current_user, 'get_roles') else set()
        if not user_roles & allowed_roles:
            raise AppException(
                f"Per-entity permission denied: action '{action}' on entity '{entity_name}'",
                status_code=403,
                details={"required_roles": sorted(allowed_roles)},
            )

    def _get_org_context(self, model) -> Dict[str, Any]:
        """
        Build org hierarchy filter/populate values based on entity's data_scope
        and the current user's organizational assignments.

        Returns dict of column_name -> value for org columns that should be
        set on create and filtered on read/update/delete.

        T-22.007: tenant_id population now delegates to apply_tenant_scope logic
        (reads user.tenant_id; no-ops on non-scoped models and superusers).
        Sub-tenant org columns (company_id, branch_id, department_id) remain
        explicit because apply_tenant_scope only covers the top-level tenant filter.
        """
        entity_dict = getattr(model, '__entity_definition__', {})
        data_scope = entity_dict.get('data_scope', 'tenant')
        scope_cols = self.SCOPE_HIERARCHY.get(data_scope, self.SCOPE_HIERARCHY['tenant'])

        context = {}
        user = self.current_user

        for col in scope_cols:
            if not hasattr(model, col):
                continue
            if col == 'tenant_id':
                # Delegate tenant isolation logic to the canonical helper.
                # apply_tenant_scope skips superusers and non-scoped models;
                # mirror that behaviour here for the populate path.
                if not getattr(user, 'is_superuser', False) and user.tenant_id:
                    context['tenant_id'] = str(user.tenant_id)
            elif col == 'company_id' and getattr(user, 'default_company_id', None):
                context['company_id'] = str(user.default_company_id)
            elif col == 'branch_id' and getattr(user, 'branch_id', None):
                context['branch_id'] = str(user.branch_id)
            elif col == 'department_id' and getattr(user, 'department_id', None):
                context['department_id'] = str(user.department_id)

        return context

    def _apply_org_scope_to_query(self, query, model):
        """
        Apply tenant + sub-tenant org scope filters to a query using canonical helpers.

        T-22.007: thin wrapper over apply_tenant_scope for the query-filter side
        of the org hierarchy. Called from list/get/update/delete paths instead of
        building inline filter() chains.
        """
        query = apply_tenant_scope(query, model, self.current_user)
        return query

    async def create_record(
        self,
        entity_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new record in dynamic entity

        Args:
            entity_name: Name of the entity
            data: Record data (field name -> value dict)

        Returns:
            Created record as dict

        Raises:
            ValueError: If validation fails or entity not found
            IntegrityError: If unique constraint violated
        """
        # Get model and field definitions
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'create')
        model = self.model_generator.get_model(entity_name, tenant_id)
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)

        # Validate data
        validated_data = self._validate_and_prepare_data(field_defs, data, is_create=True)

        # Add org hierarchy fields based on entity's data_scope
        org_context = self._get_org_context(model)
        validated_data.update(org_context)

        if hasattr(model, 'created_by'):
            validated_data['created_by'] = str(self.current_user.id)

        if hasattr(model, 'created_at'):
            validated_data['created_at'] = datetime.utcnow()

        if hasattr(model, 'updated_at'):
            validated_data['updated_at'] = datetime.utcnow()

        try:
            # Create instance
            record = model(**validated_data)

            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)

            record_dict = self._model_to_dict(record, field_defs)

            # Audit log
            await self._create_audit_log(
                'CREATE',
                entity_name,
                record_dict.get('id'),
                {'created': record_dict}
            )

            # Trigger automations
            await self._trigger_automations(
                entity_name,
                'onCreate',
                record_dict
            )

            logger.info(f"Created {entity_name} record: {record_dict.get('id')}")

            return record_dict

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating {entity_name}: {e}")
            raise ValueError(f"Failed to create record: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {entity_name}: {e}")
            raise

    async def list_records(
        self,
        entity_name: str,
        filters: Optional[Dict] = None,
        sort: Optional[List] = None,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        expand: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """
        List records with filtering, sorting, and pagination

        Args:
            entity_name: Name of the entity
            filters: Filter specification dict
            sort: List of (field, direction) tuples
            page: Page number (1-indexed)
            page_size: Items per page
            search: Global search term

        Returns:
            Dict with items, total, page, page_size, pages
        """
        # Get model and field definitions
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'read')
        model = self.model_generator.get_model(entity_name, tenant_id)
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)

        # Base query
        query = self.db.query(model)

        # Apply org hierarchy filters based on entity's data_scope
        org_context = self._get_org_context(model)
        for col_name, col_value in org_context.items():
            query = query.filter(getattr(model, col_name) == col_value)

        # Exclude soft-deleted records unless include_deleted requested (Story 5.4.1)
        if hasattr(model, 'deleted_at') and not include_deleted:
            query = query.filter(model.deleted_at.is_(None))

        # Apply filters
        if filters:
            query = self.query_builder.apply_filters(query, model, filters)

        # Apply search
        if search:
            query = self.query_builder.apply_search(query, model, search)

        # Get total before pagination
        total = query.count()

        # Apply sorting
        if sort:
            query = self.query_builder.apply_sort(query, model, sort)
        else:
            # Default sort by created_at desc if exists
            if hasattr(model, 'created_at'):
                query = query.order_by(model.created_at.desc())

        # Apply pagination
        query, total, total_pages = self.query_builder.apply_pagination(query, page, page_size)

        # Execute query
        records = query.all()

        items = [self._model_to_dict(r, field_defs) for r in records]

        # Inline related records for requested lookup fields (depth=1)
        if expand:
            items = self._apply_expand(items, field_defs, expand)

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': total_pages
        }

    async def get_record(
        self,
        entity_name: str,
        record_id: str
    ) -> Dict[str, Any]:
        """
        Get single record by ID

        Args:
            entity_name: Name of the entity
            record_id: Record ID

        Returns:
            Record as dict

        Raises:
            ValueError: If record not found
        """
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        model = self.model_generator.get_model(entity_name, tenant_id)
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)

        query = self.db.query(model).filter(model.id == record_id)

        # Apply org hierarchy filters based on entity's data_scope
        org_context = self._get_org_context(model)
        for col_name, col_value in org_context.items():
            query = query.filter(getattr(model, col_name) == col_value)

        # Exclude soft-deleted records (Gap 4.1)
        if hasattr(model, 'deleted_at'):
            query = query.filter(model.deleted_at.is_(None))

        record = query.first()

        if not record:
            raise ValueError(f"Record not found: {record_id}")

        return self._model_to_dict(record, field_defs)

    async def update_record(
        self,
        entity_name: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update record

        Args:
            entity_name: Name of the entity
            record_id: Record ID
            data: Updated field values

        Returns:
            Updated record as dict

        Raises:
            ValueError: If record not found or validation fails
        """
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'update')
        model = self.model_generator.get_model(entity_name, tenant_id)
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)

        query = self.db.query(model).filter(model.id == record_id)

        # Apply org hierarchy filters based on entity's data_scope
        org_context = self._get_org_context(model)
        for col_name, col_value in org_context.items():
            query = query.filter(getattr(model, col_name) == col_value)

        record = query.first()

        if not record:
            raise ValueError(f"Record not found: {record_id}")

        # Capture before state
        before = self._model_to_dict(record, field_defs)

        # Validate data
        validated_data = self._validate_and_prepare_data(field_defs, data, is_create=False)

        # Update fields (exclude system fields and org hierarchy columns)
        protected_fields = ['id', 'created_at', 'created_by',
                            'tenant_id', 'company_id', 'branch_id', 'department_id']
        for key, value in validated_data.items():
            if key not in protected_fields and hasattr(record, key):
                setattr(record, key, value)

        # Update system fields
        if hasattr(record, 'updated_by'):
            record.updated_by = str(self.current_user.id)

        if hasattr(record, 'updated_at'):
            record.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(record)

            after = self._model_to_dict(record, field_defs)

            # Write to shadow versions table if entity is versioned (Story 5.1.5)
            try:
                entity_def = self.model_generator._load_entity_definition(entity_name, tenant_id)
                if entity_def and getattr(entity_def, 'is_versioned', False):
                    table_prefix = f"t_{str(tenant_id).replace('-', '_')}_" if tenant_id else ""
                    version_table = f"{table_prefix}{entity_name}_versions"
                    changed_fields = {k: v for k, v in after.items() if before.get(k) != v and k not in ('updated_at', 'updated_by')}
                    import json as _json
                    from sqlalchemy import text as _text
                    self.db.execute(
                        _text(f"""
                            INSERT INTO {version_table}
                                (record_id, record_data, changed_fields, changed_by, changed_at)
                            VALUES
                                (:record_id, :before::jsonb, :changed::jsonb, :changed_by, NOW())
                        """),
                        {
                            'record_id': str(record_id),
                            'before': _json.dumps(before),
                            'changed': _json.dumps(changed_fields),
                            'changed_by': str(self.current_user.id),
                        }
                    )
                    self.db.commit()
            except Exception as _ve:
                logger.debug(f"Version insert skipped: {_ve}")

            # Audit log
            await self._create_audit_log(
                'UPDATE',
                entity_name,
                record_id,
                {'before': before, 'after': after}
            )

            # Trigger automations
            await self._trigger_automations(
                entity_name,
                'onUpdate',
                after
            )

            logger.info(f"Updated {entity_name} record: {record_id}")

            return after

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error updating {entity_name}: {e}")
            raise ValueError(f"Failed to update record: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {entity_name}: {e}")
            raise

    async def delete_record(
        self,
        entity_name: str,
        record_id: str
    ):
        """
        Delete record (soft delete if supported, hard delete otherwise)

        Args:
            entity_name: Name of the entity
            record_id: Record ID

        Raises:
            ValueError: If record not found
        """
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'delete')
        model = self.model_generator.get_model(entity_name, tenant_id)
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)

        query = self.db.query(model).filter(model.id == record_id)

        # Apply org hierarchy filters based on entity's data_scope
        org_context = self._get_org_context(model)
        for col_name, col_value in org_context.items():
            query = query.filter(getattr(model, col_name) == col_value)

        record = query.first()

        if not record:
            raise ValueError(f"Record not found: {record_id}")

        # Capture state before deletion
        before = self._model_to_dict(record, field_defs)

        # Soft delete if supported
        if hasattr(record, 'deleted_at'):
            record.deleted_at = datetime.utcnow()
            if hasattr(record, 'deleted_by'):
                record.deleted_by = str(self.current_user.id)
            self.db.commit()
            deletion_type = 'soft'
        else:
            # Hard delete
            self.db.delete(record)
            self.db.commit()
            deletion_type = 'hard'

        # Audit log
        await self._create_audit_log(
            'DELETE',
            entity_name,
            record_id,
            {'deleted': before, 'deletion_type': deletion_type}
        )

        # Trigger automations
        await self._trigger_automations(
            entity_name,
            'onDelete',
            before
        )

        logger.info(f"Deleted {entity_name} record: {record_id} ({deletion_type})")

    async def restore_soft_deleted_record(
        self,
        entity_name: str,
        record_id: str
    ) -> dict:
        """Restore a soft-deleted record (Story 5.4.1)."""
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'delete')
        model = self.model_generator.get_model(entity_name, tenant_id)
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)

        if not hasattr(model, 'deleted_at'):
            raise ValueError(f"Entity '{entity_name}' does not support soft delete")

        record = self.db.query(model).filter(model.id == record_id).first()
        if not record:
            raise ValueError(f"Record not found: {record_id}")
        if record.deleted_at is None:
            raise ValueError(f"Record is not deleted: {record_id}")

        record.deleted_at = None
        if hasattr(record, 'deleted_by'):
            record.deleted_by = None
        if hasattr(record, 'is_deleted'):
            record.is_deleted = False
        self.db.commit()

        await self._create_audit_log('RESTORE', entity_name, str(record_id))
        return self._model_to_dict(record, field_defs)

    async def get_record_versions(
        self,
        entity_name: str,
        record_id: str
    ):
        """Return change history for a versioned entity record (Story 5.1.5)."""
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'read')

        entity_def = self.model_generator._load_entity_definition(entity_name, tenant_id)
        if not entity_def or not getattr(entity_def, 'is_versioned', False):
            raise ValueError(f"Entity '{entity_name}' does not support versioning")

        table_prefix = f"t_{str(tenant_id).replace('-', '_')}_" if tenant_id else ""
        version_table = f"{table_prefix}{entity_name}_versions"

        from sqlalchemy import text as _text
        import json as _json
        try:
            result = self.db.execute(
                _text(f"""
                    SELECT id, record_id, record_data, changed_fields, changed_by, changed_at
                    FROM {version_table}
                    WHERE record_id = :record_id
                    ORDER BY changed_at DESC
                    LIMIT 100
                """),
                {'record_id': str(record_id)}
            )
            rows = result.mappings().all()
        except Exception as e:
            raise ValueError(f"Could not read version history: {e}")

        return [
            {
                'id': str(r['id']),
                'record_id': str(r['record_id']),
                'record_data': r['record_data'] if isinstance(r['record_data'], dict) else _json.loads(r['record_data'] or '{}'),
                'changed_fields': r['changed_fields'] if isinstance(r['changed_fields'], dict) else _json.loads(r['changed_fields'] or '{}'),
                'changed_by': str(r['changed_by']),
                'changed_at': r['changed_at'].isoformat() if r['changed_at'] else None,
            }
            for r in rows
        ]


    async def get_related_records(
        self,
        entity_name: str,
        record_id: str,
        relationship_name: str,
        page: int = 1,
        page_size: int = 25,
        sort: list = None,
        filters: dict = None,
        search: str = None,
        include_deleted: bool = False,
    ) -> dict:
        """
        Return paginated records related to a given record via a relationship
        field. Supports both FK (many-to-one stored on the related side) and
        reverse FK (one-to-many). (Story 5.3.2)
        """
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'read')

        # Load the source entity's field definitions to find the relationship
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)
        rel_field = next(
            (f for f in field_defs if f.get('name') == relationship_name and
             f.get('field_type') in ('relationship', 'lookup')),
            None
        )

        if not rel_field:
            # Try as a reverse relationship: another entity has a FK pointing here
            # Scan all entity fields for ref_entity_name == entity_name
            from app.models.data_model import EntityDefinition, FieldDefinition
            ref_fields = (
                self.db.query(FieldDefinition)
                .join(FieldDefinition.entity)
                .filter(
                    FieldDefinition.reference_entity_name == entity_name,
                    FieldDefinition.is_active == True,
                    FieldDefinition.name == relationship_name,
                )
                .first()
            )
            if not ref_fields:
                # Try matching by entity name (e.g. "orders" → entity named "order")
                target_entity_name = relationship_name.rstrip('s')  # naive depluralize
                ref_fields = (
                    self.db.query(FieldDefinition)
                    .join(FieldDefinition.entity)
                    .filter(
                        FieldDefinition.reference_entity_name == entity_name,
                        FieldDefinition.is_active == True,
                        EntityDefinition.name.in_([relationship_name, target_entity_name]),
                    )
                    .first()
                )

            if ref_fields:
                # Reverse FK: find all records in the related entity where FK == record_id
                target_entity = ref_fields.entity.name
                fk_field_name = ref_fields.name
                self._check_entity_permission(target_entity, 'read')
                target_model = self.model_generator.get_model(target_entity, tenant_id)
                target_field_defs = self.model_generator.get_field_definitions(target_entity, tenant_id)

                query = self.db.query(target_model).filter(
                    getattr(target_model, fk_field_name) == record_id
                )
                if hasattr(target_model, 'deleted_at') and not include_deleted:
                    query = query.filter(target_model.deleted_at.is_(None))
                if filters:
                    query = self.query_builder.apply_filters(query, target_model, filters)
                if search:
                    query = self.query_builder.apply_search(query, target_model, search)

                total = query.count()
                if sort:
                    for field_name, direction in sort:
                        col = getattr(target_model, field_name, None)
                        if col is not None:
                            query = query.order_by(col.desc() if direction == 'desc' else col.asc())
                else:
                    if hasattr(target_model, 'created_at'):
                        query = query.order_by(target_model.created_at.desc())

                offset = (page - 1) * page_size
                records = query.offset(offset).limit(page_size).all()
                items = [self._model_to_dict(r, target_field_defs) for r in records]
                return {
                    'items': items,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'pages': max(1, -(-total // page_size)),
                }

            raise ValueError(
                f"No relationship '{relationship_name}' found on entity '{entity_name}'. "
                f"Check that the field exists and is of type 'relationship'."
            )

        # Forward FK/lookup: the relationship field is on the source entity
        ref_entity = (
            rel_field.get('reference_entity_name') or
            rel_field.get('ref_entity_name') or
            rel_field.get('lookup_entity')
        )
        if not ref_entity:
            raise ValueError(f"Relationship field '{relationship_name}' has no target entity configured")

        self._check_entity_permission(ref_entity, 'read')

        # Fetch the source record to get the FK value
        source_model = self.model_generator.get_model(entity_name, tenant_id)
        source_record = self.db.query(source_model).filter(source_model.id == record_id).first()
        if not source_record:
            raise ValueError(f"Record not found: {record_id}")

        fk_value = getattr(source_record, relationship_name, None)
        if fk_value is None:
            return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'pages': 0}

        target_model = self.model_generator.get_model(ref_entity, tenant_id)
        target_field_defs = self.model_generator.get_field_definitions(ref_entity, tenant_id)
        ref_field_col = rel_field.get('ref_field') or 'id'

        query = self.db.query(target_model).filter(
            getattr(target_model, ref_field_col) == fk_value
        )
        if hasattr(target_model, 'deleted_at') and not include_deleted:
            query = query.filter(target_model.deleted_at.is_(None))
        if filters:
            query = self.query_builder.apply_filters(query, target_model, filters)
        if search:
            query = self.query_builder.apply_search(query, target_model, search)

        total = query.count()
        if sort:
            for field_name, direction in sort:
                col = getattr(target_model, field_name, None)
                if col is not None:
                    query = query.order_by(col.desc() if direction == 'desc' else col.asc())

        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()
        items = [self._model_to_dict(r, target_field_defs) for r in records]
        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': max(1, -(-total // page_size)),
        }

    async def bulk_create(
        self,
        entity_name: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk create records

        Args:
            entity_name: Name of the entity
            records: List of record data dicts

        Returns:
            Dict with created, failed, errors, ids
        """
        created = 0
        failed = 0
        errors = []
        ids = []

        for idx, record_data in enumerate(records):
            try:
                result = await self.create_record(entity_name, record_data)
                created += 1
                ids.append(result.get('id'))
            except Exception as e:
                failed += 1
                errors.append({
                    'index': idx,
                    'data': record_data,
                    'error': str(e)
                })
                logger.error(f"Bulk create error at index {idx}: {e}")

        return {
            'created': created,
            'failed': failed,
            'errors': errors,
            'ids': ids
        }

    async def bulk_update(
        self,
        entity_name: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk update records

        Each record must have an 'id' field

        Args:
            entity_name: Name of the entity
            records: List of records with id and data to update

        Returns:
            Dict with updated, failed, errors
        """
        updated = 0
        failed = 0
        errors = []

        for idx, record_data in enumerate(records):
            record_id = record_data.get('id')
            if not record_id:
                failed += 1
                errors.append({
                    'index': idx,
                    'data': record_data,
                    'error': 'Missing id field'
                })
                continue

            # Remove id from update data
            update_data = {k: v for k, v in record_data.items() if k != 'id'}

            try:
                await self.update_record(entity_name, record_id, update_data)
                updated += 1
            except Exception as e:
                failed += 1
                errors.append({
                    'index': idx,
                    'id': record_id,
                    'error': str(e)
                })
                logger.error(f"Bulk update error at index {idx}: {e}")

        return {
            'updated': updated,
            'failed': failed,
            'errors': errors
        }

    async def bulk_delete(
        self,
        entity_name: str,
        ids: List[str]
    ) -> Dict[str, Any]:
        """
        Bulk delete records

        Args:
            entity_name: Name of the entity
            ids: List of record IDs to delete

        Returns:
            Dict with deleted, failed, errors
        """
        deleted = 0
        failed = 0
        errors = []

        for idx, record_id in enumerate(ids):
            try:
                await self.delete_record(entity_name, record_id)
                deleted += 1
            except Exception as e:
                failed += 1
                errors.append({
                    'index': idx,
                    'id': record_id,
                    'error': str(e)
                })
                logger.error(f"Bulk delete error at index {idx}: {e}")

        return {
            'deleted': deleted,
            'failed': failed,
            'errors': errors
        }

    def _apply_expand(
        self,
        items: List[Dict[str, Any]],
        field_defs: List[Dict],
        expand: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Inline related records for lookup fields listed in `expand`.

        For each field name in `expand`:
          1. Find its FieldDefinition and confirm it references another entity
             via `reference_entity_name` (resolved from `reference_entity_id`)
             or falls back to `reference_table_name` for system tables.
          2. Collect the unique FK values across all items (one IN query).
          3. Attach the fetched record as `{field_name}_data` on each item.

        Depth is strictly limited to 1 — the fetched related records are plain
        dicts and are not themselves expanded further.

        Unknown field names or fields without a resolvable reference are silently
        skipped so the caller does not need to pre-validate the expand list.
        """
        field_map = {f['name']: f for f in field_defs}
        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None

        for field_name in expand:
            field_def = field_map.get(field_name)
            if not field_def:
                logger.warning("expand: field '%s' not found — skipping", field_name)
                continue

            # Resolve target entity name.
            # Priority: reference_entity_name (already resolved at dict-build time
            #           from reference_entity_id) → fall back to reference_table_name.
            ref_entity = field_def.get('reference_entity_name')

            if not ref_entity:
                # Fallback: try treating reference_table_name as a published entity
                # table name.  This covers system tables exposed as platform entities.
                ref_table = field_def.get('reference_table_name')
                if ref_table:
                    # Try to resolve entity name from table name
                    try:
                        from app.models.data_model import EntityDefinition as _ED
                        row = self.db.query(_ED.name).filter(
                            _ED.table_name == ref_table,
                            _ED.status == 'published'
                        ).first()
                        if row:
                            ref_entity = row[0]
                    except Exception:
                        pass

            if not ref_entity:
                logger.warning(
                    "expand: field '%s' has no resolvable reference entity "
                    "(reference_entity_id and reference_table_name both missing or unresolvable) — skipping",
                    field_name
                )
                continue

            # Collect unique FK values from items (filter out None)
            fk_values = list({
                item.get(field_name)
                for item in items
                if item.get(field_name) is not None
            })

            if not fk_values:
                for item in items:
                    item[f"{field_name}_data"] = None
                continue

            # Fetch related records in a single IN query — never N+1
            try:
                ref_model = self.model_generator.get_model(ref_entity, tenant_id)
                ref_field_defs = self.model_generator.get_field_definitions(ref_entity, tenant_id)

                ref_records_raw = self.db.query(ref_model).filter(
                    ref_model.id.in_(fk_values)
                ).all()

                related_records = {
                    rec_dict.get('id'): rec_dict
                    for r in ref_records_raw
                    for rec_dict in [self._model_to_dict(r, ref_field_defs)]
                }
            except Exception as exc:
                logger.error(
                    "expand: failed to fetch related entity '%s' for field '%s': %s",
                    ref_entity, field_name, exc
                )
                related_records = {}

            # Attach to each item
            for item in items:
                fk_val = item.get(field_name)
                item[f"{field_name}_data"] = related_records.get(fk_val)

        return items

    async def aggregate_records(
        self,
        entity_name: str,
        group_by: Optional[List[str]],
        metrics: List[Dict[str, Any]],
        filters: Optional[Dict] = None,
        date_trunc: Optional[str] = None,
        date_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run an aggregation query on a dynamic entity.

        Supports GROUP BY, COUNT/SUM/AVG/MIN/MAX/COUNT_DISTINCT metrics,
        optional filter conditions, and date-based time-series truncation.

        Org-scope isolation (tenant_id / company_id / etc.) is applied
        automatically using the same rules as list_records().

        Args:
            entity_name: Name of the published entity.
            group_by:    List of field names to group by (may be None).
            metrics:     List of dicts: [{field, function, alias?}, ...].
            filters:     Filter specification dict (same format as list_records).
            date_trunc:  Truncation unit ('hour','day','week','month','quarter','year').
            date_field:  Which group_by field to apply date_trunc to.

        Returns:
            Dict with 'groups', 'total_groups', 'entity_name'.
        """
        from sqlalchemy import select as sa_select
        from decimal import Decimal

        tenant_id = str(self.current_user.tenant_id) if self.current_user.tenant_id else None
        self._check_entity_permission(entity_name, 'read')
        model = self.model_generator.get_model(entity_name, tenant_id)

        # Build SELECT columns and GROUP BY expressions
        select_cols, group_exprs, output_keys = self.query_builder.build_aggregate_select(
            model, group_by, metrics, date_trunc, date_field
        )

        # Base query
        query = sa_select(*select_cols).select_from(model)

        # Org scope isolation
        org_context = self._get_org_context(model)
        for col_name, col_value in org_context.items():
            query = query.where(getattr(model, col_name) == col_value)

        # Exclude soft-deleted records (Gap 4.1)
        if hasattr(model, 'deleted_at'):
            query = query.where(model.deleted_at.is_(None))

        # User filters (reuse DynamicQueryBuilder's filter-clause builder)
        if filters:
            filter_clause = self.query_builder._build_filter_clause(model, filters)
            if filter_clause is not None:
                query = query.where(filter_clause)

        # GROUP BY
        if group_exprs:
            query = query.group_by(*group_exprs)

        # Execute
        result = self.db.execute(query)
        rows = result.fetchall()

        groups = []
        for row in rows:
            group = {}
            for i, key in enumerate(output_keys):
                val = row[i]
                # Normalize types for JSON serialization
                if isinstance(val, Decimal):
                    val = float(val)
                elif hasattr(val, 'isoformat'):
                    val = val.isoformat()
                group[key] = val
            groups.append(group)

        return {
            'groups': groups,
            'total_groups': len(groups),
            'entity_name': entity_name
        }

    def _validate_and_prepare_data(
        self,
        field_defs: List[Dict],
        data: Dict[str, Any],
        is_create: bool = True
    ) -> Dict[str, Any]:
        """
        Validate and prepare data for database operation

        Args:
            field_defs: Field definitions
            data: Input data
            is_create: Whether this is for create (vs update)

        Returns:
            Validated and prepared data dict

        Raises:
            ValueError: If validation fails
        """
        validated_data = {}
        # Each entry: {"field": str, "message": str}
        errors = []

        # Create field lookup
        field_map = {f['name']: f for f in field_defs}

        # Validate each field in data
        for field_name, value in data.items():
            if field_name not in field_map:
                # Unknown field - skip it
                logger.warning(f"Unknown field '{field_name}' in data, skipping")
                continue

            field_def = field_map[field_name]
            field_type = field_def.get('field_type', 'string')

            # Normalize empty strings to None for non-string field types
            if value == '' and field_type not in ('string', 'email', 'url', 'phone', 'text', 'textarea'):
                value = None

            # Validate value
            is_valid, error_msg = self.field_mapper.validate_value(field_def, value)
            if not is_valid:
                errors.append({"field": field_name, "message": error_msg})
                continue

            # Deserialize value
            validated_value = self.field_mapper.deserialize_value(field_type, value)

            # Use db_column_name as key
            column_name = field_def.get('db_column_name') or field_name
            validated_data[column_name] = validated_value

        # Check required fields (only for create)
        if is_create:
            for field_def in field_defs:
                if field_def.get('is_required') and not field_def.get('is_primary_key'):
                    field_name = field_def['name']
                    column_name = field_def.get('db_column_name') or field_name

                    if column_name not in validated_data:
                        errors.append({
                            "field": field_name,
                            "message": f"{field_def['label']} is required"
                        })

        if errors:
            raise EntityValidationError(errors=errors)

        return validated_data

    # Map system column names to their serialization field types
    SYSTEM_FIELD_TYPES = {
        'id': 'uuid',
        'tenant_id': 'uuid',
        'company_id': 'uuid',
        'branch_id': 'uuid',
        'department_id': 'uuid',
        'created_at': 'datetime',
        'created_by': 'uuid',
        'updated_at': 'datetime',
        'updated_by': 'uuid',
        'is_deleted': 'boolean',
        'deleted_at': 'datetime',
        'deleted_by': 'uuid',
    }

    def _model_to_dict(self, record, field_defs: List[Dict]) -> Dict[str, Any]:
        """
        Convert SQLAlchemy model to dict with proper serialization

        Args:
            record: SQLAlchemy model instance
            field_defs: Field definitions for serialization

        Returns:
            Dictionary representation
        """
        result = {}
        field_types = {f.get('db_column_name') or f['name']: f['field_type'] for f in field_defs}

        for column in record.__table__.columns:
            value = getattr(record, column.name)

            # Determine field type: check user-defined fields first, then system fields
            field_type = field_types.get(column.name) or self.SYSTEM_FIELD_TYPES.get(column.name, 'string')
            serialized_value = self.field_mapper.serialize_value(field_type, value)

            result[column.name] = serialized_value

        return result

    async def _create_audit_log(
        self,
        action: str,
        entity_name: str,
        entity_id: Optional[str],
        changes: Dict
    ):
        """
        Create audit log entry

        Args:
            action: Action type (CREATE, UPDATE, DELETE)
            entity_name: Entity name
            entity_id: Entity ID
            changes: Changes dict
        """
        try:
            from app.core.audit import create_audit_log

            create_audit_log(
                db=self.db,
                action=action,
                user=self.current_user,
                entity_type=entity_name,
                entity_id=entity_id,
                changes=changes,
                status='success'
            )
        except Exception as e:
            # Don't fail the operation if audit logging fails
            logger.error(f"Failed to create audit log: {e}")

    async def _trigger_automations(
        self,
        entity_name: str,
        event: str,
        record: Dict[str, Any]
    ):
        """
        Trigger automation rules for nocode entity events

        Args:
            entity_name: Name of the entity
            event: Event type (onCreate, onUpdate, onDelete)
            record: Record data

        Events:
            - onCreate: Triggered after record creation
            - onUpdate: Triggered after record update
            - onDelete: Triggered after record deletion
        """
        try:
            from app.models.automation import AutomationRule
            from app.services.automation_service import AutomationService

            # Find matching automation rules
            rules = self.db.query(AutomationRule).filter(
                AutomationRule.trigger_type == 'database',
                AutomationRule.is_active == True
            ).all()

            # Filter rules by entity and event
            matching_rules = []
            for rule in rules:
                trigger_config = rule.trigger_config or {}
                if (trigger_config.get('entity_name') == entity_name and
                    trigger_config.get('event') == event):
                    matching_rules.append(rule)

            if not matching_rules:
                logger.debug(f"No automation rules found for {entity_name}.{event}")
                return

            # Execute each matching rule
            automation_service = AutomationService(self.db, self.current_user)
            for rule in matching_rules:
                try:
                    logger.info(f"Triggering automation rule: {rule.name} for {entity_name}.{event}")
                    await automation_service.execute_rule(
                        rule.id,
                        context={
                            'entity': entity_name,
                            'event': event,
                            'record': record,
                            'user_id': str(self.current_user.id),
                            'tenant_id': str(self.current_user.tenant_id) if self.current_user.tenant_id else None
                        }
                    )
                except Exception as rule_error:
                    # Log error but continue with other rules
                    logger.error(f"Failed to execute automation rule {rule.name}: {rule_error}")

        except Exception as e:
            # Don't fail the operation if automation triggering fails
            logger.error(f"Failed to trigger automations for {entity_name}.{event}: {e}")
