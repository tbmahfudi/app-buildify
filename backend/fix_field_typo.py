#!/usr/bin/env python3
"""
Fix typo in field_definitions table: is_acrive -> is_active
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_typo():
    """Fix the is_acrive typo in field_definitions"""
    db_url = settings.SQLALCHEMY_DATABASE_URL
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Check if the typo exists
        result = conn.execute(text(
            "SELECT id, name, entity_id FROM field_definitions WHERE name = 'is_acrive'"
        ))
        rows = result.fetchall()

        if rows:
            print(f"Found {len(rows)} field(s) with typo 'is_acrive':")
            for row in rows:
                print(f"  - ID: {row[0]}, Entity ID: {row[2]}")

            # Fix the typo
            conn.execute(text(
                "UPDATE field_definitions SET name = 'is_active' WHERE name = 'is_acrive'"
            ))
            conn.commit()
            print("\nFixed: Updated 'is_acrive' to 'is_active'")
        else:
            print("No typo found - 'is_acrive' not present in field_definitions")

if __name__ == "__main__":
    fix_typo()
