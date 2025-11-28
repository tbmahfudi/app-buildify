"""
Master seed script to run all permission seeds and role templates
"""
import sys
from .seed_organization_permissions import seed_organization_permissions
from .seed_rbac_permissions import seed_rbac_permissions
from .seed_dashboard_permissions import seed_dashboard_permissions
from .seed_report_permissions import seed_report_permissions
from .seed_scheduler_permissions import seed_scheduler_permissions
from .seed_audit_permissions import seed_audit_permissions
from .seed_settings_permissions import seed_settings_permissions
from .seed_role_templates import seed_role_templates

def seed_all_permissions():
    """Run all permission seed scripts and create role templates"""

    print("\n" + "="*70)
    print("SEEDING ALL PERMISSIONS AND ROLE TEMPLATES")
    print("="*70 + "\n")

    try:
        # Seed organization permissions
        print("\n[1/8] Seeding Organization Permissions...")
        print("-" * 70)
        seed_organization_permissions()

        # Seed RBAC permissions
        print("\n[2/8] Seeding RBAC Permissions...")
        print("-" * 70)
        seed_rbac_permissions()

        # Seed dashboard permissions
        print("\n[3/8] Seeding Dashboard Permissions...")
        print("-" * 70)
        seed_dashboard_permissions()

        # Seed report permissions
        print("\n[4/8] Seeding Report Permissions...")
        print("-" * 70)
        seed_report_permissions()

        # Seed scheduler permissions
        print("\n[5/8] Seeding Scheduler Permissions...")
        print("-" * 70)
        seed_scheduler_permissions()

        # Seed audit permissions
        print("\n[6/8] Seeding Audit Permissions...")
        print("-" * 70)
        seed_audit_permissions()

        # Seed settings permissions
        print("\n[7/8] Seeding Settings Permissions...")
        print("-" * 70)
        seed_settings_permissions()

        # Seed role templates with permission assignments
        print("\n[8/8] Seeding Role Templates...")
        print("-" * 70)
        seed_role_templates()

        print("\n" + "="*70)
        print("✅ ALL PERMISSIONS AND ROLE TEMPLATES SEEDED SUCCESSFULLY")
        print("="*70)
        print("\nNext steps:")
        print("1. Review the created permissions and roles in the database")
        print("2. Assign roles to users")
        print("3. Update API endpoints to use these permissions")
        print("4. Test permission enforcement")
        print("\n" + "="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error seeding permissions: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_all_permissions()
