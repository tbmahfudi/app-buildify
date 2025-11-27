"""
Create audit and monitoring permissions
Covers: Audit Logs, System Logs, API Activity, Analytics
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission

def seed_audit_permissions():
    """Seed all audit and monitoring-related permissions"""
    db = SessionLocal()

    try:
        # Define all audit permissions
        permissions = [
            # ==================== AUDIT LOGS ====================
            {
                "code": "audit:read:all",
                "name": "View All Audit Logs",
                "description": "View all audit logs across all tenants (Superuser)",
                "resource": "audit",
                "action": "read",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "audit:read:tenant",
                "name": "View Tenant Audit Logs",
                "description": "View audit logs within tenant",
                "resource": "audit",
                "action": "read",
                "scope": "tenant",
                "category": "audit"
            },
            {
                "code": "audit:read:company",
                "name": "View Company Audit Logs",
                "description": "View audit logs within company",
                "resource": "audit",
                "action": "read",
                "scope": "company",
                "category": "audit"
            },
            {
                "code": "audit:read:department",
                "name": "View Department Audit Logs",
                "description": "View audit logs within department",
                "resource": "audit",
                "action": "read",
                "scope": "department",
                "category": "audit"
            },
            {
                "code": "audit:read:own",
                "name": "View Own Audit Trail",
                "description": "View own audit trail",
                "resource": "audit",
                "action": "read",
                "scope": "own",
                "category": "audit"
            },
            {
                "code": "audit:summary:read:all",
                "name": "View All Audit Summaries",
                "description": "View audit summaries for all tenants (Admin)",
                "resource": "audit",
                "action": "summary:read",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "audit:summary:read:tenant",
                "name": "View Tenant Audit Summary",
                "description": "View audit summary statistics for tenant",
                "resource": "audit",
                "action": "summary:read",
                "scope": "tenant",
                "category": "audit"
            },
            {
                "code": "audit:export:all",
                "name": "Export All Audit Logs",
                "description": "Export all audit logs to files (Admin)",
                "resource": "audit",
                "action": "export",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "audit:export:tenant",
                "name": "Export Tenant Audit Logs",
                "description": "Export tenant audit logs to CSV/JSON",
                "resource": "audit",
                "action": "export",
                "scope": "tenant",
                "category": "audit"
            },
            {
                "code": "audit:delete:all",
                "name": "Delete Audit Logs",
                "description": "Delete old audit logs (Superuser only)",
                "resource": "audit",
                "action": "delete",
                "scope": "all",
                "category": "audit"
            },

            # ==================== SYSTEM LOGS ====================
            {
                "code": "logs:read:all",
                "name": "View System Logs",
                "description": "View application system logs (Superuser only)",
                "resource": "logs",
                "action": "read",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "logs:download:all",
                "name": "Download System Logs",
                "description": "Download system log files (Superuser only)",
                "resource": "logs",
                "action": "download",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "logs:delete:all",
                "name": "Delete System Logs",
                "description": "Delete old system log files (Superuser only)",
                "resource": "logs",
                "action": "delete",
                "scope": "all",
                "category": "audit"
            },

            # ==================== API ACTIVITY ====================
            {
                "code": "api_activity:read:all",
                "name": "View All API Activity",
                "description": "View all API activity logs (Admin)",
                "resource": "api_activity",
                "action": "read",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "api_activity:read:tenant",
                "name": "View Tenant API Activity",
                "description": "View API activity within tenant",
                "resource": "api_activity",
                "action": "read",
                "scope": "tenant",
                "category": "audit"
            },
            {
                "code": "api_activity:read:own",
                "name": "View Own API Activity",
                "description": "View own API activity",
                "resource": "api_activity",
                "action": "read",
                "scope": "own",
                "category": "audit"
            },
            {
                "code": "api_activity:metrics:all",
                "name": "View All API Metrics",
                "description": "View API performance metrics for all tenants (Admin)",
                "resource": "api_activity",
                "action": "metrics",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "api_activity:metrics:tenant",
                "name": "View Tenant API Metrics",
                "description": "View API performance metrics for tenant",
                "resource": "api_activity",
                "action": "metrics",
                "scope": "tenant",
                "category": "audit"
            },

            # ==================== ANALYTICS ====================
            {
                "code": "analytics:read:all",
                "name": "View All Analytics",
                "description": "View analytics for all tenants (Admin)",
                "resource": "analytics",
                "action": "read",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "analytics:read:tenant",
                "name": "View Tenant Analytics",
                "description": "View usage analytics for tenant",
                "resource": "analytics",
                "action": "read",
                "scope": "tenant",
                "category": "audit"
            },
            {
                "code": "analytics:read:company",
                "name": "View Company Analytics",
                "description": "View analytics for company",
                "resource": "analytics",
                "action": "read",
                "scope": "company",
                "category": "audit"
            },
            {
                "code": "analytics:read:department",
                "name": "View Department Analytics",
                "description": "View analytics for department",
                "resource": "analytics",
                "action": "read",
                "scope": "department",
                "category": "audit"
            },
            {
                "code": "analytics:export:all",
                "name": "Export All Analytics",
                "description": "Export analytics data for all tenants (Admin)",
                "resource": "analytics",
                "action": "export",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "analytics:export:tenant",
                "name": "Export Tenant Analytics",
                "description": "Export analytics data to files",
                "resource": "analytics",
                "action": "export",
                "scope": "tenant",
                "category": "audit"
            },

            # ==================== MONITORING ====================
            {
                "code": "monitoring:system:read:all",
                "name": "View System Monitoring",
                "description": "View system health and performance monitoring (Admin)",
                "resource": "monitoring",
                "action": "system:read",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "monitoring:database:read:all",
                "name": "View Database Monitoring",
                "description": "View database performance monitoring (Admin)",
                "resource": "monitoring",
                "action": "database:read",
                "scope": "all",
                "category": "audit"
            },
            {
                "code": "monitoring:alerts:read:all",
                "name": "View System Alerts",
                "description": "View system alerts and notifications (Admin)",
                "resource": "monitoring",
                "action": "alerts:read",
                "scope": "all",
                "category": "audit"
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
        print(f"Audit & Monitoring Permissions Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} permissions")
        print(f"• Updated: {updated_count} permissions")
        print(f"📊 Total: {len(permissions)} audit permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_audit_permissions()
