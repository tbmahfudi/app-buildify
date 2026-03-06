"""
Metadata Sync Service

Generates and syncs UI configuration (table_config, form_config) directly onto
EntityDefinition when entities are published or their fields change.
entity_metadata table has been removed; all config now lives on entity_definitions.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.data_model import EntityDefinition, FieldDefinition

logger = logging.getLogger(__name__)


class MetadataSyncService:
    """Service for syncing UI config on EntityDefinition"""

    def __init__(self, db: Session):
        self.db = db

    def auto_generate_metadata(
        self,
        entity_definition: EntityDefinition,
        created_by: Optional[str] = None
    ) -> EntityDefinition:
        """
        Auto-generate UI config on EntityDefinition.

        Called when an entity is published to create sensible default UI configuration.
        Users can then customise the config through the metadata API.

        Args:
            entity_definition: The published EntityDefinition
            created_by: User ID who triggered the generation

        Returns:
            EntityDefinition: The updated entity definition
        """
        logger.info(f"Auto-generating UI config for entity: {entity_definition.name}")

        if entity_definition.table_config:
            logger.info(f"UI config already exists for {entity_definition.name}, syncing instead")
            return self.sync_metadata(entity_definition, created_by)

        # Generate table and form configurations
        entity_definition.table_config = self._generate_table_config(entity_definition)
        entity_definition.form_config = self._generate_form_config(entity_definition)
        if entity_definition.permissions is None:
            entity_definition.permissions = {}

        self.db.commit()
        self.db.refresh(entity_definition)

        logger.info(f"Generated UI config for {entity_definition.name}")
        return entity_definition

    def sync_metadata(
        self,
        entity_definition: EntityDefinition,
        updated_by: Optional[str] = None
    ) -> EntityDefinition:
        """
        Sync existing UI config on EntityDefinition with field changes.

        Updates table_config and form_config to reflect changes in fields while
        preserving user customisations where possible.

        Args:
            entity_definition: The updated EntityDefinition
            updated_by: User ID who triggered the sync

        Returns:
            EntityDefinition: The updated entity definition
        """
        logger.info(f"Syncing UI config for entity: {entity_definition.name}")

        # Read existing configs (already JSONB dicts, not strings)
        existing_table_config = entity_definition.table_config or {}
        existing_form_config = entity_definition.form_config or {}

        # Generate fresh configs
        new_table_config = self._generate_table_config(entity_definition)
        new_form_config = self._generate_form_config(entity_definition)

        # Merge (preserve user customisations)
        entity_definition.table_config = self._merge_table_config(existing_table_config, new_table_config)
        entity_definition.form_config = self._merge_form_config(existing_form_config, new_form_config)
        entity_definition.version = (entity_definition.version or 1) + 1
        entity_definition.updated_by = updated_by

        self.db.commit()
        self.db.refresh(entity_definition)

        logger.info(f"Synced UI config for {entity_definition.name}")
        return entity_definition

    def _generate_table_config(self, entity_def: EntityDefinition) -> Dict[str, Any]:
        """Generate table configuration from entity fields"""
        columns = []

        for field in entity_def.fields:
            if field.is_deleted:
                continue
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
            columns.append(column)

        # Fallback: include first few fields if everything was filtered out
        if not columns:
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
            if field.is_deleted:
                continue
            if field.is_system:
                continue
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

            # Field-specific configuration
            if field.field_type in ('choice', 'select'):
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
                form_field['options'] = options
            elif field.field_type in ('lookup', 'reference'):
                if field.reference_entity_id:
                    form_field['reference_entity_id'] = str(field.reference_entity_id)
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
            'layout': 'single_column',
            'groups': [],
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
        Merge table configurations, preserving user customisations.

        Strategy:
        - Keep user-modified column orders and visibility
        - Add new columns from entity definition
        - Remove columns for deleted fields
        """
        if not existing:
            return new

        existing_columns = {col['field']: col for col in existing.get('columns', [])}
        new_columns = {col['field']: col for col in new.get('columns', [])}

        merged_columns = []

        # Keep existing columns that still exist, preserving user customisations
        for col in existing.get('columns', []):
            field_name = col['field']
            if field_name in new_columns:
                merged_col = {**new_columns[field_name], **col}
                merged_columns.append(merged_col)

        # Add new columns not in existing config
        for field_name, col in new_columns.items():
            if field_name not in existing_columns:
                merged_columns.append(col)

        merged = {**new}
        merged['columns'] = merged_columns

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
        Merge form configurations, preserving user customisations.

        Strategy:
        - Keep user-modified field orders and groupings
        - Add new fields from entity definition
        - Remove fields for deleted fields
        - Always refresh schema-driven properties from the freshly-generated config
        """
        if not existing:
            return new

        existing_fields = {self._get_field_name(f): f for f in existing.get('fields', [])}
        new_fields = {self._get_field_name(f): f for f in new.get('fields', [])}

        merged_fields = []

        for field in existing.get('fields', []):
            field_name = self._get_field_name(field)
            if field_name and field_name in new_fields:
                new_field = new_fields[field_name]
                merged_field = {**new_field, **field}
                # Always restore schema-driven keys from fresh config
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

        merged = {**new}
        merged['fields'] = merged_fields

        if 'layout' in existing:
            merged['layout'] = existing['layout']
        if 'groups' in existing:
            merged['groups'] = existing['groups']
        if 'submit_button_text' in existing:
            merged['submit_button_text'] = existing['submit_button_text']

        return merged
