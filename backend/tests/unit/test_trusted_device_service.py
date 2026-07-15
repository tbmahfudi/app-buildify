"""Unit tests for the trusted-device store (ADR-HC-009 D4).

Covers the properties that make "remember this device" safe to persist: the raw
secret never reaches the database, a trust is scoped to one user, and expiry /
revocation actually stop suppressing the MFA challenge.

Uses an in-memory SQLite session so no live stack is needed.
"""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user_trusted_device import UserTrustedDevice
from app.services import trusted_device_service as tds


class FakeUser:
    """Stands in for a User row — the service only reads .id and .tenant_id."""

    def __init__(self, user_id=None, tenant_id=None):
        self.id = user_id or str(uuid.uuid4())
        self.tenant_id = tenant_id


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    # Only the one table is under test; the rest of the metadata needs a live PG.
    UserTrustedDevice.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def no_security_config(monkeypatch):
    """window_days() consults SecurityConfigService, which needs real tables."""
    monkeypatch.setattr(tds, "window_days", lambda db, user: tds.DEFAULT_TRUST_DAYS)


def test_remember_device_never_stores_the_raw_secret(db):
    user = FakeUser()
    raw = tds.remember_device(db, user)

    row = db.query(UserTrustedDevice).one()
    assert row.device_hash != raw, "the raw secret must not be the stored value"
    assert raw not in row.device_hash
    # What IS stored is the keyed HMAC of the secret.
    assert row.device_hash == tds._hash_secret(raw)


def test_secret_is_high_entropy_and_unique(db):
    user = FakeUser()
    secrets_seen = {tds.remember_device(db, FakeUser()) for _ in range(5)}
    assert len(secrets_seen) == 5
    assert all(len(s) > 30 for s in secrets_seen)


def test_is_trusted_matches_the_minted_secret(db):
    user = FakeUser()
    raw = tds.remember_device(db, user)
    assert tds.is_trusted(db, user, raw) is True


def test_is_trusted_rejects_unknown_or_missing_secret(db):
    user = FakeUser()
    tds.remember_device(db, user)
    assert tds.is_trusted(db, user, "not-the-secret") is False
    assert tds.is_trusted(db, user, None) is False
    assert tds.is_trusted(db, user, "") is False


def test_trust_is_scoped_to_its_user(db):
    """A cookie minted for one account must never suppress MFA on another."""
    alice, bob = FakeUser(), FakeUser()
    alice_secret = tds.remember_device(db, alice)
    assert tds.is_trusted(db, alice, alice_secret) is True
    assert tds.is_trusted(db, bob, alice_secret) is False


def test_expired_trust_is_not_honoured(db):
    user = FakeUser()
    raw = tds.remember_device(db, user)
    row = db.query(UserTrustedDevice).one()
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    assert tds.is_trusted(db, user, raw) is False


def test_revoked_trust_is_not_honoured(db):
    user = FakeUser()
    raw = tds.remember_device(db, user)
    assert tds.revoke_all(db, user) == 1
    assert tds.is_trusted(db, user, raw) is False


def test_default_window_is_30_days(db):
    user = FakeUser()
    tds.remember_device(db, user)
    row = db.query(UserTrustedDevice).one()
    delta = row.expires_at - row.created_at if row.created_at else None
    # created_at is a server_default; compare against now instead.
    assert (row.expires_at - datetime.utcnow()).days == 29  # 29.99... days out


def test_is_trusted_slides_last_used_at(db):
    user = FakeUser()
    raw = tds.remember_device(db, user)
    row = db.query(UserTrustedDevice).one()
    row.last_used_at = datetime.utcnow() - timedelta(days=5)
    db.commit()
    before = row.last_used_at

    tds.is_trusted(db, user, raw)
    db.refresh(row)
    assert row.last_used_at > before


def test_revoke_all_returns_count_and_is_idempotent(db):
    user = FakeUser()
    tds.remember_device(db, user)
    tds.remember_device(db, user)
    assert tds.revoke_all(db, user) == 2
    # Already revoked -> nothing left to revoke.
    assert tds.revoke_all(db, user) == 0


def test_revoke_all_only_touches_its_own_user(db):
    alice, bob = FakeUser(), FakeUser()
    tds.remember_device(db, alice)
    bob_secret = tds.remember_device(db, bob)
    tds.revoke_all(db, alice)
    assert tds.is_trusted(db, bob, bob_secret) is True


def test_revoke_device_is_scoped_to_its_owner(db):
    """Device ids must not be addressable across users."""
    alice, bob = FakeUser(), FakeUser()
    tds.remember_device(db, alice)
    alice_row = db.query(UserTrustedDevice).one()
    assert tds.revoke_device(db, bob, str(alice_row.id)) is False
    assert tds.revoke_device(db, alice, str(alice_row.id)) is True


def test_revoke_device_unknown_id(db):
    user = FakeUser()
    assert tds.revoke_device(db, user, str(uuid.uuid4())) is False


def test_list_devices_hides_revoked_and_expired(db):
    user = FakeUser()
    tds.remember_device(db, user)
    tds.remember_device(db, user)
    assert len(tds.list_devices(db, user)) == 2

    tds.revoke_all(db, user)
    assert tds.list_devices(db, user) == []


@pytest.mark.parametrize(
    "ua,expected",
    [
        ("Mozilla/5.0 (Windows NT 10.0) Chrome/120 Safari/537", "Chrome on Windows"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/604", "Safari on iOS"),
        ("Mozilla/5.0 (X11; Linux x86_64) Firefox/121", "Firefox on Linux"),
        (None, None),
    ],
)
def test_label_from_user_agent(ua, expected):
    assert tds._label_from_user_agent(ua) == expected
