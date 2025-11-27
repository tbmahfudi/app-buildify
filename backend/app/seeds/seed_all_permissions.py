"""
Master seed script to run all permission seeds
"""
import sys
from seed_organization_permissions import seed_organization_permissions
from seed_rbac_permissions import seed_rbac_permissions
from seed_dashboard_permissions import seed_dashboard_permissions
from seed_report_permissions import seed_report_permissions
from seed_scheduler_permissions import seed_scheduler_permissions
from seed_audit_permissions import seed_audit_permissions
from seed_settings_permissions import seed_settings_permissions

def seed_all_permissions():
    """Run all permission seed scripts"""

    print("\n" + "="*70)
    print("SEEDING ALL PERMISSIONS")
    print("="*70 + "\n")

    try:
        # Seed organization permissions
        print("\n[1/7] Seeding Organization Permissions...")
        print("-" * 70)
        seed_organization_permissions()

        # Seed RBAC permissions
        print("\n[2/7] Seeding RBAC Permissions...")
        print("-" * 70)
        seed_rbac_permissions()

        # Seed dashboard permissions
        print("\n[3/7] Seeding Dashboard Permissions...")
        print("-" * 70)
        seed_dashboard_permissions()

        # Seed report permissions
        print("\n[4/7] Seeding Report Permissions...")
        print("-" * 70)
        seed_report_permissions()

        # Seed scheduler permissions
        print("\n[5/7] Seeding Scheduler Permissions...")
        print("-" * 70)
        seed_scheduler_permissions()

        # Seed audit permissions
        print("\n[6/7] Seeding Audit Permissions...")
        print("-" * 70)
        seed_audit_permissions()

        # Seed settings permissions
        print("\n[7/7] Seeding Settings Permissions...")
        print("-" * 70)
        seed_settings_permissions()

        print("\n" + "="*70)
        print("✅ ALL PERMISSIONS SEEDED SUCCESSFULLY")
        print("="*70)
        print("\nNext steps:")
        print("1. Review the created permissions in the database")
        print("2. Update API endpoints to use these permissions")
        print("3. Create role templates with permission assignments")
        print("4. Test permission enforcement")
        print("\n" + "="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error seeding permissions: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_all_permissions()
