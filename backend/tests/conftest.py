import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker
from faker import Faker

from app.main import app
from app.core.db import Base, get_db
from app.core.auth import create_access_token, hash_password
from app.models.user import User


# ---------------------------------------------------------------------------
# SQLite fixtures — used by existing auth tests
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

fake = Faker()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        tenant_id="tenant-123",
        roles='["user"]'
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_superuser(db_session):
    """Create a test superuser"""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
        tenant_id="tenant-123",
        roles='["admin"]'
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for test user"""
    token = create_access_token({
        "sub": str(test_user.id),
        "email": test_user.email,
        "tenant_id": test_user.tenant_id,
        "roles": ["user"]
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(test_superuser):
    """Generate authentication headers for superuser"""
    token = create_access_token({
        "sub": str(test_superuser.id),
        "email": test_superuser.email,
        "tenant_id": test_superuser.tenant_id,
        "roles": ["admin"]
    })
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# PostgreSQL fixtures — used by dynamic-entity integration tests
#
# Set TEST_DATABASE_URL to a real PostgreSQL URL to enable these fixtures.
# Example:
#   TEST_DATABASE_URL=postgresql://testuser:testpass@localhost:5433/appbuildify_test
#
# All pg_* fixtures are automatically skipped when TEST_DATABASE_URL is unset.
# ---------------------------------------------------------------------------

PG_URL = os.getenv("TEST_DATABASE_URL", "")

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(scope="session")
def pg_engine():
    """Session-scoped PostgreSQL engine.  Skipped when TEST_DATABASE_URL is unset."""
    if not PG_URL:
        pytest.skip("TEST_DATABASE_URL not set — skipping PostgreSQL integration tests")
    eng = create_engine(PG_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=eng)
    yield eng
    # Do NOT drop all tables here — leave schema intact for inspection after failure.


@pytest.fixture(scope="function")
def pg_session(pg_engine):
    """Function-scoped PostgreSQL session with automatic rollback."""
    Session = sessionmaker(bind=pg_engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def pg_admin_user(pg_session):
    """Creates (or reuses) a superuser in the test PostgreSQL database."""
    admin_email = f"pgadmin_{uuid.uuid4().hex[:8]}@test.com"
    user = User(
        email=admin_email,
        hashed_password=hash_password("pgadmin123"),
        full_name="PG Admin",
        is_active=True,
        is_superuser=True,
        tenant_id=TEST_TENANT_ID,
        roles='["admin"]',
    )
    pg_session.add(user)
    pg_session.commit()
    pg_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def pg_admin_headers(pg_admin_user):
    """JWT Bearer headers for the pg admin user."""
    token = create_access_token({
        "sub": str(pg_admin_user.id),
        "email": pg_admin_user.email,
        "tenant_id": pg_admin_user.tenant_id,
        "roles": ["admin"],
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def pg_client(pg_session):
    """TestClient wired to the pg_session."""
    def override_get_db():
        yield pg_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def _create_entity_via_api(client, headers, entity_payload, fields_payload):
    """
    Helper: create + publish an entity via data-model API.
    Returns (entity_id, entity_name, table_name).
    """
    # 1. Create entity definition
    resp = client.post("/api/v1/data-model/entities", json=entity_payload, headers=headers)
    assert resp.status_code == 201, f"Entity create failed: {resp.text}"
    entity = resp.json()
    entity_id = entity["id"]
    entity_name = entity["name"]
    table_name = entity["table_name"]

    # 2. Add fields
    for field in fields_payload:
        resp = client.post(
            f"/api/v1/data-model/entities/{entity_id}/fields",
            json=field,
            headers=headers,
        )
        assert resp.status_code == 201, f"Field create failed ({field['name']}): {resp.text}"

    # 3. Publish (runs DDL migration)
    resp = client.post(
        f"/api/v1/data-model/entities/{entity_id}/publish",
        headers=headers,
    )
    assert resp.status_code == 200, f"Publish failed: {resp.text}"

    return entity_id, entity_name, table_name


def _drop_entity(pg_session, entity_id, table_name):
    """
    Teardown helper: drop the dynamic table and remove the entity definition.
    Wrapped in try/except so teardown never masks test failures.
    """
    try:
        pg_session.execute(sa_text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        pg_session.execute(
            sa_text("DELETE FROM entity_definitions WHERE id = :id"),
            {"id": entity_id},
        )
        pg_session.commit()
    except Exception:
        pg_session.rollback()


@pytest.fixture(scope="function")
def published_entity(pg_client, pg_session, pg_admin_headers):
    """
    Creates and publishes a test entity via the data-model API.

    Entity fields:
      - name    (string, required)
      - price   (decimal 10,2)
      - status  (string, allowed: active / inactive / pending)
      - quantity (integer)

    Yields a dict:
      {
        "entity_id":   str,
        "entity_name": str,
        "table_name":  str,
        "client":      TestClient,
        "headers":     dict,
      }

    Cleans up the table + entity definition after the test.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    entity_name = f"test_product_{unique_suffix}"
    table_name = f"test_product_{unique_suffix}"

    entity_payload = {
        "name": entity_name,
        "label": "Test Product",
        "plural_label": "Test Products",
        "table_name": table_name,
        "data_scope": "tenant",
        "supports_soft_delete": True,
        "is_audited": False,
    }

    fields_payload = [
        {
            "name": "name",
            "label": "Name",
            "field_type": "string",
            "data_type": "VARCHAR",
            "is_required": True,
            "max_length": 255,
            "display_order": 1,
        },
        {
            "name": "price",
            "label": "Price",
            "field_type": "decimal",
            "data_type": "DECIMAL",
            "is_required": False,
            "precision": 10,
            "decimal_places": 2,
            "display_order": 2,
        },
        {
            "name": "status",
            "label": "Status",
            "field_type": "string",
            "data_type": "VARCHAR",
            "is_required": False,
            "max_length": 50,
            "allowed_values": ["active", "inactive", "pending"],
            "display_order": 3,
        },
        {
            "name": "quantity",
            "label": "Quantity",
            "field_type": "integer",
            "data_type": "INTEGER",
            "is_required": False,
            "display_order": 4,
        },
    ]

    entity_id, entity_name, table_name = _create_entity_via_api(
        pg_client, pg_admin_headers, entity_payload, fields_payload
    )

    yield {
        "entity_id": entity_id,
        "entity_name": entity_name,
        "table_name": table_name,
        "client": pg_client,
        "headers": pg_admin_headers,
    }

    _drop_entity(pg_session, entity_id, table_name)


# ---------------------------------------------------------------------------
# Sample data:  5 records seeded for filter / aggregate / soft-delete tests
# ---------------------------------------------------------------------------

SAMPLE_RECORDS = [
    {"name": "Widget A", "price": "1.99",  "status": "active",   "quantity": 10},
    {"name": "Widget B", "price": "5.99",  "status": "active",   "quantity": 20},
    {"name": "Widget C", "price": "9.99",  "status": "active",   "quantity": 5},
    {"name": "Gadget A", "price": "99.99", "status": "inactive", "quantity": 3},
    {"name": "Gadget B", "price": None,    "status": "pending",  "quantity": 0},
]


@pytest.fixture(scope="function")
def sample_records(published_entity):
    """
    Seeds SAMPLE_RECORDS into the published entity.

    Yields a dict:
      {
        "entity": published_entity dict,
        "record_ids": [list of created record UUIDs],
        "records": [list of raw data dicts],
      }
    """
    client = published_entity["client"]
    headers = published_entity["headers"]
    entity_name = published_entity["entity_name"]

    record_ids = []
    records = []
    for row in SAMPLE_RECORDS:
        data = {k: v for k, v in row.items() if v is not None}
        resp = client.post(
            f"/api/v1/dynamic-data/{entity_name}/records",
            json={"data": data},
            headers=headers,
        )
        assert resp.status_code == 201, f"Seed record failed: {resp.text}"
        body = resp.json()
        record_ids.append(body["id"])
        records.append(row)

    yield {
        "entity": published_entity,
        "record_ids": record_ids,
        "records": records,
    }
