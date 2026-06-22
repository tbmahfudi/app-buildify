"""
Unit tests for app/core/audit.py

Uses an in-memory SQLite session for create_audit_log;
compute_diff is pure Python.
"""
import json
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.audit import compute_diff, create_audit_log
from app.models.base import Base


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


USER_ID = "550e8400-e29b-41d4-a716-446655440001"
TENANT_ID = "550e8400-e29b-41d4-a716-446655440002"
ENTITY_ID = "550e8400-e29b-41d4-a716-446655440003"


def _mock_user(user_id=USER_ID, email="test@example.com", tenant_id=TENANT_ID):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.tenant_id = tenant_id
    return user


# ── compute_diff ──────────────────────────────────────────────────────────


def test_compute_diff_changed_field():
    diff = compute_diff({"name": "old"}, {"name": "new"})
    assert diff == {"name": {"before": "old", "after": "new"}}


def test_compute_diff_added_field():
    diff = compute_diff({}, {"key": "value"})
    assert diff == {"key": {"before": None, "after": "value"}}


def test_compute_diff_removed_field():
    diff = compute_diff({"key": "value"}, {})
    assert diff == {"key": {"before": "value", "after": None}}


def test_compute_diff_unchanged_field_not_included():
    diff = compute_diff({"a": 1, "b": 2}, {"a": 1, "b": 3})
    assert "a" not in diff
    assert "b" in diff


def test_compute_diff_empty_both():
    assert compute_diff({}, {}) == {}


def test_compute_diff_multiple_changes():
    diff = compute_diff({"a": 1, "b": 2}, {"a": 9, "b": 2, "c": 3})
    assert set(diff.keys()) == {"a", "c"}
    assert diff["a"]["before"] == 1
    assert diff["a"]["after"] == 9
    assert diff["c"]["before"] is None
    assert diff["c"]["after"] == 3


def test_compute_diff_type_change():
    diff = compute_diff({"val": "str"}, {"val": 42})
    assert diff["val"]["before"] == "str"
    assert diff["val"]["after"] == 42


# ── create_audit_log — no request, no user ────────────────────────────────


def test_create_audit_log_minimal(db):
    log = create_audit_log(db, action="test.action")
    assert log is not None
    assert log.action == "test.action"
    assert log.user_id is None
    assert log.user_email is None
    assert log.ip_address is None
    assert log.status == "success"


def test_create_audit_log_returns_persisted_object(db):
    log = create_audit_log(db, action="entity.create")
    assert log.id is not None


def test_create_audit_log_custom_status(db):
    log = create_audit_log(db, action="login.fail", status="failure",
                           error_message="Bad credentials")
    assert log.status == "failure"
    assert log.error_message == "Bad credentials"


# ── create_audit_log — with user ─────────────────────────────────────────


def test_create_audit_log_with_user(db):
    uid = "550e8400-e29b-41d4-a716-446655440011"
    tid = "550e8400-e29b-41d4-a716-446655440012"
    user = _mock_user(user_id=uid, email="admin@test.com", tenant_id=tid)
    log = create_audit_log(db, action="user.update", user=user)
    assert log.user_email == "admin@test.com"
    assert log.user_id is not None
    assert log.tenant_id is not None


def test_create_audit_log_user_no_tenant(db):
    user = _mock_user(tenant_id=None)
    log = create_audit_log(db, action="action", user=user)
    assert log.tenant_id is None


# ── create_audit_log — entity info ───────────────────────────────────────


def test_create_audit_log_entity_info(db):
    log = create_audit_log(db, action="record.delete",
                           entity_type="Invoice", entity_id=ENTITY_ID)
    assert log.entity_type == "Invoice"
    assert log.entity_id is not None


def test_create_audit_log_changes_serialised(db):
    changes = {"amount": {"before": 100, "after": 200}}
    log = create_audit_log(db, action="record.update", changes=changes)
    parsed = json.loads(log.changes)
    assert parsed["amount"]["after"] == 200


def test_create_audit_log_context_info_serialised(db):
    ctx = {"reason": "bulk import", "batch_id": "b1"}
    log = create_audit_log(db, action="import.run", context_info=ctx)
    parsed = json.loads(log.context_info)
    assert parsed["reason"] == "bulk import"


# ── create_audit_log — with request ──────────────────────────────────────


def test_create_audit_log_with_request(db):
    request = MagicMock()
    request.client.host = "192.168.1.1"
    request.headers = {"user-agent": "TestBrowser/1.0"}

    log = create_audit_log(db, action="login.success", request=request)
    assert log.ip_address == "192.168.1.1"
    assert log.user_agent == "TestBrowser/1.0"


def test_create_audit_log_request_no_client(db):
    request = MagicMock()
    request.client = None
    request.headers = {}

    log = create_audit_log(db, action="action", request=request)
    assert log.ip_address is None


# ── create_audit_log — request_id uniqueness ──────────────────────────────


def test_create_audit_log_request_id_unique(db):
    log1 = create_audit_log(db, action="a")
    log2 = create_audit_log(db, action="b")
    assert log1.request_id != log2.request_id
