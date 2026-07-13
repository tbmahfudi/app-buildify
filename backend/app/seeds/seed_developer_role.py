"""
Developer role + platform no-code permissions seed (idempotent).

Creates / updates:
  1. Two new permissions used only for menu gating:
       - nocode:access:tenant   -> gates previously-ungated No-Code / Developer
                                   leaf items (Components Showcase, Sample
                                   Reports & Dashboards) so regular users don't
                                   see them.
       - settings:manage:tenant -> gates the new "Admin Settings" menu item.
  2. A reusable system-level `developer` role (tenant_id=None, is_system=True)
     whose permissions are the full no-code bundle. This is tenant-assignable
     (grant it to a group at tenant / company / branch level).
  3. Grants nocode:access:tenant + the no-code bundle to `developer`, and
     nocode:access:tenant to `superuser` conceptually (superusers bypass checks,
     so no grant needed).
  4. Grants settings:manage:tenant to the admin roles
     (tenant_admin, company_manager, security_admin, module_admin) and, for the
     per-tenant seeded roles, `tenant_admin` copies.

IMPORTANT: this script only ADDS grants; it never strips the no-code bundle from
other roles. We separately assert (see verify) that the no-code permissions are
NOT part of `regular_user`.

Run: docker exec app_buildify_backend python -m app.seeds.seed_developer_role
"""

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.rbac_junctions import RolePermission
from app.models.role import Role

# The exact permission codes that already exist in the DB for the no-code bundle.
NOCODE_BUNDLE = [
    # Data & schema
    "data_model:read:tenant",
    "data_model:create:tenant",
    "data_model:update:tenant",
    "data_model:delete:tenant",
    "data_model:execute:tenant",
    # Lookups
    "lookups:read:tenant",
    "lookups:create:tenant",
    "lookups:update:tenant",
    "lookups:delete:tenant",
    # Builder / UI & pages
    "builder:design:tenant",
    "builder:publish:tenant",
    "builder:manage-menus:tenant",
    "builder:manage-permissions:tenant",
    "builder:pages:read:tenant",
    "builder:pages:create:tenant",
    "builder:pages:edit:tenant",
    "builder:pages:delete:tenant",
    # Reports & dashboards (create/read enough to build for subscribed modules)
    "reports:create:tenant",
    "reports:read:tenant",
    "reports:update:tenant",
    "reports:execute:tenant",
    "reports:export:tenant",
    "dashboards:read:tenant",
    "dashboards:create:tenant",
    "dashboards:update:tenant",
    # Business logic
    "workflows:read:tenant",
    "workflows:create:tenant",
    "workflows:update:tenant",
    "workflows:delete:tenant",
    "workflows:execute:tenant",
    "automations:read:tenant",
    "automations:create:tenant",
    "automations:update:tenant",
    "automations:delete:tenant",
    "automations:execute:tenant",
    # Menu access to the no-code area itself
    "nocode:access:tenant",
]

NEW_PERMISSIONS = [
    {
        "code": "nocode:access:tenant",
        "name": "Access No-Code Platform",
        "description": "Access the No-Code / Developer tooling area",
        "resource": "nocode",
        "action": "access",
        "scope": "tenant",
        "category": "nocode",
        "is_system": True,
    },
    {
        "code": "settings:manage:tenant",
        "name": "Manage Admin Settings",
        "description": "Manage tenant/company administrative settings",
        "resource": "settings",
        "action": "manage",
        "scope": "tenant",
        "category": "settings",
        "is_system": True,
    },
    {
        "code": "notifications:read:tenant",
        "name": "View Notification Settings",
        "description": "View tenant notification configuration (operator-facing " "System Management menu gate)",
        "resource": "notifications",
        "action": "read",
        "scope": "tenant",
        "category": "settings",
        "is_system": True,
    },
]

# Admin roles: full Admin Settings (menu gate + backend read/update) plus the
# operator-facing System Management items (Monitoring & Audit, Notifications).
SETTINGS_MANAGE_ROLES = [
    "tenant_admin",
    "company_manager",
    "company_admin",
    "branch_admin",
    "security_admin",
    "module_admin",
]
# Backend settings endpoints require these granular scopes (settings:manage is
# only the menu gate); grant them to the admin roles too or Admin Settings 403s.
ADMIN_SETTINGS_GRANTS = [
    "settings:manage:tenant",
    "settings:read:tenant",
    "settings:update:tenant",
]
# Operator (non-admin staff) roles that also need Monitoring & Audit and the
# Notifications settings item under System Management. Admins get these as well.
OPERATOR_ROLES = ["employee", "manager", "department_manager", "auditor"]
OPERATOR_SYSTEM_GRANTS = ["audit:read:tenant", "notifications:read:tenant"]


def _ensure_permission(db: Session, spec: dict) -> Permission:
    perm = db.query(Permission).filter(Permission.code == spec["code"]).first()
    if perm:
        print(f"  • Permission exists: {spec['code']}")
        return perm
    perm = Permission(
        code=spec["code"],
        name=spec["name"],
        description=spec["description"],
        resource=spec["resource"],
        action=spec["action"],
        scope=spec["scope"],
        category=spec["category"],
        is_system=spec["is_system"],
    )
    db.add(perm)
    db.flush()
    print(f"  ✓ Created permission: {spec['code']}")
    return perm


def _grant(db: Session, role: Role, perm_code: str) -> bool:
    perm = db.query(Permission).filter(Permission.code == perm_code).first()
    if not perm:
        print(f"    ⚠️  Permission not found (skipped): {perm_code}")
        return False
    exists = (
        db.query(RolePermission)
        .filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == perm.id,
        )
        .first()
    )
    if exists:
        return False
    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    return True


def seed_developer_role():
    db = SessionLocal()
    try:
        print("\n" + "=" * 70)
        print("DEVELOPER ROLE + NO-CODE PERMISSIONS SEED")
        print("=" * 70 + "\n")

        # 1. Permissions
        print("Step 1: Ensuring permissions...")
        for spec in NEW_PERMISSIONS:
            _ensure_permission(db, spec)
        db.commit()

        # 2. System-level `developer` role (tenant_id=None, is_system=True).
        #    Distinct from any per-tenant `developer` role already in tenants.
        print("\nStep 2: Ensuring system 'developer' role...")
        role = db.query(Role).filter(Role.code == "developer", Role.tenant_id.is_(None)).first()
        if not role:
            role = Role(
                code="developer",
                name="Developer",
                description="No-code / low-code builder: customize subscribed "
                "modules (data models, pages, reports, workflows).",
                role_type="default",
                is_system=True,
                is_active=True,
                tenant_id=None,
            )
            db.add(role)
            db.flush()
            print("  ✓ Created system role: developer")
        else:
            role.name = "Developer"
            role.description = (
                "No-code / low-code builder: customize subscribed " "modules (data models, pages, reports, workflows)."
            )
            role.is_system = True
            role.is_active = True
            print("  • System role exists: developer")
        db.commit()

        # 3. Grant no-code bundle to developer
        print("\nStep 3: Granting no-code bundle to 'developer'...")
        granted = 0
        for code in NOCODE_BUNDLE:
            if _grant(db, role, code):
                granted += 1
        db.commit()
        print(f"  ✓ Newly granted {granted} permissions to developer")

        # 4. Grant settings scopes to admin roles (all copies across tenants).
        #    Admins get the full Admin Settings bundle AND the operator-facing
        #    System Management items (so they see Monitoring & Audit / Notifications).
        print("\nStep 4: Granting settings + system perms to admin roles...")
        admin_roles = db.query(Role).filter(Role.code.in_(SETTINGS_MANAGE_ROLES)).all()
        cnt = 0
        for r in admin_roles:
            for code in ADMIN_SETTINGS_GRANTS + OPERATOR_SYSTEM_GRANTS:
                if _grant(db, r, code):
                    cnt += 1
        db.commit()
        print(f"  ✓ Granted {cnt} settings/system perms across " f"{len(admin_roles)} admin role rows")

        # 4b. Grant operator-facing System Management perms to operator roles
        #     (non-admin staff): Monitoring & Audit + Notifications only.
        print("\nStep 4b: Granting operator System Management perms...")
        operator_roles = db.query(Role).filter(Role.code.in_(OPERATOR_ROLES)).all()
        ocnt = 0
        for r in operator_roles:
            for code in OPERATOR_SYSTEM_GRANTS:
                if _grant(db, r, code):
                    ocnt += 1
        db.commit()
        print(
            f"  ✓ Granted {ocnt} operator perms across "
            f"{len(operator_roles)} operator role rows "
            f"({sorted({r.code for r in operator_roles})})"
        )

        # 5. Safety assertion: regular_user must NOT have no-code perms.
        print("\nStep 5: Verifying regular_user has no no-code permissions...")
        ru = db.query(Role).filter(Role.code == "regular_user").all()
        leaked = []
        for r in ru:
            rp = db.query(RolePermission).filter(RolePermission.role_id == r.id).all()
            codes = {db.get(Permission, x.permission_id).code for x in rp}
            leaked += [c for c in codes if c in set(NOCODE_BUNDLE)]
        if leaked:
            print(f"  ⚠️  regular_user has no-code perms: {sorted(set(leaked))}")
        else:
            print("  ✓ regular_user clean (no no-code permissions)")

        print("\n" + "=" * 70)
        print("DEVELOPER ROLE SEED COMPLETE")
        print("=" * 70 + "\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_developer_role()
