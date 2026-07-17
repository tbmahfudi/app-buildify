"""Health, docs, and OpenAPI surface — the smoke baseline."""
import pytest

pytestmark = pytest.mark.e2e


def test_healthz_absolute(base_url):
    import httpx
    r = httpx.get(f"{base_url}/api/healthz", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_comprehensive_health_reports_healthy(base_url):
    """The /api/health DB probe must return 200/healthy.

    Regression guard: the probe used a bare ``db.execute("SELECT 1")``, which
    SQLAlchemy 2.x rejects, so the except branch marked the database unhealthy on
    every call — a permanent 503 while the DB was fine. Any load balancer / k8s
    readiness probe on /api/health then treats the backend as down. `/healthz` never
    caught it (it does no DB probe) and the smoke suite explicitly skips both.
    """
    import httpx
    r = httpx.get(f"{base_url}/api/health", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "healthy", body
    assert body["components"]["database"]["status"] == "healthy", body


def test_openapi_served(base_url):
    import httpx
    r = httpx.get(f"{base_url}/api/openapi.json", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "paths" in body and body["paths"], "OpenAPI exposes no paths"


def test_unknown_route_404(su):
    r = su.get("/this-route-does-not-exist-xyz")
    assert r.status_code == 404
