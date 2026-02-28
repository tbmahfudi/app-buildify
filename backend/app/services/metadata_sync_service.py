"""
Metadata Sync Service

Auto-generates and syncs EntityMetadata from EntityDefinition when entities are published.
This bridges the gap between schema design (EntityDefinition) and UI configuration (EntityMetadata).
"""

import json
import logging
from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.data_model import EntityDefinition, FieldDefinition
from app.models.metadata import EntityMetadata

logger = logging.getLogger(__name__)


class MetadataSyncService:
    """Service for syncing EntityMetadata from EntityDefinition"""

    def __init__(self, db: Session):
        self.db = db

    def auto_generate_metadata(
        self,
        entity_definition: EntityDefinition,
        created_by: Optional[str] = None
    ) -> EntityMetadata:
        """
        Auto-generate EntityMetadata from EntityDefinition.

        Called when an entity is published to create sensible default UI configuration.
        Users can then customize the metadata through the metadata API.

        Args:
            entity_definition: The published EntityDefinition
            created_by: User ID who triggered the generation

        Returns:
            EntityMetadata: The created metadata record
        """
        logger.info(f"Auto-generating EntityMetadata for entity: {entity_definition.name}")

        # Check if metadata already exists
        existing = self.db.query(EntityMetadata).filter(
            EntityMetadata.entity_name == entity_definition.name
        ).first()

        if existing:
            logger.info(f"EntityMetadata already exists for {entity_definition.name}, updating instead")
            return self.sync_metadata(entity_definition, existing, created_by)

        # Generate table configuration
        table_config = self._generate_table_config(entity_definition)

        # Generate form configuration
        form_config = self._generate_form_config(entity_definition)

        # Create EntityMetadata
        metadata = EntityMetadata(
            id=str(uuid4()),
            entity_name=entity_definition.name,
            display_name=entity_definition.label or entity_definition.name.replace('_', ' ').title(),
            description=entity_definition.description,
            icon=entity_definition.icon or 'table',
            table_config=json.dumps(table_config),
            form_config=json.dumps(form_config),
            permissions=json.dumps({}),  # Empty permissions, will inherit from RBAC
            version=1,
            is_active=True,
            is_system=False,
            created_by=created_by
        )

        self.db.add(metadata)
        self.db.commit()
        self.db.refresh(metadata)

        logger.info(f"Created EntityMetadata for {entity_definition.name}")

        return metadata

    def sync_metadata(
        self,
        entity_definition: EntityDefinition,
        metadata: EntityMetadata,
        updated_by: Optional[str] = None
    ) -> EntityMetadata:
        """
        Sync existing EntityMetadata with EntityDefinition changes.

        Updates metadata to reflect changes in entity definition while preserving
        user customizations where possible.

        Args:
            entity_definition: The updated EntityDefinition
            metadata: The existing EntityMetadata
            updated_by: User ID who triggered the sync

        Returns:
            EntityMetadata: The updated metadata record
        """
        logger.info(f"Syncing EntityMetadata for entity: {entity_definition.name}")

        # Parse existing configs
        existing_table_config = json.loads(metadata.table_config) if metadata.table_config else {}
        existing_form_config = json.loads(metadata.form_config) if metadata.form_config else {}

        # Generate new configs
        new_table_config = self._generate_table_config(entity_definition)
        new_form_config = self._generate_form_config(entity_definition)

        # Merge configs (preserve user customizations)
        merged_table_config = self._merge_table_config(existing_table_config, new_table_config)
        merged_form_config = self._merge_form_config(existing_form_config, new_form_config)

        # Update metadata
        metadata.display_name = entity_definition.label or metadata.display_name
        metadata.description = entity_definition.description or metadata.description
        metadata.icon = entity_definition.icon or metadata.icon
        metadata.table_config = json.dumps(merged_table_config)
        metadata.form_config = json.dumps(merged_form_config)
        metadata.version += 1
        metadata.updated_by = updated_by

        self.db.commit()
        self.db.refresh(metadata)

        logger.info(f"Synced EntityMetadata for {entity_definition.name}")

        return metadata

    def _generate_table_config(self, entity_def: EntityDefinition) -> Dict[str, Any]:
        """Generate table configuration from entity fields"""
        columns = []

        for field in entity_def.fields:
            # Skip deleted fields
            if field.is_deleted:
                continue

            # Skip system fields
            if field.is_system:
                continue

            # Skip large text fields in table view
            if field.field_type in ['text', 'json']:
                continue

            column = {
                'field': field.name,
                'title': field.label or field.name.replace('_', ' ').title(),
                'type': field.field_type,
                'sortable': True,
                'filterable': True,
                'visible': True,
                'width': self._get_column_width(field)
            }

            # Add to columns
            columns.append(column)

        # Ensure we have at least some columns
        if not columns:
            # Add first few fields as fallback
            for field in entity_def.fields[:5]:
                columns.append({
                    'field': field.name,
                    'title': field.label or field.name.replace('_', ' ').title(),
                    'type': field.field_type,
                    'sortable': True,
                    'filterable': True,
                    'visible': True,
                    'width': 150
                })

        return {
            'columns': columns,
            'default_sort': [[entity_def.default_sort_field or 'created_at', 'desc']],
            'default_page_size': 25,
            'enable_search': True,
            'enable_filters': True,
            'enable_export': True,
            'actions': ['view', 'edit', 'delete']
        }

    def _generate_form_config(self, entity_def: EntityDefinition) -> Dict[str, Any]:
        """Generate form configuration from entity fields"""
        fields = []

        for field in entity_def.fields:
            # Skip deleted fields
            if field.is_deleted:
                continue

            # Skip system fields
            if field.is_system:
                continue

            # Skip auto-generated fields
            if field.name in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                continue

            form_field = {
                'name': field.name,
                'label': field.label or field.name.replace('_', ' ').title(),
                'type': self._map_field_type_to_form_type(field.field_type),
                'required': field.is_required,
                'help_text': field.help_text or '',
                'placeholder': f"Enter {field.label or field.name}",
                'validation': self._get_validation_rules(field),
                'visible': True,
                'editable': not field.is_readonly,
                'order': len(fields) + 1
            }

            # Add field-specific configuration
            if field.field_type in ('choice', 'select'):
                # Build options list from allowed_values (set by frontend) or field_config (legacy)
                options = []
                if field.allowed_values:
                    raw = field.allowed_values
                    if isinstance(raw, str):
                        try:
                            raw = json.loads(raw)
                        except (json.JSONDecodeError, TypeError):
                            raw = []
                    if isinstance(raw, list):
                        for opt in raw:
                            if isinstance(opt, dict):
                                options.append({'value': opt.get('value', opt), 'label': opt.get('label', opt.get('value', opt))})
                            else:
                                options.append({'value': str(opt), 'label': str(opt)})
                elif field.field_config:
                    try:
                        config = json.loads(field.field_config) if isinstance(field.field_config, str) else field.field_config
                        raw_choices = config.get('choices', [])
                        for choice in raw_choices:
                            if isinstance(choice, dict):
                                options.append({'value': choice.get('value', choice), 'label': choice.get('label', choice.get('value', choice))})
                            else:
                                options.append({'value': str(choice), 'label': str(choice)})
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        pass
                form_field['options'] = options
            elif field.field_type in ('lookup', 'reference'):
                # Include reference entity info so frontend can fetch lookup options
                if field.reference_entity_id:
                    form_field['reference_entity_id'] = str(field.reference_entity_id)
                    # Include entity name so frontend can call the correct API endpoint
                    try:
                        if field.reference_entity:
                            form_field['reference_entity_name'] = field.reference_entity.name
                    except Exception:
                        pass
                if field.reference_table_name:
                    form_field['reference_table_name'] = field.reference_table_name
                form_field['reference_field'] = field.reference_field or 'id'
                form_field['display_field'] = field.display_field or 'name'
                if field.lookup_search_fields:
                    form_field['lookup_search_fields'] = field.lookup_search_fields
                if field.lookup_allow_create:
                    form_field['lookup_allow_create'] = field.lookup_allow_create
                if field.lookup_display_template:
                    form_field['lookup_display_template'] = field.lookup_display_template
                # Also include depends_on_field for cascading lookups
                if field.depends_on_field:
                    form_field['depends_on_field'] = field.depends_on_field
                if field.filter_expression:
                    form_field['filter_expression'] = field.filter_expression
            elif field.field_type in ['string', 'email', 'url']:
                form_field['max_length'] = field.max_length or 255
            elif field.field_type in ['integer', 'decimal']:
                if field.min_value is not None:
                    form_field['min'] = field.min_value
                if field.max_value is not None:
                    form_field['max'] = field.max_value

            fields.append(form_field)

        return {
            'fields': fields,
            'layout': 'single_column',  # or 'two_column', 'tabs'
            'groups': [],  # Field groups for organization
            'submit_button_text': 'Save',
            'cancel_button_text': 'Cancel',
            'show_required_indicator': True
        }

    def _get_column_width(self, field: FieldDefinition) -> int:
        """Get appropriate column width based on field type"""
        width_map = {
            'boolean': 80,
            'date': 120,
            'datetime': 160,
            'email': 200,
            'string': 150,
            'text': 300,
            'integer': 100,
            'decimal': 120,
            'uuid': 280,
            'choice': 150,
            'lookup': 150,
            'reference': 150
        }
        return width_map.get(field.field_type, 150)

    def _map_field_type_to_form_type(self, field_type: str) -> str:
        """Map database field type to form field type"""
        type_map = {
            'string': 'text',
            'email': 'email',
            'text': 'textarea',
            'integer': 'number',
            'decimal': 'number',
            'boolean': 'checkbox',
            'date': 'date',
            'datetime': 'datetime',
            'uuid': 'text',
            'select': 'select',
            'choice': 'select',
            'lookup': 'select',
            'reference': 'select',
            'json': 'json',
            'file': 'file',
            'url': 'url',
            'phone': 'text',
        }
        return type_map.get(field_type, 'text')

    def _get_validation_rules(self, field: FieldDefinition) -> Dict[str, Any]:
        """Get validation rules for field"""
        rules = {}

        if field.is_required:
            rules['required'] = True

        if field.is_unique:
            rules['unique'] = True

        if field.min_value is not None:
            rules['min'] = field.min_value

        if field.max_value is not None:
            rules['max'] = field.max_value

        if field.max_length:
            rules['max_length'] = field.max_length

        if field.validation_rules:
            try:
                custom_rules = json.loads(field.validation_rules) if isinstance(field.validation_rules, str) else field.validation_rules
                rules.update(custom_rules)
            except (json.JSONDecodeError, TypeError):
                pass

        return rules

    def _merge_table_config(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge table configurations, preserving user customizations.

        Strategy:
        - Keep user-modified column orders and visibility
        - Add new columns from entity definition
        - Remove columns for deleted fields
        """
        if not existing:
            return new

        # Get existing columns by field name
        existing_columns = {col['field']: col for col in existing.get('columns', [])}
        new_columns = {col['field']: col for col in new.get('columns', [])}

        # Merge columns
        merged_columns = []

        # First, add existing columns that still exist in new definition
        for col in existing.get('columns', []):
            field_name = col['field']
            if field_name in new_columns:
                # Keep user customizations (visibility, width, order)
                # Update field metadata from new definition
                merged_col = {**new_columns[field_name], **col}
                merged_columns.append(merged_col)

        # Add new columns not in existing config
        for field_name, col in new_columns.items():
            if field_name not in existing_columns:
                merged_columns.append(col)

        # Preserve other settings
        merged = {**new}
        merged['columns'] = merged_columns

        # Keep user's custom settings
        if 'default_sort' in existing:
            merged['default_sort'] = existing['default_sort']
        if 'default_page_size' in existing:
            merged['default_page_size'] = existing['default_page_size']
        if 'actions' in existing:
            merged['actions'] = existing['actions']

        return merged

    # Field properties that are always derived from the entity definition.
    # These must never be overridden by stale stored values when re-syncing.
    _SCHEMA_DRIVEN_FIELD_KEYS = frozenset({
        'type', 'required',
        'options',
        'reference_entity_id', 'reference_entity_name',
        'reference_table_name', 'reference_field', 'display_field',
        'lookup_search_fields', 'lookup_allow_create', 'lookup_display_template',
        'depends_on_field', 'filter_expression',
    })

    def _get_field_name(self, field: Dict[str, Any]) -> str:
        """Get field name from a field dict, supporting both 'name' and 'field' keys"""
        return field.get('name') or field.get('field') or ''

    def _merge_form_config(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge form configurations, preserving user customizations.

        Strategy:
        - Keep user-modified field orders and groupings
        - Add new fields from entity definition
        - Remove fields for deleted fields
        - Always refresh schema-driven properties (type, options, reference info)
          from the freshly-generated config so stale DB values can never override
          a code-level fix to field-type mapping.
        """
        if not existing:
            return new

        # Get existing fields by name - support both 'name' and 'field' keys
        existing_fields = {self._get_field_name(f): f for f in existing.get('fields', [])}
        new_fields = {self._get_field_name(f): f for f in new.get('fields', [])}

        # Merge fields
        merged_fields = []

        # First, add existing fields that still exist in new definition
        for field in existing.get('fields', []):
            field_name = self._get_field_name(field)
            if field_name and field_name in new_fields:
                new_field = new_fields[field_name]
                # Start with new as base, layer existing on top to preserve
                # user customisations (help_text, placeholder, rbac, etc.)
                merged_field = {**new_field, **field}
                # Always restore schema-driven keys from the freshly generated
                # config so a code fix to type-mapping is picked up on re-sync.
                for key in self._SCHEMA_DRIVEN_FIELD_KEYS:
                    if key in new_field:
                        merged_field[key] = new_field[key]
                    else:
                        merged_field.pop(key, None)
                merged_fields.append(merged_field)

        # Add new fields not in existing config
        for field_name, field in new_fields.items():
            if field_name not in existing_fields:
                merged_fields.append(field)

        # Preserve other settings
        merged = {**new}
        merged['fields'] = merged_fields

        # Keep user's custom settings
        if 'layout' in existing:
            merged['layout'] = existing['layout']
        if 'groups' in existing:
            merged['groups'] = existing['groups']
        if 'submit_button_text' in existing:
            merged['submit_button_text'] = existing['submit_button_text']

        return merged

    def delete_metadata(self, entity_name: str) -> bool:
        """
        Delete EntityMetadata when EntityDefinition is deleted.

        Args:
            entity_name: Name of the entity

        Returns:
            bool: True if deleted, False if not found
        """
        metadata = self.db.query(EntityMetadata).filter(
            EntityMetadata.entity_name == entity_name
        ).first()

        if metadata:
            # Soft delete
            metadata.is_active = False
            self.db.commit()
            logger.info(f"Soft deleted EntityMetadata for {entity_name}")
            return True

        return False
