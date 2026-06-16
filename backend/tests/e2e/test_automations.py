"""
Deep coverage of the `automations` router (16 operations):
rules (CRUD + toggle + test + execute), executions, action-templates, webhooks.
Tenant-scoped; run as `user` (ceo).
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)


@pytest.fixture
def rule(user):
    sfx = uuid.uuid4().hex[:6]
    rid = user.post("/automations/rules", json={"name": f"rule_{sfx}", "label": "Rule", "trigger_type": "manual"}).json()["id"]
    yield rid
    user.delete(f"/automations/rules/{rid}")


@pytest.fixture
def webhook(user):
    sfx = uuid.uuid4().hex[:6]
    wid = user.post("/automations/webhooks", json={"name": f"wh_{sfx}", "label": "WH", "webhook_type": "outbound"}).json()["id"]
    yield wid
    user.delete(f"/automations/webhooks/{wid}")


# --------------------------------------------------------------------------- #
# Rules
# --------------------------------------------------------------------------- #
class TestRules:
    def test_create_get_update_delete(self, user):
        sfx = uuid.uuid4().hex[:6]
        cr = user.post("/automations/rules", json={"name": f"rule_{sfx}", "label": "L", "trigger_type": "manual"})
        assert cr.status_code in OK, cr.text
        rid = cr.json()["id"]
        try:
            assert user.get(f"/automations/rules/{rid}").json()["id"] == rid
            assert rid in [r["id"] for r in user.get("/automations/rules").json()]
            up = user.put(f"/automations/rules/{rid}", json={"label": "Updated"})
            assert up.status_code == 200 and up.json()["label"] == "Updated"
        finally:
            assert user.delete(f"/automations/rules/{rid}").status_code in (200, 204)
        assert user.get(f"/automations/rules/{rid}").status_code == 404

    def test_toggle(self, user, rule):
        before = user.get(f"/automations/rules/{rule}").json().get("is_active")
        user.post(f"/automations/rules/{rule}/toggle")
        after = user.get(f"/automations/rules/{rule}").json().get("is_active")
        assert before != after

    def test_test_endpoint(self, user, rule):
        r = user.post(f"/automations/rules/{rule}/test", json={"test_data": {}})
        assert r.status_code == 200
        assert "success" in r.json()

    def test_execute_requires_active_rule(self, user, rule):
        # rules are created inactive; executing one must be rejected with 400
        assert user.post(f"/automations/rules/{rule}/execute").status_code == 400

    def test_execute_when_active(self, user, rule):
        # activate, then execute should be accepted
        user.post(f"/automations/rules/{rule}/toggle")
        r = user.post(f"/automations/rules/{rule}/execute")
        assert r.status_code in (200, 202), r.text

    def test_create_missing_trigger_422(self, user):
        assert user.post("/automations/rules", json={"name": "x", "label": "x"}).status_code == 422

    def test_get_unknown_404(self, user):
        assert user.get(f"/automations/rules/{uuid.uuid4()}").status_code == 404

    def test_create_requires_auth(self, anon):
        assert anon.post("/automations/rules", json={"name": "x", "label": "x", "trigger_type": "manual"}).status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Executions & action templates
# --------------------------------------------------------------------------- #
class TestExecutionsTemplates:
    def test_list_executions(self, user):
        r = user.get("/automations/executions")
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_get_execution_unknown_404(self, user):
        assert user.get(f"/automations/executions/{uuid.uuid4()}").status_code == 404

    def test_action_templates(self, user):
        r = user.get("/automations/action-templates")
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_executions_requires_auth(self, anon):
        assert anon.get("/automations/executions").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Webhooks
# --------------------------------------------------------------------------- #
class TestWebhooks:
    def test_create_get_update_delete(self, user):
        sfx = uuid.uuid4().hex[:6]
        cr = user.post("/automations/webhooks", json={"name": f"wh_{sfx}", "label": "L", "webhook_type": "outbound"})
        assert cr.status_code in OK, cr.text
        wid = cr.json()["id"]
        try:
            assert user.get(f"/automations/webhooks/{wid}").json()["id"] == wid
            assert wid in [w["id"] for w in user.get("/automations/webhooks").json()]
            up = user.put(f"/automations/webhooks/{wid}", json={"label": "Updated"})
            assert up.status_code == 200 and up.json()["label"] == "Updated"
        finally:
            assert user.delete(f"/automations/webhooks/{wid}").status_code in (200, 204)
        assert user.get(f"/automations/webhooks/{wid}").status_code == 404

    def test_create_missing_type_422(self, user):
        assert user.post("/automations/webhooks", json={"name": "x", "label": "x"}).status_code == 422

    def test_get_unknown_404(self, user):
        assert user.get(f"/automations/webhooks/{uuid.uuid4()}").status_code == 404
