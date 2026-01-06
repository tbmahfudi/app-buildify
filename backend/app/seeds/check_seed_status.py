"""
Diagnostic script to check tenant data and seed status

Run: python -m app.seeds.check_seed_status
"""

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.data_model import EntityDefinition
from app.models.workflow import WorkflowDefinition
from app.models.automation import AutomationRule
from app.models.lookup import LookupConfiguration


def check_seed_status():
    """Check which tenants have sample data."""
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("SEED DATA DIAGNOSTIC")
        print("="*80 + "\n")

        # List all tenants
        tenants = db.query(Tenant).filter(
            Tenant.is_active == True,
            Tenant.deleted_at == None
        ).all()

        print(f"📋 Found {len(tenants)} active tenant(s):\n")

        for tenant in tenants:
            print(f"Tenant: {tenant.name} (code: {tenant.code})")
            print(f"  ID: {tenant.id}")

            # Count users
            user_count = db.query(User).filter(
                User.tenant_id == tenant.id,
                User.is_active == True
            ).count()
            print(f"  Users: {user_count}")

            # Check for sysadmin
            sysadmin = db.query(User).filter(
                User.tenant_id == tenant.id,
                User.is_superuser == True,
                User.is_active == True
            ).first()
            if sysadmin:
                print(f"  ⭐ Sysadmin: {sysadmin.email}")

            # Count sample data
            entity_count = db.query(EntityDefinition).filter(
                EntityDefinition.tenant_id == tenant.id,
                EntityDefinition.is_deleted == False
            ).count()

            workflow_count = db.query(WorkflowDefinition).filter(
                WorkflowDefinition.tenant_id == tenant.id,
                WorkflowDefinition.is_deleted == False
            ).count()

            automation_count = db.query(AutomationRule).filter(
                AutomationRule.tenant_id == tenant.id,
                AutomationRule.is_deleted == False
            ).count()

            lookup_count = db.query(LookupConfiguration).filter(
                LookupConfiguration.tenant_id == tenant.id,
                LookupConfiguration.is_deleted == False
            ).count()

            print(f"\n  Sample Data:")
            print(f"    Entities: {entity_count}")
            print(f"    Workflows: {workflow_count}")
            print(f"    Automations: {automation_count}")
            print(f"    Lookups: {lookup_count}")

            if entity_count > 0:
                entities = db.query(EntityDefinition).filter(
                    EntityDefinition.tenant_id == tenant.id,
                    EntityDefinition.is_deleted == False
                ).all()
                print(f"    Entity names: {', '.join([e.name for e in entities])}")

            print()

        print("="*80)
        print("RECOMMENDATION")
        print("="*80 + "\n")

        # Find tenant with sysadmin
        sysadmin_tenant = None
        for tenant in tenants:
            sysadmin = db.query(User).filter(
                User.tenant_id == tenant.id,
                User.is_superuser == True,
                User.is_active == True
            ).first()
            if sysadmin:
                sysadmin_tenant = tenant
                break

        if sysadmin_tenant:
            entity_count = db.query(EntityDefinition).filter(
                EntityDefinition.tenant_id == sysadmin_tenant.id,
                EntityDefinition.is_deleted == False
            ).count()

            if entity_count == 0:
                print(f"❌ No sample data found for sysadmin's tenant: {sysadmin_tenant.name}")
                print(f"\nTo seed data for the sysadmin tenant, run:")
                print(f"  python -m app.seeds.seed_for_tenant {sysadmin_tenant.code}")
                print(f"\nOr manually specify tenant ID in seed_nocode_samples.py")
            else:
                print(f"✅ Sample data exists for sysadmin's tenant: {sysadmin_tenant.name}")
        else:
            print("⚠️  No sysadmin user found")

        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_seed_status()
