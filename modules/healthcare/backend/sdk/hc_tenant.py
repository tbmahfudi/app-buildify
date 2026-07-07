"""
Healthcare SDK — shared-tenant resolution (SaaS tenancy migration, ADR-HC-010).

After migration-plan-saas-tenancy-01, ALL healthcare data lives on ONE shared
platform Tenant (`tenants.code = 'SAAS'`); per-clinic isolation is by **Company**
(`hc_patients.company_id`, the branch/owner Company GUC), not by tenant. The
platform *staff user* still belongs to their original clinic tenant, so
`current_user.tenant_id` no longer matches the (SAAS) tenant the hc rows carry.

`hc_shared_tenant_id()` returns the single hc tenant id used for every healthcare
query/insert/audit, decoupling the hc data layer from the platform user's tenant.
It is resolved once (from `tenants.code='SAAS'`) and cached for the process.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)

# The migration provisions SAAS with this fixed id (saas_phase0_provision.sql); used
# only as a last-resort fallback if the tenants row can't be read (e.g. early boot).
_SAAS_FALLBACK_ID = os.environ.get("HC_SHARED_TENANT_ID", "5aa50000-0000-4000-8000-000000000001")
_SAAS_TENANT_CODE = "SAAS"

_cached_tenant_id: Optional[str] = None


def set_shared_tenant_id(tenant_id: str) -> None:
    """Prime the cache (called at healthcare service startup)."""
    global _cached_tenant_id
    _cached_tenant_id = str(tenant_id)
    logger.info("hc shared tenant id set to %s", _cached_tenant_id)


def resolve_shared_tenant_id(db) -> str:
    """Resolve + cache the SAAS tenant id from the DB, or fall back to the fixed id."""
    global _cached_tenant_id
    if _cached_tenant_id:
        return _cached_tenant_id
    try:
        row = db.execute(
            text("SELECT id FROM tenants WHERE code = :c LIMIT 1"), {"c": _SAAS_TENANT_CODE}
        ).fetchone()
        if row and row[0]:
            _cached_tenant_id = str(row[0])
            return _cached_tenant_id
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("Could not resolve SAAS tenant id from DB: %s", exc)
    _cached_tenant_id = _SAAS_FALLBACK_ID
    return _cached_tenant_id


def hc_shared_tenant_id() -> str:
    """
    Return the single shared hc tenant id (the SAAS tenant).

    Preferred call site is inside a session where the cache is already primed (by
    the service-startup resolver or the branch/patient session dependency). Falls
    back to the fixed provisioned id if the cache was never primed.
    """
    return _cached_tenant_id or _SAAS_FALLBACK_ID


__all__ = ["set_shared_tenant_id", "resolve_shared_tenant_id", "hc_shared_tenant_id"]
