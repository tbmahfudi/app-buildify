# Platform SDK — FastAPI dependencies for module routes
# Re-exports platform dependencies so modules never import from app.
from app.core.dependencies import (
    tenant_scoped_session,
    get_current_user as _platform_get_current_user,
    has_permission,
)
from app.core.auth import decode_token as _decode_token

# Re-export decode_token so module SDK files never import from backend.app directly
decode_token = _decode_token
from fastapi import HTTPException, status
from functools import wraps


def get_current_user(*args, **kwargs):
    """
    Staff-only get_current_user wrapper.

    Delegates to the platform implementation and then asserts that the
    authenticated user does NOT carry the "patient" role. Patient JWTs
    must use get_current_patient() from modules.healthcare.sdk.patient_auth.

    Raises:
        HTTP 401: if the JWT is a patient-role token.
    """
    # _platform_get_current_user is a FastAPI dependency function — it must be
    # used via Depends() in route signatures, not called directly. This wrapper
    # preserves the same call signature by delegating to the platform function.
    # The actual patient-role rejection is injected via a dependency override
    # (see _StaffOnlyGuard below).
    return _platform_get_current_user(*args, **kwargs)


# Alias for direct import compatibility
get_current_user = _platform_get_current_user


class _PatientRoleRejector:
    """
    FastAPI dependency that wraps get_current_user and rejects patient JWTs.

    Installed as the canonical get_current_user for all healthcare and platform
    staff routes. Patient-facing routes use get_current_patient() instead.
    """
    def __call__(self, user=None):
        if user is None:
            return self
        roles = getattr(user, "roles", None)
        if roles is None:
            # Roles stored in RBAC groups — check via get_roles()
            try:
                roles = list(user.get_roles()) if hasattr(user, "get_roles") else []
            except Exception:
                roles = []
        if "patient" in (roles or []):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Staff credentials required. Patient tokens are not accepted on this endpoint.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user


def _make_staff_get_current_user():
    """
    Return a FastAPI dependency that:
    1. Calls the platform get_current_user.
    2. Rejects any token where roles contains "patient".

    This is the safe re-export for all staff endpoints in the healthcare module.
    """
    from fastapi import Depends
    from app.core.dependencies import get_current_user as _gu

    async def _staff_get_current_user(user=Depends(_gu)):
        roles = getattr(user, "roles", None)
        if roles is None:
            try:
                roles = list(user.get_roles()) if hasattr(user, "get_roles") else []
            except Exception:
                roles = []
        if "patient" in (roles or []):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Staff credentials required. Patient tokens are not accepted on this endpoint.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    return _staff_get_current_user


# Re-export: get_current_user from this module is the patient-rejecting variant
get_current_user = _make_staff_get_current_user()

__all__ = ["tenant_scoped_session", "get_current_user", "has_permission", "decode_token"]
