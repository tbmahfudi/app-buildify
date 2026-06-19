"""
Deep coverage of the `scheduler` router (14 ops): configs CRUD + effective
config resolution, jobs CRUD + manual execute, execution list/get, execution
logs.

Includes regression coverage for three defects found and fixed in this
router:

- DEF-015 (Critical): `SchedulerConfig`/`SchedulerJob`/`SchedulerJobExecution`/
  `SchedulerJobLog` models declared their GUID primary key with no
  `default=generate_uuid` (every other GUID-PK model in the codebase has
  this), and the service layer never set `id=` explicitly — every create
  500'd with a Postgres NotNullViolation. Compounded by every schema/router
  path param typing these ids as `int` instead of `UUID` (the real DB
  columns are `uuid`), so even a manually-inserted row 422'd on GET/PUT/DELETE
  by id. Fixed by adding the default to the 4 model columns and correcting
  every `int` annotation to `UUID`.
- DEF-016 (Critical/High, IDOR): most by-id endpoints (config get/update/
  delete, job update/delete, execution list/get, execution logs) had zero
  tenant-ownership checks, and the two create endpoints plus the job-list
  endpoint accepted a caller-controlled `tenant_id` with no restriction to
  the caller's own tenant. Fixed via a shared `_enforce_tenant_access` helper
  applied to every tenant-scoped endpoint, plus explicit cross-tenant guards
  on both create endpoints and forced tenant-scoping in `list_scheduler_jobs`.
- DEF-017 (Medium): `list_job_executions`'s `status` query parameter shadowed
  the `fastapi.status` module used later in the same function body, turning
  the job-not-found path into a 500 (`AttributeError`) instead of a 404.
  Fixed by renaming the parameter to `execution_status` with
  `Query(None, alias="status", ...)`.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)

MEDCARE_CREDS = {"email": "ceo@medcare.com", "password": "password123"}


@pytest.fixture(scope="session")
def tech_tenant_id(user):
    return user.get("/auth/me").json()["tenant_id"]


@pytest.fixture
def config(user, tech_tenant_id, unique):
    # The DB has a unique constraint on (config_level, tenant_id), so only one
    # TENANT-level config can exist per tenant.  An interrupted test run may
    # leave a stale row behind, which would 500 the next create attempt.
    # Self-heal: if a TENANT-level config already exists, delete it first.
    eff = user.get("/scheduler/configs/effective")
    if eff.status_code == 200 and eff.json().get("config_level") == "TENANT":
        user.delete(f"/scheduler/configs/{eff.json()['id']}")

    body = {
        "name": unique("sched-cfg"),
        "config_level": "tenant",
        "tenant_id": tech_tenant_id,
    }
    r = user.post("/scheduler/configs", json=body)
    assert r.status_code in OK, r.text
    cid = r.json()["id"]
    yield cid
    user.delete(f"/scheduler/configs/{cid}")


@pytest.fixture
def job(user, config, unique):
    body = {
        "name": unique("sched-job"),
        "job_type": "custom",
        "config_id": config,
        "cron_expression": "0 9 * * 1",
    }
    r = user.post("/scheduler/jobs", json=body)
    assert r.status_code in OK, r.text
    jid = r.json()["id"]
    yield jid
    user.delete(f"/scheduler/jobs/{jid}")


# --------------------------------------------------------------------------- #
# Configs
# --------------------------------------------------------------------------- #
class TestConfigs:
    def test_create_get_update_delete(self, user, tech_tenant_id, unique):
        cr = user.post("/scheduler/configs", json={
            "name": unique("sched-cfg"),
            "config_level": "tenant",
            "tenant_id": tech_tenant_id,
        })
        assert cr.status_code in OK, cr.text
        cid = cr.json()["id"]
        # DEF-015 regression: id is a real UUID, not the integer literal 1.
        uuid.UUID(cid)
        try:
            got = user.get(f"/scheduler/configs/{cid}")
            assert got.status_code == 200 and got.json()["id"] == cid

            up = user.put(f"/scheduler/configs/{cid}", json={"max_concurrent_jobs": 10})
            assert up.status_code == 200 and up.json()["max_concurrent_jobs"] == 10
        finally:
            dele = user.delete(f"/scheduler/configs/{cid}")
            assert dele.status_code == 204

        assert user.get(f"/scheduler/configs/{cid}").status_code == 404

    def test_create_tenant_level_requires_tenant_id(self, user, unique):
        r = user.post("/scheduler/configs", json={
            "name": unique("sched-cfg"), "config_level": "tenant",
        })
        assert r.status_code == 400

    def test_create_system_level_forbidden_for_non_superuser(self, user, unique):
        r = user.post("/scheduler/configs", json={
            "name": unique("sched-cfg"), "config_level": "system",
        })
        assert r.status_code == 403

    def test_create_system_level_allowed_for_superuser(self, su, unique):
        r = su.post("/scheduler/configs", json={
            "name": unique("sched-cfg"), "config_level": "system",
        })
        assert r.status_code in OK, r.text
        su.delete(f"/scheduler/configs/{r.json()['id']}")

    def test_create_cross_tenant_id_forbidden(self, user, unique):
        r = user.post("/scheduler/configs", json={
            "name": unique("sched-cfg"), "config_level": "tenant",
            "tenant_id": str(uuid.uuid4()),
        })
        assert r.status_code == 403

    def test_get_unknown_404(self, user):
        assert user.get(f"/scheduler/configs/{uuid.uuid4()}").status_code == 404

    def test_update_unknown_404(self, user):
        assert user.put(f"/scheduler/configs/{uuid.uuid4()}", json={"max_concurrent_jobs": 1}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/scheduler/configs/{uuid.uuid4()}").status_code == 404

    def test_get_effective_config(self, user, config):
        r = user.get("/scheduler/configs/effective")
        assert r.status_code == 200, r.text

    def test_requires_auth(self, anon, config):
        assert anon.get(f"/scheduler/configs/{config}").status_code in UNAUTH
        assert anon.post("/scheduler/configs", json={"name": "x", "config_level": "system"}).status_code in UNAUTH

    # ---- DEF-016 regression: cross-tenant IDOR closed ---- #
    def test_cross_tenant_get_forbidden(self, ephemeral, config):
        with ephemeral(MEDCARE_CREDS) as med:
            r = med.get(f"/scheduler/configs/{config}")
            assert r.status_code == 403, r.text

    def test_cross_tenant_update_forbidden(self, ephemeral, config):
        with ephemeral(MEDCARE_CREDS) as med:
            r = med.put(f"/scheduler/configs/{config}", json={"max_concurrent_jobs": 99})
            assert r.status_code == 403, r.text

    def test_cross_tenant_delete_forbidden(self, ephemeral, config):
        with ephemeral(MEDCARE_CREDS) as med:
            r = med.delete(f"/scheduler/configs/{config}")
            assert r.status_code == 403, r.text


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
class TestJobs:
    def test_create_get_update_delete(self, user, config, unique):
        cr = user.post("/scheduler/jobs", json={
            "name": unique("sched-job"), "job_type": "custom",
            "config_id": config, "cron_expression": "0 9 * * 1",
        })
        assert cr.status_code in OK, cr.text
        jid = cr.json()["id"]
        uuid.UUID(jid)  # DEF-015 regression
        try:
            got = user.get(f"/scheduler/jobs/{jid}")
            assert got.status_code == 200 and got.json()["id"] == jid

            up = user.put(f"/scheduler/jobs/{jid}", json={"is_active": False})
            assert up.status_code == 200 and up.json()["is_active"] is False
        finally:
            dele = user.delete(f"/scheduler/jobs/{jid}")
            assert dele.status_code == 204

        assert user.get(f"/scheduler/jobs/{jid}").status_code == 404

    def test_create_requires_schedule(self, user, config, unique):
        r = user.post("/scheduler/jobs", json={
            "name": unique("sched-job"), "job_type": "custom", "config_id": config,
        })
        assert r.status_code == 422

    def test_create_unknown_config_400(self, user, unique):
        r = user.post("/scheduler/jobs", json={
            "name": unique("sched-job"), "job_type": "custom",
            "config_id": str(uuid.uuid4()), "cron_expression": "0 9 * * 1",
        })
        assert r.status_code == 400

    def test_create_cross_tenant_id_forbidden(self, user, config, unique):
        r = user.post("/scheduler/jobs", json={
            "name": unique("sched-job"), "job_type": "custom", "config_id": config,
            "cron_expression": "0 9 * * 1", "tenant_id": str(uuid.uuid4()),
        })
        assert r.status_code == 403

    def test_list_jobs(self, user, job):
        r = user.get("/scheduler/jobs")
        assert r.status_code == 200
        assert job in [j["id"] for j in r.json()["items"]]

    def test_list_jobs_ignores_foreign_tenant_id_query_param(self, user, job, tech_tenant_id):
        """DEF-016 regression: non-superusers are forced to their own tenant
        regardless of an explicit ?tenant_id= query param."""
        r = user.get("/scheduler/jobs", params={"tenant_id": str(uuid.uuid4())})
        assert r.status_code == 200
        assert job in [j["id"] for j in r.json()["items"]]

    def test_get_unknown_404(self, user):
        assert user.get(f"/scheduler/jobs/{uuid.uuid4()}").status_code == 404

    def test_update_unknown_404(self, user):
        assert user.put(f"/scheduler/jobs/{uuid.uuid4()}", json={"is_active": False}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/scheduler/jobs/{uuid.uuid4()}").status_code == 404

    def test_requires_auth(self, anon, job):
        assert anon.get(f"/scheduler/jobs/{job}").status_code in UNAUTH
        assert anon.get("/scheduler/jobs").status_code in UNAUTH

    # ---- DEF-016 regression: cross-tenant IDOR closed ---- #
    def test_cross_tenant_get_forbidden(self, ephemeral, job):
        with ephemeral(MEDCARE_CREDS) as med:
            assert med.get(f"/scheduler/jobs/{job}").status_code == 403

    def test_cross_tenant_update_forbidden(self, ephemeral, job):
        with ephemeral(MEDCARE_CREDS) as med:
            assert med.put(f"/scheduler/jobs/{job}", json={"is_active": False}).status_code == 403

    def test_cross_tenant_delete_forbidden(self, ephemeral, job):
        with ephemeral(MEDCARE_CREDS) as med:
            assert med.delete(f"/scheduler/jobs/{job}").status_code == 403

    def test_cross_tenant_execute_forbidden(self, ephemeral, job):
        with ephemeral(MEDCARE_CREDS) as med:
            assert med.post(f"/scheduler/jobs/{job}/execute", json={}).status_code == 403


# --------------------------------------------------------------------------- #
# Manual execution + execution history
# --------------------------------------------------------------------------- #
class TestExecutions:
    def test_execute_then_list_and_get(self, user, job):
        ex = user.post(f"/scheduler/jobs/{job}/execute", json={})
        assert ex.status_code == 200, ex.text
        execution_id = ex.json()["execution_id"]
        uuid.UUID(execution_id)  # DEF-015 regression

        listed = user.get(f"/scheduler/jobs/{job}/executions")
        assert listed.status_code == 200
        assert execution_id in [e["id"] for e in listed.json()["items"]]

        got = user.get(f"/scheduler/executions/{execution_id}")
        assert got.status_code == 200 and got.json()["id"] == execution_id

    def test_execute_unknown_job_404(self, user):
        assert user.post(f"/scheduler/jobs/{uuid.uuid4()}/execute", json={}).status_code == 404

    # ---- DEF-017 regression: status-filter on missing job is a clean 404 ---- #
    def test_list_executions_with_status_filter_unknown_job_404_not_500(self, user):
        r = user.get(f"/scheduler/jobs/{uuid.uuid4()}/executions", params={"status": "pending"})
        assert r.status_code == 404, r.text

    def test_list_executions_with_status_filter(self, user, job):
        user.post(f"/scheduler/jobs/{job}/execute", json={})
        r = user.get(f"/scheduler/jobs/{job}/executions", params={"status": "pending"})
        assert r.status_code == 200, r.text
        assert all(e["status"] == "pending" for e in r.json()["items"])

    def test_get_execution_unknown_404(self, user):
        assert user.get(f"/scheduler/executions/{uuid.uuid4()}").status_code == 404

    def test_requires_auth(self, anon, job):
        assert anon.get(f"/scheduler/jobs/{job}/executions").status_code in UNAUTH
        assert anon.post(f"/scheduler/jobs/{job}/execute", json={}).status_code in UNAUTH

    # ---- DEF-016 regression: cross-tenant IDOR closed ---- #
    def test_cross_tenant_list_executions_forbidden(self, ephemeral, job):
        with ephemeral(MEDCARE_CREDS) as med:
            assert med.get(f"/scheduler/jobs/{job}/executions").status_code == 403

    def test_cross_tenant_get_execution_forbidden(self, user, ephemeral, job):
        ex = user.post(f"/scheduler/jobs/{job}/execute", json={})
        execution_id = ex.json()["execution_id"]
        with ephemeral(MEDCARE_CREDS) as med:
            assert med.get(f"/scheduler/executions/{execution_id}").status_code == 403


# --------------------------------------------------------------------------- #
# Execution logs
# --------------------------------------------------------------------------- #
class TestExecutionLogs:
    def test_get_logs_for_execution(self, user, job):
        ex = user.post(f"/scheduler/jobs/{job}/execute", json={})
        execution_id = ex.json()["execution_id"]
        r = user.get(f"/scheduler/executions/{execution_id}/logs")
        assert r.status_code == 200, r.text
        assert "items" in r.json()

    def test_get_logs_unknown_execution_404(self, user):
        assert user.get(f"/scheduler/executions/{uuid.uuid4()}/logs").status_code == 404

    def test_requires_auth(self, anon, job):
        ex_response = anon.get(f"/scheduler/executions/{uuid.uuid4()}/logs")
        assert ex_response.status_code in UNAUTH

    # ---- DEF-016 regression: cross-tenant IDOR closed ---- #
    def test_cross_tenant_get_logs_forbidden(self, user, ephemeral, job):
        ex = user.post(f"/scheduler/jobs/{job}/execute", json={})
        execution_id = ex.json()["execution_id"]
        with ephemeral(MEDCARE_CREDS) as med:
            assert med.get(f"/scheduler/executions/{execution_id}/logs").status_code == 403
