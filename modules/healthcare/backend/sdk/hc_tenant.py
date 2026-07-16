"""
Healthcare SDK — shared-tenant resolution.

**Deprecated (ADR-012 D3).** This module is now a thin wrapper over the platform seam
``app.core.module_system.tenancy``, which resolves the shared SaaS tenant for *any*
module that declares ``tenancy.mode = shared_saas`` in its manifest — healthcare being
the first. Tenancy is a platform concern, not a healthcare one; keeping the ``'SAAS'``
constant here meant the next SaaS module would copy this file and re-solve it by hand.

The wrapper exists rather than a delete because this module has ~100 call sites across 19
files; delegating puts the constant in exactly one place (the platform) with zero
call-site churn. It is removed with ADR-011 S6b via a mechanical import rewrite.

**New code should import from the platform directly:**

    from app.core.module_system.tenancy import shared_tenant_id
    tid = shared_tenant_id(module="healthcare")

Background: after migration-plan-saas-tenancy-01, ALL healthcare data lives on ONE shared
platform Tenant (``tenants.code = 'SAAS'``); per-clinic isolation is by **Company**
(``hc_patients.company_id``, the branch/owner Company GUC), not by tenant. The platform
*staff user* still belongs to their original clinic tenant, so ``current_user.tenant_id``
does not match the (SAAS) tenant the hc rows carry.
"""
from __future__ import annotations

from app.core.module_system.tenancy import resolve_shared_tenant_id as _platform_resolve
from app.core.module_system.tenancy import set_shared_tenant_id as _platform_set
from app.core.module_system.tenancy import shared_tenant_id as _platform_shared

_MODULE = "healthcare"


def set_shared_tenant_id(tenant_id: str) -> None:
    """Prime the cache (called at healthcare service startup). Deprecated: see module docstring."""
    _platform_set(tenant_id)


def resolve_shared_tenant_id(db) -> str:
    """Resolve + cache the SAAS tenant id from the DB. Deprecated: see module docstring."""
    return _platform_resolve(db, module=_MODULE)


def hc_shared_tenant_id() -> str:
    """
    Return the single shared hc tenant id (the SAAS tenant).

    Deprecated: see module docstring. Preferred call site is inside a session where the
    cache is already primed (by the service-startup resolver or the branch/patient session
    dependency). Falls back to the fixed provisioned id if the cache was never primed.
    """
    return _platform_shared(module=_MODULE)


__all__ = ["set_shared_tenant_id", "resolve_shared_tenant_id", "hc_shared_tenant_id"]
