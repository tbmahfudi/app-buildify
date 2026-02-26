#!/usr/bin/env python3
"""
Diagnose primary-key mismatches between entity_definitions and actual database tables.

For each published entity, this script checks:
  1. What table_name the runtime model generator will use (with module prefix applied)
  2. Whether that table exists in the database
  3. What the real PK column is in the database
  4. Whether the entity has a field whose name matches the PK (so it won't get
     a phantom 'id' column added and won't silently create without a PK)

Usage (run from the backend/ directory):
    python scripts/diagnose_entity_pk.py [entity_name]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.db import SessionLocal
from app.models.data_model import EntityDefinition


def get_table_columns(db, table_name, schema="public"):
    rows = db.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=:s AND table_name=:t ORDER BY ordinal_position"
    ), {"s": schema, "t": table_name}).fetchall()
    return rows


def get_pk_columns(db, table_name, schema="public"):
    rows = db.execute(text("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name=kcu.constraint_name
           AND tc.table_schema=kcu.table_schema
           AND tc.table_name=kcu.table_name
        WHERE tc.constraint_type='PRIMARY KEY'
          AND tc.table_schema=:s AND tc.table_name=:t
        ORDER BY kcu.ordinal_position
    """), {"s": schema, "t": table_name}).fetchall()
    return [r[0] for r in rows]


def resolve_table_name(entity):
    """Mirror _entity_to_dict module prefix logic."""
    table_name = entity.table_name
    if entity.module_id and entity.module and entity.module.table_prefix:
        prefix = entity.module.table_prefix
        if not table_name.startswith(f"{prefix}_"):
            table_name = f"{prefix}_{table_name}"
    return table_name


def main():
    filter_name = sys.argv[1] if len(sys.argv) > 1 else None

    db = SessionLocal()
    try:
        query = db.query(EntityDefinition).filter(EntityDefinition.status == "published")
        if filter_name:
            query = query.filter(EntityDefinition.name == filter_name)

        entities = query.order_by(EntityDefinition.name).all()

        if not entities:
            print(f"No published entities found{f' matching {filter_name!r}' if filter_name else ''}.")
            return

        issues = []

        for entity in entities:
            schema = entity.schema_name or "public"
            stored_table = entity.table_name
            resolved_table = resolve_table_name(entity)

            # Get field names (to check PK field existence)
            field_names = {f.name for f in entity.fields}

            # Check actual DB
            db_cols = get_table_columns(db, resolved_table, schema)
            db_pk = get_pk_columns(db, resolved_table, schema)

            table_exists = len(db_cols) > 0
            db_col_names = {r[0] for r in db_cols}
            has_id_col = "id" in db_col_names
            has_id_field = "id" in field_names

            problems = []
            if not table_exists:
                problems.append(f"table '{schema}.{resolved_table}' does not exist in DB")
            if table_exists and not db_pk:
                problems.append("no PRIMARY KEY constraint found")
            if table_exists and db_pk and "id" not in db_pk and not any(f in field_names for f in db_pk):
                problems.append(
                    f"PK column '{db_pk[0]}' is not defined as a field in entity_definitions — "
                    "runtime will fall back to DB introspection (OK) but field won't have uuid4 default"
                )
            if stored_table != resolved_table:
                problems.append(f"stored table_name '{stored_table}' missing module prefix; "
                                 f"runtime uses '{resolved_table}' (run fix_entity_table_names.py --apply)")

            status = "ISSUE" if problems else "OK"
            issues.append((entity.name, resolved_table, db_pk, problems, status))

        print(f"\n{'Entity':<35} {'Table':<45} {'DB PK':<20} Status")
        print(f"{'─'*35} {'─'*45} {'─'*20} {'─'*6}")
        for name, table, pk, problems, status in issues:
            print(f"{name:<35} {table:<45} {', '.join(pk) or '?':<20} {status}")
            for p in problems:
                print(f"  {'':35} ↳ {p}")

        n_issues = sum(1 for *_, s in issues if s == "ISSUE")
        print(f"\n{len(issues)} entities checked, {n_issues} with issues.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
