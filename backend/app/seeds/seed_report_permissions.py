"""
Create report management permissions
Covers: Report Definitions, Execution, Scheduling, Templates
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission

def seed_report_permissions():
    """Seed all report-related permissions"""
    db = SessionLocal()

    try:
        # Define all report permissions
        permissions = [
            # ==================== REPORT DEFINITION MANAGEMENT ====================
            {
                "code": "reports:read:all",
                "name": "View All Reports",
                "description": "View all reports across all tenants (Admin)",
                "resource": "reports",
                "action": "read",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:read:tenant",
                "name": "View Tenant Reports",
                "description": "View all reports within tenant",
                "resource": "reports",
                "action": "read",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:read:company",
                "name": "View Company Reports",
                "description": "View reports within company",
                "resource": "reports",
                "action": "read",
                "scope": "company",
                "category": "reports"
            },
            {
                "code": "reports:read:department",
                "name": "View Department Reports",
                "description": "View reports within department",
                "resource": "reports",
                "action": "read",
                "scope": "department",
                "category": "reports"
            },
            {
                "code": "reports:read:own",
                "name": "View Own Reports",
                "description": "View own reports",
                "resource": "reports",
                "action": "read",
                "scope": "own",
                "category": "reports"
            },
            {
                "code": "reports:create:tenant",
                "name": "Create Reports",
                "description": "Create new report definitions",
                "resource": "reports",
                "action": "create",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:update:all",
                "name": "Update Any Report",
                "description": "Update any report definition (Admin)",
                "resource": "reports",
                "action": "update",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:update:tenant",
                "name": "Update Tenant Reports",
                "description": "Update reports within tenant",
                "resource": "reports",
                "action": "update",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:update:own",
                "name": "Update Own Reports",
                "description": "Update own report definitions",
                "resource": "reports",
                "action": "update",
                "scope": "own",
                "category": "reports"
            },
            {
                "code": "reports:delete:all",
                "name": "Delete Any Report",
                "description": "Delete any report (Admin)",
                "resource": "reports",
                "action": "delete",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:delete:tenant",
                "name": "Delete Tenant Reports",
                "description": "Delete reports within tenant",
                "resource": "reports",
                "action": "delete",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:delete:own",
                "name": "Delete Own Reports",
                "description": "Delete own reports",
                "resource": "reports",
                "action": "delete",
                "scope": "own",
                "category": "reports"
            },

            # ==================== REPORT EXECUTION ====================
            {
                "code": "reports:execute:all",
                "name": "Execute Any Report",
                "description": "Execute any report (Admin)",
                "resource": "reports",
                "action": "execute",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:execute:tenant",
                "name": "Execute Tenant Reports",
                "description": "Execute reports within tenant",
                "resource": "reports",
                "action": "execute",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:execute:company",
                "name": "Execute Company Reports",
                "description": "Execute reports within company",
                "resource": "reports",
                "action": "execute",
                "scope": "company",
                "category": "reports"
            },
            {
                "code": "reports:execute:department",
                "name": "Execute Department Reports",
                "description": "Execute reports within department",
                "resource": "reports",
                "action": "execute",
                "scope": "department",
                "category": "reports"
            },
            {
                "code": "reports:execute:own",
                "name": "Execute Own Reports",
                "description": "Execute own reports",
                "resource": "reports",
                "action": "execute",
                "scope": "own",
                "category": "reports"
            },
            {
                "code": "reports:run:tenant",
                "name": "Run Reports (Legacy)",
                "description": "Run reports - legacy permission for frontend compatibility",
                "resource": "reports",
                "action": "run",
                "scope": "tenant",
                "category": "reports"
            },

            # ==================== REPORT EXPORT ====================
            {
                "code": "reports:export:all",
                "name": "Export Any Report",
                "description": "Export any report to PDF/CSV/Excel (Admin)",
                "resource": "reports",
                "action": "export",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:export:tenant",
                "name": "Export Tenant Reports",
                "description": "Export reports to PDF/CSV/Excel",
                "resource": "reports",
                "action": "export",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:export:company",
                "name": "Export Company Reports",
                "description": "Export company reports to files",
                "resource": "reports",
                "action": "export",
                "scope": "company",
                "category": "reports"
            },
            {
                "code": "reports:export:department",
                "name": "Export Department Reports",
                "description": "Export department reports to files",
                "resource": "reports",
                "action": "export",
                "scope": "department",
                "category": "reports"
            },

            # ==================== REPORT EXECUTION HISTORY ====================
            {
                "code": "reports:history:read:all",
                "name": "View All Report History",
                "description": "View all report execution history (Admin)",
                "resource": "reports",
                "action": "history:read",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:history:read:tenant",
                "name": "View Tenant Report History",
                "description": "View report execution history within tenant",
                "resource": "reports",
                "action": "history:read",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:history:read:own",
                "name": "View Own Report History",
                "description": "View own report execution history",
                "resource": "reports",
                "action": "history:read",
                "scope": "own",
                "category": "reports"
            },

            # ==================== REPORT SCHEDULING ====================
            {
                "code": "reports:schedule:create:all",
                "name": "Create Any Report Schedule",
                "description": "Create schedule for any report (Admin)",
                "resource": "reports",
                "action": "schedule:create",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:schedule:create:tenant",
                "name": "Create Report Schedules",
                "description": "Create report schedules within tenant",
                "resource": "reports",
                "action": "schedule:create",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:schedule:read:all",
                "name": "View All Report Schedules",
                "description": "View all report schedules (Admin)",
                "resource": "reports",
                "action": "schedule:read",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:schedule:read:tenant",
                "name": "View Tenant Report Schedules",
                "description": "View report schedules within tenant",
                "resource": "reports",
                "action": "schedule:read",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:schedule:read:own",
                "name": "View Own Report Schedules",
                "description": "View own report schedules",
                "resource": "reports",
                "action": "schedule:read",
                "scope": "own",
                "category": "reports"
            },
            {
                "code": "reports:schedule:update:all",
                "name": "Update Any Report Schedule",
                "description": "Update any report schedule (Admin)",
                "resource": "reports",
                "action": "schedule:update",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:schedule:update:tenant",
                "name": "Update Tenant Report Schedules",
                "description": "Update report schedules within tenant",
                "resource": "reports",
                "action": "schedule:update",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:schedule:update:own",
                "name": "Update Own Report Schedules",
                "description": "Update own report schedules",
                "resource": "reports",
                "action": "schedule:update",
                "scope": "own",
                "category": "reports"
            },
            {
                "code": "reports:schedule:delete:all",
                "name": "Delete Any Report Schedule",
                "description": "Delete any report schedule (Admin)",
                "resource": "reports",
                "action": "schedule:delete",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:schedule:delete:tenant",
                "name": "Delete Tenant Report Schedules",
                "description": "Delete report schedules within tenant",
                "resource": "reports",
                "action": "schedule:delete",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:schedule:delete:own",
                "name": "Delete Own Report Schedules",
                "description": "Delete own report schedules",
                "resource": "reports",
                "action": "schedule:delete",
                "scope": "own",
                "category": "reports"
            },
            {
                "code": "reports:schedule:tenant",
                "name": "Schedule Reports (Legacy)",
                "description": "Schedule reports - legacy permission for frontend compatibility",
                "resource": "reports",
                "action": "schedule",
                "scope": "tenant",
                "category": "reports"
            },

            # ==================== REPORT TEMPLATES ====================
            {
                "code": "reports:templates:read:all",
                "name": "View All Report Templates",
                "description": "View all report templates (Admin)",
                "resource": "reports",
                "action": "templates:read",
                "scope": "all",
                "category": "reports"
            },
            {
                "code": "reports:templates:read:tenant",
                "name": "View Tenant Report Templates",
                "description": "View report templates within tenant",
                "resource": "reports",
                "action": "templates:read",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:templates:create:tenant",
                "name": "Create Report Templates",
                "description": "Create new report templates",
                "resource": "reports",
                "action": "templates:create",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:templates:update:tenant",
                "name": "Update Report Templates",
                "description": "Update report templates",
                "resource": "reports",
                "action": "templates:update",
                "scope": "tenant",
                "category": "reports"
            },
            {
                "code": "reports:templates:delete:tenant",
                "name": "Delete Report Templates",
                "description": "Delete report templates",
                "resource": "reports",
                "action": "templates:delete",
                "scope": "tenant",
                "category": "reports"
            },

            # ==================== REPORT SHARING ====================
            {
                "code": "reports:share:tenant",
                "name": "Share Reports",
                "description": "Share reports with other users",
                "resource": "reports",
                "action": "share",
                "scope": "tenant",
                "category": "reports"
            },
        ]

        # Create permissions
        created_count = 0
        updated_count = 0

        for perm_data in permissions:
            perm = db.query(Permission).filter(
                Permission.code == perm_data["code"]
            ).first()

            if not perm:
                perm = Permission(**perm_data, is_active=True)
                db.add(perm)
                db.flush()
                print(f"✓ Created: {perm_data['code']}")
                created_count += 1
            else:
                # Update existing permission details
                for key, value in perm_data.items():
                    setattr(perm, key, value)
                perm.is_active = True
                print(f"• Updated: {perm_data['code']}")
                updated_count += 1

        db.commit()

        print(f"\n{'='*60}")
        print(f"Report Permissions Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} permissions")
        print(f"• Updated: {updated_count} permissions")
        print(f"📊 Total: {len(permissions)} report permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_report_permissions()
