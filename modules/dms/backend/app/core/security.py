"""JWT validation, request principal, and the tenant-scoped DB dependency.

The DMS module runs standalone; nginx forwards the platform's `Authorization:
Bearer <jwt>` header unchanged. We decode it with the SAME SECRET_KEY the core
backend signs with, so platform sessions work transparently. Claims of interest
(set in backend/app/routers/auth.py): `sub` (user id), `tenant_id`.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from .database import get_tenant_db


class Principal:
    def __init__(self, user_id: str, tenant_id: Optional[str], token: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.token = token


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_principal(authorization: Optional[str] = Header(None)) -> Principal:
    """Decode the forwarded JWT and return the caller principal."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise _unauthorized("Invalid or expired token")

    if payload.get("type") not in (None, "access"):
        raise _unauthorized("Wrong token type")

    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized("Token missing subject")

    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        # DMS is tenant-scoped; a token with no tenant (bare platform superadmin)
        # cannot resolve an RLS scope. Cross-tenant admin is out of scope for MVP.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A tenant-scoped session is required to access documents.",
        )
    return Principal(user_id=str(user_id), tenant_id=str(tenant_id), token=token)


async def tenant_session(
    principal: Principal = Depends(get_principal),
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: a DB session with RLS bound to the caller's tenant."""
    async for session in get_tenant_db(principal.tenant_id):
        yield session


def require_permission(code: str):
    """Permission guard.

    Phase 0: authenticates the caller and yields the principal. Full RBAC
    enforcement (checking `code` against the platform-seeded permissions) lands
    in Phase 2 (E3); the manifest already declares the permission codes so the
    platform seeds them on enable.
    """

    async def _guard(principal: Principal = Depends(get_principal)) -> Principal:
        return principal

    return _guard
