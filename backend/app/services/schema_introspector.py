"""
Schema Introspection Service

Automatically generates EntityDefinition and FieldDefinitions by introspecting
existing database objects (tables, views, materialized views).
"""

from sqlalchemy import inspect, MetaData, text
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import re


class SchemaIntrospector:
    """
    Introspect existing database objects and generate EntityDefinitions
    """

    def __init__(self, db: Session):
        self.db = db
        self.inspector = inspect(db.bind)
        self.metadata = MetaData()

    async def list_database_objects(self, schema: str = 'public') -> Dict[str, List[Dict]]:
        """
        List all tables and views in the database
        """
        # Get tables
        tables = self.inspector.get_table_names(schema=schema)

        # Get views
        views = self.inspector.get_view_names(schema=schema)

        # Get materialized views (PostgreSQL specific)
        materialized_views = self._get_materialized_views(schema)

        return {
            'tables': [
                {
                    'name': table,
                    'type': 'table',
                    'schema': schema,
                    'comment': self._get_table_comment(table, schema)
                }
                for table in tables
                if not self._is_system_table(table)
            ],
            'views': [
                {
                    'name': view,
                    'type': 'view',
                    'schema': schema,
                    'definition': self._get_view_definition(view, schema)
                }
                for view in views
                if not self._is_system_view(view)
            ],
            'materialized_views': [
                {
                    'name': mv,
                    'type': 'materialized_view',
                    'schema': schema,
                    'definition': self._get_materialized_view_definition(mv, schema)
                }
                for mv in materialized_views
            ]
        }

    def _get_materialized_views(self, schema: str) -> List[str]:
        """Get list of materialized views"""
        query = """
            SELECT matviewname
            FROM pg_matviews
            WHERE schemaname = :schema
        """
        result = self.db.execute(text(query), {'schema': schema})
        return [row[0] for row in result]

    def _get_view_definition(self, view_name: str, schema: str) -> Optional[str]:
        """Get SQL definition of a view"""
        query = """
            SELECT definition
            FROM pg_views
            WHERE viewname = :view_name
            AND schemaname = :schema
        """
        result = self.db.execute(text(query), {
            'view_name': view_name,
            'schema': schema
        }).fetchone()

        return result[0] if result else None

    def _get_materialized_view_definition(self, view_name: str, schema: str) -> Optional[str]:
        """Get SQL definition of a materialized view"""
        query = """
            SELECT definition
            FROM pg_matviews
            WHERE matviewname = :view_name
            AND schemaname = :schema
        """
        result = self.db.execute(text(query), {
            'view_name': view_name,
            'schema': schema
        }).fetchone()

        return result[0] if result else None

    def _get_table_comment(self, table_name: str, schema: str) -> Optional[str]:
        """Get table comment"""
        query = """
            SELECT obj_description(
                (quote_ident(:schema) || '.' || quote_ident(:table))::regclass,
                'pg_class'
            ) as comment
        """
        result = self.db.execute(text(query), {
            'table': table_name,
            'schema': schema
        }).fetchone()

        return result[0] if result and result[0] else None

    def _is_system_table(self, table_name: str) -> bool:
        """Check if table is a system table to exclude"""
        system_prefixes = ['pg_', 'sql_', 'information_schema']
        return any(table_name.startswith(prefix) for prefix in system_prefixes)

    def _is_system_view(self, view_name: str) -> bool:
        """Check if view is a system view to exclude"""
        system_prefixes = ['pg_', 'information_schema']
        return any(view_name.startswith(prefix) for prefix in system_prefixes)

    async def introspect_object(
        self,
        object_name: str,
        object_type: str,
        schema: str = 'public'
    ) -> Dict[str, Any]:
        """
        Introspect a specific database object and generate EntityDefinition structure
        """

        if object_type == 'table':
            return await self._introspect_table(object_name, schema)
        elif object_type in ['view', 'materialized_view']:
            return await self._introspect_view(object_name, object_type, schema)
        else:
            raise ValueError(f"Unsupported object type: {object_type}")

    async def _introspect_table(self, table_name: str, schema: str) -> Dict[str, Any]:
        """
        Introspect a table and generate EntityDefinition structure
        """

        # Get columns
        columns = self.inspector.get_columns(table_name, schema=schema)

        # Get primary keys
        pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
        pk_columns = pk_constraint.get('constrained_columns', [])

        # Get foreign keys
        fk_constraints = self.inspector.get_foreign_keys(table_name, schema=schema)

        # Get indexes
        indexes = self.inspector.get_indexes(table_name, schema=schema)

        # Get unique constraints
        unique_constraints = self.inspector.get_unique_constraints(table_name, schema=schema)

        # Get table comment
        comment = self._get_table_comment(table_name, schema)

        # Build EntityDefinition structure
        entity_def = {
            'name': table_name,
            'label': self._humanize_name(table_name),
            'description': comment,
            'object_type': 'table',
            'table_name': table_name,
            'schema_name': schema,

            # Detect capabilities
            'supports_insert': True,
            'supports_update': True,
            'supports_delete': True,

            # Detect if table has audit fields
            'is_audited': self._has_audit_fields(columns),
            'supports_soft_delete': self._has_soft_delete_field(columns),

            # Generate fields
            'fields': self._generate_field_definitions(
                columns,
                pk_columns,
                fk_constraints,
                unique_constraints
            ),

            # Generate relationships from foreign keys
            'relationships': self._generate_relationships(fk_constraints, table_name),

            # Generate indexes
            'indexes': self._generate_index_definitions(indexes, pk_columns)
        }

        return entity_def

    async def _introspect_view(
        self,
        view_name: str,
        object_type: str,
        schema: str
    ) -> Dict[str, Any]:
        """
        Introspect a view and generate EntityDefinition structure
        """

        # Get columns
        columns = self.inspector.get_columns(view_name, schema=schema)

        # Get view definition SQL
        if object_type == 'materialized_view':
            view_definition = self._get_materialized_view_definition(view_name, schema)
        else:
            view_definition = self._get_view_definition(view_name, schema)

        # Determine if view is updatable
        is_updatable = self._check_if_view_updatable(view_name, schema)

        entity_def = {
            'name': view_name,
            'label': self._humanize_name(view_name),
            'object_type': object_type,
            'table_name': view_name,
            'schema_name': schema,
            'view_definition': view_definition,

            # Views are read-only by default
            'supports_insert': False,
            'supports_update': is_updatable,
            'supports_delete': False,

            # Generate fields
            'fields': self._generate_field_definitions_from_view(columns),

            # For materialized views
            'is_materialized': object_type == 'materialized_view',
            'refresh_strategy': 'manual' if object_type == 'materialized_view' else None,

            'relationships': [],
            'indexes': []
        }

        return entity_def

    def _generate_field_definitions(
        self,
        columns: List[Dict],
        pk_columns: List[str],
        fk_constraints: List[Dict],
        unique_constraints: List[Dict]
    ) -> List[Dict]:
        """
        Generate field definitions from table columns
        """
        fields = []

        # Build FK lookup map
        fk_map = {}
        for fk in fk_constraints:
            for local_col, ref_col in zip(
                fk['constrained_columns'],
                fk['referred_columns']
            ):
                fk_map[local_col] = {
                    'ref_table': fk['referred_table'],
                    'ref_column': ref_col,
                    'ref_schema': fk.get('referred_schema', 'public')
                }

        # Build unique constraint map
        unique_cols = set()
        for uc in unique_constraints:
            unique_cols.update(uc['column_names'])

        for col in columns:
            col_name = col['name']
            col_type = col['type']

            # Skip system audit fields (they'll be auto-managed)
            if col_name in ['created_at', 'updated_at', 'created_by', 'updated_by',
                           'deleted_at', 'is_deleted']:
                continue

            # Map SQL type to field type
            field_type, data_type = self._map_column_type(col_type)

            # Check if foreign key
            is_fk = col_name in fk_map

            field_def = {
                'name': col_name,
                'label': self._humanize_name(col_name),
                'field_type': field_type,
                'data_type': data_type,

                # Constraints
                'is_required': not col['nullable'] and col_name not in pk_columns,
                'is_nullable': col['nullable'],
                'is_unique': col_name in unique_cols,
                'is_indexed': col_name in pk_columns,

                # Default value
                'default_value': str(col['default']) if col['default'] else None,

                # String constraints
                'max_length': getattr(col_type, 'length', None),

                # Numeric constraints
                'decimal_places': getattr(col_type, 'scale', None),

                # Mark as system field if PK
                'is_system': col_name in pk_columns or col_name == 'id',
                'is_readonly': col_name in pk_columns or col_name == 'id',

                # Foreign key relationship
                'reference_entity_id': None,  # Will be resolved later
                'reference_table': fk_map[col_name]['ref_table'] if is_fk else None,
                'reference_field': fk_map[col_name]['ref_column'] if is_fk else None,
                'relationship_type': 'many-to-one' if is_fk else None,

                # Display order
                'display_order': len(fields)
            }

            fields.append(field_def)

        return fields

    def _generate_field_definitions_from_view(self, columns: List[Dict]) -> List[Dict]:
        """
        Generate field definitions from view columns
        """
        fields = []

        for idx, col in enumerate(columns):
            field_type, data_type = self._map_column_type(col['type'])

            fields.append({
                'name': col['name'],
                'label': self._humanize_name(col['name']),
                'field_type': field_type,
                'data_type': data_type,

                # Views: all fields are computed/readonly
                'is_computed': True,
                'is_readonly': True,
                'is_nullable': col['nullable'],

                # Can't determine these for views
                'is_required': False,
                'is_unique': False,
                'is_system': col['name'] == 'id',

                'display_order': idx
            })

        return fields

    def _map_column_type(self, sql_type) -> tuple:
        """
        Map SQLAlchemy column type to field_type and data_type
        """
        type_name = sql_type.__class__.__name__.upper()

        # Handle VARCHAR/CHAR with length
        if type_name in ['VARCHAR', 'CHAR']:
            length = getattr(sql_type, 'length', 255)
            data_type = f'{type_name}({length})'
            return ('string', data_type)

        # Handle NUMERIC/DECIMAL with precision and scale
        if type_name in ['NUMERIC', 'DECIMAL']:
            precision = getattr(sql_type, 'precision', 10)
            scale = getattr(sql_type, 'scale', 2)
            data_type = f'{type_name}({precision},{scale})'
            return ('decimal', data_type)

        # Standard type mapping
        mapping = {
            'TEXT': ('text', 'TEXT'),
            'INTEGER': ('integer', 'INTEGER'),
            'BIGINT': ('biginteger', 'BIGINT'),
            'SMALLINT': ('integer', 'SMALLINT'),
            'FLOAT': ('decimal', 'FLOAT'),
            'DOUBLE': ('decimal', 'DOUBLE PRECISION'),
            'REAL': ('decimal', 'REAL'),
            'BOOLEAN': ('boolean', 'BOOLEAN'),
            'DATE': ('date', 'DATE'),
            'TIMESTAMP': ('datetime', 'TIMESTAMP'),
            'TIMESTAMPTZ': ('datetime', 'TIMESTAMP WITH TIME ZONE'),
            'TIME': ('time', 'TIME'),
            'UUID': ('uuid', 'UUID'),
            'JSONB': ('json', 'JSONB'),
            'JSON': ('json', 'JSON'),
        }

        return mapping.get(type_name, ('string', 'TEXT'))

    def _generate_relationships(
        self,
        fk_constraints: List[Dict],
        source_table: str
    ) -> List[Dict]:
        """
        Generate relationship definitions from foreign keys
        """
        relationships = []

        for fk in fk_constraints:
            rel_name = f"{source_table}_to_{fk['referred_table']}"

            relationships.append({
                'name': rel_name,
                'label': self._humanize_name(rel_name),
                'relationship_type': 'one-to-many',  # FK = many-to-one from FK side
                'source_entity_name': source_table,
                'source_entity_id': None,  # Will be resolved
                'target_entity_name': fk['referred_table'],
                'target_entity_id': None,  # Will be resolved
                'source_field_name': fk['constrained_columns'][0] if fk['constrained_columns'] else None,
                'target_field_name': fk['referred_columns'][0] if fk['referred_columns'] else None,
                'on_delete': fk.get('ondelete', 'NO ACTION'),
                'on_update': fk.get('onupdate', 'NO ACTION')
            })

        return relationships

    def _generate_index_definitions(
        self,
        indexes: List[Dict],
        pk_columns: List[str]
    ) -> List[Dict]:
        """Generate index definitions"""
        index_defs = []

        for idx in indexes:
            # Skip primary key indexes (already handled)
            if set(idx['column_names']) == set(pk_columns):
                continue

            index_defs.append({
                'name': idx['name'],
                'field_names': idx['column_names'],
                'is_unique': idx['unique'],
                'index_type': 'btree'  # Default, could be detected from index info
            })

        return index_defs

    def _humanize_name(self, snake_case_name: str) -> str:
        """Convert snake_case to Human Readable"""
        # Remove common prefixes
        name = re.sub(r'^(tbl_|vw_|mv_)', '', snake_case_name)
        # Split on underscores and capitalize
        words = name.split('_')
        return ' '.join(word.capitalize() for word in words)

    def _has_audit_fields(self, columns: List[Dict]) -> bool:
        """Check if table has audit fields"""
        col_names = {col['name'] for col in columns}
        audit_fields = {'created_at', 'updated_at', 'created_by', 'updated_by'}
        return audit_fields.issubset(col_names)

    def _has_soft_delete_field(self, columns: List[Dict]) -> bool:
        """Check if table has soft delete field"""
        col_names = {col['name'] for col in columns}
        return 'is_deleted' in col_names or 'deleted_at' in col_names

    def _check_if_view_updatable(self, view_name: str, schema: str) -> bool:
        """
        Check if view is updatable
        """
        query = """
            SELECT is_updatable
            FROM information_schema.views
            WHERE table_name = :view_name
            AND table_schema = :schema
        """
        result = self.db.execute(text(query), {
            'view_name': view_name,
            'schema': schema
        }).fetchone()

        return result[0] == 'YES' if result else False
