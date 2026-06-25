"""
T-23.015 Integration test: post_install hook sentinel via audit_log.

Strategy
--------
The /register endpoint loads module code from disk at
  <backend>/modules/<name>/module.py
via an inline import of ModuleLoader from app.core.module_system.loader.

We patch app.core.module_system.loader.ModuleLoader (the class in the
loader module) so that every `from app.core.module_system.loader import
ModuleLoader` inside the /register handler picks up our mock.

The mock returns a real ModuleLoader instance pointed at a temp directory
containing a stub module whose post_install() writes a sentinel AuditLog row.

After /register we assert the sentinel row exists in the in-memory SQLite DB.
"""

import json
import uuid
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.models.module_registry import ModuleRegistry
from app.models.audit import AuditLog

STUB_MODULE_NAME = "test_hook_sentinel"
SENTINEL_ACTION = "test_sentinel_post_install"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_stub_module_on_disk(tmp_dir: Path) -> Path:
    """Write a minimal module stub whose post_install writes a sentinel row."""
    module_dir = tmp_dir / STUB_MODULE_NAME
    module_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": STUB_MODULE_NAME,
        "display_name": "Test Hook Sentinel Module",
        "version": "0.0.1",
        "description": "Ephemeral test stub for T-23.015",
        "category": "test",
        "subscription_tier": "free",
        "permissions": [],
        "routes": [],
        "dependencies": [],
        "configuration": {"settings": []},
    }
    (module_dir / "manifest.json").write_text(json.dumps(manifest))

    # Class name derived from STUB_MODULE_NAME by PascalCase + Module:
    # test_hook_sentinel -> TestHookSentinelModule
    module_code = textwrap.dedent("""
        from pathlib import Path
        from typing import Any, List, Dict
        from fastapi import APIRouter
        from app.core.module_system.base_module import BaseModule

        _SENTINEL_ACTION = "test_sentinel_post_install"


        class TestHookSentinelModule(BaseModule):

            def get_router(self) -> APIRouter:
                return APIRouter()

            def get_permissions(self) -> List[Dict[str, Any]]:
                return []

            def post_install(self, db_session: Any) -> None:
                from app.models.audit import AuditLog
                import uuid as _uuid
                row = AuditLog(
                    id=str(_uuid.uuid4()),
                    action=_SENTINEL_ACTION,
                    entity_type="module",
                    status="success",
                    context_info='{"module_name": "test_hook_sentinel"}',
                )
                db_session.add(row)
                db_session.commit()
    """)
    (module_dir / "module.py").write_text(module_code)
    return module_dir


def _cleanup_module_registry(db_session, module_name: str):
    try:
        db_session.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name
        ).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stub_module_dir(tmp_path):
    _create_stub_module_on_disk(tmp_path)
    yield tmp_path


@pytest.fixture()
def admin_client(db_session):
    """TestClient with a superuser stub to satisfy require_superuser."""
    import uuid as _uuid
    from fastapi.testclient import TestClient
    from fastapi import HTTPException, Request, status as http_status
    from app.main import app
    from app.core.dependencies import get_db, get_current_user, get_current_active_user
    from app.models.user import User

    stub = MagicMock(spec=User)
    stub.id = _uuid.UUID("00000000-0000-0000-0000-000000000999")
    stub.email = "superadmin@test.com"
    stub.full_name = "Super Admin"
    stub.is_active = True
    stub.is_superuser = True
    stub.is_tenant_admin = True
    stub.tenant_id = "00000000-0000-0000-0000-000000000123"
    stub.roles = []

    def _auth_guard(request: Request):
        if "authorization" not in request.headers:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN)
        return stub

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _auth_guard
    app.dependency_overrides[get_current_active_user] = lambda: stub

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def _register_payload(module_name: str, version: str = "0.0.1") -> dict:
    """Build the ModuleRegistrationRequest payload required by /register."""
    return {
        "manifest": {
            "name": module_name,
            "display_name": "Test Hook Sentinel Module",
            "version": version,
            "description": "Ephemeral test stub for T-23.015",
            "module_type": "code",
            "category": "test",
            "api_prefix": "/api/v1/test-hook-sentinel",
            "subscription_tier": "free",
            "permissions": [],
            "routes": [],
            "dependencies": [],
        },
        "backend_service_url": "http://localhost:9999",
        "health_check_url": "http://localhost:9999/health",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPostInstallHookSentinel:

    def test_post_install_writes_sentinel_to_audit_log(
        self, admin_client, db_session, stub_module_dir
    ):
        """
        Register the stub module; assert post_install sentinel row in audit_logs.

        The /register handler imports ModuleLoader inline from
        app.core.module_system.loader.  Patching the class in that module
        ensures all subsequent `from ... import ModuleLoader` calls in the
        same request get our loader pointed at the stub directory.
        """
        auth_headers = {"Authorization": "Bearer integration-test-token"}

        from app.core.module_system.loader import ModuleLoader as RealLoader
        real_loader_instance = RealLoader(stub_module_dir)

        # Patch the class in the source module; the inline import inside the
        # /register handler will resolve to our mock because Python caches
        # modules in sys.modules and our patch replaces the class attribute.
        with patch(
            "app.core.module_system.loader.ModuleLoader",
            return_value=real_loader_instance,
        ):
            resp = admin_client.post(
                "/api/v1/module-registry/register",
                json=_register_payload(STUB_MODULE_NAME),
                headers=auth_headers,
            )

        assert resp.status_code == 200, (
            f"Expected 200 from /register, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body.get("success") is True, f"Register returned success=False: {body}"

        # Key assertion: sentinel row written by stub post_install must exist
        sentinel = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == SENTINEL_ACTION)
            .first()
        )
        assert sentinel is not None, (
            f"post_install sentinel row NOT found in audit_logs "
            f"(action='{SENTINEL_ACTION}'). "
            "post_install was NOT called by the /register endpoint."
        )
        assert sentinel.entity_type == "module"
        assert sentinel.status == "success"

        _cleanup_module_registry(db_session, STUB_MODULE_NAME)

    def test_register_endpoint_writes_module_installed_audit(
        self, admin_client, db_session
    ):
        """
        Baseline: /register always writes action=module.installed (T-23.027)
        even when the module has no disk-backed class (no post_install hook).
        """
        auth_headers = {"Authorization": "Bearer integration-test-token"}
        unique_name = f"test_audit_baseline_{uuid.uuid4().hex[:6]}"

        resp = admin_client.post(
            "/api/v1/module-registry/register",
            json=_register_payload(unique_name),
            headers=auth_headers,
        )

        assert resp.status_code == 200, (
            f"Expected 200 from /register, got {resp.status_code}: {resp.text}"
        )

        installed_log = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.action == "module.installed",
                AuditLog.entity_type == "module",
            )
            .first()
        )
        assert installed_log is not None, (
            "module.installed audit log not found after /register. "
            "T-23.027 baseline audit path may be broken."
        )

        _cleanup_module_registry(db_session, unique_name)
