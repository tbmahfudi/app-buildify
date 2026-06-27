"""
T-22.023 — Adversarial: cross-tenant SELECT.

A SELECT against a ``__tenant_scoped__`` model executed while the ContextVar
holds *another* tenant's id must return nothing for the foreign tenant's rows
(the listener injects ``WHERE tenant_id = :scope``). With no scope set at all the
listener fails loud. The ``__superuser__`` sentinel bypasses scoping entirely.
"""
import pytest

from app.core.tenant.scope import _current_tenant_id, TenantScopeMissingError
from app.models.user import User

from .conftest import TENANT_A, TENANT_B, seed_user


def _scoped(session, tenant):
    """Run a User query under the given scope, returning all visible rows."""
    token = _current_tenant_id.set(tenant)
    try:
        return session.query(User).all()
    finally:
        _current_tenant_id.reset(token)


def test_select_under_own_scope_sees_own_rows(db):
    seed_user(db, TENANT_A, email="a@example.com")
    seed_user(db, TENANT_B, email="b@example.com")

    rows = _scoped(db, TENANT_A)
    emails = {u.email for u in rows}
    assert "a@example.com" in emails
    assert "b@example.com" not in emails
    assert all(str(u.tenant_id) == TENANT_A for u in rows)


def test_select_with_other_tenant_scope_returns_empty(db):
    """Tenant A's rows are invisible when querying under Tenant B's scope."""
    seed_user(db, TENANT_A, email="only-a@example.com")

    rows = _scoped(db, TENANT_B)
    assert rows == []  # foreign tenant cannot see A's row


def test_select_cannot_be_widened_by_explicit_filter(db):
    """Even an explicit filter for tenant A is intersected with the scope filter."""
    seed_user(db, TENANT_A, email="target@example.com")

    token = _current_tenant_id.set(TENANT_B)
    try:
        # Caller tries to reach tenant A explicitly; listener ANDs in tenant B.
        rows = db.query(User).filter(User.tenant_id == TENANT_A).all()  # tenant-scope-ok
    finally:
        _current_tenant_id.reset(token)
    assert rows == []


def test_select_without_scope_raises(db):
    seed_user(db, TENANT_A)
    # ContextVar is None (autouse reset fixture) -> fail loud.
    with pytest.raises(TenantScopeMissingError):
        db.query(User).all()


def test_superuser_bypass_sees_all_tenants(db):
    seed_user(db, TENANT_A, email="a@example.com")
    seed_user(db, TENANT_B, email="b@example.com")

    token = _current_tenant_id.set("__superuser__")
    try:
        rows = db.query(User).all()
    finally:
        _current_tenant_id.reset(token)

    emails = {u.email for u in rows}
    assert {"a@example.com", "b@example.com"} <= emails
