"""
Deep coverage of the `data` router (6 ops):
  - POST /{entity}/list  — search / paginate data
  - GET  /{entity}/{id}  — get record by id
  - POST /{entity}       — create record
  - PUT  /{entity}/{id}  — update record
  - DELETE /{entity}/{id}— hard-delete record
  - POST /{entity}/bulk  — bulk create/update/delete

ENTITY_REGISTRY: companies, branches, departments, users
Tests use `companies` for lifecycle ops (minimal FK: only tenant_id required).
"""
import uuid

import pytest

pytestmark = pytest.mark.e2e

UNAUTH = (401, 403)
OK = (200, 201)


def _co(unique, suffix=""):
    """Return (name, code) for a test company, collision-free."""
    u = unique(f"co{suffix}")
    return {"name": f"E2E {u}", "code": u[-10:].upper()}


@pytest.fixture(scope="session")
def tenant_id(user):
    return user.get("/auth/me").json()["tenant_id"]


@pytest.fixture
def company(user, tenant_id, unique):
    """Create a company, yield its id, hard-delete on teardown."""
    body = {**_co(unique), "tenant_id": tenant_id}
    r = user.post("/data/companies", json={"entity": "companies", "data": body, "return_record": True})
    assert r.status_code in OK, r.text
    cid = r.json()["id"]
    yield cid
    user.delete(f"/data/companies/{cid}")


# ─── unknown entity ───────────────────────────────────────────────────────────

class TestUnknownEntity:
    def test_list_unknown_entity_404(self, user):
        r = user.post("/data/nonexistent/list", json={"entity": "nonexistent"})
        assert r.status_code == 404, r.text

    def test_get_unknown_entity_404(self, user):
        assert user.get(f"/data/nonexistent/{uuid.uuid4()}").status_code == 404

    def test_create_unknown_entity_404(self, user):
        r = user.post("/data/nonexistent", json={"entity": "nonexistent", "data": {"name": "x"}})
        assert r.status_code == 404

    def test_update_unknown_entity_404(self, user):
        r = user.put(f"/data/nonexistent/{uuid.uuid4()}", json={
            "entity": "nonexistent", "id": str(uuid.uuid4()), "data": {"name": "x"},
        })
        assert r.status_code == 404

    def test_delete_unknown_entity_404(self, user):
        assert user.delete(f"/data/nonexistent/{uuid.uuid4()}").status_code == 404

    def test_bulk_unknown_entity_404(self, user):
        r = user.post("/data/nonexistent/bulk", json={
            "entity": "nonexistent", "operation": "create", "records": [{"name": "x"}],
        })
        assert r.status_code == 404


# ─── auth required ────────────────────────────────────────────────────────────

class TestAuthRequired:
    def test_list_requires_auth(self, anon):
        r = anon.post("/data/companies/list", json={"entity": "companies"})
        assert r.status_code in UNAUTH

    def test_get_requires_auth(self, anon):
        assert anon.get(f"/data/companies/{uuid.uuid4()}").status_code in UNAUTH

    def test_create_requires_auth(self, anon, tenant_id):
        r = anon.post("/data/companies", json={
            "entity": "companies", "data": {"name": "x", "code": "X", "tenant_id": tenant_id},
        })
        assert r.status_code in UNAUTH

    def test_update_requires_auth(self, anon):
        r = anon.put(f"/data/companies/{uuid.uuid4()}", json={
            "entity": "companies", "id": str(uuid.uuid4()), "data": {"name": "x"},
        })
        assert r.status_code in UNAUTH

    def test_delete_requires_auth(self, anon, company):
        assert anon.delete(f"/data/companies/{company}").status_code in UNAUTH

    def test_bulk_requires_auth(self, anon):
        r = anon.post("/data/companies/bulk", json={
            "entity": "companies", "operation": "create", "records": [],
        })
        assert r.status_code in UNAUTH


# ─── list / search ────────────────────────────────────────────────────────────

class TestDataList:
    def test_list_returns_search_response_shape(self, user):
        r = user.post("/data/companies/list", json={"entity": "companies"})
        assert r.status_code == 200, r.text
        body = r.json()
        for key in ("rows", "total", "filtered", "page", "page_size", "has_next", "has_prev"):
            assert key in body, f"missing key: {key}"
        assert isinstance(body["rows"], list)
        assert body["total"] >= 0

    def test_list_default_page_1(self, user):
        body = user.post("/data/companies/list", json={"entity": "companies"}).json()
        assert body["page"] == 1
        assert body["has_prev"] is False

    def test_list_pagination_has_prev(self, user):
        """Page 2 of any non-empty entity must have has_prev=True (DEF-029 regression)."""
        body = user.post("/data/companies/list", json={
            "entity": "companies", "page": 2, "page_size": 1,
        }).json()
        if body["total"] >= 2:
            assert body["has_prev"] is True, "has_prev must be True on page 2"

    def test_list_pagination_has_next(self, user):
        """has_next should be True when more pages remain."""
        body = user.post("/data/companies/list", json={
            "entity": "companies", "page": 1, "page_size": 1,
        }).json()
        if body["total"] >= 2:
            assert body["has_next"] is True, "has_next must be True when more rows remain"

    def test_list_filter_eq(self, user, company):
        """Filter by exact code returns the target company."""
        code = user.get(f"/data/companies/{company}").json()["data"]["code"]
        body = user.post("/data/companies/list", json={
            "entity": "companies",
            "filters": [{"field": "code", "operator": "eq", "value": code}],
        }).json()
        assert any(r["id"] == company for r in body["rows"]), "eq filter did not return the company"

    def test_list_filter_contains(self, user, company):
        """Contains operator finds partial name match (DEF-028 regression)."""
        full_name = user.get(f"/data/companies/{company}").json()["data"]["name"]
        partial = full_name[4:12]
        body = user.post("/data/companies/list", json={
            "entity": "companies",
            "filters": [{"field": "name", "operator": "contains", "value": partial}],
        }).json()
        assert any(r["id"] == company for r in body["rows"]), "contains filter did not match"

    def test_list_filter_startswith(self, user, company):
        full_name = user.get(f"/data/companies/{company}").json()["data"]["name"]
        prefix = full_name[:8]
        body = user.post("/data/companies/list", json={
            "entity": "companies",
            "filters": [{"field": "name", "operator": "startswith", "value": prefix}],
        }).json()
        assert any(r["id"] == company for r in body["rows"])

    def test_list_filter_endswith(self, user, company):
        full_name = user.get(f"/data/companies/{company}").json()["data"]["name"]
        suffix = full_name[-8:]
        body = user.post("/data/companies/list", json={
            "entity": "companies",
            "filters": [{"field": "name", "operator": "endswith", "value": suffix}],
        }).json()
        assert any(r["id"] == company for r in body["rows"])

    def test_list_filter_ne(self, user, company):
        code = user.get(f"/data/companies/{company}").json()["data"]["code"]
        body = user.post("/data/companies/list", json={
            "entity": "companies",
            "filters": [{"field": "code", "operator": "ne", "value": code}],
        }).json()
        assert all(r["code"] != code for r in body["rows"])

    def test_list_filter_invalid_operator_422(self, user):
        r = user.post("/data/companies/list", json={
            "entity": "companies",
            "filters": [{"field": "name", "operator": "like", "value": "x"}],
        })
        assert r.status_code == 422

    def test_list_sort_asc(self, user):
        body = user.post("/data/companies/list", json={
            "entity": "companies", "sort": [["name", "asc"]],
        }).json()
        names = [r["name"] for r in body["rows"]]
        assert names == sorted(names)

    def test_list_sort_desc(self, user):
        body = user.post("/data/companies/list", json={
            "entity": "companies", "sort": [["name", "desc"]],
        }).json()
        names = [r["name"] for r in body["rows"]]
        assert names == sorted(names, reverse=True)

    def test_list_search_param(self, user):
        r = user.post("/data/companies/list", json={"entity": "companies", "search": "E2E"})
        assert r.status_code == 200
        assert "rows" in r.json()

    def test_list_page_size_respected(self, user):
        body = user.post("/data/companies/list", json={
            "entity": "companies", "page": 1, "page_size": 2,
        }).json()
        assert len(body["rows"]) <= 2

    def test_list_missing_entity_in_body_422(self, user):
        r = user.post("/data/companies/list", json={"page": 1})
        assert r.status_code == 422

    def test_list_path_entity_wins_over_body(self, user):
        """When path=companies but body entity=branches, path entity is used."""
        companies = user.post("/data/companies/list", json={"entity": "companies"}).json()
        mismatch = user.post("/data/companies/list", json={"entity": "branches"}).json()
        assert companies["total"] == mismatch["total"], \
            "path entity must take precedence over body entity"

    def test_list_branches(self, user):
        r = user.post("/data/branches/list", json={"entity": "branches"})
        assert r.status_code == 200
        assert "rows" in r.json()

    def test_list_departments(self, user):
        r = user.post("/data/departments/list", json={"entity": "departments"})
        assert r.status_code == 200

    def test_list_users(self, user):
        r = user.post("/data/users/list", json={"entity": "users"})
        assert r.status_code == 200


# ─── get by id ────────────────────────────────────────────────────────────────

class TestDataGet:
    def test_get_returns_data_response_shape(self, user, company):
        r = user.get(f"/data/companies/{company}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "id" in body
        assert "data" in body
        assert isinstance(body["data"], dict)

    def test_get_id_matches_path(self, user, company):
        assert user.get(f"/data/companies/{company}").json()["id"] == company

    def test_get_data_contains_expected_fields(self, user, company):
        data = user.get(f"/data/companies/{company}").json()["data"]
        for key in ("id", "code", "name", "tenant_id"):
            assert key in data, f"missing field: {key}"

    def test_get_unknown_id_404(self, user):
        assert user.get(f"/data/companies/{uuid.uuid4()}").status_code == 404

    def test_get_requires_auth(self, anon, company):
        assert anon.get(f"/data/companies/{company}").status_code in UNAUTH


# ─── create ───────────────────────────────────────────────────────────────────

class TestDataCreate:
    def test_create_returns_201_and_data_response(self, user, tenant_id, unique):
        body = {**_co(unique, "cr"), "tenant_id": tenant_id}
        r = user.post("/data/companies", json={"entity": "companies", "data": body})
        assert r.status_code in OK, r.text
        created = r.json()
        assert "id" in created
        assert "data" in created
        user.delete(f"/data/companies/{created['id']}")

    def test_create_record_readable_by_get(self, user, company):
        assert user.get(f"/data/companies/{company}").json()["id"] == company

    def test_create_missing_data_field_422(self, user):
        assert user.post("/data/companies", json={"entity": "companies"}).status_code == 422

    def test_create_requires_auth(self, anon, tenant_id):
        r = anon.post("/data/companies", json={
            "entity": "companies", "data": {"name": "x", "code": "X", "tenant_id": tenant_id},
        })
        assert r.status_code in UNAUTH


# ─── update ───────────────────────────────────────────────────────────────────

class TestDataUpdate:
    def test_update_returns_200_with_updated_data(self, user, company, unique):
        new_name = unique("upd")
        r = user.put(f"/data/companies/{company}", json={
            "entity": "companies", "id": company, "data": {"name": new_name}, "partial": True,
        })
        assert r.status_code == 200, r.text
        assert r.json()["data"]["name"] == new_name

    def test_update_persisted_on_get(self, user, company, unique):
        new_name = unique("upd2")
        user.put(f"/data/companies/{company}", json={
            "entity": "companies", "id": company, "data": {"name": new_name},
        })
        assert user.get(f"/data/companies/{company}").json()["data"]["name"] == new_name

    def test_update_unknown_id_404(self, user):
        r = user.put(f"/data/companies/{uuid.uuid4()}", json={
            "entity": "companies", "id": str(uuid.uuid4()), "data": {"name": "x"},
        })
        assert r.status_code == 404

    def test_update_requires_auth(self, anon, company):
        r = anon.put(f"/data/companies/{company}", json={
            "entity": "companies", "id": company, "data": {"name": "x"},
        })
        assert r.status_code in UNAUTH


# ─── delete ───────────────────────────────────────────────────────────────────

class TestDataDelete:
    def test_delete_returns_204(self, user, tenant_id, unique):
        body = {**_co(unique, "del"), "tenant_id": tenant_id}
        cid = user.post("/data/companies", json={"entity": "companies", "data": body}).json()["id"]
        r = user.delete(f"/data/companies/{cid}")
        assert r.status_code == 204
        assert r.text == ""

    def test_delete_record_gone_from_get(self, user, tenant_id, unique):
        body = {**_co(unique, "del2"), "tenant_id": tenant_id}
        cid = user.post("/data/companies", json={"entity": "companies", "data": body}).json()["id"]
        user.delete(f"/data/companies/{cid}")
        assert user.get(f"/data/companies/{cid}").status_code == 404

    def test_delete_unknown_id_404(self, user):
        assert user.delete(f"/data/companies/{uuid.uuid4()}").status_code == 404

    def test_delete_requires_auth(self, anon, company):
        assert anon.delete(f"/data/companies/{company}").status_code in UNAUTH


# ─── bulk operations ──────────────────────────────────────────────────────────

class TestDataBulk:
    def test_bulk_create_returns_bulk_response_shape(self, user, tenant_id, unique):
        records = [
            {**_co(unique, f"bka"), "tenant_id": tenant_id},
            {**_co(unique, f"bkb"), "tenant_id": tenant_id},
        ]
        r = user.post("/data/companies/bulk", json={
            "entity": "companies", "operation": "create", "records": records,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        for key in ("total", "success", "failed", "errors"):
            assert key in body, f"missing key: {key}"
        assert body["total"] == 2
        assert body["success"] == 2
        assert body["failed"] == 0
        for rid in (body.get("created_ids") or []):
            user.delete(f"/data/companies/{rid}")

    def test_bulk_create_total_matches_records_count(self, user, tenant_id, unique):
        """DEF-027 regression: total must equal len(records)."""
        records = [{**_co(unique, "bkt"), "tenant_id": tenant_id}]
        r = user.post("/data/companies/bulk", json={
            "entity": "companies", "operation": "create", "records": records,
        })
        assert r.status_code == 200, r.text
        assert r.json()["total"] == 1
        for rid in (r.json().get("created_ids") or []):
            user.delete(f"/data/companies/{rid}")

    def test_bulk_empty_records_returns_200(self, user):
        """DEF-027 regression: empty records must not 500."""
        r = user.post("/data/companies/bulk", json={
            "entity": "companies", "operation": "create", "records": [],
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["total"] == 0
        assert body["success"] == 0
        assert body["failed"] == 0

    def test_bulk_delete(self, user, tenant_id, unique):
        created = []
        for i in range(2):
            body = {**_co(unique, f"bkd{i}"), "tenant_id": tenant_id}
            cid = user.post("/data/companies", json={"entity": "companies", "data": body}).json()["id"]
            created.append(cid)
        r = user.post("/data/companies/bulk", json={
            "entity": "companies",
            "operation": "delete",
            "records": [{"id": cid} for cid in created],
        })
        assert r.status_code == 200
        assert r.json()["success"] == 2
        for cid in created:
            assert user.get(f"/data/companies/{cid}").status_code == 404

    def test_bulk_update(self, user, tenant_id, unique):
        body = {**_co(unique, "bku"), "tenant_id": tenant_id}
        cid = user.post("/data/companies", json={"entity": "companies", "data": body}).json()["id"]
        new_name = unique("bkuname")
        r = user.post("/data/companies/bulk", json={
            "entity": "companies",
            "operation": "update",
            "records": [{"id": cid, "name": new_name}],
        })
        assert r.status_code == 200
        assert r.json()["success"] == 1
        assert user.get(f"/data/companies/{cid}").json()["data"]["name"] == new_name
        user.delete(f"/data/companies/{cid}")

    def test_bulk_invalid_operation_422(self, user):
        r = user.post("/data/companies/bulk", json={
            "entity": "companies", "operation": "destroy", "records": [],
        })
        assert r.status_code == 422

    def test_bulk_missing_entity_in_body_422(self, user):
        r = user.post("/data/companies/bulk", json={"operation": "create", "records": []})
        assert r.status_code == 422

    def test_bulk_requires_auth(self, anon):
        r = anon.post("/data/companies/bulk", json={
            "entity": "companies", "operation": "create", "records": [],
        })
        assert r.status_code in UNAUTH
