"""
Local fixtures for the adversarial tenant-isolation suite (T-22.023 .. T-22.025).

These tests exercise the ContextVar + ORM-listener enforcement layer directly.
They deliberately avoid importing ``app.main`` (and the heavy app-wide conftest)
so they can run without the full FastAPI dependency stack — only the scope
helper, the listener, and a couple of ORM models are needed.

A dedicated in-memory SQLite engine is built per test, the ``TenantScopeListener``
is installed on the SQLAlchemy ``Session`` class, and the ContextVar is reset
before and after every test so leakage between tests is impossible.
"""
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# JSONB -> JSON shim for SQLite (mirrors the top-level conftest).
try:
    from sqlalchemy.dialects.sqlite import base as _sqlite_base

    if not hasattr(_sqlite_base.SQLiteTypeCompiler, "visit_JSONB"):
        def _visit_jsonb(self, type_, **kw):
            return self.visit_JSON(type_, **kw)

        _sqlite_base.SQLiteTypeCompiler.visit_JSONB = _visit_jsonb
except Exception:  # pragma: no cover
    pass

from app.models.base import Base  # noqa: E402
from app.models.user import User  # noqa: E402  (User.__tenant_scoped__ == True)
from app.models.tenant_module_database import (  # noqa: E402
    TenantModuleDatabase,  # NOT tenant-scoped — used for the negative case
)
from app.core.tenant.scope import _current_tenant_id  # noqa: E402
from app.core.tenant_listener import TenantScopeListener  # noqa: E402

# Stable tenant ids reused across the suite.
TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"


@pytest.fixture(autouse=True)
def _reset_scope():
    """Guarantee a clean ContextVar around every test (T-22.024 invariant)."""
    token = _current_tenant_id.set(None)
    try:
        yield
    finally:
        _current_tenant_id.reset(token)
        _current_tenant_id.set(None)


@pytest.fixture
def listener_installed():
    """Install the listener once for the test session-class.

    The listener attaches to the ``Session`` class via ``do_orm_execute``;
    we remove it afterwards so other test modules are unaffected.
    """
    TenantScopeListener.install(None)  # engine arg is unused; listens on Session
    yield
    event.remove(Session, "do_orm_execute", TenantScopeListener._on_orm_execute)
    event.remove(Session, "before_flush", TenantScopeListener._on_before_flush)


@pytest.fixture
def db(listener_installed):
    """Fresh in-memory SQLite session with all tables and the listener active."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create every table that SQLite can build. A few unrelated models (e.g.
    # ``modules``) use PostgreSQL-only CHECK constraints (regex ``~``) and fail
    # to compile on SQLite; we skip just those and keep the rest so relationship
    # loads on User work.
    for table in Base.metadata.sorted_tables:
        try:
            table.create(bind=engine, checkfirst=True)
        except Exception:  # pragma: no cover - PG-only DDL skipped on SQLite
            continue
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def make_user(tenant_id, email=None, is_superuser=False):
    """Build (unpersisted) User row carrying the given tenant."""
    return User(
        id=str(uuid.uuid4()),
        email=email or f"{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="x",
        full_name="Adversarial User",
        is_active=True,
        is_superuser=is_superuser,
        tenant_id=tenant_id,
    )


def seed_user(session, tenant_id, **kw):
    """Insert a user under the superuser bypass so the listener allows the write."""
    token = _current_tenant_id.set("__superuser__")
    try:
        user = make_user(tenant_id, **kw)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        _current_tenant_id.reset(token)
