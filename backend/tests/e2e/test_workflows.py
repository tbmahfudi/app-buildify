"""
Deep coverage of the `workflows` router (20 operations).

Two flows:
  * Definition design-time: create → states → transitions → publish/unpublish →
    simulate → update → delete.
  * Runtime instance execution: a self-contained fixture publishes an entity,
    creates a record, builds a workflow bound to that entity, then drives an
    instance through a transition and inspects its history.

All tenant-scoped, run as the `user` (ceo) fixture.
"""
import uuid

import pytest

from .conftest import drop_table_best_effort

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)


@pytest.fixture
def workflow(user):
    """A workflow with start+end states and one transition; cleaned up after."""
    sfx = uuid.uuid4().hex[:6]
    wid = user.post("/workflows/", json={"name": f"wf_{sfx}", "label": f"WF {sfx}", "canvas_data": {}}).json()["id"]
    s1 = user.post(f"/workflows/{wid}/states", json={"name": "open", "label": "Open", "state_type": "start"}).json()["id"]
    s2 = user.post(f"/workflows/{wid}/states", json={"name": "closed", "label": "Closed", "state_type": "end", "is_final": True}).json()["id"]
    tr = user.post(f"/workflows/{wid}/transitions", json={"name": "close", "label": "Close", "from_state_id": s1, "to_state_id": s2}).json()["id"]
    yield {"id": wid, "start": s1, "end": s2, "transition": tr}
    user.delete(f"/workflows/{wid}")


# --------------------------------------------------------------------------- #
# Definition CRUD
# --------------------------------------------------------------------------- #
class TestDefinition:
    def test_create_get_update_delete(self, user):
        sfx = uuid.uuid4().hex[:6]
        cr = user.post("/workflows/", json={"name": f"wf_{sfx}", "label": "L", "canvas_data": {}})
        assert cr.status_code in OK, cr.text
        wid = cr.json()["id"]
        try:
            assert user.get(f"/workflows/{wid}").json()["id"] == wid
            assert wid in [w["id"] for w in user.get("/workflows/").json()]
            up = user.put(f"/workflows/{wid}", json={"label": "Updated"})
            assert up.status_code == 200 and up.json()["label"] == "Updated"
        finally:
            assert user.delete(f"/workflows/{wid}").status_code in (200, 204)
        assert user.get(f"/workflows/{wid}").status_code == 404

    def test_create_missing_canvas_422(self, user):
        assert user.post("/workflows/", json={"name": "x", "label": "x"}).status_code == 422

    def test_get_unknown_404(self, user):
        assert user.get(f"/workflows/{uuid.uuid4()}").status_code == 404

    def test_create_requires_auth(self, anon):
        assert anon.post("/workflows/", json={"name": "x", "label": "x", "canvas_data": {}}).status_code in UNAUTH

    def test_list_requires_auth(self, anon):
        assert anon.get("/workflows/").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# States & transitions
# --------------------------------------------------------------------------- #
class TestStatesTransitions:
    def test_states_listed(self, user, workflow):
        states = user.get(f"/workflows/{workflow['id']}/states").json()
        names = [s["name"] for s in states]
        assert "open" in names and "closed" in names

    def test_update_state(self, user, workflow):
        r = user.put(f"/workflows/{workflow['id']}/states/{workflow['start']}", json={"label": "Reopened"})
        assert r.status_code == 200 and r.json()["label"] == "Reopened"

    def test_transitions_listed(self, user, workflow):
        trs = user.get(f"/workflows/{workflow['id']}/transitions").json()
        assert any(t["id"] == workflow["transition"] for t in trs)

    def test_delete_transition(self, user, workflow):
        r = user.delete(f"/workflows/{workflow['id']}/transitions/{workflow['transition']}")
        assert r.status_code in (200, 204)


# --------------------------------------------------------------------------- #
# Publish / unpublish / simulate
# --------------------------------------------------------------------------- #
class TestPublishSimulate:
    def test_publish_unpublish(self, user, workflow):
        assert user.post(f"/workflows/{workflow['id']}/publish").status_code == 200
        assert user.post(f"/workflows/{workflow['id']}/unpublish").status_code == 200

    def test_simulate(self, user, workflow):
        user.post(f"/workflows/{workflow['id']}/publish")
        r = user.post(f"/workflows/{workflow['id']}/simulate", json={})
        assert r.status_code == 200
        assert r.json().get("success") is True


# --------------------------------------------------------------------------- #
# Instance execution (self-contained: entity + record + bound workflow)
# --------------------------------------------------------------------------- #
@pytest.fixture
def instance_env(user):
    sfx = uuid.uuid4().hex[:8]
    name = f"e2e_wf_{sfx}"
    eid = user.post("/data-model/entities", json={
        "name": name, "label": "WF Ent", "plural_label": "WF Ents",
        "table_name": name, "data_scope": "tenant",
    }).json()["id"]
    user.post(f"/data-model/entities/{eid}/fields",
              json={"name": "title", "label": "Title", "field_type": "text", "data_type": "VARCHAR"})
    assert user.post(f"/data-model/entities/{eid}/publish", json={"commit_message": "e2e"}).status_code == 200
    rid = user.post(f"/dynamic-data/{name}/records", json={"data": {"title": "wf"}}).json()["id"]

    wid = user.post("/workflows/", json={"name": f"wf_{sfx}", "label": "WF", "entity_id": eid, "canvas_data": {}}).json()["id"]
    s1 = user.post(f"/workflows/{wid}/states", json={"name": "open", "label": "Open", "state_type": "start"}).json()["id"]
    s2 = user.post(f"/workflows/{wid}/states", json={"name": "closed", "label": "Closed", "state_type": "end", "is_final": True}).json()["id"]
    tr = user.post(f"/workflows/{wid}/transitions", json={"name": "close", "label": "Close", "from_state_id": s1, "to_state_id": s2}).json()["id"]
    user.post(f"/workflows/{wid}/publish")

    yield {"entity_id": eid, "record_id": rid, "workflow_id": wid, "transition": tr}

    user.delete(f"/workflows/{wid}")
    user.delete(f"/dynamic-data/{name}/records/{rid}")
    user.delete(f"/data-model/entities/{eid}")
    drop_table_best_effort(name)


class TestInstances:
    def test_instance_create_execute_history(self, user, instance_env):
        inst = user.post("/workflows/instances", json={
            "workflow_id": instance_env["workflow_id"],
            "entity_id": instance_env["entity_id"],
            "record_id": instance_env["record_id"],
            "context_data": {},
        })
        assert inst.status_code in OK, inst.text
        iid = inst.json()["id"]

        avail = user.get(f"/workflows/instances/{iid}/available-transitions")
        assert avail.status_code == 200
        assert any(t["id"] == instance_env["transition"] for t in avail.json())

        ex = user.post(f"/workflows/instances/{iid}/execute",
                       json={"transition_id": instance_env["transition"], "comment": "done", "data": {}})
        assert ex.status_code == 200, ex.text

        hist = user.get(f"/workflows/instances/{iid}/history")
        assert hist.status_code == 200 and len(hist.json()) >= 1

    def test_list_instances(self, user):
        assert user.get("/workflows/instances").status_code == 200

    def test_instance_unknown_404(self, user):
        assert user.get(f"/workflows/instances/{uuid.uuid4()}").status_code == 404
