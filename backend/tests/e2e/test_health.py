"""Health, docs, and OpenAPI surface — the smoke baseline."""
import pytest

pytestmark = pytest.mark.e2e


def test_healthz_absolute(base_url):
    import httpx
    r = httpx.get(f"{base_url}/api/healthz", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_openapi_served(base_url):
    import httpx
    r = httpx.get(f"{base_url}/api/openapi.json", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "paths" in body and body["paths"], "OpenAPI exposes no paths"


def test_unknown_route_404(su):
    r = su.get("/this-route-does-not-exist-xyz")
    assert r.status_code == 404
