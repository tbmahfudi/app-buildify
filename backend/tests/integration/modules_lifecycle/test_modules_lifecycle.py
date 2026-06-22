"""
T-23.005 Integration tests for Epic-23 API contract gate.

Covers (all against SQLite in-memory DB via conftest fixtures):
  1. GET  /api/v1/modules                              - list installed modules
  2. GET  /api/v1/modules/{name}/activation-preview    - preview before activation
  3. POST /api/v1/modules/{name}/enable                - activate happy path
  4. POST /api/v1/modules/{name}/disable               - deactivate happy path
  5. POST /api/v1/modules/{name}/enable  (dep unmet)   - 409 DEPS_UNMET
  6. POST /api/v1/modules/{name}/enable  (core module) - 403 SYSTEM_MODULE_PROTECTED
  7. POST /api/v1/modules/{name}/disable (core module) - 403 SYSTEM_MODULE_PROTECTED
  8. GET  activation-preview for unknown module        - 404 MODULE_NOT_FOUND
"""

import uuid
import pytest
from fastapi import status

from app.models.module_registry import ModuleRegistry, TenantModule


def _make_module(db_session, *, name, display_name="Test Module", is_core=False, dependencies=None):
    """Seed a Module row and flush it."""
    m = ModuleRegistry(
        id=str(uuid.uuid4()),
        name=name,
        display_name=display_name,
        module_type="code",
        version="1.0.0",
        description="Test module",
        category="test",
        is_installed=True,
        is_core=is_core,
        manifest={
            "name": name,
            "display_name": display_name,
            "version": "1.0.0",
            "permissions": [
                {"name": f"{name}:read", "description": f"Read {name} data"},
            ],
            "frontend": {
                "menu_items": [
                    {"label": display_name, "route": f"#/{name}", "icon": "ph-cube"},
                ]
            },
            "dependencies": dependencies or {},
        },
        status="available",
    )
    db_session.add(m)
    db_session.flush()
    return m


@pytest.fixture
def crm_module(db_session):
    return _make_module(db_session, name="crm", display_name="CRM")


@pytest.fixture
def core_module(db_session):
    return _make_module(db_session, name="core_auth", display_name="Core Auth", is_core=True)


@pytest.fixture
def dep_provider(db_session):
    return _make_module(db_session, name="base_accounting", display_name="Base Accounting")


@pytest.fixture
def crm_with_dep(db_session, dep_provider):
    return _make_module(
        db_session, name="crm_dep", display_name="CRM with dep",
        dependencies={"required": ["base_accounting"]}
    )


class TestModuleList:
    def test_list_returns_installed_modules(self, client, auth_headers, crm_module, db_session):
        db_session.commit()
        resp = client.get("/api/v1/modules", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] >= 1
        assert any(m["name"] == "crm" for m in body["modules"])

    def test_list_shows_activation_status_inactive_by_default(self, client, auth_headers, crm_module, db_session):
        db_session.commit()
        resp = client.get("/api/v1/modules", headers=auth_headers)
        crm = next(m for m in resp.json()["modules"] if m["name"] == "crm")
        assert crm["activation_status"] == "inactive"

    def test_list_requires_auth(self, client, crm_module, db_session):
        db_session.commit()
        resp = client.get("/api/v1/modules")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class TestActivationPreview:
    def test_preview_returns_permissions_and_menu(self, client, auth_headers, crm_module, db_session):
        db_session.commit()
        resp = client.get("/api/v1/modules/crm/activation-preview", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["module_name"] == "crm"
        assert len(body["permissions"]) == 1
        assert body["permissions"][0]["name"] == "crm:read"
        assert len(body["menu_items"]) == 1
        assert body["menu_items"][0]["route"] == "#/crm"
        assert body["dependencies"] == []

    def test_preview_shows_dep_status_inactive(self, client, auth_headers, crm_with_dep, dep_provider, db_session):
        db_session.commit()
        resp = client.get("/api/v1/modules/crm_dep/activation-preview", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        deps = resp.json()["dependencies"]
        assert len(deps) == 1
        assert deps[0]["name"] == "base_accounting"
        assert deps[0]["status"] == "inactive"

    def test_preview_shows_dep_active_when_enabled(
        self, client, auth_headers, test_user, crm_with_dep, dep_provider, db_session
    ):
        db_session.add(TenantModule(
            id=str(uuid.uuid4()),
            module_id=dep_provider.id,
            tenant_id=test_user.tenant_id,
            is_enabled=True,
        ))
        db_session.commit()
        resp = client.get("/api/v1/modules/crm_dep/activation-preview", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["dependencies"][0]["status"] == "active"

    def test_preview_404_for_unknown_module(self, client, auth_headers, db_session):
        db_session.commit()
        resp = client.get("/api/v1/modules/no_such_module/activation-preview", headers=auth_headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.json()["detail"]["code"] == "MODULE_NOT_FOUND"


class TestEnableDisableCycle:
    def test_enable_activates_module(self, client, auth_headers, crm_module, db_session):
        db_session.commit()
        resp = client.post("/api/v1/modules/crm/enable", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["success"] is True
        crm = next(m for m in client.get("/api/v1/modules", headers=auth_headers).json()["modules"] if m["name"] == "crm")
        assert crm["activation_status"] == "active"

    def test_disable_deactivates_module(self, client, auth_headers, test_user, crm_module, db_session):
        db_session.add(TenantModule(
            id=str(uuid.uuid4()),
            module_id=crm_module.id,
            tenant_id=test_user.tenant_id,
            is_enabled=True,
        ))
        db_session.commit()
        resp = client.post("/api/v1/modules/crm/disable", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["success"] is True

    def test_full_enable_disable_cycle(self, client, auth_headers, crm_module, db_session):
        db_session.commit()
        assert client.post("/api/v1/modules/crm/enable", headers=auth_headers).status_code == 200
        assert client.post("/api/v1/modules/crm/disable", headers=auth_headers).status_code == 200
        crm = next(m for m in client.get("/api/v1/modules", headers=auth_headers).json()["modules"] if m["name"] == "crm")
        assert crm["activation_status"] == "inactive"

    def test_enable_twice_returns_409(self, client, auth_headers, test_user, crm_module, db_session):
        db_session.add(TenantModule(
            id=str(uuid.uuid4()),
            module_id=crm_module.id,
            tenant_id=test_user.tenant_id,
            is_enabled=True,
        ))
        db_session.commit()
        resp = client.post("/api/v1/modules/crm/enable", headers=auth_headers)
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert resp.json()["detail"]["code"] == "ALREADY_ENABLED"

    def test_disable_when_not_enabled_returns_409(self, client, auth_headers, crm_module, db_session):
        db_session.commit()
        resp = client.post("/api/v1/modules/crm/disable", headers=auth_headers)
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert resp.json()["detail"]["code"] == "ALREADY_DISABLED"


class TestDependencyEnforcement:
    def test_unmet_dep_blocks_enable_409(
        self, client, auth_headers, crm_with_dep, dep_provider, db_session
    ):
        db_session.commit()
        resp = client.post("/api/v1/modules/crm_dep/enable", headers=auth_headers)
        assert resp.status_code == status.HTTP_409_CONFLICT
        body = resp.json()
        assert body["detail"]["code"] == "DEPS_UNMET"
        assert "base_accounting" in body["detail"]["detail"]["unmet_dependencies"]

    def test_enable_succeeds_when_dep_active(
        self, client, auth_headers, test_user, crm_with_dep, dep_provider, db_session
    ):
        db_session.add(TenantModule(
            id=str(uuid.uuid4()),
            module_id=dep_provider.id,
            tenant_id=test_user.tenant_id,
            is_enabled=True,
        ))
        db_session.commit()
        resp = client.post("/api/v1/modules/crm_dep/enable", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK


class TestCoreModuleProtection:
    def test_enable_core_module_403(self, client, auth_headers, core_module, db_session):
        db_session.commit()
        resp = client.post("/api/v1/modules/core_auth/enable", headers=auth_headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["detail"]["code"] == "SYSTEM_MODULE_PROTECTED"

    def test_disable_core_module_403(self, client, auth_headers, core_module, db_session):
        db_session.commit()
        resp = client.post("/api/v1/modules/core_auth/disable", headers=auth_headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["detail"]["code"] == "SYSTEM_MODULE_PROTECTED"

    def test_enable_unknown_module_404(self, client, auth_headers, db_session):
        db_session.commit()
        resp = client.post("/api/v1/modules/ghost_module/enable", headers=auth_headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.json()["detail"]["code"] == "MODULE_NOT_FOUND"
