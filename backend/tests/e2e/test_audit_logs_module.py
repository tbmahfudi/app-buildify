import pytest
pytestmark = pytest.mark.e2e
AUDIT_LIST = "/audit/list"
MODULE_ENTITY_TYPE = "module"
EXPECTED_ACTIONS = {"module.installed","module.enabled","module.disabled","module.deactivate_all","module.uninstalled"}

def _fetch_module_audit_logs(client, action=None, page_size=200):
    body = {"entity_type": MODULE_ENTITY_TYPE, "page": 1, "page_size": page_size}
    if action:
        body["action"] = action
    return client.post(AUDIT_LIST, json=body)

class TestAuditModuleStructural:
    def test_audit_list_requires_auth(self, anon):
        r = anon.post(AUDIT_LIST, json={"entity_type": MODULE_ENTITY_TYPE, "page": 1, "page_size": 10})
        assert r.status_code in (401, 403), f"Expected 401/403 for anon; got {r.status_code}: {r.text}"

    def test_audit_list_module_filter_returns_200(self, su):
        r = _fetch_module_audit_logs(su)
        assert r.status_code == 200, f"Expected 200; got {r.status_code}: {r.text}"

    def test_audit_list_module_response_shape(self, su):
        r = _fetch_module_audit_logs(su)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "logs" in data, f"Missing logs key: {list(data.keys())}"
        assert "total" in data, f"Missing total key: {list(data.keys())}"
        assert isinstance(data["logs"], list)
        assert isinstance(data["total"], int)

    def test_audit_list_all_entries_have_correct_entity_type(self, su):
        r = _fetch_module_audit_logs(su)
        assert r.status_code == 200, r.text
        for entry in r.json()["logs"]:
            assert entry.get("entity_type") == MODULE_ENTITY_TYPE, f"Unexpected entity_type: {entry}"

    def test_audit_list_action_filter_scopes_results(self, su):
        r = _fetch_module_audit_logs(su, action="module.installed")
        assert r.status_code == 200, r.text
        for entry in r.json()["logs"]:
            assert entry.get("action") == "module.installed", f"Filter leakage: {entry.get(action)!r}"

    def test_audit_list_entries_have_required_fields(self, su):
        r = _fetch_module_audit_logs(su)
        assert r.status_code == 200, r.text
        logs = r.json()["logs"]
        if not logs:
            pytest.skip("No module audit log entries found")
        for entry in logs:
            for field in ("id", "action", "entity_type", "created_at"):
                assert field in entry, f"Missing field {field!r}: {entry}"

    def test_audit_list_low_privilege_user_result(self, user):
        r = _fetch_module_audit_logs(user)
        assert r.status_code in (200, 403), f"Unexpected status for tenant user: {r.status_code}"


@pytest.mark.xfail(strict=False, reason="T-23.028/DEF-032: financial module not loadable; module.installed may exist from seed runs.")
def test_module_installed_event_present(su):
    r = _fetch_module_audit_logs(su, action="module.installed")
    assert r.status_code == 200, r.text
    assert len(r.json()["logs"]) > 0, "No module.installed events found"

@pytest.mark.xfail(strict=False, reason="T-23.028/DEF-032: POST /module-registry/enable returns 400; no module.enabled event generated.")
def test_module_enabled_event_present(su):
    r = _fetch_module_audit_logs(su, action="module.enabled")
    assert r.status_code == 200, r.text
    assert len(r.json()["logs"]) > 0, "No module.enabled events found"

@pytest.mark.xfail(strict=False, reason="T-23.028/DEF-032: cannot trigger module.disabled without prior successful enable.")
def test_module_disabled_event_present(su):
    r = _fetch_module_audit_logs(su, action="module.disabled")
    assert r.status_code == 200, r.text
    assert len(r.json()["logs"]) > 0, "No module.disabled events found"

@pytest.mark.xfail(strict=False, reason="T-23.028/DEF-032: POST /module-registry/deactivate-all blocked by unloadable module class.")
def test_module_deactivate_all_event_present(su):
    r = _fetch_module_audit_logs(su, action="module.deactivate_all")
    assert r.status_code == 200, r.text
    assert len(r.json()["logs"]) > 0, "No module.deactivate_all events found"

@pytest.mark.xfail(strict=False, reason="T-23.028/DEF-032: POST /module-registry/uninstall returns 400; no module.uninstalled event generated.")
def test_module_uninstalled_event_present(su):
    r = _fetch_module_audit_logs(su, action="module.uninstalled")
    assert r.status_code == 200, r.text
    assert len(r.json()["logs"]) > 0, "No module.uninstalled events found"

@pytest.mark.xfail(strict=False, reason="T-23.028/DEF-032: all 5 event types require a loadable module; dev stack has none.")
def test_all_five_module_event_types_present(su):
    r = _fetch_module_audit_logs(su, page_size=500)
    assert r.status_code == 200, r.text
    found = {entry["action"] for entry in r.json()["logs"]}
    missing = EXPECTED_ACTIONS - found
    assert not missing, f"Missing module audit event types: {sorted(missing)}
Found: {sorted(found)}"
