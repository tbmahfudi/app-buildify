"""
Integration conftest — module-lifecycle tests only.

Provides a 'client' fixture override that bypasses token-blacklist DB lookups
by replacing get_current_user with an auth-header-aware stub.  Auth tests
(test_auth.py) use the parent conftest's 'client' fixture which keeps the
real get_current_user; those tests now work because the parent conftest uses
StaticPool so the token_blacklist table is visible across threads.
"""
import uuid
import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException, Request, status
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_db, get_current_user, get_current_active_user
from app.models.user import User


INTEGRATION_TENANT_ID = '00000000-0000-0000-0000-000000000123'


def _stub_user():
    """Return a User-like object that satisfies all field access by lifecycle endpoints."""
    user = MagicMock(spec=User)
    user.id = uuid.UUID(INTEGRATION_TENANT_ID)
    user.email = 'integration-test@example.com'
    user.full_name = 'Integration Test User'
    user.is_active = True
    user.is_superuser = False
    user.tenant_id = INTEGRATION_TENANT_ID
    return user


def _auth_aware_stub(stub):
    """Return a get_current_user replacement that still rejects header-less requests."""
    def _override(request: Request):
        if 'authorization' not in request.headers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not authenticated',
            )
        return stub
    return _override


@pytest.fixture(scope='function')
def client(db_session):
    """
    Override of the parent conftest's 'client'.

    In addition to wiring get_db to the in-memory test session, this version
    replaces get_current_user with an auth-header-aware stub so that
    token_blacklist is never queried.  Only used by tests in this directory
    (module lifecycle tests); test_auth.py picks up the parent fixture.
    """
    stub = _stub_user()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _auth_aware_stub(stub)
    app.dependency_overrides[get_current_active_user] = lambda: stub

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
