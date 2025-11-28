"""
Create dashboard management permissions
Covers: Dashboards, Pages, Widgets, Shares, Snapshots
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission

def seed_dashboard_permissions():
    """Seed all dashboard-related permissions"""
    db = SessionLocal()

    try:
        # Define all dashboard permissions
        permissions = [
            # ==================== DASHBOARD MANAGEMENT ====================
            {
                "code": "dashboards:read:all",
                "name": "View All Dashboards",
                "description": "View all dashboards across all tenants (Admin)",
                "resource": "dashboards",
                "action": "read",
                "scope": "all",
                "category": "dashboard"
            },
            {
                "code": "dashboards:read:tenant",
                "name": "View Tenant Dashboards",
                "description": "View all dashboards within tenant",
                "resource": "dashboards",
                "action": "read",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:read:own",
                "name": "View Own Dashboards",
                "description": "View own dashboards",
                "resource": "dashboards",
                "action": "read",
                "scope": "own",
                "category": "dashboard"
            },
            {
                "code": "dashboards:create:tenant",
                "name": "Create Dashboards",
                "description": "Create new dashboards",
                "resource": "dashboards",
                "action": "create",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:update:all",
                "name": "Update Any Dashboard",
                "description": "Update any dashboard (Admin)",
                "resource": "dashboards",
                "action": "update",
                "scope": "all",
                "category": "dashboard"
            },
            {
                "code": "dashboards:update:tenant",
                "name": "Update Tenant Dashboards",
                "description": "Update dashboards within tenant",
                "resource": "dashboards",
                "action": "update",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:update:own",
                "name": "Update Own Dashboards",
                "description": "Update own dashboards",
                "resource": "dashboards",
                "action": "update",
                "scope": "own",
                "category": "dashboard"
            },
            {
                "code": "dashboards:delete:all",
                "name": "Delete Any Dashboard",
                "description": "Delete any dashboard (Admin)",
                "resource": "dashboards",
                "action": "delete",
                "scope": "all",
                "category": "dashboard"
            },
            {
                "code": "dashboards:delete:tenant",
                "name": "Delete Tenant Dashboards",
                "description": "Delete dashboards within tenant",
                "resource": "dashboards",
                "action": "delete",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:delete:own",
                "name": "Delete Own Dashboards",
                "description": "Delete own dashboards",
                "resource": "dashboards",
                "action": "delete",
                "scope": "own",
                "category": "dashboard"
            },
            {
                "code": "dashboards:clone:tenant",
                "name": "Clone Dashboards",
                "description": "Clone existing dashboards",
                "resource": "dashboards",
                "action": "clone",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:share:tenant",
                "name": "Share Dashboards",
                "description": "Share dashboards with other users",
                "resource": "dashboards",
                "action": "share",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:snapshot:tenant",
                "name": "Create Dashboard Snapshots",
                "description": "Create snapshots of dashboards",
                "resource": "dashboards",
                "action": "snapshot",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:export:tenant",
                "name": "Export Dashboards",
                "description": "Export dashboards to PDF/image",
                "resource": "dashboards",
                "action": "export",
                "scope": "tenant",
                "category": "dashboard"
            },

            # ==================== DASHBOARD PAGES ====================
            {
                "code": "dashboards:create_page:tenant",
                "name": "Create Dashboard Pages",
                "description": "Create new pages within dashboards",
                "resource": "dashboards",
                "action": "create_page",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:update_page:all",
                "name": "Update Any Dashboard Page",
                "description": "Update any dashboard page (Admin)",
                "resource": "dashboards",
                "action": "update_page",
                "scope": "all",
                "category": "dashboard"
            },
            {
                "code": "dashboards:update_page:own",
                "name": "Update Own Dashboard Pages",
                "description": "Update pages in own dashboards",
                "resource": "dashboards",
                "action": "update_page",
                "scope": "own",
                "category": "dashboard"
            },
            {
                "code": "dashboards:delete_page:all",
                "name": "Delete Any Dashboard Page",
                "description": "Delete any dashboard page (Admin)",
                "resource": "dashboards",
                "action": "delete_page",
                "scope": "all",
                "category": "dashboard"
            },
            {
                "code": "dashboards:delete_page:own",
                "name": "Delete Own Dashboard Pages",
                "description": "Delete pages in own dashboards",
                "resource": "dashboards",
                "action": "delete_page",
                "scope": "own",
                "category": "dashboard"
            },

            # ==================== DASHBOARD WIDGETS ====================
            {
                "code": "dashboards:create_widget:tenant",
                "name": "Create Dashboard Widgets",
                "description": "Create new widgets in dashboards",
                "resource": "dashboards",
                "action": "create_widget",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboards:update_widget:all",
                "name": "Update Any Dashboard Widget",
                "description": "Update any dashboard widget (Admin)",
                "resource": "dashboards",
                "action": "update_widget",
                "scope": "all",
                "category": "dashboard"
            },
            {
                "code": "dashboards:update_widget:own",
                "name": "Update Own Dashboard Widgets",
                "description": "Update widgets in own dashboards",
                "resource": "dashboards",
                "action": "update_widget",
                "scope": "own",
                "category": "dashboard"
            },
            {
                "code": "dashboards:delete_widget:all",
                "name": "Delete Any Dashboard Widget",
                "description": "Delete any dashboard widget (Admin)",
                "resource": "dashboards",
                "action": "delete_widget",
                "scope": "all",
                "category": "dashboard"
            },
            {
                "code": "dashboards:delete_widget:own",
                "name": "Delete Own Dashboard Widgets",
                "description": "Delete widgets in own dashboards",
                "resource": "dashboards",
                "action": "delete_widget",
                "scope": "own",
                "category": "dashboard"
            },

            # ==================== LEGACY DASHBOARD PERMISSIONS ====================
            {
                "code": "dashboard:view:tenant",
                "name": "View Dashboard (Legacy)",
                "description": "View dashboard - legacy permission for frontend compatibility",
                "resource": "dashboard",
                "action": "view",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboard:edit:own",
                "name": "Edit Own Dashboard (Legacy)",
                "description": "Edit own dashboard - legacy permission for frontend compatibility",
                "resource": "dashboard",
                "action": "edit",
                "scope": "own",
                "category": "dashboard"
            },
            {
                "code": "dashboard:edit:tenant",
                "name": "Edit Dashboard (Legacy)",
                "description": "Edit dashboards - legacy permission for frontend compatibility",
                "resource": "dashboard",
                "action": "edit",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboard:create:tenant",
                "name": "Create Dashboard (Legacy)",
                "description": "Create dashboards - legacy permission for frontend compatibility",
                "resource": "dashboard",
                "action": "create",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboard:delete:tenant",
                "name": "Delete Dashboard (Legacy)",
                "description": "Delete dashboards - legacy permission for frontend compatibility",
                "resource": "dashboard",
                "action": "delete",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboard:share:tenant",
                "name": "Share Dashboard (Legacy)",
                "description": "Share dashboards - legacy permission for frontend compatibility",
                "resource": "dashboard",
                "action": "share",
                "scope": "tenant",
                "category": "dashboard"
            },
            {
                "code": "dashboard:export:tenant",
                "name": "Export Dashboard (Legacy)",
                "description": "Export dashboards - legacy permission for frontend compatibility",
                "resource": "dashboard",
                "action": "export",
                "scope": "tenant",
                "category": "dashboard"
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
        print(f"Dashboard Permissions Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} permissions")
        print(f"• Updated: {updated_count} permissions")
        print(f"📊 Total: {len(permissions)} dashboard permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_dashboard_permissions()
