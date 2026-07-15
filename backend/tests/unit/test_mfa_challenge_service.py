"""Unit tests for the MFA login challenge (ADR-HC-009 D3).

The properties under test are the ones that keep a half-authenticated caller from
becoming an authenticated one: the challenge token is not an access token, it is
single-use, and it cannot be forged.
"""
import uuid
from datetime import datetime, timedelta

import jwt
import pytest

from app.core.auth import ALGORITHM, create_access_token
from app.core.config import SECRET_KEY
from app.services import mfa_challenge_service as mcs


class FakeRedis:
    def __init__(self):
        self.store = {}

    def setex(self, k, ttl, v):
        self.store[k] = v

    def exists(self, k):
        return 1 if k in self.store else 0

    def delete(self, k):
        return 1 if self.store.pop(k, None) is not None else 0


@pytest.fixture
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(mcs.otp, "get_redis", lambda: r)
    return r


def _mint(user_id="u1", factor_id="f1", ttl=300, token_type=mcs.TOKEN_TYPE, jti=None):
    now = datetime.utcnow()
    return jwt.encode(
        {
            "sub": user_id,
            "type": token_type,
            "jti": jti or str(uuid.uuid4()),
            "factor_id": factor_id,
            "iat": now,
            "exp": now + timedelta(seconds=ttl),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def test_validate_accepts_a_registered_challenge(fake_redis):
    jti = str(uuid.uuid4())
    token = _mint(jti=jti)
    fake_redis.setex(mcs._redis_key(jti), 300, "u1")

    user_id, factor_id, got_jti = mcs.validate_challenge(token)
    assert (user_id, factor_id, got_jti) == ("u1", "f1", jti)


def test_an_access_token_is_not_a_challenge(fake_redis):
    """The whole point of a distinct type: a real token must not open this door."""
    access = create_access_token({"sub": "u1"})
    with pytest.raises(mcs.ChallengeError):
        mcs.validate_challenge(access)


def test_wrong_token_type_rejected(fake_redis):
    jti = str(uuid.uuid4())
    token = _mint(jti=jti, token_type="refresh")
    fake_redis.setex(mcs._redis_key(jti), 300, "u1")
    with pytest.raises(mcs.ChallengeError):
        mcs.validate_challenge(token)


def test_expired_challenge_rejected(fake_redis):
    jti = str(uuid.uuid4())
    token = _mint(jti=jti, ttl=-10)
    fake_redis.setex(mcs._redis_key(jti), 300, "u1")
    with pytest.raises(mcs.ChallengeError):
        mcs.validate_challenge(token)


def test_forged_signature_rejected(fake_redis):
    now = datetime.utcnow()
    token = jwt.encode(
        {"sub": "u1", "type": mcs.TOKEN_TYPE, "jti": "j", "factor_id": "f", "exp": now + timedelta(seconds=300)},
        "not-the-app-secret",
        algorithm=ALGORITHM,
    )
    with pytest.raises(mcs.ChallengeError):
        mcs.validate_challenge(token)


def test_unregistered_jti_rejected(fake_redis):
    """A structurally valid token that was never issued (or already burned)."""
    token = _mint()
    with pytest.raises(mcs.ChallengeError):
        mcs.validate_challenge(token)


def test_garbage_token_rejected(fake_redis):
    with pytest.raises(mcs.ChallengeError):
        mcs.validate_challenge("not-a-jwt")


def test_burn_makes_the_challenge_single_use(fake_redis):
    jti = str(uuid.uuid4())
    token = _mint(jti=jti)
    fake_redis.setex(mcs._redis_key(jti), 300, "u1")

    mcs.validate_challenge(token)          # first use: fine
    assert mcs.burn_challenge(jti) is True

    with pytest.raises(mcs.ChallengeError):  # replay: refused
        mcs.validate_challenge(token)


def test_burn_twice_only_wins_once(fake_redis):
    """Two concurrent verifies must not both mint a session."""
    jti = str(uuid.uuid4())
    fake_redis.setex(mcs._redis_key(jti), 300, "u1")
    assert mcs.burn_challenge(jti) is True
    assert mcs.burn_challenge(jti) is False


def test_validate_does_not_burn(fake_redis):
    """A wrong code must not cost the user their challenge (and another SMS)."""
    jti = str(uuid.uuid4())
    token = _mint(jti=jti)
    fake_redis.setex(mcs._redis_key(jti), 300, "u1")

    for _ in range(3):
        mcs.validate_challenge(token)
    assert fake_redis.exists(mcs._redis_key(jti)) == 1


@pytest.mark.parametrize(
    "factor_type,target,expected",
    [
        ("email_otp", "jonathan@example.com", "j***n@example.com"),
        ("email_otp", "ab@example.com", "a*@example.com"),
        ("email_otp", "a@example.com", "a*@example.com"),
        ("phone_otp", "+6281234567890", "***********890"),
    ],
)
def test_mask_target_hides_the_address_but_stays_recognizable(factor_type, target, expected):
    assert mcs.mask_target(factor_type, target) == expected


def test_mask_target_leaks_nothing_for_empty():
    assert mcs.mask_target("email_otp", "") == ""
