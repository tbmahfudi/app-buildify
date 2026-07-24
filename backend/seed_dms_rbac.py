"""
DMS Module RBAC Seed
====================
Creates the DMS permissions, three roles (Manager / Editor / Viewer), matching
groups, and assigns a user to the Managers group — so the platform's
User -> Group -> Role -> Permission chain resolves DMS permissions and the JWT
`permissions[]` claim carries them (which the DMS module now enforces).

Mirrors backend/app/seeds/seed_financial_rbac.py. Idempotent.

Usage (inside the backend container):
    docker exec app_buildify_backend python seed_dms_rbac.py TECHSTART ceo@techstart.com
    docker exec app_buildify_backend python seed_dms_rbac.py TECHSTART   # manager user defaults to ceo@<tenant>
"""
import sys
import uuid
from datetime import datetime

from app.core.db import SessionLocal
from app.models.company import Company
from app.models.group import Group
from app.models.permission import Permission
from app.models.rbac_junctions import GroupRole, RolePermission, UserGroup
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User

# code -> (name, description). Format: dms:<resource>:<action>:<scope> (4 parts).
DMS_PERMISSIONS = {
    "dms:document:read:company":   ("View Documents", "View and download documents"),
    "dms:document:write:company":  ("Write Documents", "Upload documents and new versions"),
    "dms:document:delete:company": ("Delete Documents", "Delete documents"),
    "dms:folder:read:company":     ("Browse Folders", "Browse folders"),
    "dms:folder:manage:company":   ("Manage Folders", "Create, move, and configure folders"),
    "dms:share:create:company":    ("Create Share Links", "Create external share links"),
    "dms:audit:view:company":      ("View Audit Trail", "View the document audit trail"),
}

ROLES = {
    "DMS Manager": {
        "code": "DMS_MANAGER",
        "description": "Full document management access",
        "permissions": list(DMS_PERMISSIONS.keys()),
    },
    "DMS Editor": {
        "code": "DMS_EDITOR",
        "description": "Upload, organize and share documents (no delete or audit)",
        "permissions": [
            "dms:document:read:company", "dms:document:write:company",
            "dms:folder:read:company", "dms:folder:manage:company",
            "dms:share:create:company",
        ],
    },
    "DMS Viewer": {
        "code": "DMS_VIEWER",
        "description": "Read-only document access",
        "permissions": ["dms:document:read:company", "dms:folder:read:company"],
    },
}

GROUPS = {
    "DMS Managers": {"code": "DMS_MANAGERS", "roles": ["DMS Manager"]},
    "DMS Editors": {"code": "DMS_EDITORS", "roles": ["DMS Editor"]},
    "DMS Viewers": {"code": "DMS_VIEWERS", "roles": ["DMS Viewer"]},
}


def main():
    tenant_code = (sys.argv[1] if len(sys.argv) > 1 else "TECHSTART").upper()
    manager_email = sys.argv[2] if len(sys.argv) > 2 else f"ceo@{tenant_code.lower()}.com"

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            print(f"❌ Tenant '{tenant_code}' not found")
            sys.exit(1)
        company = (
            db.query(Company)
            .filter(Company.tenant_id == tenant.id, Company.code == tenant_code)
            .first()
        ) or db.query(Company).filter(Company.tenant_id == tenant.id).first()
        if not company:
            print(f"❌ No company found for tenant '{tenant_code}'")
            sys.exit(1)
        print(f"✓ Tenant {tenant.name} / Company {company.name}")

        # --- permissions ----------------------------------------------------
        perm_map = {}
        for code, (name, desc) in DMS_PERMISSIONS.items():
            perm = db.query(Permission).filter(Permission.code == code).first()
            if not perm:
                _, resource, action, scope = code.split(":")
                perm = Permission(
                    code=code, name=name, description=desc, resource=resource,
                    action=action, scope=scope, category="dms", is_system=False,
                )
                db.add(perm)
                db.flush()
                print(f"  + permission {code}")
            perm_map[code] = perm
        db.commit()

        # --- roles + role_permissions --------------------------------------
        role_map = {}
        for role_name, cfg in ROLES.items():
            role = db.query(Role).filter(Role.code == cfg["code"], Role.tenant_id == tenant.id).first()
            if not role:
                role = Role(code=cfg["code"], name=role_name, description=cfg["description"],
                            tenant_id=tenant.id, is_active=True, created_at=datetime.utcnow())
                db.add(role)
                db.flush()
                print(f"  + role {role_name}")
            for code in cfg["permissions"]:
                perm = perm_map[code]
                exists = db.query(RolePermission).filter(
                    RolePermission.role_id == role.id, RolePermission.permission_id == perm.id
                ).first()
                if not exists:
                    db.add(RolePermission(id=str(uuid.uuid4()), role_id=str(role.id),
                                          permission_id=str(perm.id), created_at=datetime.utcnow()))
            db.commit()
            role_map[role_name] = role

        # --- groups + group_roles ------------------------------------------
        group_map = {}
        for group_name, cfg in GROUPS.items():
            group = db.query(Group).filter(
                Group.code == cfg["code"], Group.tenant_id == tenant.id, Group.company_id == company.id
            ).first()
            if not group:
                group = Group(code=cfg["code"], name=group_name, description=group_name,
                              tenant_id=tenant.id, company_id=company.id, group_type="team",
                              is_active=True, created_at=datetime.utcnow())
                db.add(group)
                db.flush()
                print(f"  + group {group_name}")
            for role_name in cfg["roles"]:
                role = role_map[role_name]
                exists = db.query(GroupRole).filter(
                    GroupRole.group_id == group.id, GroupRole.role_id == role.id
                ).first()
                if not exists:
                    db.add(GroupRole(id=str(uuid.uuid4()), group_id=str(group.id),
                                     role_id=str(role.id), created_at=datetime.utcnow()))
            db.commit()
            group_map[group_name] = group

        # --- assign the manager user ---------------------------------------
        user = db.query(User).filter(User.email == manager_email, User.tenant_id == tenant.id).first()
        if not user:
            print(f"⚠ User '{manager_email}' not found — roles/groups created but not assigned.")
        else:
            mgr_group = group_map["DMS Managers"]
            exists = db.query(UserGroup).filter(
                UserGroup.user_id == user.id, UserGroup.group_id == mgr_group.id
            ).first()
            if not exists:
                db.add(UserGroup(id=str(uuid.uuid4()), user_id=str(user.id),
                                 group_id=str(mgr_group.id), created_at=datetime.utcnow()))
                db.commit()
                print(f"  + {manager_email} → DMS Managers")
            else:
                print(f"  • {manager_email} already in DMS Managers")

        print("\n✅ DMS RBAC seeded. Re-login to refresh the JWT permissions claim.")
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
