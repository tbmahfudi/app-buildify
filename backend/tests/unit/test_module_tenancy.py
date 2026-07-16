"""
Unit tests for app/core/module_system/tenancy.py (ADR-012 D1/D3).

No DB required — the declaration helpers and the namespace gate are pure functions.
"""
from unittest.mock import MagicMock

import pytest

from app.core.module_system.tenancy import (
    MODE_PER_TENANT,
    MODE_SHARED_SAAS,
    end_user_rbac,
    is_shared_saas,
    reset_shared_tenant_cache,
    resolve_shared_tenant_id,
    set_shared_tenant_id,
    shared_tenant_id,
    tenancy_mode,
    validate_tenancy_block,
)


def _shared_saas(name="healthcare", permissions=None):
    rbac = {"role": "patient", "group": "patients"}
    if permissions is not None:
        rbac["permissions"] = permissions
    return {"name": name, "tenancy": {"mode": MODE_SHARED_SAAS, "end_user_rbac": rbac}}


# ---------------------------------------------------------------------------
# Declaration defaults (D1)
# ---------------------------------------------------------------------------


def test_absent_block_defaults_to_per_tenant():
    """The default must be per_tenant so existing modules are untouched (D1)."""
    assert tenancy_mode({"name": "financial"}) == MODE_PER_TENANT
    assert is_shared_saas({"name": "financial"}) is False
    assert end_user_rbac({"name": "financial"}) == {}


def test_shared_saas_declaration_is_read():
    m = _shared_saas()
    assert tenancy_mode(m) == MODE_SHARED_SAAS
    assert is_shared_saas(m) is True
    assert end_user_rbac(m)["group"] == "patients"


def test_non_dict_tenancy_is_ignored_by_readers():
    assert tenancy_mode({"name": "x", "tenancy": "shared_saas"}) == MODE_PER_TENANT


# ---------------------------------------------------------------------------
# The namespace gate (Resolution Q1) — the security-relevant check
# ---------------------------------------------------------------------------


def test_absent_block_is_valid():
    assert validate_tenancy_block({"name": "financial"}) == []


def test_per_tenant_is_valid():
    assert validate_tenancy_block({"name": "f", "tenancy": {"mode": MODE_PER_TENANT}}) == []


def test_own_namespace_permission_is_allowed():
    assert validate_tenancy_block(_shared_saas(permissions=["healthcare:portal:access"])) == []


def test_foreign_module_namespace_is_rejected():
    """A module may not grant its end users another module's permissions."""
    errors = validate_tenancy_block(_shared_saas(permissions=["financial:invoices:read"]))
    assert errors
    assert "must be namespaced to this module" in errors[0]


def test_platform_namespace_is_rejected():
    """The case that matters: a manifest granting its end users platform authority."""
    errors = validate_tenancy_block(_shared_saas(permissions=["system:users:delete"]))
    assert errors
    assert any("namespaced" in e for e in errors)


def test_namespace_check_is_not_a_prefix_trick():
    """'healthcare-evil:...' must not pass as the 'healthcare' namespace."""
    errors = validate_tenancy_block(_shared_saas(permissions=["healthcareevil:steal"]))
    assert errors


def test_shared_saas_requires_end_user_rbac():
    errors = validate_tenancy_block({"name": "x", "tenancy": {"mode": MODE_SHARED_SAAS}})
    assert errors
    assert "end_user_rbac" in errors[0]


def test_shared_saas_requires_role_and_group():
    m = {"name": "x", "tenancy": {"mode": MODE_SHARED_SAAS, "end_user_rbac": {"role": "patient"}}}
    errors = validate_tenancy_block(m)
    assert any("group" in e for e in errors)


def test_end_user_rbac_on_per_tenant_is_rejected():
    """Declaring end-user RBAC without shared_saas is a mistake worth surfacing."""
    m = {
        "name": "x",
        "tenancy": {"mode": MODE_PER_TENANT, "end_user_rbac": {"role": "r", "group": "g"}},
    }
    errors = validate_tenancy_block(m)
    assert errors
    assert "only meaningful" in errors[0]


def test_unknown_mode_is_rejected():
    errors = validate_tenancy_block({"name": "x", "tenancy": {"mode": "sneaky"}})
    assert any("tenancy.mode" in e for e in errors)


def test_permissions_must_be_a_list():
    m = _shared_saas()
    m["tenancy"]["end_user_rbac"]["permissions"] = "healthcare:portal:access"
    assert validate_tenancy_block(m)


def test_empty_permissions_is_valid():
    assert validate_tenancy_block(_shared_saas(permissions=[])) == []


# ---------------------------------------------------------------------------
# Resolution (D2/D3)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_shared_tenant_cache()
    yield
    reset_shared_tenant_cache()


def test_resolve_reads_the_tenant_code_then_caches():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = ("tenant-abc",)
    assert resolve_shared_tenant_id(db, module="healthcare") == "tenant-abc"
    assert resolve_shared_tenant_id(db, module="healthcare") == "tenant-abc"
    assert db.execute.call_count == 1  # cached after the first resolve


def test_every_module_resolves_the_same_tenant():
    """D2: one shared tenant platform-wide — the module arg is provenance only."""
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = ("tenant-abc",)
    assert resolve_shared_tenant_id(db, module="healthcare") == resolve_shared_tenant_id(
        db, module="financial"
    )


def test_resolve_falls_back_when_db_unreadable():
    db = MagicMock()
    db.execute.side_effect = RuntimeError("boom")
    assert resolve_shared_tenant_id(db) == "5aa50000-0000-4000-8000-000000000001"


def test_resolve_falls_back_when_row_missing():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = None
    assert resolve_shared_tenant_id(db) == "5aa50000-0000-4000-8000-000000000001"


def test_set_primes_the_cache():
    set_shared_tenant_id("primed-id")
    assert shared_tenant_id() == "primed-id"
    assert shared_tenant_id(module="healthcare") == "primed-id"
