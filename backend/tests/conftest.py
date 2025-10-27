import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker

from app.main import app
from app.core.db import Base, get_db
from app.core.auth import create_access_token, hash_password
from app.models.user import User


# Test database URL (SQLite in-memory for fast tests)
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
