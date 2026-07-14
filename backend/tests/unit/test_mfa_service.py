"""
Unit tests for app/services/mfa_service.py (ADR-011 S4).

Mocked Session, no DB — mirrors test_account_service.py.
"""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.services import mfa_service
from app.services.mfa_service import (
    AlreadyEnrolledError,
    InvalidFactorError,
)

USER = "11111111-1111-1111-1111-111111111111"


def _mock_db(first_result=None):
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = first_result
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    return db


# --- channel + target normalization ---------------------------------------- #

def test_channel_for_factor():
    assert mfa_service.channel_for_factor("phone_otp") == "phone"
    assert mfa_service.channel_for_factor("email_otp") == "email"


def test_channel_for_unknown_factor_raises():
    with pytest.raises(InvalidFactorError):
        mfa_service.channel_for_factor("totp")


def test_normalize_email_lowercased():
    assert mfa_service.normalize_target("email_otp", "  Foo@Bar.COM ") == "foo@bar.com"


@pytest.mark.parametrize("bad", ["", "   ", "notanemail", "@no-local", "no-domain@"])
def test_normalize_email_rejects_bad(bad):
    with pytest.raises(InvalidFactorError):
        mfa_service.normalize_target("email_otp", bad)


def test_normalize_phone_ok():
    assert mfa_service.normalize_target("phone_otp", "  +12345678  ") == "+12345678"
    assert mfa_service.normalize_target("phone_otp", "12345678") == "12345678"


@pytest.mark.parametrize("bad", ["", "12345", "phone", "+++"])
def test_normalize_phone_rejects_bad(bad):
    with pytest.raises(InvalidFactorError):
        mfa_service.normalize_target("phone_otp", bad)


# --- enroll (get_or_create_pending_factor) --------------------------------- #

def test_enroll_creates_inactive_factor():
    db = _mock_db(first_result=None)
    factor, channel = mfa_service.get_or_create_pending_factor(
        db, user_id=USER, factor_type="email_otp", target="Me@Ex.com"
    )
    assert channel == "email"
    assert factor.is_active is False
    assert factor.factor_type == "email_otp"
    assert factor.target == "me@ex.com"  # normalized
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_enroll_reuses_existing_pending_factor():
    existing = MagicMock(is_active=False)
    db = _mock_db(first_result=existing)
    factor, channel = mfa_service.get_or_create_pending_factor(
        db, user_id=USER, factor_type="phone_otp", target="+12345678"
    )
    assert factor is existing
    assert channel == "phone"
    db.add.assert_not_called()  # no new row


def test_enroll_active_factor_raises_already_enrolled():
    existing = MagicMock(is_active=True)
    db = _mock_db(first_result=existing)
    with pytest.raises(AlreadyEnrolledError):
        mfa_service.get_or_create_pending_factor(
            db, user_id=USER, factor_type="phone_otp", target="+12345678"
        )


def test_enroll_bad_factor_type_raises_before_db():
    db = _mock_db()
    with pytest.raises(InvalidFactorError):
        mfa_service.get_or_create_pending_factor(
            db, user_id=USER, factor_type="totp", target="x"
        )
    db.add.assert_not_called()


# --- activate / disable ---------------------------------------------------- #

def test_activate_sets_active_and_verified_at():
    db = MagicMock(spec=Session)
    factor = MagicMock(is_active=False, verified_at=None)
    mfa_service.activate_factor(db, factor)
    assert factor.is_active is True
    assert factor.verified_at is not None
    db.commit.assert_called_once()


def test_disable_returns_false_when_not_found():
    db = _mock_db(first_result=None)
    assert mfa_service.disable_factor(db, USER, "nope") is False
    db.delete.assert_not_called()


def test_disable_deletes_when_found():
    factor = MagicMock()
    db = _mock_db(first_result=factor)
    assert mfa_service.disable_factor(db, USER, "abc") is True
    db.delete.assert_called_once_with(factor)
    db.commit.assert_called_once()
