"""
Unit tests for app/services/account_service.py (ADR-011 S1).

Uses a mocked Session + a real env password policy — no DB required.
"""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security_config import load_from_env
from app.services.account_service import (
    AccountExistsError,
    WeakPasswordError,
    create_patient_account,
)

POLICY = load_from_env().password  # env baseline (min_length 12, mixed classes)
STRONG = "Xy9$kLmn2Pqr"            # satisfies the baseline policy
TENANT = "11111111-1111-1111-1111-111111111111"


def _mock_db():
    """A Session mock whose begin_nested() is a real (non-suppressing) context manager."""
    db = MagicMock(spec=Session)
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)  # must NOT swallow exceptions
    db.begin_nested.return_value = cm
    return db


def test_missing_email_raises_value_error():
    with pytest.raises(ValueError):
        create_patient_account(
            _mock_db(), tenant_id=TENANT, email="  ", password=STRONG, full_name="A B", policy=POLICY
        )


def test_missing_full_name_raises_value_error():
    with pytest.raises(ValueError):
        create_patient_account(
            _mock_db(), tenant_id=TENANT, email="a@b.com", password=STRONG, full_name="  ", policy=POLICY
        )


def test_weak_password_raises_before_touching_db():
    db = _mock_db()
    with pytest.raises(WeakPasswordError) as ei:
        create_patient_account(
            db, tenant_id=TENANT, email="a@b.com", password="short", full_name="A B", policy=POLICY
        )
    assert ei.value.errors  # carries policy messages
    db.add.assert_not_called()  # no row attempted on a policy failure


def test_success_creates_active_unverified_patient_user():
    db = _mock_db()
    user = create_patient_account(
        db,
        tenant_id=TENANT,
        email="  New.Patient@Example.COM ",
        password=STRONG,
        full_name="  New Patient  ",
        username="newpatient",
        policy=POLICY,
    )
    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert added is user
    assert user.email == "new.patient@example.com"   # normalized
    assert user.full_name == "New Patient"           # trimmed
    assert user.is_active is True
    assert user.is_verified is False                 # activation is a separate step
    assert user.must_set_password is False           # registrant chose a password
    assert user.tenant_id == TENANT
    assert user.hashed_password and user.hashed_password != STRONG  # hashed, not plaintext


def test_duplicate_email_raises_account_exists():
    db = _mock_db()
    db.flush.side_effect = IntegrityError("INSERT", {}, Exception("duplicate key"))
    with pytest.raises(AccountExistsError):
        create_patient_account(
            db, tenant_id=TENANT, email="dupe@b.com", password=STRONG, full_name="A B", policy=POLICY
        )
