"""
E2E: the strict register schema accepts the manifest shapes real modules actually ship.

Black-box against ``POST /api/v1/modules/validate`` (the dry-run of the same
``ModuleLoader.validate_manifest`` that ``POST /modules/register`` uses to admit a manifest).

Regression guard for a three-way contract drift that had shipped: the strict register
schema (``backend/app/core/module_system/manifest.schema.json``) disagreed with BOTH the
manifests on disk AND the reader in ``app/routers/modules.py`` about the shape of a module.
The financial module — a real, registered module — failed the gate on five points, and the
scaffold generator (``scripts/create-module.sh``) emitted the same broken shape, so every
new module was born failing it. Nothing calls ``/register`` today, so it was latent; these
tests keep it from silently returning.

The specific rules the schema and the code must agree on:
  * a permission is keyed by ``code`` (matching the permissions table and the reader at
    ``modules.py`` ``str(p.get("code") or p.get("name"))``), and may carry ``scope`` /
    ``category`` — the permissions table requires a scope;
  * ``dependencies`` may be the array form OR the ``{required, optional}`` object form,
    because ``modules.py`` reads both.
"""
import pytest

BASE = {
    "name": "e2e_contract",
    "display_name": "E2E Contract Probe",
    "version": "1.0.0",
    "module_type": "code",
    "category": "vertical",
    "api_prefix": "/api/v1/e2e_contract",
    "routes": [],
}


def _validate(su, manifest):
    return su.post("/modules/validate", json={"manifest": manifest})


def _errors(resp) -> str:
    body = resp.json()
    return str(body.get("detail", body))


def test_permissions_are_keyed_by_code(su):
    """The shape financial/template ship and modules.py reads: code + scope + category."""
    m = dict(BASE)
    m["permissions"] = [
        {
            "code": "e2e_contract:invoices:read:company",
            "name": "Read invoices",
            "description": "Read invoices",
            "category": "e2e_contract",
            "scope": "company",
        }
    ]
    r = _validate(su, m)
    assert r.status_code == 200, _errors(r)
    assert r.json() == {"valid": True}


def test_dependencies_array_form_is_valid(su):
    m = dict(BASE)
    m["dependencies"] = [{"name": "healthcare", "optional": True}]
    r = _validate(su, m)
    assert r.status_code == 200, _errors(r)


def test_dependencies_object_form_is_valid(su):
    """{required, optional} — the form financial/template historically shipped."""
    m = dict(BASE)
    m["dependencies"] = {"required": [], "optional": []}
    r = _validate(su, m)
    assert r.status_code == 200, _errors(r)


def test_missing_structural_fields_still_rejected(su):
    """The fix widened the schema where it was wrong — it did NOT stop requiring the
    load-bearing fields. module_type/category/api_prefix are still mandatory."""
    m = dict(BASE)
    del m["module_type"]
    del m["category"]
    del m["api_prefix"]
    r = _validate(su, m)
    assert r.status_code == 422, r.text
    errs = _errors(r)
    assert "module_type" in errs


def test_permission_without_code_is_rejected(su):
    """code is the identity of a permission; a name-only permission is not admissible."""
    m = dict(BASE)
    m["permissions"] = [{"name": "Read invoices", "description": "no code"}]
    r = _validate(su, m)
    assert r.status_code == 422, r.text
