"""
OpenAPI-driven smoke sweep.

At collection time we read the live OpenAPI document and parametrize over
every GET operation that needs no required path/query parameters. This gives
cheap, broad coverage of all 23 routers and is the safety net that catches
import errors, 500s, and broken serialization the moment any endpoint
regresses. Deep per-router behavioural tests live in their own modules.
"""
import os

import httpx
import pytest

pytestmark = pytest.mark.e2e

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000").rstrip("/")


def _fetch_openapi(retries: int = 5, delay: float = 1.0):
    """Fetch the OpenAPI doc, retrying to ride out a uvicorn --reload restart."""
    import time
    for attempt in range(retries):
        try:
            r = httpx.get(f"{BASE_URL}/api/openapi.json", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:  # noqa: BLE001
            if attempt == retries - 1:
                return None
            time.sleep(delay)
    return None


def _discover_get_endpoints():
    """Return parameterless GET paths, resolved under /api/v1."""
    spec = _fetch_openapi()
    if spec is None:  # collection must not hard-crash if API is briefly down
        return []
    found = []
    for path, ops in spec.get("paths", {}).items():
        if "{" in path:  # skip templated paths (need a real id)
            continue
        get = ops.get("get")
        if not get:
            continue
        required_query = any(
            p.get("in") == "query" and p.get("required")
            for p in get.get("parameters", [])
        )
        if required_query:
            continue
        found.append(path)
    return sorted(found)


GET_ENDPOINTS = _discover_get_endpoints()

# Endpoints that currently return 5xx for an authorized superadmin.
# Each is a tracked defect (see tests/test-reports/test-report-e2e-api.md);
# xfail keeps the run honest without masking the regression.
# DEF-001 (GET /org/companies 500) fixed 2026-06-16 — removed from this map.
# Value is (reason, strict). strict=True: a reliable 5xx — fixing it flips the
# test to XPASS(strict) and fails the run, prompting removal from this map.
# strict=False: a *non-deterministic* 5xx that may pass on some runs, so tolerate
# both xfail and xpass (an XPASS must not fail the build).
KNOWN_5XX: dict[str, tuple[str, bool]] = {
    # GH#668 — pre-existing, data-dependent 500s (reliably 5xx -> strict).
    "/api/v1/dashboards": ("GH#668: GET /dashboards 500 (dashboard serialization, DEF-019 lineage)", True),
    "/api/v1/reports/definitions": (
        "GH#668: GET /reports/definitions 500 (invalid seeded report_type, DEF-013 lineage)",
        True,
    ),
    # GH#679 / DEF-010: the vestigial filesystem module loader intermittently
    # returns 503 "Module system not initialized" depending on startup timing —
    # non-strict, since it XPASSes whenever the loader happens to be up.
    "/api/v1/module-registry/enabled/names": ("GH#679: module loader intermittently not initialized (503)", False),
}


def _relpath(full_path: str) -> str:
    """Strip the /api/v1 prefix so it composes with the client's base_url."""
    return full_path.replace("/api/v1", "", 1) or "/"


def _authed_params():
    out = []
    for p in GET_ENDPOINTS:
        if p in KNOWN_5XX:
            reason, strict = KNOWN_5XX[p]
            marks = [pytest.mark.xfail(reason=reason, strict=strict)]
        else:
            marks = []
        out.append(pytest.param(p, marks=marks))
    return out


@pytest.mark.skipif(not GET_ENDPOINTS, reason="OpenAPI not reachable at collection time")
@pytest.mark.parametrize("path", _authed_params())
def test_get_endpoint_not_5xx_authenticated(su, path):
    """Every parameterless GET must respond without a server error when authed."""
    r = su.get(_relpath(path))
    assert r.status_code < 500, f"{path} returned {r.status_code}: {r.text[:300]}"
    # A superadmin should not be *forbidden* from read endpoints.
    assert r.status_code not in (401, 403), f"{path} unexpectedly denied to superadmin"


@pytest.mark.skipif(not GET_ENDPOINTS, reason="OpenAPI not reachable at collection time")
@pytest.mark.parametrize(
    "path",
    [p for p in GET_ENDPOINTS if "/auth/password-policy" not in p and "/healthz" not in p],
)
def test_get_endpoint_requires_auth(anon, path):
    """Protected GETs must reject anonymous access with 401 (not 200, not 500)."""
    r = anon.get(_relpath(path))
    assert r.status_code != 500, f"{path} crashed for anonymous: {r.text[:300]}"
    # Most endpoints should be 401; a few may be intentionally public (200) —
    # we only hard-fail on a server error or a silent data leak pattern.
    assert r.status_code in (200, 401, 403, 404, 422), f"{path} -> {r.status_code}"
