"""
E2E black-box test harness for the App-Buildify backend API.

These tests run against a *live, running* container — they make real HTTP
requests over the network and never import application code. This is what
makes them an honest test of the deployed artifact (routing, middleware,
auth, DB, serialization) rather than an in-process unit of it.

Run (from inside the backend container, which already has pytest + httpx):

    docker exec app_buildify_backend python -m pytest tests/e2e \
        --confcutdir=tests/e2e -v

`--confcutdir=tests/e2e` is required: it stops pytest from loading the
in-process `tests/conftest.py` (TestClient + app imports), which is a
different harness and must not be mixed with these black-box tests.

Or from any host that can reach the API:

    E2E_BASE_URL=http://localhost:8000 python -m pytest tests/e2e -v

A note on session limits: the platform enforces `max_concurrent_sessions`
(default 3) and evicts the *oldest* session on overflow. The shared `su` /
`user` clients therefore auto-reauthenticate on a 401, and one-off logins in
tests should use the `ephemeral` fixture so they release their session slot.

Configuration (all via env, with seed-based defaults):

    E2E_BASE_URL        default http://localhost:8000
    E2E_SU_EMAIL        default superadmin@system.com
    E2E_SU_PASSWORD     default SuperAdmin123!
    E2E_USER_EMAIL      default ceo@techstart.com      (a seeded non-superuser)
    E2E_USER_PASSWORD   default password123
"""
import contextlib
import os
import uuid

import httpx
import pytest

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api/v1"
TIMEOUT = float(os.environ.get("E2E_TIMEOUT", "30"))

SUPERADMIN = {
    "email": os.environ.get("E2E_SU_EMAIL", "superadmin@system.com"),
    "password": os.environ.get("E2E_SU_PASSWORD", "SuperAdmin123!"),
}
TENANT_USER = {
    "email": os.environ.get("E2E_USER_EMAIL", "ceo@techstart.com"),
    "password": os.environ.get("E2E_USER_PASSWORD", "password123"),
}


def login_raw(creds: dict) -> dict:
    """Bare login (no shared client) → full token payload, raises on failure."""
    r = httpx.post(f"{API}/auth/login", json=creds, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def logout_token(token: str) -> None:
    """Best-effort logout to free a concurrent-session slot."""
    with contextlib.suppress(Exception):
        httpx.post(
            f"{API}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )


# --------------------------------------------------------------------------- #
# Auto-reauthenticating client
# --------------------------------------------------------------------------- #
class AuthClient(httpx.Client):
    """
    httpx client bound to a set of credentials that transparently re-logs-in
    once when it sees a 401. This keeps long-lived shared sessions valid even
    when the server evicts the oldest session under `max_concurrent_sessions`.
    """

    def __init__(self, creds: dict, **kwargs):
        self._creds = creds
        kwargs.setdefault("base_url", API)
        kwargs.setdefault("timeout", TIMEOUT)
        headers = kwargs.pop("headers", {}) or {}
        headers.setdefault("Accept", "application/json")
        super().__init__(headers=headers, **kwargs)
        self._authenticate()

    def _authenticate(self) -> None:
        self.headers["Authorization"] = f"Bearer {login_raw(self._creds)['access_token']}"

    def request(self, method, url, **kwargs):  # noqa: D401
        resp = super().request(method, url, **kwargs)
        if resp.status_code == 401 and "auth/login" not in str(url):
            self._authenticate()
            resp = super().request(method, url, **kwargs)
        return resp


# --------------------------------------------------------------------------- #
# Connectivity guard — fail fast and clearly if the stack is down
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session", autouse=True)
def _require_live_api():
    try:
        httpx.get(f"{BASE_URL}/api/healthz", timeout=5).raise_for_status()
    except Exception as exc:  # noqa: BLE001
        pytest.exit(
            f"\nE2E target {BASE_URL} is not reachable ({exc}).\n"
            f"Start the stack first:  ./manage.sh start postgres\n",
            returncode=3,
        )


# --------------------------------------------------------------------------- #
# Clients & tokens
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def anon():
    """Unauthenticated client (negative-auth and public-endpoint tests)."""
    with httpx.Client(base_url=API, timeout=TIMEOUT, headers={"Accept": "application/json"}) as c:
        yield c


@pytest.fixture(scope="session")
def su():
    """Authenticated client acting as the platform superadmin (auto-reauth)."""
    with AuthClient(SUPERADMIN) as c:
        yield c


@pytest.fixture(scope="session")
def user():
    """
    Authenticated client acting as a *tenant-scoped admin* (auto-reauth).

    The seeded `ceo@techstart.com` belongs to a tenant and can perform
    tenant-scoped writes (e.g. create roles) that the superadmin cannot — the
    superadmin has `tenant_id = NULL` and is rejected from tenant-scoped
    creates. Use this fixture for tenant-scoped CRUD.
    """
    try:
        client = AuthClient(TENANT_USER)
    except Exception:  # noqa: BLE001
        pytest.skip(f"seeded tenant user {TENANT_USER['email']} not available")
    with client as c:
        yield c


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@pytest.fixture
def ephemeral():
    """
    Factory yielding a short-lived authenticated client that logs out on exit,
    releasing its concurrent-session slot. Use for auth-flow tests that must
    not disturb the shared `su` session.

        with ephemeral(SUPERADMIN) as c:
            ...
    """
    minted: list[str] = []

    @contextlib.contextmanager
    def _make(creds: dict):
        payload = login_raw(creds)
        token = payload["access_token"]
        minted.append(token)
        client = httpx.Client(
            base_url=API,
            timeout=TIMEOUT,
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
        )
        try:
            yield client
        finally:
            client.close()
            logout_token(token)

    yield _make
    for tok in minted:
        logout_token(tok)


@pytest.fixture
def unique():
    """Return a factory for collision-free names within a single test run."""
    def _make(prefix: str = "e2e") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    return _make


def drop_table_best_effort(table_name: str) -> None:
    """
    Best-effort drop of a physical table created by publishing a test entity.

    Deleting a *published* entity via the API does not drop its backing table,
    so published-entity fixtures call this on teardown to avoid leaving orphan
    tables behind. Silently does nothing if the DB is unreachable (e.g. when the
    suite runs from a host without DB access) — it is cleanup, not an assertion.
    """
    url = os.environ.get("SQLALCHEMY_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return
    try:
        import psycopg2

        dsn = (
            url.replace("postgresql+psycopg2://", "postgresql://")
            .replace("postgresql+psycopg://", "postgresql://")
        )
        conn = psycopg2.connect(dsn)
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — cleanup must never fail a test
        pass


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: Black-box API tests against a live running container"
    )
