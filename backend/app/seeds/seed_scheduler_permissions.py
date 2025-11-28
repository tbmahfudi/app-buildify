"""
Create scheduler management permissions
Covers: Scheduler Configuration, Jobs, Executions
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission

def seed_scheduler_permissions():
    """Seed all scheduler-related permissions"""
    db = SessionLocal()

    try:
        # Define all scheduler permissions
        permissions = [
            # ==================== SCHEDULER CONFIGURATION ====================
            {
                "code": "scheduler:config:read:all",
                "name": "View All Scheduler Configs",
                "description": "View all scheduler configurations (Admin)",
                "resource": "scheduler",
                "action": "config:read",
                "scope": "all",
                "category": "scheduler"
            },
            {
                "code": "scheduler:config:read:tenant",
                "name": "View Tenant Scheduler Config",
                "description": "View scheduler configuration for tenant",
                "resource": "scheduler",
                "action": "config:read",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:config:create:tenant",
                "name": "Create Scheduler Config",
                "description": "Create scheduler configuration",
                "resource": "scheduler",
                "action": "config:create",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:config:update:tenant",
                "name": "Update Scheduler Config",
                "description": "Update scheduler configuration",
                "resource": "scheduler",
                "action": "config:update",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:config:delete:tenant",
                "name": "Delete Scheduler Config",
                "description": "Delete scheduler configuration",
                "resource": "scheduler",
                "action": "config:delete",
                "scope": "tenant",
                "category": "scheduler"
            },

            # ==================== SCHEDULED JOBS ====================
            {
                "code": "scheduler:jobs:read:all",
                "name": "View All Scheduled Jobs",
                "description": "View all scheduled jobs across all tenants (Admin)",
                "resource": "scheduler",
                "action": "jobs:read",
                "scope": "all",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:read:tenant",
                "name": "View Tenant Scheduled Jobs",
                "description": "View all scheduled jobs within tenant",
                "resource": "scheduler",
                "action": "jobs:read",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:read:own",
                "name": "View Own Scheduled Jobs",
                "description": "View own scheduled jobs",
                "resource": "scheduler",
                "action": "jobs:read",
                "scope": "own",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:create:tenant",
                "name": "Create Scheduled Jobs",
                "description": "Create new scheduled jobs",
                "resource": "scheduler",
                "action": "jobs:create",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:update:all",
                "name": "Update Any Scheduled Job",
                "description": "Update any scheduled job (Admin)",
                "resource": "scheduler",
                "action": "jobs:update",
                "scope": "all",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:update:tenant",
                "name": "Update Tenant Scheduled Jobs",
                "description": "Update scheduled jobs within tenant",
                "resource": "scheduler",
                "action": "jobs:update",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:update:own",
                "name": "Update Own Scheduled Jobs",
                "description": "Update own scheduled jobs",
                "resource": "scheduler",
                "action": "jobs:update",
                "scope": "own",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:delete:all",
                "name": "Delete Any Scheduled Job",
                "description": "Delete any scheduled job (Admin)",
                "resource": "scheduler",
                "action": "jobs:delete",
                "scope": "all",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:delete:tenant",
                "name": "Delete Tenant Scheduled Jobs",
                "description": "Delete scheduled jobs within tenant",
                "resource": "scheduler",
                "action": "jobs:delete",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:delete:own",
                "name": "Delete Own Scheduled Jobs",
                "description": "Delete own scheduled jobs",
                "resource": "scheduler",
                "action": "jobs:delete",
                "scope": "own",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:execute:all",
                "name": "Execute Any Scheduled Job",
                "description": "Manually execute any scheduled job (Admin)",
                "resource": "scheduler",
                "action": "jobs:execute",
                "scope": "all",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:execute:tenant",
                "name": "Execute Tenant Scheduled Jobs",
                "description": "Manually execute scheduled jobs within tenant",
                "resource": "scheduler",
                "action": "jobs:execute",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:jobs:execute:own",
                "name": "Execute Own Scheduled Jobs",
                "description": "Manually execute own scheduled jobs",
                "resource": "scheduler",
                "action": "jobs:execute",
                "scope": "own",
                "category": "scheduler"
            },

            # ==================== JOB EXECUTIONS & HISTORY ====================
            {
                "code": "scheduler:executions:read:all",
                "name": "View All Job Executions",
                "description": "View all job execution history (Admin)",
                "resource": "scheduler",
                "action": "executions:read",
                "scope": "all",
                "category": "scheduler"
            },
            {
                "code": "scheduler:executions:read:tenant",
                "name": "View Tenant Job Executions",
                "description": "View job execution history within tenant",
                "resource": "scheduler",
                "action": "executions:read",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:executions:read:own",
                "name": "View Own Job Executions",
                "description": "View own job execution history",
                "resource": "scheduler",
                "action": "executions:read",
                "scope": "own",
                "category": "scheduler"
            },
            {
                "code": "scheduler:executions:cancel:all",
                "name": "Cancel Any Running Job",
                "description": "Cancel any running job execution (Admin)",
                "resource": "scheduler",
                "action": "executions:cancel",
                "scope": "all",
                "category": "scheduler"
            },
            {
                "code": "scheduler:executions:cancel:tenant",
                "name": "Cancel Tenant Running Jobs",
                "description": "Cancel running job executions within tenant",
                "resource": "scheduler",
                "action": "executions:cancel",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:executions:cancel:own",
                "name": "Cancel Own Running Jobs",
                "description": "Cancel own running job executions",
                "resource": "scheduler",
                "action": "executions:cancel",
                "scope": "own",
                "category": "scheduler"
            },

            # ==================== LEGACY SCHEDULER PERMISSIONS ====================
            {
                "code": "scheduler:read:tenant",
                "name": "View Scheduler (Legacy)",
                "description": "View scheduler - legacy permission for frontend compatibility",
                "resource": "scheduler",
                "action": "read",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:create:tenant",
                "name": "Create Scheduler Jobs (Legacy)",
                "description": "Create scheduler jobs - legacy permission for frontend compatibility",
                "resource": "scheduler",
                "action": "create",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:update:tenant",
                "name": "Update Scheduler Jobs (Legacy)",
                "description": "Update scheduler jobs - legacy permission for frontend compatibility",
                "resource": "scheduler",
                "action": "update",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:delete:tenant",
                "name": "Delete Scheduler Jobs (Legacy)",
                "description": "Delete scheduler jobs - legacy permission for frontend compatibility",
                "resource": "scheduler",
                "action": "delete",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:execute:tenant",
                "name": "Execute Scheduler Jobs (Legacy)",
                "description": "Execute scheduler jobs - legacy permission for frontend compatibility",
                "resource": "scheduler",
                "action": "execute",
                "scope": "tenant",
                "category": "scheduler"
            },
            {
                "code": "scheduler:history:read:tenant",
                "name": "View Scheduler History (Legacy)",
                "description": "View scheduler history - legacy permission for frontend compatibility",
                "resource": "scheduler",
                "action": "history:read",
                "scope": "tenant",
                "category": "scheduler"
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
        print(f"Scheduler Permissions Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} permissions")
        print(f"• Updated: {updated_count} permissions")
        print(f"📊 Total: {len(permissions)} scheduler permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_scheduler_permissions()
