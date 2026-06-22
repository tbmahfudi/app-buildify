# T-23.028  QA Smoke Checklist — Module Lifecycle Audit Log
# D1 verification: all 5 lifecycle events produce audit_log rows.
#
# Run against a live stack: SUPERADMIN_TOKEN and APP_URL must be set.
# Usage: pytest tests/smoke/test_audit_lifecycle_smoke.py -v -s
#
# Each test uses the real HTTP API (not TestClient) so audit writes go to
# the actual PostgreSQL database — confirming end-to-end persistence.

import os
import pytest
import requests
from typing import Optional

BASE = os.environ.get("APP_URL", "http://localhost:8000") + "/api/v1"
TOKEN = os.environ.get("SUPERADMIN_TOKEN", "")
TENANT_TOKEN = os.environ.get("TENANT_TOKEN", TOKEN)
MODULE = os.environ.get("SMOKE_MODULE", "test_smoke_module")

pytestmark = pytest.mark.skipif(
    not TOKEN,
    reason="SUPERADMIN_TOKEN not set — skipping live smoke tests",
)


def _admin_headers():
    return {"Authorization": f"Bearer {TOKEN}"}


def _tenant_headers():
    return {"Authorization": f"Bearer {TENANT_TOKEN}"}


def _latest_audit(action: str) -> Optional[dict]:
    r = requests.get(
        f"{BASE}/audit-logs",
        params={"action": action, "limit": 1},
        headers=_admin_headers(),
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json().get("logs") or r.json().get("items") or r.json()
    return rows[0] if rows else None


# ── 1. module_install ────────────────────────────────────────────────────────

def test_audit_module_install():
    payload = {
        "name": MODULE,
        "display_name": "Smoke Test Module",
        "version": "1.0.0",
        "description": "Created by T-23.028 smoke test",
    }
    r = requests.post(
        f"{BASE}/modules/register",
        json=payload,
        headers=_admin_headers(),
        timeout=10,
    )
    assert r.status_code in (200, 201, 409), f"register returned {r.status_code}: {r.text}"
    entry = _latest_audit("module_install")
    assert entry is not None, "No module_install audit entry found"
    assert entry.get("entity_id") == MODULE or entry.get("entity_type") == "module"


# ── 2. module.enabled ────────────────────────────────────────────────────────

def test_audit_module_enable():
    r = requests.post(
        f"{BASE}/modules/{MODULE}/enable",
        headers=_tenant_headers(),
        timeout=10,
    )
    assert r.status_code in (200, 409), f"enable returned {r.status_code}: {r.text}"
    entry = _latest_audit("module.enabled")
    assert entry is not None, "No module.enabled audit entry found"


# ── 3. module.disabled ───────────────────────────────────────────────────────

def test_audit_module_disable():
    r = requests.post(
        f"{BASE}/modules/{MODULE}/disable",
        headers=_tenant_headers(),
        timeout=10,
    )
    assert r.status_code in (200, 409), f"disable returned {r.status_code}: {r.text}"
    entry = _latest_audit("module.disabled")
    assert entry is not None, "No module.disabled audit entry found"


# ── 4. module.admin_deactivate_all ───────────────────────────────────────────

def test_audit_admin_deactivate_all():
    r = requests.get(f"{BASE}/modules/{MODULE}", headers=_admin_headers(), timeout=10)
    if r.status_code == 404:
        pytest.skip("module not found — run install test first")
    mod_id = r.json().get("id", MODULE)

    r = requests.post(
        f"{BASE}/admin/modules/{mod_id}/deactivate-all",
        headers=_admin_headers(),
        timeout=10,
    )
    assert r.status_code == 200, f"deactivate-all returned {r.status_code}: {r.text}"
    entry = _latest_audit("module.admin_deactivate_all")
    assert entry is not None, "No module.admin_deactivate_all audit entry found"


# ── 5. module.uninstalled ────────────────────────────────────────────────────

def test_audit_module_uninstall():
    r = requests.get(f"{BASE}/modules/{MODULE}", headers=_admin_headers(), timeout=10)
    if r.status_code == 404:
        pytest.skip("module not found — run install test first")
    mod_id = r.json().get("id", MODULE)

    r = requests.delete(
        f"{BASE}/admin/modules/{mod_id}",
        headers={**_admin_headers(), "X-Confirm-Uninstall": "true"},
        timeout=10,
    )
    assert r.status_code == 200, f"uninstall returned {r.status_code}: {r.text}"
    entry = _latest_audit("module.uninstalled")
    assert entry is not None, "No module.uninstalled audit entry found"
