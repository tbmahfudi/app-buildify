"""
Module tenancy — declaration + shared-tenant resolution (ADR-012).

A module declares how it is tenanted in its manifest:

    "tenancy": {"mode": "per_tenant"}                    # default when absent

    "tenancy": {
      "mode": "shared_saas",
      "end_user_rbac": {
        "role": "patient", "group": "patients",
        "permissions": ["healthcare:portal:access"]
      }
    }

``per_tenant`` is the default, so modules that never declare a block keep today's
behaviour exactly (ADR-012 D1).

**There is ONE shared SaaS tenant for the whole platform, not one per module**
(ADR-012 D2). That is forced, not preferred: ``companies.tenant_id`` is singular, so a
Company using two SaaS modules could not exist in two shared tenants at once. Modules
*opt in* to the one shared tenant; isolation between them is Company + permissions
(ADR-HC-010 D1/D2), never the tenant. Hence ``shared_tenant_id(module=...)`` takes a
module name for provenance/logging but every module resolves the same id.

This replaces the healthcare-local hardcode in
``modules/healthcare/backend/sdk/hc_tenant.py`` (ADR-012 D3), which now delegates here.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)

MODE_PER_TENANT = "per_tenant"
MODE_SHARED_SAAS = "shared_saas"
VALID_MODES = (MODE_PER_TENANT, MODE_SHARED_SAAS)

# Deployment config. SAAS_SHARED_TENANT_CODE must not drift between the platform and a
# module service, or a module resolves a different tenant than its data lives in.
SHARED_TENANT_CODE = os.environ.get("SAAS_SHARED_TENANT_CODE", "SAAS")

# The migration provisions SAAS with this fixed id (saas_phase0_provision.sql); used only
# as a last-resort fallback when the tenants row cannot be read (e.g. early boot).
# ADR-012 D3: HC_SHARED_TENANT_ID is the old healthcare-only name, honoured for one
# release so an existing deployment's env keeps working.
_FALLBACK_ID = (
    os.environ.get("SAAS_SHARED_TENANT_ID")
    or os.environ.get("HC_SHARED_TENANT_ID")
    or "5aa50000-0000-4000-8000-000000000001"
)

if os.environ.get("HC_SHARED_TENANT_ID") and not os.environ.get("SAAS_SHARED_TENANT_ID"):
    logger.warning("HC_SHARED_TENANT_ID is deprecated (ADR-012 D3); rename it to SAAS_SHARED_TENANT_ID")

# One id for the whole process: there is one shared tenant (D2), so one cache.
_cached_tenant_id: Optional[str] = None

# A permission code a manifest grants its own end users must be namespaced to the
# declaring module: "healthcare:portal:access" is fine, "system:users:delete" is not.
_PERMISSION_CODE_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")


# ---------------------------------------------------------------------------
# Declaration
# ---------------------------------------------------------------------------


def tenancy_block(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Return the manifest's tenancy block ({} when absent)."""
    block = (manifest or {}).get("tenancy")
    return block if isinstance(block, dict) else {}


def tenancy_mode(manifest: Dict[str, Any]) -> str:
    """Return the module's tenancy mode, defaulting to ``per_tenant`` (D1)."""
    return tenancy_block(manifest).get("mode") or MODE_PER_TENANT


def is_shared_saas(manifest: Dict[str, Any]) -> bool:
    return tenancy_mode(manifest) == MODE_SHARED_SAAS


def end_user_rbac(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Return the declared end-user RBAC ({} when absent)."""
    block = tenancy_block(manifest).get("end_user_rbac")
    return block if isinstance(block, dict) else {}


def validate_tenancy_block(manifest: Dict[str, Any]) -> List[str]:
    """Validate the tenancy block; return human-readable errors ([] == valid).

    This is a **security gate, not a style check** (ADR-012 D1 / Resolution Q1). A
    manifest may declare permissions — that is existing precedent (``permissions[]``) and
    harmless, because a *defined* permission nobody holds grants nothing. What is new here
    is *granting* permissions to a role every end user is auto-joined to. So the codes are
    constrained to the declaring module's own namespace: a module may grant its own end
    users its own permissions, and nothing else.

    JSON Schema cannot express the namespace rule (it compares against a sibling field),
    which is why it lives here and is called from every path that admits a manifest.
    """
    errors: List[str] = []
    if not isinstance(manifest, dict):
        return errors  # shape errors are reported by the caller's own checks

    block = manifest.get("tenancy")
    if block is None:
        return errors  # absent == per_tenant (D1)
    if not isinstance(block, dict):
        return ["'tenancy' must be an object when present"]

    mode = block.get("mode")
    if mode is not None and mode not in VALID_MODES:
        errors.append(f"tenancy.mode must be one of {', '.join(VALID_MODES)} (got {mode!r})")

    rbac = block.get("end_user_rbac")

    if mode != MODE_SHARED_SAAS:
        if rbac is not None:
            errors.append(
                "tenancy.end_user_rbac is only meaningful when tenancy.mode is "
                f"'{MODE_SHARED_SAAS}' (mode is '{mode or MODE_PER_TENANT}')"
            )
        return errors

    if rbac is None:
        errors.append(
            f"tenancy.mode '{MODE_SHARED_SAAS}' requires tenancy.end_user_rbac "
            "(the role/group its end users are provisioned into)"
        )
        return errors
    if not isinstance(rbac, dict):
        return errors + ["tenancy.end_user_rbac must be an object"]

    for field in ("role", "group"):
        val = rbac.get(field)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"tenancy.end_user_rbac.{field} is required and must be a non-empty string")

    perms = rbac.get("permissions", [])
    if perms is None:
        perms = []
    if not isinstance(perms, list):
        errors.append("tenancy.end_user_rbac.permissions must be an array")
        return errors

    module_name = manifest.get("name")
    for i, code in enumerate(perms):
        if not isinstance(code, str) or not code.strip():
            errors.append(f"tenancy.end_user_rbac.permissions[{i}] must be a non-empty string")
            continue
        if not _PERMISSION_CODE_RE.match(code):
            errors.append(f"tenancy.end_user_rbac.permissions[{i}] '{code}' is not a valid permission code")
            continue
        if isinstance(module_name, str) and module_name:
            if not code.startswith(f"{module_name}:"):
                errors.append(
                    f"tenancy.end_user_rbac.permissions[{i}] '{code}' must be namespaced to "
                    f"this module ('{module_name}:...'). A manifest may only grant its own "
                    "end users its own permissions (ADR-012 Resolution Q1)."
                )

    return errors


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def set_shared_tenant_id(tenant_id: str) -> None:
    """Prime the cache (called at service startup)."""
    global _cached_tenant_id
    _cached_tenant_id = str(tenant_id)
    logger.info("shared SaaS tenant id set to %s", _cached_tenant_id)


def reset_shared_tenant_cache() -> None:
    """Drop the cached id. For tests; not used in request paths."""
    global _cached_tenant_id
    _cached_tenant_id = None


def resolve_shared_tenant_id(db, module: Optional[str] = None) -> str:
    """Resolve + cache the shared SaaS tenant id from the DB.

    Falls back to the fixed provisioned id if the tenants row cannot be read, so an
    early-boot hiccup degrades to the known id rather than a 500.

    ``module`` is provenance only — every module shares one tenant (D2).
    """
    global _cached_tenant_id
    if _cached_tenant_id:
        return _cached_tenant_id
    try:
        row = db.execute(text("SELECT id FROM tenants WHERE code = :c LIMIT 1"), {"c": SHARED_TENANT_CODE}).fetchone()
        if row and row[0]:
            _cached_tenant_id = str(row[0])
            return _cached_tenant_id
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("Could not resolve shared tenant id (%s) from DB: %s", SHARED_TENANT_CODE, exc)
    _cached_tenant_id = _FALLBACK_ID
    return _cached_tenant_id


def shared_tenant_id(module: Optional[str] = None) -> str:
    """Return the shared SaaS tenant id without a session.

    Preferred call site is inside a session where the cache is already primed (by service
    startup or a session dependency). Falls back to the fixed provisioned id if the cache
    was never primed.
    """
    return _cached_tenant_id or _FALLBACK_ID


__all__ = [
    "MODE_PER_TENANT",
    "MODE_SHARED_SAAS",
    "VALID_MODES",
    "SHARED_TENANT_CODE",
    "tenancy_block",
    "tenancy_mode",
    "is_shared_saas",
    "end_user_rbac",
    "validate_tenancy_block",
    "set_shared_tenant_id",
    "reset_shared_tenant_cache",
    "resolve_shared_tenant_id",
    "shared_tenant_id",
]
