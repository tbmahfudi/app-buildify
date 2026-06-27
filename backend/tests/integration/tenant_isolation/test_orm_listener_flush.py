"""
T-22.025 — Adversarial: ORM listener fires on write DML, and only for
``__tenant_scoped__`` models.

The listener guards SELECT *and* UPDATE/DELETE (sec-review-22 H-1: the previous
SELECT-only guard was a HIGH finding). These tests confirm:

  * INSERT (via flush), UPDATE, and DELETE on a scoped model with no scope set
    raise ``TenantScopeMissingError``.
  * The same operations under a valid scope succeed.
  * Operations on a NON-scoped model (``TenantModuleDatabase``) never trip the
    listener, even with no scope set — admin/provisioning code must keep working.
"""
import uuid

import pytest

from app.core.tenant.scope import _current_tenant_id, TenantScopeMissingError
from app.models.user import User
from app.models.tenant_module_database import TenantModuleDatabase

from .conftest import TENANT_A, make_user, seed_user


# --------------------------------------------------------------------------
# Scoped model: writes without scope must fail loud
# --------------------------------------------------------------------------

def test_insert_scoped_model_without_scope_raises(db):
    db.add(make_user(TENANT_A))
    with pytest.raises(TenantScopeMissingError):
        db.flush()
    db.rollback()


def test_update_scoped_model_without_scope_raises(db):
    user = seed_user(db, TENANT_A)
    # Scope is reset to None by the autouse fixture after seed_user.
    user.full_name = "Renamed Without Scope"
    db.add(user)
    with pytest.raises(TenantScopeMissingError):
        db.flush()
    db.rollback()


def test_delete_scoped_model_without_scope_raises(db):
    user = seed_user(db, TENANT_A)
    db.delete(user)
    with pytest.raises(TenantScopeMissingError):
        db.flush()
    db.rollback()


# --------------------------------------------------------------------------
# Scoped model: writes under valid scope succeed
# --------------------------------------------------------------------------

def test_insert_scoped_model_with_scope_succeeds(db):
    token = _current_tenant_id.set(TENANT_A)
    try:
        db.add(make_user(TENANT_A, email="ok@example.com"))
        db.commit()
    finally:
        _current_tenant_id.reset(token)

    # Verify the row landed (read back under scope).
    token = _current_tenant_id.set(TENANT_A)
    try:
        assert db.query(User).filter(User.email == "ok@example.com").count() == 1  # tenant-scope-ok
    finally:
        _current_tenant_id.reset(token)


# --------------------------------------------------------------------------
# Non-scoped model: listener must NOT fire
# --------------------------------------------------------------------------

def test_insert_non_scoped_model_without_scope_succeeds(db):
    """TenantModuleDatabase is NOT __tenant_scoped__ — admin scripts need it."""
    assert getattr(TenantModuleDatabase, "__tenant_scoped__", False) is False

    row = TenantModuleDatabase(
        id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        module_id=str(uuid.uuid4()),
        db_name="mod_financial_abcdef12",
        status="provisioning",
    )
    # No scope set, yet this must succeed.
    assert _current_tenant_id.get() is None
    db.add(row)
    db.commit()
    assert db.query(TenantModuleDatabase).count() == 1


def test_select_non_scoped_model_without_scope_succeeds(db):
    row = TenantModuleDatabase(
        id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        module_id=str(uuid.uuid4()),
        db_name="mod_x_00000000",
        status="ready",
    )
    db.add(row)
    db.commit()

    assert _current_tenant_id.get() is None
    rows = db.query(TenantModuleDatabase).all()  # would raise if listener fired
    assert len(rows) == 1
