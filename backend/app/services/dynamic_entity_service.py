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
from app.utils.field_type_mapper import FieldTypeMapper
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

    def _get_org_context(self, model) -> Dict[str, Any]:
        """
        Build org hierarchy filter/populate values based on entity's data_scope
        and the current user's organizational assignments.

        Returns dict of column_name -> value for org columns that should be
        set on create and filtered on read/update/delete.
        """
        entity_dict = getattr(model, '__entity_definition__', {})
        data_scope = entity_dict.get('data_scope', 'tenant')
        scope_cols = self.SCOPE_HIERARCHY.get(data_scope, self.SCOPE_HIERARCHY['tenant'])

        context = {}
        user = self.current_user

        for col in scope_cols:
            if not hasattr(model, col):
                continue
            if col == 'tenant_id' and user.tenant_id:
                context['tenant_id'] = str(user.tenant_id)
            elif col == 'company_id' and getattr(user, 'default_company_id', None):
                context['company_id'] = str(user.default_company_id)
            elif col == 'branch_id' and getattr(user, 'branch_id', None):
                context['branch_id'] = str(user.branch_id)
            elif col == 'department_id' and getattr(user, 'department_id', None):
                context['department_id'] = str(user.department_id)

        return context

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
        search: Optional[str] = None
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
        model = self.model_generator.get_model(entity_name, tenant_id)
        field_defs = self.model_generator.get_field_definitions(entity_name, tenant_id)

        # Base query
        query = self.db.query(model)

        # Apply org hierarchy filters based on entity's data_scope
        org_context = self._get_org_context(model)
        for col_name, col_value in org_context.items():
            query = query.filter(getattr(model, col_name) == col_value)

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

        return {
            'items': [self._model_to_dict(r, field_defs) for r in records],
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
                errors.append(error_msg)
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
                        errors.append(f"{field_def['label']} is required")

        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")

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
