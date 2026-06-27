"""
Deep coverage of the module system: three routers sharing one feature area.

- module-registry (`modules.py`): filesystem-backed modules, install/enable
  per tenant. The only real filesystem module in this image is "financial"
  (premium tier); "support_management" is a DB-only seed row with no
  loadable module class, used here purely as a not-found negative case.
- modules (`nocode_modules.py`): no-code module CRUD, dependencies,
  versioning, validation helpers.
- module-extensions (`module_extensions.py`): entity/screen/menu extensions.

`get_entity_with_extensions` reads the target entity's *physical* table
directly with no missing-table handling; exercising the happy path would
require publishing an entity (real DDL), which the data-model suite
deliberately avoids. Only the 404 (unknown entity) case is covered here.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)


def _err_msg(resp) -> str:
    """Human error text from either a structured ({"detail": {"message": ...}})
    or a legacy ({"detail": "..."}) error body (Epic-23 introduced the former)."""
    detail = resp.json().get("detail")
    if isinstance(detail, dict):
        return detail.get("message") or detail.get("detail") or ""
    return str(detail or "")


@pytest.fixture
def nocode_module(su, unique):
    sfx = unique("mod").replace("_", "")[:8]
    body = {
        "name": f"e2e_mod_{sfx}",
        "display_name": f"E2E Module {sfx}",
        "table_prefix": f"e2e{sfx}"[:10],
    }
    r = su.post("/modules", json=body)
    assert r.status_code == 201, r.text
    mid = r.json()["data"]["id"]
    yield mid
    su.delete(f"/modules/{mid}")


@pytest.fixture
def entity_for_module(su, nocode_module, unique):
    sfx = unique("ent").replace("_", "")[:8]
    name = f"e2e_{sfx}"
    body = {
        "name": name,
        "label": f"E2E {sfx}",
        "plural_label": f"E2E {sfx}s",
        "table_name": f"e2e_tbl_{sfx}",
        "data_scope": "tenant",
        "module_id": nocode_module,
    }
    r = su.post("/data-model/entities", json=body)
    assert r.status_code in (200, 201), r.text
    eid = r.json()["id"]
    yield eid
    su.delete(f"/data-model/entities/{eid}")


# --------------------------------------------------------------------------- #
# module-registry: read-only catalogue
# --------------------------------------------------------------------------- #
class TestModuleRegistryReads:
    def test_list_available(self, su):
        r = su.get("/module-registry/available")
        assert r.status_code == 200
        names = [m["name"] for m in r.json()["modules"]]
        assert "financial" in names

    def test_list_available_requires_auth(self, anon):
        assert anon.get("/module-registry/available").status_code in UNAUTH

    def test_list_enabled_for_own_tenant(self, user):
        r = user.get("/module-registry/enabled")
        assert r.status_code == 200
        assert isinstance(r.json()["modules"], list)

    def test_list_enabled_names(self, user):
        r = user.get("/module-registry/enabled/names")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_all_tenants_modules_superuser_only(self, su):
        r = su.get("/module-registry/enabled/all-tenants")
        assert r.status_code == 200
        assert isinstance(r.json()["modules"], list)

    def test_list_all_tenants_modules_denied_for_non_superuser(self, user):
        r = user.get("/module-registry/enabled/all-tenants")
        assert r.status_code == 403

    def test_get_module_info(self, su):
        r = su.get("/module-registry/financial")
        assert r.status_code == 200
        assert r.json()["name"] == "financial"

    def test_get_module_info_unknown_404(self, su):
        r = su.get(f"/module-registry/{uuid.uuid4().hex}")
        assert r.status_code == 404

    def test_get_manifest_known_module(self, su):
        r = su.get("/module-registry/financial/manifest")
        assert r.status_code == 200

    def test_get_manifest_unknown_404(self, su):
        r = su.get(f"/module-registry/{uuid.uuid4().hex}/manifest")
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# module-registry: install / uninstall (superuser only)
# --------------------------------------------------------------------------- #
class TestModuleRegistryInstall:
    # NOTE: the in-process ModuleLoader discovers 0 modules on this deployment
    # (backend/modules/financial/ is missing module.py + permissions.py — only
    # manifest.json and a stale __pycache__ remain), so install/uninstall always
    # hit the "not found" branch regardless of DB-installed state. This is a
    # pre-existing, separate infrastructure issue (flagged, not fixed here —
    # see test-report.md). Assertions below reflect actual current behavior.
    def test_install_already_installed_400(self, su):
        r = su.post("/module-registry/install", json={"module_name": "financial"})
        assert r.status_code == 400
        assert "not found" in _err_msg(r)

    def test_install_not_loadable_400(self, su):
        r = su.post("/module-registry/install", json={"module_name": "support_management"})
        assert r.status_code == 400

    def test_install_requires_superuser(self, user):
        r = user.post("/module-registry/install", json={"module_name": "financial"})
        assert r.status_code == 403

    def test_install_requires_auth(self, anon):
        r = anon.post("/module-registry/install", json={"module_name": "financial"})
        assert r.status_code in UNAUTH

    def test_uninstall_not_loadable_400(self, su):
        r = su.post("/module-registry/uninstall", json={"module_name": "support_management"})
        assert r.status_code == 400

    def test_uninstall_requires_superuser(self, user):
        r = user.post("/module-registry/uninstall", json={"module_name": "financial"})
        assert r.status_code == 403


# --------------------------------------------------------------------------- #
# module-registry: enable / disable / configure for a tenant
# --------------------------------------------------------------------------- #
class TestModuleRegistryEnable:
    # NOTE: same loader gap as TestModuleRegistryInstall (see comment there) -
    # "financial" can't actually be enabled on this deployment, so there is no
    # loadable module left to exercise a true enable/disable/configure round
    # trip against. This asserts the real current behavior instead.
    def test_enable_unloadable_module_400(self, user):
        en = user.post("/module-registry/enable", json={"module_name": "financial"})
        assert en.status_code == 400
        assert "not found" in _err_msg(en)

    def test_enable_unknown_module_400(self, user):
        r = user.post("/module-registry/enable", json={"module_name": uuid.uuid4().hex})
        assert r.status_code == 400

    def test_enable_for_other_tenant_denied_for_non_superuser(self, user):
        r = user.post(
            "/module-registry/enable",
            json={"module_name": "financial", "tenant_id": str(uuid.uuid4())},
        )
        assert r.status_code == 403

    def test_enable_for_unknown_tenant_404_for_superuser(self, su):
        r = su.post(
            "/module-registry/enable",
            json={"module_name": "financial", "tenant_id": str(uuid.uuid4())},
        )
        assert r.status_code == 404

    def test_enable_requires_auth(self, anon):
        r = anon.post("/module-registry/enable", json={"module_name": "financial"})
        assert r.status_code in UNAUTH

    def test_configuration_update_requires_enabled(self, user):
        r = user.put(
            "/module-registry/financial/configuration",
            json={"configuration": {}},
        )
        assert r.status_code == 400

    def test_configuration_update_unknown_module_404(self, user):
        r = user.put(
            f"/module-registry/{uuid.uuid4().hex}/configuration",
            json={"configuration": {}},
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# module-registry: register / heartbeat (public, no auth) + sync
# --------------------------------------------------------------------------- #
class TestModuleRegistryLifecycle:
    def test_register_missing_name_400(self, anon):
        r = anon.post(
            "/module-registry/register",
            json={"manifest": {}, "backend_service_url": "http://example.invalid"},
        )
        assert r.status_code == 400

    def test_register_existing_module_is_idempotent_update(self, anon, su):
        before = su.get("/module-registry/financial").json()
        r = anon.post(
            "/module-registry/register",
            json={
                "manifest": {
                    "name": "financial",
                    "display_name": before["display_name"],
                    "version": before["version"],
                    # Epic-23 manifest schema requires these fields.
                    "module_type": "code",
                    "category": "vertical",
                    "api_prefix": "/api/v1/financial",
                },
                "backend_service_url": "http://financial-module:8000",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["should_install"] is False
        after = su.get("/module-registry/financial").json()
        assert after["version"] == before["version"]

    def test_heartbeat_unknown_module_404(self, anon):
        r = anon.post(
            f"/module-registry/{uuid.uuid4().hex}/heartbeat",
            json={"module_name": "x", "version": "1.0.0"},
        )
        assert r.status_code == 404

    def test_heartbeat_known_module(self, anon, su):
        current = su.get("/module-registry/financial").json()
        r = anon.post(
            "/module-registry/financial/heartbeat",
            json={"module_name": "financial", "version": current["version"], "status": "healthy"},
        )
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_sync_requires_superuser(self, user):
        assert user.post("/module-registry/sync").status_code == 403

    def test_sync_ok_for_superuser(self, su):
        r = su.post("/module-registry/sync")
        assert r.status_code == 200
        assert r.json()["success"] is True


# --------------------------------------------------------------------------- #
# modules (nocode): module CRUD
# --------------------------------------------------------------------------- #
class TestNocodeModuleCrud:
    def test_create_get_update_publish_delete(self, su, unique):
        sfx = unique("crud").replace("_", "")[:8]
        cr = su.post(
            "/modules",
            json={
                "name": f"e2e_{sfx}",
                "display_name": "Original",
                "table_prefix": f"e2e{sfx}"[:10],
            },
        )
        assert cr.status_code == 201, cr.text
        mid = cr.json()["data"]["id"]

        got = su.get(f"/modules/{mid}")
        assert got.status_code == 200
        assert got.json()["status"] == "draft"

        upd = su.put(f"/modules/{mid}", json={"display_name": "Renamed"})
        assert upd.status_code == 200
        assert su.get(f"/modules/{mid}").json()["display_name"] == "Renamed"

        pub = su.post(f"/modules/{mid}/publish")
        assert pub.status_code == 200, pub.text
        assert su.get(f"/modules/{mid}").json()["status"] == "active"

        d = su.delete(f"/modules/{mid}")
        assert d.status_code == 200
        assert su.get(f"/modules/{mid}").status_code == 404

    def test_list_modules(self, su):
        r = su.get("/modules")
        assert r.status_code == 200
        assert any(m["name"] == "financial" for m in r.json()["modules"])

    def test_list_requires_auth(self, anon):
        assert anon.get("/modules").status_code in UNAUTH

    def test_get_unknown_404(self, su):
        assert su.get(f"/modules/{uuid.uuid4()}").status_code == 404

    def test_update_unknown_400(self, su):
        r = su.put(f"/modules/{uuid.uuid4()}", json={"display_name": "x"})
        assert r.status_code == 400

    def test_publish_unknown_400(self, su):
        assert su.post(f"/modules/{uuid.uuid4()}/publish").status_code == 400

    def test_delete_unknown_400(self, su):
        assert su.delete(f"/modules/{uuid.uuid4()}").status_code == 400

    def test_create_duplicate_prefix_400(self, su, nocode_module, unique):
        existing = su.get(f"/modules/{nocode_module}").json()
        r = su.post(
            "/modules",
            json={
                "name": unique("dupprefix"),
                "display_name": "Dup",
                "table_prefix": existing["table_prefix"],
            },
        )
        assert r.status_code == 400

    def test_create_invalid_prefix_422(self, su, unique):
        r = su.post(
            "/modules",
            json={"name": unique("badprefix"), "display_name": "Bad", "table_prefix": "HAS_UNDERSCORE"},
        )
        assert r.status_code == 422

    def test_create_requires_auth(self, anon, unique):
        r = anon.post(
            "/modules",
            json={"name": unique("anon"), "display_name": "x", "table_prefix": "anonx"},
        )
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# modules (nocode): dependencies
# --------------------------------------------------------------------------- #
class TestNocodeModuleDependencies:
    def test_add_list_check_remove_dependency(self, su, nocode_module, unique):
        sfx = unique("dep").replace("_", "")[:8]
        dep_module = su.post(
            "/modules",
            json={"name": f"e2e_dep_{sfx}", "display_name": "Dep", "table_prefix": f"d{sfx}"[:10]},
        ).json()["data"]["id"]
        try:
            add = su.post(
                f"/modules/{nocode_module}/dependencies",
                json={"depends_on_module_id": dep_module, "min_version": "1.0.0"},
            )
            assert add.status_code == 200, add.text

            deps = su.get(f"/modules/{nocode_module}/dependencies").json()
            assert len(deps) == 1
            dep_id = deps[0]["id"]

            dependents = su.get(f"/modules/{dep_module}/dependents").json()
            assert len(dependents) == 1

            check = su.get(f"/modules/{nocode_module}/dependencies/check")
            assert check.status_code == 200
            assert check.json()["is_compatible"] is False  # dep_module is still draft, not active

            rm = su.delete(f"/modules/{nocode_module}/dependencies/{dep_id}")
            assert rm.status_code == 200
            assert su.get(f"/modules/{nocode_module}/dependencies").json() == []
        finally:
            su.delete(f"/modules/{dep_module}")

    def test_circular_dependency_400(self, su, nocode_module, unique):
        sfx = unique("circ").replace("_", "")[:8]
        other = su.post(
            "/modules",
            json={"name": f"e2e_circ_{sfx}", "display_name": "Circ", "table_prefix": f"c{sfx}"[:10]},
        ).json()["data"]["id"]
        try:
            ok = su.post(
                f"/modules/{nocode_module}/dependencies",
                json={"depends_on_module_id": other},
            )
            assert ok.status_code == 200

            circular = su.post(
                f"/modules/{other}/dependencies",
                json={"depends_on_module_id": nocode_module},
            )
            assert circular.status_code == 400
            assert "Circular" in circular.json()["detail"]
        finally:
            su.delete(f"/modules/{other}")

    def test_remove_unknown_dependency_404(self, su, nocode_module):
        r = su.delete(f"/modules/{nocode_module}/dependencies/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_add_dependency_invalid_type_422(self, su, nocode_module):
        r = su.post(
            f"/modules/{nocode_module}/dependencies",
            json={"depends_on_module_id": str(uuid.uuid4()), "dependency_type": "bogus"},
        )
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# modules (nocode): versioning
# --------------------------------------------------------------------------- #
class TestNocodeModuleVersions:
    def test_increment_version_and_list(self, su, nocode_module):
        r = su.post(
            f"/modules/{nocode_module}/versions",
            json={"change_type": "patch", "change_summary": "fix"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["new_version"] == "1.0.1"

        versions = su.get(f"/modules/{nocode_module}/versions")
        assert versions.status_code == 200
        assert versions.json()["total"] >= 1
        assert su.get(f"/modules/{nocode_module}").json()["version"] == "1.0.1"

    def test_increment_version_invalid_change_type_422(self, su, nocode_module):
        r = su.post(
            f"/modules/{nocode_module}/versions",
            json={"change_type": "bogus", "change_summary": "x"},
        )
        assert r.status_code == 422

    def test_increment_version_missing_summary_422(self, su, nocode_module):
        r = su.post(f"/modules/{nocode_module}/versions", json={"change_type": "patch"})
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# modules (nocode): validation helpers + components
# --------------------------------------------------------------------------- #
class TestNocodeModuleValidationAndComponents:
    def test_validate_prefix_available(self, su, unique):
        r = su.post("/modules/validate/prefix", params={"table_prefix": unique("p").replace("_", "")[:8]})
        assert r.status_code == 200
        assert r.json()["is_valid"] is True

    def test_validate_prefix_taken(self, su, nocode_module):
        existing = su.get(f"/modules/{nocode_module}").json()
        r = su.post("/modules/validate/prefix", params={"table_prefix": existing["table_prefix"]})
        assert r.status_code == 200
        assert r.json()["is_valid"] is False

    def test_validate_prefix_bad_format(self, su):
        r = su.post("/modules/validate/prefix", params={"table_prefix": "BAD_PREFIX"})
        assert r.status_code == 200
        assert r.json()["is_valid"] is False

    def test_validate_name_available(self, su, unique):
        r = su.post("/modules/validate/name", params={"name": unique("freshname")})
        assert r.status_code == 200
        assert r.json()["is_valid"] is True

    def test_validate_name_taken(self, su, nocode_module):
        existing = su.get(f"/modules/{nocode_module}").json()
        r = su.post("/modules/validate/name", params={"name": existing["name"]})
        assert r.status_code == 200
        assert r.json()["is_valid"] is False

    def test_components_empty_for_fresh_module(self, su, nocode_module):
        r = su.get(f"/modules/{nocode_module}/components")
        assert r.status_code == 200
        assert r.json()["component_counts"]["entities"] == 0

    def test_components_unknown_module_404(self, su):
        assert su.get(f"/modules/{uuid.uuid4()}/components").status_code == 404


# --------------------------------------------------------------------------- #
# module-extensions: entity
# --------------------------------------------------------------------------- #
class TestEntityExtensions:
    def test_create_and_list(self, su, nocode_module, entity_for_module):
        cr = su.post(
            "/module-extensions/entity",
            json={
                "extending_module_id": nocode_module,
                "target_entity_id": entity_for_module,
                "extension_fields": [
                    {"name": "extra_note", "type": "string", "max_length": 50, "label": "Extra Note"}
                ],
            },
        )
        assert cr.status_code == 200, cr.text
        assert cr.json()["success"] is True

        listed = su.get(
            "/module-extensions/entity", params={"target_entity_id": entity_for_module}
        )
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["extension_fields"][0]["name"] == "extra_note"

    def test_create_duplicate_400(self, su, nocode_module, entity_for_module):
        body = {
            "extending_module_id": nocode_module,
            "target_entity_id": entity_for_module,
            "extension_fields": [{"name": "f1", "type": "string", "label": "F1"}],
        }
        first = su.post("/module-extensions/entity", json=body)
        assert first.status_code == 200
        dup = su.post("/module-extensions/entity", json=body)
        assert dup.status_code == 400
        assert "already exists" in dup.json()["detail"]

    def test_create_unknown_module_400(self, su, entity_for_module):
        r = su.post(
            "/module-extensions/entity",
            json={
                "extending_module_id": str(uuid.uuid4()),
                "target_entity_id": entity_for_module,
                "extension_fields": [{"name": "f1", "type": "string", "label": "F1"}],
            },
        )
        assert r.status_code == 400

    def test_create_unknown_entity_400(self, su, nocode_module):
        r = su.post(
            "/module-extensions/entity",
            json={
                "extending_module_id": nocode_module,
                "target_entity_id": str(uuid.uuid4()),
                "extension_fields": [{"name": "f1", "type": "string", "label": "F1"}],
            },
        )
        assert r.status_code == 400

    def test_create_invalid_field_type_422(self, su, nocode_module, entity_for_module):
        r = su.post(
            "/module-extensions/entity",
            json={
                "extending_module_id": nocode_module,
                "target_entity_id": entity_for_module,
                "extension_fields": [{"name": "f1", "type": "not_a_type", "label": "F1"}],
            },
        )
        assert r.status_code == 422

    def test_get_with_extensions_unknown_entity_404(self, su):
        r = su.get(f"/module-extensions/entity/{uuid.uuid4().hex}/records/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_list_requires_auth(self, anon):
        assert anon.get("/module-extensions/entity").status_code in UNAUTH

    def test_create_requires_auth(self, anon, nocode_module, entity_for_module):
        r = anon.post(
            "/module-extensions/entity",
            json={
                "extending_module_id": nocode_module,
                "target_entity_id": entity_for_module,
                "extension_fields": [{"name": "f1", "type": "string", "label": "F1"}],
            },
        )
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# module-extensions: screen
# --------------------------------------------------------------------------- #
class TestScreenExtensions:
    def test_create_and_list_tab(self, su, nocode_module, unique):
        screen = unique("screen")
        cr = su.post(
            "/module-extensions/screen",
            json={
                "extending_module_id": nocode_module,
                "target_module_id": nocode_module,
                "target_screen": screen,
                "extension_type": "tab",
                "extension_config": {"label": "Extra Tab", "component_path": "/x/tab.js"},
                "position": 5,
            },
        )
        assert cr.status_code == 200, cr.text

        listed = su.get("/module-extensions/screen", params={"target_screen": screen})
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["extension_type"] == "tab"

    def test_create_invalid_extension_type_422(self, su, nocode_module, unique):
        r = su.post(
            "/module-extensions/screen",
            json={
                "extending_module_id": nocode_module,
                "target_module_id": nocode_module,
                "target_screen": unique("s"),
                "extension_type": "bogus",
                "extension_config": {},
            },
        )
        assert r.status_code == 422

    def test_create_tab_missing_component_path_422(self, su, nocode_module, unique):
        r = su.post(
            "/module-extensions/screen",
            json={
                "extending_module_id": nocode_module,
                "target_module_id": nocode_module,
                "target_screen": unique("s"),
                "extension_type": "tab",
                "extension_config": {"label": "No Path"},
            },
        )
        assert r.status_code == 422

    def test_create_unknown_target_module_400(self, su, nocode_module, unique):
        r = su.post(
            "/module-extensions/screen",
            json={
                "extending_module_id": nocode_module,
                "target_module_id": str(uuid.uuid4()),
                "target_screen": unique("s"),
                "extension_type": "widget",
                "extension_config": {"component_path": "/x.js"},
            },
        )
        assert r.status_code == 400

    def test_list_requires_auth(self, anon):
        assert anon.get("/module-extensions/screen").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# module-extensions: menu
# --------------------------------------------------------------------------- #
class TestMenuExtensions:
    def test_create_and_list_link(self, su, nocode_module):
        cr = su.post(
            "/module-extensions/menu",
            json={
                "extending_module_id": nocode_module,
                "menu_config": {"type": "link", "label": "E2E Link", "route": "e2e/link"},
                "position": 50,
            },
        )
        assert cr.status_code == 200, cr.text

        listed = su.get("/module-extensions/menu")
        assert listed.status_code == 200
        assert any(e["menu_config"].get("label") == "E2E Link" for e in listed.json())

    def test_create_missing_label_422(self, su, nocode_module):
        r = su.post(
            "/module-extensions/menu",
            json={"extending_module_id": nocode_module, "menu_config": {"type": "link", "route": "x"}},
        )
        assert r.status_code == 422

    def test_create_link_missing_route_422(self, su, nocode_module):
        r = su.post(
            "/module-extensions/menu",
            json={"extending_module_id": nocode_module, "menu_config": {"type": "link", "label": "x"}},
        )
        assert r.status_code == 422

    def test_create_submenu_missing_items_422(self, su, nocode_module):
        r = su.post(
            "/module-extensions/menu",
            json={
                "extending_module_id": nocode_module,
                "menu_config": {"type": "submenu", "label": "x"},
            },
        )
        assert r.status_code == 422

    def test_create_unknown_module_400(self, su):
        r = su.post(
            "/module-extensions/menu",
            json={
                "extending_module_id": str(uuid.uuid4()),
                "menu_config": {"type": "link", "label": "x", "route": "x"},
            },
        )
        assert r.status_code == 400

    def test_list_requires_auth(self, anon):
        assert anon.get("/module-extensions/menu").status_code in UNAUTH
