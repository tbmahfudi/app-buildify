"""
E2E: the module tenancy block and its namespace gate (ADR-012 D1 / Resolution Q1).

Black-box against `POST /api/v1/modules/validate`, which is a dry-run of the same
`ModuleLoader.validate_manifest` that `POST /modules/register` uses to admit a manifest —
so these exercise the real gate over HTTP, no app imports.

Why these live in e2e rather than only in tests/unit: CI runs **only** `tests/e2e`
(`pytest tests/e2e --confcutdir=tests/e2e`). `tests/unit/test_module_tenancy.py` covers the
same rules more thoroughly, but nothing there runs in CI, so the security-relevant cases
are pinned here too. The rule being enforced: a manifest may grant its own end users its
own permissions and nothing else.
"""
import pytest

# A minimally valid manifest for the strict register schema. Only `tenancy` varies.
BASE = {
    "name": "e2e_tenancy",
    "display_name": "E2E Tenancy Probe",
    "version": "1.0.0",
    "module_type": "code",
    "category": "test",
    "api_prefix": "/api/v1/e2e_tenancy",
    "routes": [],
}


def _manifest(**tenancy):
    m = dict(BASE)
    if tenancy:
        m["tenancy"] = tenancy["tenancy"]
    return m


def _validate(su, manifest):
    return su.post("/modules/validate", json={"manifest": manifest})


def _errors(resp) -> str:
    """Flatten the 422 error payload to a searchable string."""
    body = resp.json()
    return str(body.get("detail", body))


# --------------------------------------------------------------------------- #
# Baseline: the gate must not break existing modules
# --------------------------------------------------------------------------- #


def test_manifest_without_tenancy_is_valid(su):
    """Absent block == per_tenant. Every module that predates ADR-012 must still pass."""
    r = _validate(su, _manifest())
    assert r.status_code == 200, r.text
    assert r.json() == {"valid": True}


def test_per_tenant_is_valid(su):
    r = _validate(su, _manifest(tenancy={"mode": "per_tenant"}))
    assert r.status_code == 200, r.text


def test_shared_saas_with_own_namespace_is_valid(su):
    r = _validate(
        su,
        _manifest(
            tenancy={
                "mode": "shared_saas",
                "end_user_rbac": {
                    "role": "enduser",
                    "group": "endusers",
                    "permissions": ["e2e_tenancy:portal:access"],
                },
            }
        ),
    )
    assert r.status_code == 200, r.text


def test_shared_saas_without_permissions_is_valid(su):
    """Declaring a role/group but granting nothing is legitimate."""
    r = _validate(
        su,
        _manifest(
            tenancy={"mode": "shared_saas", "end_user_rbac": {"role": "r", "group": "g"}}
        ),
    )
    assert r.status_code == 200, r.text


# --------------------------------------------------------------------------- #
# The gate (Resolution Q1) — a manifest may not grant itself foreign authority
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "code",
    [
        "system:users:delete",  # platform authority — the case that matters
        "users:create:tenant",
        "financial:invoices:read",  # another module's namespace
        "e2e_tenancy_evil:steal",  # prefix lookalike, must not pass as e2e_tenancy
    ],
)
def test_foreign_namespace_permission_is_rejected(su, code):
    r = _validate(
        su,
        _manifest(
            tenancy={
                "mode": "shared_saas",
                "end_user_rbac": {"role": "r", "group": "g", "permissions": [code]},
            }
        ),
    )
    assert r.status_code == 422, f"{code!r} was ACCEPTED — the namespace gate is not enforcing"
    assert "namespaced to" in _errors(r)


def test_rejection_survives_a_valid_permission_alongside(su):
    """One good code must not launder a bad one."""
    r = _validate(
        su,
        _manifest(
            tenancy={
                "mode": "shared_saas",
                "end_user_rbac": {
                    "role": "r",
                    "group": "g",
                    "permissions": ["e2e_tenancy:portal:access", "system:users:delete"],
                },
            }
        ),
    )
    assert r.status_code == 422, r.text
    assert "system:users:delete" in _errors(r)


# --------------------------------------------------------------------------- #
# Shape errors
# --------------------------------------------------------------------------- #


def test_shared_saas_requires_end_user_rbac(su):
    r = _validate(su, _manifest(tenancy={"mode": "shared_saas"}))
    assert r.status_code == 422, r.text
    assert "end_user_rbac" in _errors(r)


def test_end_user_rbac_on_per_tenant_is_rejected(su):
    r = _validate(
        su,
        _manifest(
            tenancy={"mode": "per_tenant", "end_user_rbac": {"role": "r", "group": "g"}}
        ),
    )
    assert r.status_code == 422, r.text


def test_unknown_mode_is_rejected(su):
    r = _validate(su, _manifest(tenancy={"mode": "sneaky"}))
    assert r.status_code == 422, r.text


def test_validate_requires_auth(anon):
    """The dry-run endpoint is not public."""
    r = anon.post("/modules/validate", json={"manifest": BASE})
    assert r.status_code in (401, 403), r.text
