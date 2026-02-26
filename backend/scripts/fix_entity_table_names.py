#!/usr/bin/env python3
"""
Fix entity_definitions.table_name records that are missing their module table_prefix.

When an entity is imported from an existing database (or created before module
assignment), the table_name is stored without the module prefix.  The runtime
model generator now applies the prefix on the fly, but this script updates the
stored value in entity_definitions so the database is consistent with what the
runtime produces.

Usage (run from the backend/ directory):
    python scripts/fix_entity_table_names.py [--dry-run]
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.db import SessionLocal
from app.models.data_model import EntityDefinition

DRY_RUN_DEFAULT = True  # safe default; pass --apply to actually write


def main():
    parser = argparse.ArgumentParser(description="Fix entity table_name missing module prefix")
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Actually write updates (default is dry-run / report only)",
    )
    args = parser.parse_args()
    dry_run = not args.apply

    db = SessionLocal()
    try:
        entities = (
            db.query(EntityDefinition)
            .filter(EntityDefinition.module_id.isnot(None))
            .all()
        )

        needs_fix = []
        for entity in entities:
            module = entity.module
            if not module or not module.table_prefix:
                continue
            prefix = module.table_prefix
            if not entity.table_name.startswith(f"{prefix}_"):
                correct_name = f"{prefix}_{entity.table_name}"
                needs_fix.append((entity, correct_name))

        if not needs_fix:
            print("✓ All entity table_names already include their module prefix — nothing to do.")
            return

        print(f"{'DRY RUN — ' if dry_run else ''}Found {len(needs_fix)} entity/ies that need fixing:\n")
        print(f"  {'Entity':<35} {'Module':<20} {'Current table_name':<40} {'Correct table_name'}")
        print(f"  {'-'*35} {'-'*20} {'-'*40} {'-'*40}")

        for entity, correct_name in needs_fix:
            print(f"  {entity.name:<35} {entity.module.name:<20} {entity.table_name:<40} {correct_name}")

        if dry_run:
            print("\nRe-run with --apply to commit these changes.")
        else:
            print()
            for entity, correct_name in needs_fix:
                old_name = entity.table_name
                entity.table_name = correct_name
                print(f"  Updated: {entity.name}  {old_name!r} → {correct_name!r}")
            db.commit()
            print(f"\n✓ Committed {len(needs_fix)} update(s).")
            print("  Restart the backend (or wait for model cache TTL) for the changes to take effect.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
