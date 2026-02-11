"""
Migration Generator Service

Generates SQL migration scripts for entity definitions.
Handles CREATE TABLE, ALTER TABLE, and DROP TABLE operations.
"""

from typing import Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from app.models.data_model import (
    EntityDefinition,
    FieldDefinition,
    IndexDefinition,
)


class MigrationGenerator:
    """Generates SQL migration scripts for entity definitions"""

    def __init__(self, db: Session):
        self.db = db

    async def generate_migration(self, entity: EntityDefinition) -> Tuple[str, str]:
        """
        Generate up and down migration scripts for an entity

        Returns: (up_script, down_script)
        """
        # Check if table already exists
        table_exists = await self._table_exists(entity.table_name)

        if not table_exists:
            # CREATE TABLE migration
            return await self._generate_create_table(entity)
        else:
            # ALTER TABLE migration
            return await self._generate_alter_table(entity)

    async def _table_exists(self, table_name: str) -> bool:
        """Check if table exists in database"""
        try:
            result = self.db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                )
            """), {"table_name": table_name})
            return result.scalar()
        except Exception:
            return False

    async def _generate_create_table(self, entity: EntityDefinition) -> Tuple[str, str]:
        """Generate CREATE TABLE migration"""
        table_name = entity.table_name
        fields = sorted(entity.fields, key=lambda f: f.display_order)

        # Build CREATE TABLE statement
        up_sql_parts = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]

        # Add primary key first (ALWAYS include id field)
        field_definitions = ["    id UUID PRIMARY KEY DEFAULT gen_random_uuid()"]

        # Add tenant isolation field (always present for multi-tenant support)
        field_definitions.append("    tenant_id UUID")

        # Add user-defined fields
        for field in fields:
            # Skip if user manually added 'id' or 'tenant_id' field
            if field.name in ('id', 'tenant_id'):
                continue
            field_def = self._generate_field_definition(field)
            field_definitions.append(f"    {field_def}")

        # Add audit fields if enabled
        if entity.is_audited:
            field_definitions.extend([
                "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "    created_by UUID",
                "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "    updated_by UUID"
            ])

        # Add soft delete fields if enabled
        if entity.supports_soft_delete:
            field_definitions.extend([
                "    is_deleted BOOLEAN DEFAULT FALSE",
                "    deleted_at TIMESTAMP",
                "    deleted_by UUID"
            ])

        up_sql_parts.append(",\n".join(field_definitions))
        up_sql_parts.append(");")

        up_sql = "\n".join(up_sql_parts)

        # Add indexes
        index_sql = []
        for index in entity.indexes:
            if index.is_active:
                index_sql.append(self._generate_index_sql(table_name, index))

        if index_sql:
            up_sql += "\n\n" + "\n".join(index_sql)

        # Add comments
        if entity.description:
            up_sql += f"\n\nCOMMENT ON TABLE {table_name} IS '{self._escape_sql_string(entity.description)}';"

        for field in fields:
            if field.help_text:
                up_sql += f"\nCOMMENT ON COLUMN {table_name}.{field.name} IS '{self._escape_sql_string(field.help_text)}';"

        # Generate DOWN script (DROP TABLE)
        down_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;"

        return (up_sql, down_sql)

    async def _generate_alter_table(self, entity: EntityDefinition) -> Tuple[str, str]:
        """Generate ALTER TABLE migration for schema changes"""
        table_name = entity.table_name

        # Get current table structure from database
        current_columns = await self._get_current_columns(table_name)
        current_indexes = await self._get_current_indexes(table_name)

        # Get desired structure from entity definition
        desired_fields = {f.name: f for f in entity.fields}
        desired_indexes = {idx.name: idx for idx in entity.indexes if idx.is_active}

        up_sql_parts = []
        down_sql_parts = []

        # Detect new columns
        for field_name, field in desired_fields.items():
            if field_name not in current_columns:
                # ADD COLUMN
                field_def = self._generate_field_definition(field)
                up_sql_parts.append(f"ALTER TABLE {table_name} ADD COLUMN {field_def};")
                down_sql_parts.append(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {field_name};")

        # Detect removed columns
        for col_name in current_columns:
            if col_name not in desired_fields:
                # Check if it's a system column
                if col_name not in ['created_at', 'created_by', 'updated_at', 'updated_by',
                                    'is_deleted', 'deleted_at', 'deleted_by', 'id', 'tenant_id']:
                    # DROP COLUMN
                    up_sql_parts.append(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {col_name};")
                    # Note: We can't reliably reconstruct the down migration for dropped columns
                    down_sql_parts.append(f"-- Cannot automatically restore dropped column: {col_name}")

        # Detect modified columns (basic type changes)
        for field_name, field in desired_fields.items():
            if field_name in current_columns:
                current_col_type = current_columns[field_name]['data_type']
                desired_col_type = self._extract_base_type(field.data_type)

                if not self._types_compatible(current_col_type, desired_col_type):
                    # ALTER COLUMN TYPE
                    up_sql_parts.append(
                        f"ALTER TABLE {table_name} ALTER COLUMN {field_name} TYPE {field.data_type} USING {field_name}::{field.data_type};"
                    )
                    down_sql_parts.append(
                        f"-- Reverting type change for {field_name} may result in data loss"
                    )

                # Check nullability changes
                current_nullable = current_columns[field_name]['is_nullable']
                desired_nullable = field.is_nullable

                if current_nullable != desired_nullable:
                    if desired_nullable:
                        up_sql_parts.append(f"ALTER TABLE {table_name} ALTER COLUMN {field_name} DROP NOT NULL;")
                        down_sql_parts.append(f"ALTER TABLE {table_name} ALTER COLUMN {field_name} SET NOT NULL;")
                    else:
                        up_sql_parts.append(f"ALTER TABLE {table_name} ALTER COLUMN {field_name} SET NOT NULL;")
                        down_sql_parts.append(f"ALTER TABLE {table_name} ALTER COLUMN {field_name} DROP NOT NULL;")

        # Detect new indexes
        for idx_name, index in desired_indexes.items():
            if idx_name not in current_indexes:
                up_sql_parts.append(self._generate_index_sql(table_name, index))
                down_sql_parts.append(f"DROP INDEX IF EXISTS {idx_name};")

        # Detect removed indexes
        for idx_name in current_indexes:
            if idx_name not in desired_indexes:
                # Don't drop primary key or system indexes
                if not idx_name.endswith('_pkey') and not idx_name.startswith('pg_'):
                    up_sql_parts.append(f"DROP INDEX IF EXISTS {idx_name};")
                    # Can't reconstruct index without more info
                    down_sql_parts.append(f"-- Cannot automatically restore dropped index: {idx_name}")

        # Combine all parts
        up_sql = "\n".join(up_sql_parts) if up_sql_parts else "-- No changes detected"
        down_sql = "\n".join(reversed(down_sql_parts)) if down_sql_parts else "-- No changes to revert"

        return (up_sql, down_sql)

    async def _get_current_columns(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get current columns from database"""
        result = self.db.execute(text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = :table_name
        """), {"table_name": table_name})

        columns = {}
        for row in result:
            columns[row.column_name] = {
                'data_type': row.data_type.upper(),
                'is_nullable': row.is_nullable == 'YES',
                'column_default': row.column_default,
                'character_maximum_length': row.character_maximum_length
            }

        return columns

    async def _get_current_indexes(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get current indexes from database"""
        result = self.db.execute(text("""
            SELECT
                i.relname as index_name,
                a.attname as column_name,
                ix.indisunique as is_unique
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE t.relname = :table_name
            AND t.relkind = 'r'
        """), {"table_name": table_name})

        indexes = {}
        for row in result:
            if row.index_name not in indexes:
                indexes[row.index_name] = {
                    'columns': [],
                    'is_unique': row.is_unique
                }
            indexes[row.index_name]['columns'].append(row.column_name)

        return indexes

    def _generate_field_definition(self, field: FieldDefinition) -> str:
        """Generate SQL field definition"""
        # Handle data type with precision/scale for DECIMAL/NUMERIC types
        data_type = field.data_type
        if data_type and data_type.upper() in ['DECIMAL', 'NUMERIC']:
            if field.precision and field.decimal_places is not None:
                data_type = f"{data_type.upper()}({field.precision},{field.decimal_places})"
            elif field.precision:
                data_type = f"{data_type.upper()}({field.precision})"

        parts = [field.name, data_type]

        # Primary key (assume 'id' field is always PK)
        if field.name == 'id':
            parts.append("PRIMARY KEY")

        # NOT NULL constraint
        if field.is_required or not field.is_nullable:
            parts.append("NOT NULL")

        # UNIQUE constraint
        if field.is_unique:
            parts.append("UNIQUE")

        # DEFAULT value
        if field.default_value:
            if field.field_type in ['string', 'text', 'email', 'url', 'phone']:
                parts.append(f"DEFAULT '{self._escape_sql_string(field.default_value)}'")
            elif field.field_type == 'boolean':
                parts.append(f"DEFAULT {field.default_value.upper()}")
            else:
                parts.append(f"DEFAULT {field.default_value}")

        # Foreign key reference
        if field.reference_table:
            # Use reference_field if specified, otherwise default to 'id'
            ref_column = field.reference_field or 'id'
            parts.append(f"REFERENCES {field.reference_table}({ref_column})")
            if field.on_delete:
                parts.append(f"ON DELETE {field.on_delete}")
            if field.on_update:
                parts.append(f"ON UPDATE {field.on_update}")

        return " ".join(parts)

    def _generate_index_sql(self, table_name: str, index: IndexDefinition) -> str:
        """Generate CREATE INDEX statement"""
        unique = "UNIQUE " if index.is_unique else ""
        method = index.index_type.upper() if index.index_type else "BTREE"

        # Convert field_names list to comma-separated string
        if isinstance(index.field_names, list):
            fields = ", ".join(index.field_names)
        else:
            fields = index.field_names

        return f"CREATE {unique}INDEX IF NOT EXISTS {index.name} ON {table_name} USING {method} ({fields});"

    def _extract_base_type(self, data_type: str) -> str:
        """Extract base type from data type (e.g., VARCHAR(255) -> VARCHAR)"""
        if '(' in data_type:
            return data_type.split('(')[0].strip().upper()
        return data_type.strip().upper()

    def _types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two SQL types are compatible"""
        # Normalize types
        type1 = self._extract_base_type(type1)
        type2 = self._extract_base_type(type2)

        # Same type
        if type1 == type2:
            return True

        # Compatible type groups
        compatible_groups = [
            {'VARCHAR', 'TEXT', 'CHARACTER VARYING'},
            {'INTEGER', 'INT', 'INT4'},
            {'BIGINT', 'INT8'},
            {'NUMERIC', 'DECIMAL'},
            {'TIMESTAMP', 'TIMESTAMP WITHOUT TIME ZONE'},
        ]

        for group in compatible_groups:
            if type1 in group and type2 in group:
                return True

        return False

    def _escape_sql_string(self, value: str) -> str:
        """Escape single quotes in SQL strings"""
        if value is None:
            return ""
        return str(value).replace("'", "''")

    async def preview_changes(self, entity: EntityDefinition) -> Dict[str, Any]:
        """
        Preview what changes will be made to the database

        Returns a dictionary describing the changes
        """
        table_exists = await self._table_exists(entity.table_name)

        if not table_exists:
            return {
                'operation': 'CREATE',
                'table_name': entity.table_name,
                'changes': {
                    'new_columns': [f.name for f in entity.fields],
                    'new_indexes': [idx.name for idx in entity.indexes if idx.is_active]
                }
            }
        else:
            current_columns = await self._get_current_columns(entity.table_name)
            current_indexes = await self._get_current_indexes(entity.table_name)

            desired_fields = {f.name: f for f in entity.fields}
            desired_indexes = {idx.name: idx for idx in entity.indexes if idx.is_active}

            changes = {
                'added_columns': [name for name in desired_fields if name not in current_columns],
                'removed_columns': [name for name in current_columns if name not in desired_fields and name not in
                                    ['created_at', 'created_by', 'updated_at', 'updated_by',
                                     'is_deleted', 'deleted_at', 'deleted_by', 'id', 'tenant_id']],
                'modified_columns': [],
                'added_indexes': [name for name in desired_indexes if name not in current_indexes],
                'removed_indexes': [name for name in current_indexes if name not in desired_indexes and
                                    not name.endswith('_pkey') and not name.startswith('pg_')]
            }

            # Check for modified columns
            for field_name, field in desired_fields.items():
                if field_name in current_columns:
                    current_type = current_columns[field_name]['data_type']
                    desired_type = self._extract_base_type(field.data_type)
                    if not self._types_compatible(current_type, desired_type):
                        changes['modified_columns'].append({
                            'name': field_name,
                            'from_type': current_type,
                            'to_type': field.data_type
                        })

            return {
                'operation': 'ALTER',
                'table_name': entity.table_name,
                'changes': changes
            }
