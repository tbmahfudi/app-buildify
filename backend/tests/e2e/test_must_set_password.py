"""
E2E — ADR-HC-009 D7 `must_set_password` login gate (GH#693).

**This file previously pinned the bug.** The gate used to fire immediately after the user
lookup — *before* the credential check — so a wrong password against a backfilled account
returned `403 must_set_password` while a wrong password against an unknown address returned
401. That difference is an enumeration oracle: anybody could ask the public login form
"is this person a patient here?" and read the answer off the status code. For a healthcare
portal, mere membership is the sensitive fact.

The gate now runs **after** `verify_password`:

* wrong password → the same generic 401 as any stranger, whatever the account's state;
* right password + flag → the actionable 403, to a caller who already proved the credential
  (telling them is not a leak);
* a backfilled account can never reach the 403 at all — it carries an unusable hash, so it
  fails the credential check first. Its claim prompt arrives on the *authenticated* OTP path
  instead (`PatientTokenResponse.must_set_password`), which is where epic-18 Story 18.9.1
  specifies it.

The gate was moved rather than deleted: an account that has a real password AND the flag
must still be stopped from signing in.
"""
import os
import uuid

import pytest

PLACEHOLDER_LOGIN = "irrelevant123"
REAL_PASSWORD = "Kn0wn$Passw0rd!x"


def _connect():
    url = os.environ.get("SQLALCHEMY_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("No DB URL available for the must_set_password fixture")
    import psycopg2

    dsn = (
        url.replace("postgresql+psycopg2://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )
    return psycopg2.connect(dsn)


def _set_flag(user_id: str, value: bool) -> None:
    conn = _connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET must_set_password = %s WHERE id = %s", (value, user_id))
    finally:
        conn.close()


def _unusable_hash() -> str:
    """A valid-format but unusable bcrypt hash, mirroring what the D7 backfill writes —
    so verify_password returns False cleanly rather than erroring on a malformed hash."""
    from passlib.hash import bcrypt

    return bcrypt.hash(uuid.uuid4().hex)


def _hash(pw: str) -> str:
    from passlib.hash import bcrypt

    return bcrypt.hash(pw)


def _make_user(hashed: str, flagged: bool) -> dict:
    uid = str(uuid.uuid4())
    email = f"e2e-mustset-{uuid.uuid4().hex[:8]}@example.com"
    conn = _connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, email, hashed_password, must_set_password, is_active) "
                "VALUES (%s, %s, %s, %s, true)",
                (uid, email, hashed, flagged),
            )
    finally:
        conn.close()
    return {"id": uid, "email": email}


def _drop_user(uid: str) -> None:
    conn = _connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (uid,))
    finally:
        conn.close()


@pytest.fixture
def backfilled_user():
    """A backfilled account: flag set, unusable credential — what the D7 script creates."""
    u = _make_user(_unusable_hash(), True)
    yield u
    _drop_user(u["id"])


@pytest.fixture
def flagged_user_with_password():
    """Flag set BUT a working password — the case the gate still has to stop."""
    u = _make_user(_hash(REAL_PASSWORD), True)
    yield u
    _drop_user(u["id"])


class TestNoEnumerationOracle:
    """GH#693 — account state must not be readable from the unauthenticated login form."""

    def test_backfilled_account_wrong_password_is_generic_401(self, anon, backfilled_user):
        r = anon.post(
            "/auth/login", json={"email": backfilled_user["email"], "password": PLACEHOLDER_LOGIN}
        )
        assert r.status_code == 401, (
            f"a backfilled account leaked its state on a wrong password: {r.text}"
        )

    def test_response_is_indistinguishable_from_an_unknown_account(self, anon, backfilled_user):
        """The actual oracle test: backfilled vs. nonexistent must look identical."""
        known = anon.post(
            "/auth/login", json={"email": backfilled_user["email"], "password": PLACEHOLDER_LOGIN}
        )
        unknown = anon.post(
            "/auth/login",
            json={"email": f"no-such-{uuid.uuid4().hex[:8]}@example.com", "password": PLACEHOLDER_LOGIN},
        )
        assert known.status_code == unknown.status_code, (
            f"status differs: backfilled={known.status_code} unknown={unknown.status_code}"
        )
        assert known.json() == unknown.json(), (
            f"body differs:\n backfilled={known.text}\n unknown={unknown.text}"
        )


class TestGateStillHolds:
    """The gate was moved, not removed."""

    def test_correct_password_plus_flag_is_blocked_with_the_code(
        self, anon, flagged_user_with_password
    ):
        r = anon.post(
            "/auth/login",
            json={"email": flagged_user_with_password["email"], "password": REAL_PASSWORD},
        )
        assert r.status_code == 403, r.text
        detail = r.json().get("detail")
        assert isinstance(detail, dict), f"expected structured detail, got: {r.text}"
        assert detail.get("code") == "must_set_password", r.text

    def test_gate_lifts_when_flag_cleared(self, anon, flagged_user_with_password):
        """Flag cleared + right password → a normal login, proving the 403 came from the
        gate and not from another check."""
        _set_flag(flagged_user_with_password["id"], False)
        r = anon.post(
            "/auth/login",
            json={"email": flagged_user_with_password["email"], "password": REAL_PASSWORD},
        )
        assert r.status_code in (200, 202), r.text

    def test_wrong_password_on_flagged_account_still_401(self, anon, flagged_user_with_password):
        """Even for an account that COULD see the 403, a wrong password reveals nothing."""
        r = anon.post(
            "/auth/login",
            json={"email": flagged_user_with_password["email"], "password": "wrong-password-here"},
        )
        assert r.status_code == 401, r.text
