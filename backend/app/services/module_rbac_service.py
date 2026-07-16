"""
Module end-user RBAC provisioning (ADR-012 D4/D5).

A ``shared_saas`` module declares the role/group its end users get
(``tenancy.end_user_rbac`` in its manifest). This service provisions that role + group
**into the shared SaaS tenant** — where those end users actually live — and joins
accounts to the group.

Why this exists: ADR-HC-009 D7 told the patient backfill to "assign the ``patient`` role +
``patients`` group", but ADR-HC-010 had already moved every patient to the shared SAAS
tenant, where neither artifact exists (they exist only in the 93 old per-clinic tenants).
The step was unsatisfiable. ADR-012 D4 fixes it generically rather than hardcoding a
healthcare answer, because other modules may adopt SaaS mode too.

Two rules shape the code below:

* **Provisioning is additive and idempotent.** It never touches the legacy per-clinic
  groups/roles (D6), never widens an existing role, and is safe to re-run.
* **Consumers resolve-or-fail** (Resolution Q2). ``post_install`` swallows its own hook
  failures (``modules.py:819``: "log but do NOT roll back"), so provisioning cannot be
  trusted to have run. Account creation therefore *asserts* the group exists instead of
  silently producing a role-less end user — which is exactly the shipped defect this
  closes (a patient with no ``patient`` role lands in the staff SPA, ``app.js:112``).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.module_system.tenancy import (
    end_user_rbac,
    is_shared_saas,
    resolve_shared_tenant_id,
)
from app.models.group import Group
from app.models.permission import Permission
from app.models.rbac_junctions import GroupRole, RolePermission, UserGroup
from app.models.role import Role

logger = logging.getLogger(__name__)


class EndUserRBACNotProvisioned(RuntimeError):
    """The module's declared end-user group is missing from the shared tenant.

    Raised instead of creating an end user with no role. Recoverable by running
    ``seed_module_rbac`` for the module.
    """


def load_module_manifest(db: Session, module_name: str) -> Dict[str, Any]:
    """Load a module's manifest, DB first and disk second.

    **The DB is the primary source because not every service can see the modules
    directory.** The healthcare service mounts only ``modules/healthcare/backend`` (as
    ``/app/modules/healthcare``), so ``manifest.json`` — which lives one level *above*
    ``backend/`` — is not in that container at all; there is no ``/modules`` root there
    either. Since ``POST /patients/register`` runs in that service, reading the manifest
    off disk would fail there and 500 every registration.

    ``modules.manifest`` (JSON) is written by ``registry.sync_manifests_from_disk()``,
    which the platform runs at backend startup (``app/main.py:119``), and both services
    share the database. Disk stays as a fallback for contexts that have it (the backend
    container, the seed command) and for a module not yet synced.

    Consequence worth knowing: a manifest change reaches the DB when the **backend**
    restarts and re-syncs. A module service reading a stale declaration is possible; the
    group must still exist to be resolved, so the failure mode is a loud raise, not a
    silently wrong grant.
    """
    try:
        row = db.execute(text("SELECT manifest FROM modules WHERE name = :n LIMIT 1"), {"n": module_name}).fetchone()
        if row and row[0]:
            manifest = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            if isinstance(manifest, dict) and manifest:
                return manifest
    except Exception as exc:  # noqa: BLE001 — fall through to disk
        logger.warning("Could not read manifest for '%s' from the DB: %s", module_name, exc)

    modules_root = Path(
        os.environ.get("MODULES_ROOT")
        or (Path("/modules") if Path("/modules").is_dir() else Path(__file__).resolve().parents[3] / "modules")
    )
    manifest_path = modules_root / module_name / "manifest.json"
    if manifest_path.is_file():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise EndUserRBACNotProvisioned(
        f"no manifest for module '{module_name}': not in the modules table and not at "
        f"{manifest_path}. If the module was just changed, restart the backend so "
        f"sync_manifests_from_disk() refreshes the DB copy."
    )


def _get_or_create_permission(db: Session, code: str, module_name: str) -> Permission:
    """Get or create a permission row for a manifest-declared code.

    Only ``code`` is load-bearing: authorization compares permission *codes*
    (``User.get_permissions`` returns a set of codes, and the ``require_permission``
    dependencies match on them). ``resource``/``action``/``scope`` are display metadata for
    grouping in the admin UI — but ``scope`` is NOT NULL, so they must be filled.

    The split is positional to match how this module's existing permissions were already
    seeded: ``healthcare:appointments:read`` is stored as resource=healthcare,
    action=appointments, scope=read. That is *not* the platform's documented
    ``resource:action:scope`` convention (cf. ``analytics:export:all``), and it is why
    'read' appears as a scope value. Reproducing the sibling shape keeps a module's
    permissions grouped together in the UI; diverging here would scatter them. The
    convention collision is pre-existing and deliberately not resolved in this ADR.
    """
    perm = db.query(Permission).filter(Permission.code == code).first()
    if perm:
        return perm

    parts = code.split(":")
    if len(parts) >= 3:
        resource, action, scope = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        resource, action, scope = parts[0], parts[1], "tenant"
    else:
        resource, action, scope = module_name, code, "tenant"

    perm = Permission(
        code=code,
        name=code,
        description=f"Declared by the '{module_name}' module manifest (ADR-012 D4).",
        resource=resource[:50],
        action=action[:50],
        scope=scope[:50],
        category=module_name[:50],
    )
    db.add(perm)
    db.flush()
    return perm


def provision_end_user_rbac(db: Session, manifest: Dict[str, Any], *, commit: bool = True) -> Optional[Dict[str, str]]:
    """Provision a shared_saas module's declared end-user role/group into the shared tenant.

    Idempotent and additive: existing rows are reused, never rewritten, so re-running is a
    no-op and a hand-edited role is not clobbered.

    Returns a summary dict, or None when the module is not ``shared_saas`` (nothing to do).
    """
    if not is_shared_saas(manifest):
        return None

    module_name = manifest.get("name") or "<unknown>"
    rbac = end_user_rbac(manifest)
    role_code = rbac.get("role")
    group_code = rbac.get("group")
    if not role_code or not group_code:
        # validate_tenancy_block rejects this at every admitting path; belt and braces.
        raise ValueError(f"module '{module_name}' declares shared_saas but no end_user_rbac role/group")

    tenant_id = resolve_shared_tenant_id(db, module=module_name)

    role = db.query(Role).filter(Role.tenant_id == tenant_id, Role.code == role_code).first()
    created_role = False
    if role is None:
        role = Role(
            tenant_id=tenant_id,
            code=role_code,
            name=role_code.replace("_", " ").title(),
            description=f"End-user role for the '{module_name}' module (ADR-012 D4).",
            role_type="system",
        )
        db.add(role)
        db.flush()
        created_role = True

    # groups are unique per (tenant_id, company_id, code), so the company_id IS NULL
    # filter is load-bearing: without it a company-scoped group of the same code would
    # match here and we would never create the tenant-wide one.
    group = (
        db.query(Group)
        .filter(
            Group.tenant_id == tenant_id,
            Group.company_id.is_(None),
            Group.code == group_code,
        )
        .first()
    )
    created_group = False
    if group is None:
        # company_id NULL == tenant-wide: end users of every Company in the shared tenant
        # join the same group. Company stays the isolation axis (ADR-HC-010 D2 RLS); the
        # group only carries the role.
        group = Group(
            tenant_id=tenant_id,
            company_id=None,
            code=group_code,
            name=group_code.replace("_", " ").title(),
            description=f"End users of the '{module_name}' module (ADR-012 D4).",
        )
        db.add(group)
        db.flush()
        created_group = True

    if db.query(GroupRole).filter(GroupRole.group_id == group.id, GroupRole.role_id == role.id).first() is None:
        db.add(GroupRole(group_id=group.id, role_id=role.id))
        db.flush()

    granted: List[str] = []
    for code in rbac.get("permissions") or []:
        perm = _get_or_create_permission(db, code, module_name)
        if (
            db.query(RolePermission)
            .filter(RolePermission.role_id == role.id, RolePermission.permission_id == perm.id)
            .first()
            is None
        ):
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
            granted.append(code)
    db.flush()

    if commit:
        db.commit()

    logger.info(
        "end-user RBAC provisioned for module=%s tenant=%s role=%s(new=%s) group=%s(new=%s) " "permissions_granted=%s",
        module_name,
        tenant_id,
        role_code,
        created_role,
        group_code,
        created_group,
        granted or "none",
    )
    return {
        "module": module_name,
        "tenant_id": str(tenant_id),
        "role_id": str(role.id),
        "role_code": role_code,
        "group_id": str(group.id),
        "group_code": group_code,
    }


def resolve_end_user_group(db: Session, manifest: Dict[str, Any]) -> Group:
    """Return the module's declared end-user group in the shared tenant, or raise.

    Deliberately does **not** create it: provisioning is an admin action with its own
    command, and creating RBAC lazily from an account-creation path (some of which are
    unauthenticated) would put a privileged write behind a public endpoint.
    """
    module_name = manifest.get("name") or "<unknown>"
    rbac = end_user_rbac(manifest)
    group_code = rbac.get("group")
    if not group_code:
        raise EndUserRBACNotProvisioned(f"module '{module_name}' declares no tenancy.end_user_rbac.group")

    tenant_id = resolve_shared_tenant_id(db, module=module_name)
    group = (
        db.query(Group)
        .filter(
            Group.tenant_id == tenant_id,
            Group.company_id.is_(None),
            Group.code == group_code,
        )
        .first()
    )
    if group is None:
        raise EndUserRBACNotProvisioned(
            f"end-user group '{group_code}' is missing from the shared tenant {tenant_id} "
            f"for module '{module_name}'. Run: python -m scripts.seed_module_rbac {module_name}"
        )
    return group


def assign_end_user_group(db: Session, user, group: Group) -> bool:
    """Join ``user`` to ``group`` if not already a member. Returns True if added.

    The platform resolves permissions strictly via User->Group->Role->Permission (direct
    user_roles are deprecated and ignored by ``User.get_permissions``), so joining the
    group is the only write needed to give an end user its role.
    """
    existing = db.query(UserGroup).filter(UserGroup.user_id == user.id, UserGroup.group_id == group.id).first()
    if existing:
        return False
    db.add(UserGroup(user_id=user.id, group_id=group.id))
    db.flush()
    return True


__all__ = [
    "EndUserRBACNotProvisioned",
    "provision_end_user_rbac",
    "resolve_end_user_group",
    "assign_end_user_group",
]
