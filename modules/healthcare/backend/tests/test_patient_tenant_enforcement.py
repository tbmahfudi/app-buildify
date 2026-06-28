"""
Security regression tests — patient-token tenant_id enforcement (public-portal P2).

Proves the centralized `get_current_patient` dependency and the
`PatientTokenData.require_tenant()` gate that every `/api/v1/patients/me/*`
query relies on for tenant scoping. Self-contained: the JWT-decode boundary
and the SDK import boundary are stubbed, so no DB / live module load is needed.

Run (from repo root, or inside the backend container):
    SECRET_KEY=devsecret python -m pytest \
        modules/healthcare/backend/tests/test_patient_tenant_enforcement.py -q
"""
import importlib.util
import os
import sys
import types

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# ---------------------------------------------------------------------------
# Load the SDK file directly by path so the test runs regardless of how the
# module loader maps `modules.healthcare.*` at runtime.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_PA_PATH = os.path.normpath(os.path.join(_HERE, "..", "sdk", "patient_auth.py"))


def _load_patient_auth():
    # Stub the SDK boundary import the file depends on.
    for name in ("modules", "modules.sdk"):
        if name not in sys.modules:
            m = types.ModuleType(name)
            m.__path__ = []  # mark as package
            sys.modules[name] = m
    dep = types.ModuleType("modules.sdk.dependencies")
    dep.decode_token = lambda _t: None
    sys.modules["modules.sdk.dependencies"] = dep

    spec = importlib.util.spec_from_file_location("pa_under_test", _PA_PATH)
    pa = importlib.util.module_from_spec(spec)
    sys.modules["pa_under_test"] = pa  # required for @dataclass resolution
    spec.loader.exec_module(pa)
    return pa


pa = _load_patient_auth()


def _creds(token="x"):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _set_payload(payload):
    # Patch the *imported* name inside the module under test.
    pa.decode_token = lambda _t: payload


def test_valid_patient_token_carries_tenant():
    _set_payload({"type": "access", "roles": ["patient"],
                  "sub": "patient-A", "phone": "+62811", "tenant_id": "tenant-A"})
    data = pa.get_current_patient(_creds())
    assert data.patient_id == "patient-A"
    assert data.tenant_id == "tenant-A"
    assert data.require_tenant() == "tenant-A"


def test_token_without_tenant_claim_is_denied():
    _set_payload({"type": "access", "roles": ["patient"], "sub": "patient-A"})
    data = pa.get_current_patient(_creds())
    assert data.tenant_id is None
    with pytest.raises(HTTPException) as exc:
        data.require_tenant()
    assert exc.value.status_code == 401


def test_staff_token_rejected():
    _set_payload({"type": "access", "roles": ["staff"], "sub": "u1", "tenant_id": "tenant-A"})
    with pytest.raises(HTTPException) as exc:
        pa.get_current_patient(_creds())
    assert exc.value.status_code == 401


def test_refresh_token_rejected():
    _set_payload({"type": "refresh", "roles": ["patient"], "sub": "patient-A", "tenant_id": "tenant-A"})
    with pytest.raises(HTTPException) as exc:
        pa.get_current_patient(_creds())
    assert exc.value.status_code == 401


def test_optional_no_header_is_anonymous():
    assert pa.get_current_patient_optional(None) is None


def test_optional_with_valid_token():
    _set_payload({"type": "access", "roles": ["patient"], "sub": "patient-A", "tenant_id": "tenant-A"})
    data = pa.get_current_patient_optional(_creds())
    assert data is not None and data.tenant_id == "tenant-A"


def test_cross_tenant_param_isolation():
    # A token scoped to tenant-A yields tid='tenant-A'; the value is the only
    # binding fed to "AND tenant_id = :tid", so a tenant-B row can never match.
    _set_payload({"type": "access", "roles": ["patient"], "sub": "patient-A", "tenant_id": "tenant-A"})
    tid = pa.get_current_patient(_creds()).require_tenant()
    assert tid == "tenant-A"
    assert tid != "tenant-B"
