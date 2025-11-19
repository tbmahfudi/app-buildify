#!/usr/bin/env python3
"""
Recalculate tenant usage statistics (current_companies, current_users, current_storage_gb).

This script updates the tenant usage counters based on actual database counts.
Run this after migration or when counters are out of sync.

Usage:
    python scripts/recalculate_tenant_usage.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func
from app.core.db import SessionLocal
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.user import User


def recalculate_tenant_usage():
    """Recalculate usage statistics for all tenants."""
    db = SessionLocal()

    try:
        tenants = db.query(Tenant).all()

        print(f"Found {len(tenants)} tenants to process...")

        for tenant in tenants:
            # Count companies (excluding soft-deleted)
            company_count = db.query(func.count(Company.id)).filter(
                Company.tenant_id == tenant.id,
                Company.deleted_at.is_(None)
            ).scalar() or 0

            # Count users (excluding soft-deleted)
            user_count = db.query(func.count(User.id)).filter(
                User.tenant_id == tenant.id,
                User.deleted_at.is_(None)
            ).scalar() or 0

            # Update tenant
            old_values = {
                'companies': tenant.current_companies,
                'users': tenant.current_users
            }

            tenant.current_companies = company_count
            tenant.current_users = user_count
            # Note: current_storage_gb would require calculating actual storage usage

            print(f"Tenant: {tenant.name} ({tenant.code})")
            print(f"  Companies: {old_values['companies']} → {company_count}")
            print(f"  Users: {old_values['users']} → {user_count}")

        # Commit all changes
        db.commit()
        print(f"\n✓ Successfully updated {len(tenants)} tenants")

    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Recalculating Tenant Usage Statistics")
    print("=" * 60)
    recalculate_tenant_usage()
    print("=" * 60)
