"""JWT validation, request principal, and the tenant-scoped DB dependency.

The DMS module runs standalone; nginx forwards the platform's `Authorization:
Bearer <jwt>` header unchanged. We decode it with the SAME SECRET_KEY the core
backend signs with, so platform sessions work transparently. Claims of interest
(set in backend/app/routers/auth.py): `sub` (user id), `tenant_id`.
"""

from typing import AsyncGenerator, List, Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from .database import get_tenant_db


class Principal:
    def __init__(self, user_id: str, tenant_id: Optional[str], token: str,
                 permissions: Optional[List[str]] = None):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.token = token
        # RBAC permission codes from the platform JWT (User→Group→Role→Permission).
        self.permissions = set(permissions or [])

    def has_permission(self, required_code: str) -> bool:
        """True if a granted code satisfies `required_code`.

        Format: ``<resource>:<action>:<scope>``. A ``*`` segment on the *granted*
        side matches any value; wildcards are only honored on the granted side.
        Mirrors the platform's `matches_permission` (backend dependencies.py).
        """
        if required_code in self.permissions:
            return True
        req = required_code.split(":")
        for granted in self.permissions:
            if "*" not in granted:
                continue
            g = granted.split(":")
            if len(g) == len(req) and all(gs == "*" or gs == rs for gs, rs in zip(g, req)):
                return True
        return False


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
    perms = payload.get("permissions") or []
    if not isinstance(perms, list):
        perms = []
    return Principal(user_id=str(user_id), tenant_id=str(tenant_id), token=token,
                     permissions=perms)


async def tenant_session(
    principal: Principal = Depends(get_principal),
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: a DB session with RLS bound to the caller's tenant."""
    async for session in get_tenant_db(principal.tenant_id):
        yield session


def require_permission(code: str):
    """Permission guard (E3): 403 unless the caller's JWT grants `code`.

    Permissions are seeded via the platform RBAC chain (User→Group→Role→
    Permission) — see backend/seed_dms_rbac.py — and travel in the JWT
    `permissions[]` claim, so this standalone module enforces without a DB call.
    Grants take effect on the caller's next login (token refresh).
    """

    async def _guard(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_permission(code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {code}",
            )
        return principal

    return _guard
