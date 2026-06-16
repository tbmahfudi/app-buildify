"""
Regression test for DEF-003.

A published entity whose physical table is missing (e.g. the table creation
failed during publish, or was dropped out of band) must degrade to a clean
409 "table not provisioned" instead of leaking a raw 500 (psycopg2
UndefinedTable). See `_missing_table_error` in routers/dynamic_data.py.

The broken state cannot be produced through the API alone (publishing now
always creates the table), so this test reproduces it by dropping the backing
table via a direct DB connection. It is therefore skipped if the test process
cannot reach the database (e.g. when run from a host without DB env/driver);
inside the backend container it runs normally.
"""
import os
import uuid

import pytest

pytestmark = pytest.mark.e2e


def _drop_table(table_name: str) -> None:
    """Drop a physical table out of band to simulate the DEF-003 broken state."""
    try:
        import psycopg2
    except ImportError:  # pragma: no cover
        pytest.skip("psycopg2 not available to simulate a missing table")
    url = os.environ.get("SQLALCHEMY_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("no database URL in env to simulate a missing table")
    dsn = url.replace("postgresql+psycopg2://", "postgresql://").replace("postgresql+psycopg://", "postgresql://")
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
    finally:
        conn.close()


def test_missing_backing_table_returns_409(user):
    sfx = uuid.uuid4().hex[:8]
    name = f"e2e_prov_{sfx}"
    cr = user.post("/data-model/entities", json={
        "name": name, "label": f"Prov {sfx}", "plural_label": f"Prov {sfx}s",
        "table_name": name, "data_scope": "tenant",
    })
    assert cr.status_code in (200, 201), cr.text
    eid = cr.json()["id"]
    table_name = cr.json().get("table_name", name)
    user.post(f"/data-model/entities/{eid}/fields",
              json={"name": "title", "label": "Title", "field_type": "text", "data_type": "VARCHAR"})
    pub = user.post(f"/data-model/entities/{eid}/publish", json={"commit_message": "e2e"})
    assert pub.status_code == 200, pub.text

    try:
        # sanity: the entity serves normally while its table exists
        assert user.get(f"/dynamic-data/{name}/records").status_code == 200

        # simulate DEF-003: the backing table disappears
        _drop_table(table_name)

        # list must now be a clean 409, not a 500
        r = user.get(f"/dynamic-data/{name}/records")
        assert r.status_code == 409, f"expected 409, got {r.status_code}: {r.text}"
        assert "not provisioned" in r.json()["detail"].lower()

        # aggregate must behave the same way
        agg = user.get(f"/dynamic-data/{name}/aggregate",
                       params={"metrics": '[{"field":"*","function":"count"}]'})
        assert agg.status_code == 409, agg.text
    finally:
        user.delete(f"/data-model/entities/{eid}")
