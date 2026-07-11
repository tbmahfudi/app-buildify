"""
E2E — ADR-HC-009 D7 `must_set_password` login gate.

A backfilled/legacy account carries a placeholder credential and must set a real
password before it can sign in. The platform login endpoint must block such an
account with a distinct, machine-readable 403 (code `must_set_password`) so the
patient portal can route the user to a "set your password" claim flow instead of
showing a generic wrong-password error.

The gate fires immediately after the user lookup — before the credential /
active / lockout checks — so a test only needs the user row to EXIST with the
flag set; no valid password is required. We create a throwaway user directly in
the DB (mirroring conftest's psycopg2 access) and remove it on teardown, so the
shared superadmin/tenant fixtures are never touched.
"""
import os
import uuid

import pytest


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
            cur.execute(
                "UPDATE users SET must_set_password = %s WHERE id = %s",
                (value, user_id),
            )
    finally:
        conn.close()


def _placeholder_hash() -> str:
    """A valid-format but unusable bcrypt hash (of a random secret), mirroring
    what the D7 backfill writes — so verify_password returns False cleanly rather
    than erroring on a malformed hash."""
    from passlib.hash import bcrypt

    return bcrypt.hash(uuid.uuid4().hex)


@pytest.fixture
def flagged_user():
    """Create a throwaway user with must_set_password=true; delete on teardown."""
    uid = str(uuid.uuid4())
    email = f"e2e-mustset-{uuid.uuid4().hex[:8]}@example.com"
    conn = _connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, email, hashed_password, must_set_password) "
                "VALUES (%s, %s, %s, true)",
                (uid, email, _placeholder_hash()),
            )
    finally:
        conn.close()

    yield {"id": uid, "email": email}

    conn = _connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (uid,))
    finally:
        conn.close()


class TestMustSetPasswordGate:
    def test_flagged_account_login_returns_403_with_code(self, anon, flagged_user):
        """A must_set_password account is blocked with the machine-readable code."""
        r = anon.post(
            "/auth/login",
            json={"email": flagged_user["email"], "password": "irrelevant123"},
        )
        assert r.status_code == 403, r.text
        detail = r.json().get("detail")
        assert isinstance(detail, dict), f"expected structured detail, got: {r.text}"
        assert detail.get("code") == "must_set_password", r.text

    def test_gate_lifts_when_flag_cleared(self, anon, flagged_user):
        """With the flag cleared, the placeholder credential fails normally (401),
        proving the 403 came from the gate rather than another check."""
        _set_flag(flagged_user["id"], False)
        r = anon.post(
            "/auth/login",
            json={"email": flagged_user["email"], "password": "irrelevant123"},
        )
        assert r.status_code == 401, r.text
