"""
Unit tests for app/core/auth.py

Tests JWT creation, decoding, password hashing — no DB required.
"""
import time
import uuid
from datetime import timedelta

import jwt
import pytest

from app.core.auth import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import SECRET_KEY


# ── Password hashing ───────────────────────────────────────────────────────


def test_hash_password_returns_string():
    h = hash_password("secret")
    assert isinstance(h, str)
    assert h != "secret"


def test_hash_password_bcrypt_prefix():
    h = hash_password("secret")
    assert h.startswith("$2")


def test_verify_password_correct():
    h = hash_password("correct")
    assert verify_password("correct", h) is True


def test_verify_password_wrong():
    h = hash_password("correct")
    assert verify_password("wrong", h) is False


@pytest.mark.parametrize(
    "bad_hash",
    [
        "not-a-bcrypt-hash",           # unparseable garbage
        "",                            # empty stored hash
        "$2b$notbcrypt",               # bcrypt-looking but malformed
        "plaintext-password",          # legacy/unhashed value
    ],
)
def test_verify_password_malformed_hash_returns_false(bad_hash):
    # GH#673: a corrupt/unparseable stored hash must fail verification
    # (return False), never raise — otherwise login 500s.
    assert verify_password("anything", bad_hash) is False


def test_verify_password_non_string_hash_returns_false():
    # GH#673: a non-string stored hash (e.g. None) must not raise.
    assert verify_password("anything", None) is False


def test_hash_is_unique_per_call():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salts are random


# ── create_access_token ────────────────────────────────────────────────────


def test_create_access_token_returns_string():
    token = create_access_token({"sub": "user123"})
    assert isinstance(token, str)


def test_create_access_token_type_claim():
    token = create_access_token({"sub": "user123"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "access"


def test_create_access_token_has_jti():
    token = create_access_token({"sub": "user123"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "jti" in payload
    uuid.UUID(payload["jti"])  # must be valid UUID


def test_create_access_token_has_exp_and_iat():
    token = create_access_token({"sub": "user123"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "exp" in payload
    assert "iat" in payload


def test_create_access_token_preserves_custom_data():
    token = create_access_token({"sub": "u1", "tenant_id": "t1", "role": "admin"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "u1"
    assert payload["tenant_id"] == "t1"
    assert payload["role"] == "admin"


def test_create_access_token_custom_expiry():
    token = create_access_token({"sub": "u1"}, expires_delta=timedelta(hours=2))
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # exp should be roughly now + 2h (within a 5s window)
    assert payload["exp"] - payload["iat"] > 7100


def test_create_access_token_expired_raises():
    token = create_access_token({"sub": "u1"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ── create_refresh_token ───────────────────────────────────────────────────


def test_create_refresh_token_type_claim():
    token = create_refresh_token({"sub": "user123"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "refresh"


def test_create_refresh_token_has_jti():
    token = create_refresh_token({"sub": "user123"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "jti" in payload


def test_access_and_refresh_jti_differ():
    t1 = create_access_token({"sub": "u"})
    t2 = create_refresh_token({"sub": "u"})
    p1 = jwt.decode(t1, SECRET_KEY, algorithms=[ALGORITHM])
    p2 = jwt.decode(t2, SECRET_KEY, algorithms=[ALGORITHM])
    assert p1["jti"] != p2["jti"]


# ── decode_token ───────────────────────────────────────────────────────────


def test_decode_token_valid():
    token = create_access_token({"sub": "u1"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "u1"


def test_decode_token_expired_returns_none():
    token = create_access_token({"sub": "u1"}, expires_delta=timedelta(seconds=-1))
    assert decode_token(token) is None


def test_decode_token_wrong_key_returns_none():
    token = jwt.encode({"sub": "u1", "exp": 9999999999}, "wrong_key", algorithm=ALGORITHM)
    assert decode_token(token) is None


def test_decode_token_garbage_returns_none():
    assert decode_token("not.a.token") is None


def test_decode_token_empty_returns_none():
    assert decode_token("") is None


def test_decode_token_preserves_all_claims():
    token = create_access_token({"sub": "u1", "email": "a@b.com"})
    payload = decode_token(token)
    assert payload["email"] == "a@b.com"
    assert payload["type"] == "access"
    assert "jti" in payload
