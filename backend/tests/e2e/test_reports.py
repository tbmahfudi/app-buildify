"""
Deep coverage of the `reports` router (17 ops): definitions CRUD, execute,
execute/export, preview (ad-hoc), execution history, lookup, schedules CRUD,
templates, join-suggestions.

Includes regression coverage for the SQL injection vulnerability (CWE-89)
found and fixed in `ReportService` (the query builder interpolated filter
values and identifiers — base_entity, columns, group_by, order_by,
aggregation — directly into raw SQL with no escaping/allow-listing). Fix:
parameterize all values via bind params, validate every identifier against
the table's real columns via information_schema.
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)

# DEF-011: the seeded "Tenant Administrator" role (ceo@techstart's role) has
# zero `reports:*` permissions granted, even though all of them exist in the
# permissions catalogue — the entire reports feature is unreachable for any
# seeded tenant user out of the box. ceo *does* have `roles:assign_permissions:
# tenant`, so this fixture self-grants the missing permissions once per test
# session (idempotent — assigning an already-granted permission is a no-op).
_REPORTS_PERMISSION_CODES = [
    "reports:create:tenant", "reports:read:tenant", "reports:update:own",
    "reports:delete:own", "reports:execute:tenant", "reports:export:tenant",
    "reports:history:read:tenant", "reports:schedule:create:tenant",
    "reports:schedule:read:tenant", "reports:schedule:update:own",
    "reports:schedule:delete:own", "reports:templates:read:tenant",
    "reports:templates:create:tenant",
]


@pytest.fixture(scope="session", autouse=True)
def _grant_reports_permissions(user):
    me = user.get("/auth/me").json()
    tenant_id = me["tenant_id"]
    roles = user.get("/rbac/roles", params={"limit": 1000}).json()["items"]
    # tenant_admin is seeded both as a platform template (tenant_id None) and as
    # this tenant's own copy — only the latter is the role ceo actually holds.
    role = next(r for r in roles if r["code"] == "tenant_admin" and r["tenant_id"] == tenant_id)
    perms = user.get("/rbac/permissions", params={"limit": 1000}).json()["items"]
    perm_ids = [p["id"] for p in perms if p["code"] in _REPORTS_PERMISSION_CODES]
    assert len(perm_ids) == len(_REPORTS_PERMISSION_CODES), "reports permission codes missing from catalogue"
    r = user.post(f"/rbac/roles/{role['id']}/permissions", json=perm_ids)
    assert r.status_code in OK, r.text


@pytest.fixture
def report_def(user, unique):
    name = unique("rpt")
    body = {
        "name": name,
        "base_entity": "users",
        "columns_config": [{"name": "id"}, {"name": "email"}],
        "query_config": {},
    }
    r = user.post("/reports/definitions", json=body)
    assert r.status_code in OK, r.text
    rid = r.json()["id"]
    yield rid
    user.delete(f"/reports/definitions/{rid}")


# --------------------------------------------------------------------------- #
# Report definitions CRUD
# --------------------------------------------------------------------------- #
class TestReportDefinitions:
    def test_create_get_update_delete(self, user, unique):
        name = unique("rpt")
        cr = user.post("/reports/definitions", json={
            "name": name,
            "base_entity": "users",
            "columns_config": [{"name": "id"}],
        })
        assert cr.status_code in OK, cr.text
        rid = cr.json()["id"]
        try:
            got = user.get(f"/reports/definitions/{rid}")
            assert got.status_code == 200 and got.json()["id"] == rid

            ids = [r["id"] for r in user.get("/reports/definitions").json()]
            assert rid in ids

            up = user.put(f"/reports/definitions/{rid}", json={"title": "Updated title"})
            assert up.status_code == 200 and up.json()["title"] == "Updated title"
        finally:
            dele = user.delete(f"/reports/definitions/{rid}")
            assert dele.status_code == 204

        # soft delete: definitions list/get no longer surface it
        assert user.get(f"/reports/definitions/{rid}").status_code == 404

    def test_create_derives_base_entity_from_data_source(self, user, unique):
        name = unique("rpt")
        cr = user.post("/reports/definitions", json={
            "name": name,
            "data_source": {"entities": [{"entity_name": "users"}]},
        })
        assert cr.status_code in OK, cr.text
        rid = cr.json()["id"]
        assert cr.json()["base_entity"] == "users"
        user.delete(f"/reports/definitions/{rid}")

    def test_create_missing_name_422(self, user):
        assert user.post("/reports/definitions", json={"base_entity": "users"}).status_code == 422

    def test_get_unknown_404(self, user):
        assert user.get(f"/reports/definitions/{uuid.uuid4()}").status_code == 404

    def test_update_unknown_404(self, user):
        assert user.put(f"/reports/definitions/{uuid.uuid4()}", json={"title": "x"}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/reports/definitions/{uuid.uuid4()}").status_code == 404

    def test_list_filter_by_category(self, user, unique):
        name = unique("rpt")
        cr = user.post("/reports/definitions", json={
            "name": name, "base_entity": "users", "category": "finance",
        })
        rid = cr.json()["id"]
        try:
            results = user.get("/reports/definitions", params={"category": "finance"}).json()
            assert all(r["category"] == "finance" for r in results)
            assert rid in [r["id"] for r in results]
        finally:
            user.delete(f"/reports/definitions/{rid}")

    def test_requires_auth(self, anon):
        assert anon.get("/reports/definitions").status_code in UNAUTH
        assert anon.post("/reports/definitions", json={"name": "x"}).status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Execute / execute+export
# --------------------------------------------------------------------------- #
class TestExecute:
    def test_execute_success(self, user, report_def):
        r = user.post("/reports/execute", json={"report_definition_id": report_def, "use_cache": False})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "completed"
        assert body["report_definition_id"] == report_def

    def test_execute_unknown_report_404(self, user):
        r = user.post("/reports/execute", json={"report_definition_id": str(uuid.uuid4())})
        assert r.status_code == 404

    def test_execute_requires_auth(self, anon, report_def):
        r = anon.post("/reports/execute", json={"report_definition_id": report_def})
        assert r.status_code in UNAUTH

    def test_execute_export_csv(self, user, report_def):
        r = user.post("/reports/execute/export", json={
            "report_definition_id": report_def, "export_format": "csv",
        })
        assert r.status_code == 200, r.text
        assert "csv" in r.headers.get("content-type", "") or r.headers.get("content-disposition", "").endswith('.csv"')

    def test_execute_export_unknown_report_404(self, user):
        r = user.post("/reports/execute/export", json={"report_definition_id": str(uuid.uuid4())})
        assert r.status_code == 404

    def test_execution_history(self, user, report_def):
        user.post("/reports/execute", json={"report_definition_id": report_def, "use_cache": False})
        hist = user.get("/reports/executions/history", params={"report_id": report_def})
        assert hist.status_code == 200
        assert any(h["report_definition_id"] == report_def for h in hist.json())


# --------------------------------------------------------------------------- #
# Preview (ad-hoc) — legacy flat format + report-designer nested format
# --------------------------------------------------------------------------- #
class TestPreview:
    def test_preview_flat_format(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id"}, {"name": "email"}],
            "limit": 5,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["columns"] == ["id", "email"]
        assert body["row_count"] <= 5

    def test_preview_designer_format(self, user):
        r = user.post("/reports/preview", json={
            "data_source": {"base_entity": "users", "entities": [{"entity_name": "users"}]},
            "columns": [{"name": "id", "alias": "ID"}, {"name": "email"}],
            "limit": 5,
        })
        assert r.status_code == 200, r.text
        assert set(r.json()["columns"]) == {"ID", "email"}

    def test_preview_no_entity_returns_empty(self, user):
        r = user.post("/reports/preview", json={})
        assert r.status_code == 200
        assert r.json() == {"data": [], "columns": [], "row_count": 0}

    def test_preview_group_by_and_aggregation(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [
                {"name": "tenant_id"},
                {"name": "id", "aggregation": "count", "label": "cnt"},
            ],
            "query_config": {"group_by": ["tenant_id"]},
            "limit": 50,
        })
        assert r.status_code == 200, r.text
        assert set(r.json()["columns"]) == {"tenant_id", "cnt"}

    def test_preview_order_by(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id"}, {"name": "email"}],
            "query_config": {"order_by": [{"field": "email", "direction": "desc"}]},
            "limit": 3,
        })
        assert r.status_code == 200, r.text

    def test_preview_legit_filter(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id"}, {"name": "email"}],
            "query_config": {"filters": {"logic": "AND", "conditions": [
                {"field": "email", "operator": "eq", "value": "superadmin@system.com"},
            ]}},
            "limit": 50,
        })
        assert r.status_code == 200, r.text

    def test_preview_requires_auth(self, anon):
        assert anon.post("/reports/preview", json={"base_entity": "users"}).status_code in UNAUTH

    # ---- Security regression: SQL injection (CWE-89) closed ---- #
    def test_preview_sql_injection_filter_value_no_longer_bypasses(self, user):
        """
        Original PoC: filter value `"x' OR '1'='1"` on email used to break out
        of the quoted literal and return every row across every tenant. The
        value is now bound, so the literal string matches nothing.
        """
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id"}, {"name": "email"}],
            "query_config": {"filters": {"logic": "AND", "conditions": [
                {"field": "email", "operator": "eq", "value": "x' OR '1'='1"},
            ]}},
            "limit": 50,
        })
        assert r.status_code == 200, r.text
        assert r.json() == {"data": [], "columns": ["id", "email"], "row_count": 0}

    def test_preview_malicious_base_entity_rejected(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users; DROP TABLE users",
            "columns_config": [{"name": "id"}],
            "limit": 5,
        })
        assert r.status_code == 400

    def test_preview_malicious_column_rejected(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id; DROP TABLE users--"}],
            "limit": 5,
        })
        assert r.status_code == 400

    def test_preview_malicious_group_by_rejected(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id"}],
            "query_config": {"group_by": ["id); DROP TABLE users;--"]},
            "limit": 5,
        })
        assert r.status_code == 400

    def test_preview_malicious_order_by_field_rejected(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id"}],
            "query_config": {"order_by": [{"field": "id; DROP TABLE users", "direction": "asc"}]},
            "limit": 5,
        })
        assert r.status_code == 400

    def test_preview_malicious_order_by_direction_rejected(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id"}],
            "query_config": {"order_by": [{"field": "id", "direction": "asc; DROP TABLE users"}]},
            "limit": 5,
        })
        assert r.status_code == 400

    def test_preview_malicious_aggregation_rejected(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "users",
            "columns_config": [{"name": "id", "aggregation": "sum); DROP TABLE users; --"}],
            "limit": 5,
        })
        assert r.status_code == 400

    def test_preview_unknown_table_rejected(self, user):
        r = user.post("/reports/preview", json={
            "base_entity": "definitely_not_a_real_table",
            "columns_config": [{"name": "id"}],
            "limit": 5,
        })
        assert r.status_code == 400


# --------------------------------------------------------------------------- #
# Lookup data
# --------------------------------------------------------------------------- #
class TestLookup:
    def test_lookup_success(self, user):
        r = user.post("/reports/lookup", json={
            "entity": "users", "display_field": "email", "value_field": "id", "limit": 5,
        })
        assert r.status_code == 200, r.text
        assert "items" in r.json()

    def test_lookup_with_search(self, user):
        r = user.post("/reports/lookup", json={
            "entity": "users", "display_field": "email", "value_field": "id",
            "search": "ceo", "limit": 5,
        })
        assert r.status_code == 200, r.text

    def test_lookup_requires_auth(self, anon):
        r = anon.post("/reports/lookup", json={"entity": "users", "display_field": "email", "value_field": "id"})
        assert r.status_code in UNAUTH

    def test_lookup_malicious_entity_rejected(self, user):
        r = user.post("/reports/lookup", json={
            "entity": "users; DROP TABLE users", "display_field": "email", "value_field": "id",
        })
        assert r.status_code == 400

    def test_lookup_malicious_display_field_rejected(self, user):
        r = user.post("/reports/lookup", json={
            "entity": "users", "display_field": "email' OR '1'='1", "value_field": "id",
        })
        assert r.status_code == 400

    def test_lookup_malicious_value_field_rejected(self, user):
        r = user.post("/reports/lookup", json={
            "entity": "users", "display_field": "email", "value_field": "id; DROP TABLE users",
        })
        assert r.status_code == 400

    def test_lookup_malicious_filter_conditions_key_rejected(self, user):
        r = user.post("/reports/lookup", json={
            "entity": "users", "display_field": "email", "value_field": "id",
            "filter_conditions": {"id='1' OR '1'='1": "x"},
        })
        assert r.status_code == 400


# --------------------------------------------------------------------------- #
# Schedules
# --------------------------------------------------------------------------- #
class TestSchedules:
    def test_create_list_update_delete(self, user, report_def, unique):
        cr = user.post("/reports/schedules", json={
            "report_definition_id": report_def,
            "name": unique("sched"),
            "cron_expression": "0 0 * * *",
        })
        assert cr.status_code in OK, cr.text
        sid = cr.json()["id"]
        try:
            listed = user.get("/reports/schedules", params={"report_id": report_def}).json()
            assert sid in [s["id"] for s in listed]

            up = user.put(f"/reports/schedules/{sid}", json={"is_active": False})
            assert up.status_code == 200 and up.json()["is_active"] is False
        finally:
            dele = user.delete(f"/reports/schedules/{sid}")
            assert dele.status_code == 204

    def test_create_unknown_report_404(self, user, unique):
        r = user.post("/reports/schedules", json={
            "report_definition_id": str(uuid.uuid4()),
            "name": unique("sched"),
            "cron_expression": "0 0 * * *",
        })
        assert r.status_code == 404

    def test_update_unknown_404(self, user):
        assert user.put(f"/reports/schedules/{uuid.uuid4()}", json={"is_active": False}).status_code == 404

    def test_delete_unknown_404(self, user):
        assert user.delete(f"/reports/schedules/{uuid.uuid4()}").status_code == 404

    def test_requires_auth(self, anon, report_def):
        r = anon.post("/reports/schedules", json={
            "report_definition_id": report_def, "name": "x", "cron_expression": "0 0 * * *",
        })
        assert r.status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
class TestTemplates:
    def test_list_templates(self, user):
        r = user.get("/reports/templates")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_use_unknown_template_404(self, user):
        r = user.post(f"/reports/templates/{uuid.uuid4()}/use", params={"name": "x"})
        assert r.status_code == 404

    def test_list_requires_auth(self, anon):
        assert anon.get("/reports/templates").status_code in UNAUTH


# --------------------------------------------------------------------------- #
# Join suggestions
# --------------------------------------------------------------------------- #
class TestJoinSuggestions:
    def test_too_few_entities_returns_empty(self, user):
        r = user.post("/reports/entities/join-suggestions", json={"entities": ["users"]})
        assert r.status_code == 200
        assert r.json() == []

    def test_unknown_entities_returns_empty(self, user, unique):
        r = user.post("/reports/entities/join-suggestions", json={"entities": [unique("e"), unique("e")]})
        assert r.status_code == 200
        assert r.json() == []

    def test_requires_auth(self, anon):
        assert anon.post("/reports/entities/join-suggestions", json={"entities": ["a", "b"]}).status_code in UNAUTH
