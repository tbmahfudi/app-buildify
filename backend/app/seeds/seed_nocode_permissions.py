"""
Seed No-Code Platform Permissions
==================================
Creates granular permissions for platform-level and tenant-level no-code management.

Run: python -m app.seeds.seed_nocode_permissions
"""

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.base import generate_uuid
from datetime import datetime


def seed_nocode_permissions(db: Session):
    """Seed permissions for no-code platform features."""
    print("\n" + "="*80)
    print("NO-CODE PLATFORM PERMISSIONS")
    print("="*80 + "\n")

    permissions = [
        # ==================== Data Model Designer ====================
        {
            "code": "data_model:create:platform",
            "name": "Create Platform-Level Data Models",
            "description": "Create data model templates available to all tenants",
            "resource": "data_model",
            "action": "create",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:create:tenant",
            "name": "Create Tenant Data Models",
            "description": "Create tenant-specific data models",
            "resource": "data_model",
            "action": "create",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "data_model:read:platform",
            "name": "View Platform-Level Data Models",
            "description": "View platform-level data model templates",
            "resource": "data_model",
            "action": "read",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:read:tenant",
            "name": "View Tenant Data Models",
            "description": "View tenant-specific data models",
            "resource": "data_model",
            "action": "read",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "data_model:update:platform",
            "name": "Update Platform-Level Data Models",
            "description": "Modify platform-level data model templates",
            "resource": "data_model",
            "action": "update",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:update:tenant",
            "name": "Update Tenant Data Models",
            "description": "Modify tenant-specific data models",
            "resource": "data_model",
            "action": "update",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "data_model:delete:platform",
            "name": "Delete Platform-Level Data Models",
            "description": "Delete platform-level data model templates",
            "resource": "data_model",
            "action": "delete",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:delete:tenant",
            "name": "Delete Tenant Data Models",
            "description": "Delete tenant-specific data models",
            "resource": "data_model",
            "action": "delete",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "data_model:clone:platform",
            "name": "Clone Platform Data Models",
            "description": "Clone platform templates to tenant-specific versions",
            "resource": "data_model",
            "action": "clone",
            "scope": "platform",
            "category": "nocode",
            "is_system": True
        },

        # ==================== Workflow Designer ====================
        {
            "code": "workflow:create:platform",
            "name": "Create Platform-Level Workflows",
            "description": "Create workflow templates available to all tenants",
            "resource": "workflow",
            "action": "create",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflow:create:tenant",
            "name": "Create Tenant Workflows",
            "description": "Create tenant-specific workflows",
            "resource": "workflow",
            "action": "create",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "workflow:read:platform",
            "name": "View Platform-Level Workflows",
            "description": "View platform-level workflow templates",
            "resource": "workflow",
            "action": "read",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflow:read:tenant",
            "name": "View Tenant Workflows",
            "description": "View tenant-specific workflows",
            "resource": "workflow",
            "action": "read",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "workflow:update:platform",
            "name": "Update Platform-Level Workflows",
            "description": "Modify platform-level workflow templates",
            "resource": "workflow",
            "action": "update",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflow:update:tenant",
            "name": "Update Tenant Workflows",
            "description": "Modify tenant-specific workflows",
            "resource": "workflow",
            "action": "update",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "workflow:delete:platform",
            "name": "Delete Platform-Level Workflows",
            "description": "Delete platform-level workflow templates",
            "resource": "workflow",
            "action": "delete",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflow:delete:tenant",
            "name": "Delete Tenant Workflows",
            "description": "Delete tenant-specific workflows",
            "resource": "workflow",
            "action": "delete",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "workflow:clone:platform",
            "name": "Clone Platform Workflows",
            "description": "Clone platform workflow templates to tenant-specific versions",
            "resource": "workflow",
            "action": "clone",
            "scope": "platform",
            "category": "nocode",
            "is_system": True
        },

        # ==================== Automation System ====================
        {
            "code": "automation:create:platform",
            "name": "Create Platform-Level Automations",
            "description": "Create automation templates available to all tenants",
            "resource": "automation",
            "action": "create",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automation:create:tenant",
            "name": "Create Tenant Automations",
            "description": "Create tenant-specific automations",
            "resource": "automation",
            "action": "create",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "automation:read:platform",
            "name": "View Platform-Level Automations",
            "description": "View platform-level automation templates",
            "resource": "automation",
            "action": "read",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automation:read:tenant",
            "name": "View Tenant Automations",
            "description": "View tenant-specific automations",
            "resource": "automation",
            "action": "read",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "automation:update:platform",
            "name": "Update Platform-Level Automations",
            "description": "Modify platform-level automation templates",
            "resource": "automation",
            "action": "update",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automation:update:tenant",
            "name": "Update Tenant Automations",
            "description": "Modify tenant-specific automations",
            "resource": "automation",
            "action": "update",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "automation:delete:platform",
            "name": "Delete Platform-Level Automations",
            "description": "Delete platform-level automation templates",
            "resource": "automation",
            "action": "delete",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automation:delete:tenant",
            "name": "Delete Tenant Automations",
            "description": "Delete tenant-specific automations",
            "resource": "automation",
            "action": "delete",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "automation:clone:platform",
            "name": "Clone Platform Automations",
            "description": "Clone platform automation templates to tenant-specific versions",
            "resource": "automation",
            "action": "clone",
            "scope": "platform",
            "category": "nocode",
            "is_system": True
        },

        # ==================== Lookup Configuration ====================
        {
            "code": "lookup:create:platform",
            "name": "Create Platform-Level Lookups",
            "description": "Create lookup configurations available to all tenants",
            "resource": "lookup",
            "action": "create",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "lookup:create:tenant",
            "name": "Create Tenant Lookups",
            "description": "Create tenant-specific lookup configurations",
            "resource": "lookup",
            "action": "create",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "lookup:read:platform",
            "name": "View Platform-Level Lookups",
            "description": "View platform-level lookup configurations",
            "resource": "lookup",
            "action": "read",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "lookup:read:tenant",
            "name": "View Tenant Lookups",
            "description": "View tenant-specific lookup configurations",
            "resource": "lookup",
            "action": "read",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "lookup:update:platform",
            "name": "Update Platform-Level Lookups",
            "description": "Modify platform-level lookup configurations",
            "resource": "lookup",
            "action": "update",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "lookup:update:tenant",
            "name": "Update Tenant Lookups",
            "description": "Modify tenant-specific lookup configurations",
            "resource": "lookup",
            "action": "update",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "lookup:delete:platform",
            "name": "Delete Platform-Level Lookups",
            "description": "Delete platform-level lookup configurations",
            "resource": "lookup",
            "action": "delete",
            "scope": "platform",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "lookup:delete:tenant",
            "name": "Delete Tenant Lookups",
            "description": "Delete tenant-specific lookup configurations",
            "resource": "lookup",
            "action": "delete",
            "scope": "tenant",
            "category": "nocode",
            "is_system": True
        },
        {
            "code": "lookup:clone:platform",
            "name": "Clone Platform Lookups",
            "description": "Clone platform lookup configurations to tenant-specific versions",
            "resource": "lookup",
            "action": "clone",
            "scope": "platform",
            "category": "nocode",
            "is_system": True
        },
    ]

    created_count = 0
    skipped_count = 0

    for perm_data in permissions:
        # Check if permission already exists
        existing = db.query(Permission).filter(
            Permission.code == perm_data["code"]
        ).first()

        if existing:
            print(f"  ⏭️  Permission exists: {perm_data['code']}")
            skipped_count += 1
            continue

        # Create permission
        permission = Permission(
            id=str(generate_uuid()),
            created_at=datetime.utcnow(),
            **perm_data
        )
        db.add(permission)
        created_count += 1
        print(f"  ✅ Created permission: {perm_data['code']}")

    db.commit()

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"  ✅ Created: {created_count} permissions")
    print(f"  ⏭️  Skipped: {skipped_count} permissions (already exist)")
    print()


def main():
    """Main entry point for the permission seed script."""
    db = SessionLocal()
    try:
        seed_nocode_permissions(db)
        print("✅ No-code permissions seeded successfully!\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
