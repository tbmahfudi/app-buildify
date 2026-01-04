"""
Phase 1 No-Code Platform Permissions Seed
==========================================
Seeds permissions for:
- Priority 1: Data Model Designer
- Priority 2: Workflow Designer
- Priority 3: Automation System
- Priority 4: Lookup Configuration

Run: python -m app.seeds.seed_phase1_permissions
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.rbac_junctions import RolePermission
from app.models.base import generate_uuid


def seed_phase1_permissions(db: Session) -> dict:
    """
    Seed Phase 1 No-Code Platform permissions.

    Returns:
        Dictionary with created and existing counts
    """
    print("\n" + "="*80)
    print("PHASE 1 NO-CODE PLATFORM PERMISSIONS SETUP")
    print("="*80 + "\n")

    # Define all Phase 1 permissions
    permissions_data = [
        # Priority 1: Data Model Designer
        {
            "code": "data_model:create:tenant",
            "name": "Create Data Models",
            "description": "Permission to create entity definitions",
            "scope": "tenant",
            "resource": "data_model",
            "action": "create",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:read:tenant",
            "name": "Read Data Models",
            "description": "Permission to view entity definitions",
            "scope": "tenant",
            "resource": "data_model",
            "action": "read",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:update:tenant",
            "name": "Update Data Models",
            "description": "Permission to edit entity definitions",
            "scope": "tenant",
            "resource": "data_model",
            "action": "update",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:delete:tenant",
            "name": "Delete Data Models",
            "description": "Permission to delete entity definitions",
            "scope": "tenant",
            "resource": "data_model",
            "action": "delete",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "data_model:execute:tenant",
            "name": "Execute Migrations",
            "description": "Permission to publish entities and execute migrations",
            "scope": "tenant",
            "resource": "data_model",
            "action": "execute",
            "category": "nocode_platform",
            "is_system": True
        },

        # Priority 2: Workflow Designer
        {
            "code": "workflows:create:tenant",
            "name": "Create Workflows",
            "description": "Permission to create workflow definitions",
            "scope": "tenant",
            "resource": "workflows",
            "action": "create",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflows:read:tenant",
            "name": "Read Workflows",
            "description": "Permission to view workflow definitions",
            "scope": "tenant",
            "resource": "workflows",
            "action": "read",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflows:update:tenant",
            "name": "Update Workflows",
            "description": "Permission to edit workflow definitions",
            "scope": "tenant",
            "resource": "workflows",
            "action": "update",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflows:delete:tenant",
            "name": "Delete Workflows",
            "description": "Permission to delete workflow definitions",
            "scope": "tenant",
            "resource": "workflows",
            "action": "delete",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "workflows:execute:tenant",
            "name": "Execute Workflows",
            "description": "Permission to execute workflow transitions",
            "scope": "tenant",
            "resource": "workflows",
            "action": "execute",
            "category": "nocode_platform",
            "is_system": True
        },

        # Priority 3: Automation System
        {
            "code": "automations:create:tenant",
            "name": "Create Automations",
            "description": "Permission to create automation rules",
            "scope": "tenant",
            "resource": "automations",
            "action": "create",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automations:read:tenant",
            "name": "Read Automations",
            "description": "Permission to view automation rules",
            "scope": "tenant",
            "resource": "automations",
            "action": "read",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automations:update:tenant",
            "name": "Update Automations",
            "description": "Permission to edit automation rules",
            "scope": "tenant",
            "resource": "automations",
            "action": "update",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automations:delete:tenant",
            "name": "Delete Automations",
            "description": "Permission to delete automation rules",
            "scope": "tenant",
            "resource": "automations",
            "action": "delete",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "automations:execute:tenant",
            "name": "Execute Automations",
            "description": "Permission to execute and test automation rules",
            "scope": "tenant",
            "resource": "automations",
            "action": "execute",
            "category": "nocode_platform",
            "is_system": True
        },

        # Priority 4: Lookup Configuration
        {
            "code": "lookups:create:tenant",
            "name": "Create Lookups",
            "description": "Permission to create lookup configurations",
            "scope": "tenant",
            "resource": "lookups",
            "action": "create",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "lookups:read:tenant",
            "name": "Read Lookups",
            "description": "Permission to view lookup configurations and data",
            "scope": "tenant",
            "resource": "lookups",
            "action": "read",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "lookups:update:tenant",
            "name": "Update Lookups",
            "description": "Permission to edit lookup configurations",
            "scope": "tenant",
            "resource": "lookups",
            "action": "update",
            "category": "nocode_platform",
            "is_system": True
        },
        {
            "code": "lookups:delete:tenant",
            "name": "Delete Lookups",
            "description": "Permission to delete lookup configurations",
            "scope": "tenant",
            "resource": "lookups",
            "action": "delete",
            "category": "nocode_platform",
            "is_system": True
        },
    ]

    created_count = 0
    existing_count = 0

    print("📋 Creating Phase 1 permissions...")

    for perm_data in permissions_data:
        existing_perm = db.query(Permission).filter(
            Permission.code == perm_data["code"]
        ).first()

        if not existing_perm:
            new_perm = Permission(
                id=str(generate_uuid()),
                code=perm_data["code"],
                name=perm_data["name"],
                description=perm_data["description"],
                scope=perm_data["scope"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                category=perm_data.get("category"),
                is_system=perm_data.get("is_system", False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_perm)
            created_count += 1
            print(f"  ✅ Created: {perm_data['code']}")
        else:
            existing_count += 1
            print(f"  ⏭️  Exists: {perm_data['code']}")

    db.commit()

    print(f"\n✅ Created {created_count} new permissions")
    print(f"⏭️  Skipped {existing_count} existing permissions")

    # Assign permissions to tenant_admin role
    print("\n📋 Assigning permissions to tenant_admin role...")

    admin_role = db.query(Role).filter(Role.code == "tenant_admin").first()

    if admin_role:
        permission_codes = [p["code"] for p in permissions_data]
        permissions = db.query(Permission).filter(
            Permission.code.in_(permission_codes)
        ).all()

        assigned_count = 0
        for permission in permissions:
            # Check if already assigned
            existing = db.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == admin_role.id,
                    RolePermission.permission_id == permission.id
                )
            ).first()

            if not existing:
                role_perm = RolePermission(
                    role_id=admin_role.id,
                    permission_id=permission.id
                )
                db.add(role_perm)
                assigned_count += 1
                print(f"  ✅ Assigned: {permission.code}")

        db.commit()
        print(f"\n✅ Assigned {assigned_count} permissions to tenant_admin role")
    else:
        print("  ⚠️  Warning: tenant_admin role not found. Run seed_role_templates.py first.")

    # Also assign to security_admin role (for RBAC management)
    print("\n📋 Assigning permissions to security_admin role...")

    security_role = db.query(Role).filter(Role.code == "security_admin").first()

    if security_role:
        permission_codes = [p["code"] for p in permissions_data]
        permissions = db.query(Permission).filter(
            Permission.code.in_(permission_codes)
        ).all()

        assigned_count = 0
        for permission in permissions:
            # Check if already assigned
            existing = db.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == security_role.id,
                    RolePermission.permission_id == permission.id
                )
            ).first()

            if not existing:
                role_perm = RolePermission(
                    role_id=security_role.id,
                    permission_id=permission.id
                )
                db.add(role_perm)
                assigned_count += 1
                print(f"  ✅ Assigned: {permission.code}")

        db.commit()
        print(f"\n✅ Assigned {assigned_count} permissions to security_admin role")
    else:
        print("  ⚠️  Note: security_admin role not found (optional)")

    print("\n" + "="*80)
    print("PHASE 1 PERMISSIONS SETUP COMPLETE")
    print("="*80 + "\n")

    return {
        "created": created_count,
        "existing": existing_count,
        "total": len(permissions_data)
    }


def main():
    """Main entry point for the seed script."""
    db = SessionLocal()
    try:
        result = seed_phase1_permissions(db)
        print(f"Summary: {result['created']} created, {result['existing']} existing, {result['total']} total")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
