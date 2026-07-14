"""
Unit tests for the channel-aware OTP core (ADR-011 S4): email channel,
``purpose="mfa"``, per-target daily cap (R6), attempt lockout (R7).

Uses an in-memory fake Redis and stubs dispatch so no SMTP/threads run.
"""
import pytest
from fastapi import HTTPException

from app.routers import otp


class FakePipeline:
    def __init__(self, store):
        self._store = store
        self._ops = []

    def set(self, k, v, ex=None):
        self._ops.append(("set", k, v))
        return self

    def delete(self, k):
        self._ops.append(("delete", k))
        return self

    def incr(self, k):
        self._ops.append(("incr", k))
        return self

    def execute(self):
        for op in self._ops:
            if op[0] == "set":
                self._store[op[1]] = op[2]
            elif op[0] == "delete":
                self._store.pop(op[1], None)
            elif op[0] == "incr":
                self._store[op[1]] = str(int(self._store.get(op[1], 0)) + 1)
        self._ops = []


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, k):
        return self.store.get(k)

    def set(self, k, v, ex=None):
        self.store[k] = str(v)

    def exists(self, k):
        return 1 if k in self.store else 0

    def ttl(self, k):
        return 42 if k in self.store else -2

    def incr(self, k):
        self.store[k] = str(int(self.store.get(k, 0)) + 1)
        return int(self.store[k])

    def expire(self, k, t):
        return True

    def delete(self, k):
        self.store.pop(k, None)

    def pipeline(self):
        return FakePipeline(self.store)


@pytest.fixture
def fake(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(otp, "get_redis", lambda: r)
    calls = []
    monkeypatch.setattr(otp, "_dispatch", lambda ch, tgt, code, purpose: calls.append((ch, tgt, code, purpose)))
    return r, calls


def test_send_email_mfa_dispatches_and_stores_code(fake):
    r, calls = fake
    resend = otp.send_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1")
    assert resend == otp.COOLDOWN_TTL
    assert len(calls) == 1 and calls[0][0] == "email" and calls[0][3] == "mfa"
    # code stored under the channel-aware key
    assert r.get(otp._code_key("mfa", "email", "t1", "a@b.com")) is not None


def test_unknown_channel_rejected(fake):
    with pytest.raises(HTTPException) as ei:
        otp.send_otp(channel="carrier-pigeon", target="x", purpose="mfa", tenant_code="t1")
    assert ei.value.status_code == 400


def test_unknown_purpose_rejected(fake):
    with pytest.raises(HTTPException) as ei:
        otp.send_otp(channel="email", target="a@b.com", purpose="bogus", tenant_code="t1")
    assert ei.value.status_code == 400


def test_cooldown_blocks_immediate_resend(fake):
    r, _ = fake
    otp.send_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1")
    with pytest.raises(HTTPException) as ei:
        otp.send_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1")
    assert ei.value.status_code == 429


def test_daily_cap_blocks_after_limit(fake, monkeypatch):
    r, _ = fake
    monkeypatch.setattr(otp, "DAILY_CAP", 2)
    # Pre-load the daily counter to the cap; a fresh send must be refused.
    r.store[otp._daily_key("email", "a@b.com")] = "2"
    with pytest.raises(HTTPException) as ei:
        otp.send_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1")
    assert ei.value.status_code == 429


def test_channels_have_separate_buckets(fake):
    r, calls = fake
    otp.send_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1")
    # Same purpose/tenant but a *phone* target is an independent bucket — no cooldown clash.
    otp.send_otp(channel="phone", target="+12345678", purpose="mfa", tenant_code="t1")
    assert len(calls) == 2


def test_verify_happy_path_returns_token_and_consumes_code(fake):
    r, _ = fake
    otp.send_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1")
    code = r.get(otp._code_key("mfa", "email", "t1", "a@b.com"))
    token = otp.verify_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1", code=code)
    assert token
    # code consumed
    assert r.get(otp._code_key("mfa", "email", "t1", "a@b.com")) is None


def test_verify_wrong_code_increments_attempts_and_400(fake):
    r, _ = fake
    otp.send_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1")
    real = r.get(otp._code_key("mfa", "email", "t1", "a@b.com"))
    wrong = "000000" if real != "000000" else "111111"
    with pytest.raises(HTTPException) as ei:
        otp.verify_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1", code=wrong)
    assert ei.value.status_code == 400
    assert r.get(otp._attempts_key("mfa", "email", "t1", "a@b.com")) == "1"


def test_verify_expired_or_missing_code_400(fake):
    with pytest.raises(HTTPException) as ei:
        otp.verify_otp(channel="email", target="a@b.com", purpose="mfa", tenant_code="t1", code="123456")
    assert ei.value.status_code == 400
