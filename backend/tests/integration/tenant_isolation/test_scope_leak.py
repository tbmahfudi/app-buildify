"""
T-22.024 — Adversarial: scope leak.

Verifies the ContextVar that backs tenant scope cannot leak past the boundary
that set it:

  * ``with_tenant_scope`` restores the previous value on normal exit AND on
    exception (no leak even when the body raises).
  * ``with_admin_cross_tenant_scope`` clears the ``__superuser__`` sentinel on
    exit, including when the body raises — a leaked sentinel would silently
    disable all tenant filtering for subsequent queries on the same context.
  * A simulated request that sets scope and then clears it in ``finally`` leaves
    the ContextVar at ``None`` afterwards.
"""
import pytest

from app.core.tenant.scope import (
    _current_tenant_id,
    with_tenant_scope,
    with_admin_cross_tenant_scope,
    set_tenant_scope,
    clear_tenant_scope,
    get_tenant_scope,
    TenantScopeNotSetError,
)

from .conftest import TENANT_A, TENANT_B


class _SU:
    is_superuser = True
    id = "su-1"


def test_with_tenant_scope_restores_on_normal_exit():
    assert _current_tenant_id.get() is None
    with with_tenant_scope(TENANT_A):
        assert _current_tenant_id.get() == TENANT_A
    assert _current_tenant_id.get() is None


def test_with_tenant_scope_restores_on_exception():
    assert _current_tenant_id.get() is None
    with pytest.raises(RuntimeError):
        with with_tenant_scope(TENANT_A):
            assert _current_tenant_id.get() == TENANT_A
            raise RuntimeError("boom")
    # Must be cleaned up despite the exception — no leak.
    assert _current_tenant_id.get() is None


def test_nested_scope_restores_outer_value():
    with with_tenant_scope(TENANT_A):
        assert _current_tenant_id.get() == TENANT_A
        with with_tenant_scope(TENANT_B):
            assert _current_tenant_id.get() == TENANT_B
        # inner exit restores the outer tenant, not None
        assert _current_tenant_id.get() == TENANT_A
    assert _current_tenant_id.get() is None


def test_admin_cross_tenant_scope_clears_sentinel_on_exit():
    audit = []
    with with_admin_cross_tenant_scope(_SU(), "investigation", _rec(audit)):
        assert _current_tenant_id.get() == "__superuser__"
    assert _current_tenant_id.get() is None
    actions = [a["action"] for a in audit]
    assert actions == ["tenant.cross_scope.enter", "tenant.cross_scope.exit"]


def test_admin_cross_tenant_scope_clears_sentinel_on_exception():
    audit = []
    with pytest.raises(ValueError):
        with with_admin_cross_tenant_scope(_SU(), "investigation", _rec(audit)):
            assert _current_tenant_id.get() == "__superuser__"
            raise ValueError("body failed")
    # Sentinel must NOT leak — a leaked '__superuser__' disables all filtering.
    assert _current_tenant_id.get() is None
    # exit audit entry still written on the exception path
    assert [a["action"] for a in audit] == [
        "tenant.cross_scope.enter",
        "tenant.cross_scope.exit",
    ]


def test_set_then_clear_leaves_none():
    set_tenant_scope(TENANT_A)
    assert get_tenant_scope() == TENANT_A
    clear_tenant_scope()
    assert _current_tenant_id.get() is None
    with pytest.raises(TenantScopeNotSetError):
        get_tenant_scope()


def test_simulated_request_clears_scope_in_finally():
    """Mirrors tenant_scoped_session: set on entry, clear in finally."""
    def handle_request(tenant_id, should_raise=False):
        set_tenant_scope(tenant_id)
        try:
            if should_raise:
                raise RuntimeError("handler error")
        finally:
            clear_tenant_scope()

    handle_request(TENANT_A)
    assert _current_tenant_id.get() is None

    with pytest.raises(RuntimeError):
        handle_request(TENANT_B, should_raise=True)
    assert _current_tenant_id.get() is None


def _rec(sink):
    """Return an audit_log_fn that records (action, details) into ``sink``."""
    def _fn(action, details=None, **kw):
        sink.append({"action": action, "details": details})

    return _fn
