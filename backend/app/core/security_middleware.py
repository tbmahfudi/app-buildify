"""
Security middleware for enforcing session timeouts and password expiration.
"""
import logging
from datetime import datetime

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.auth import decode_token
from app.core.dependencies import get_db
from app.core.security_config import SecurityConfigService
from app.models.user import User
from app.models.user_session import UserSession

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """
    Middleware to enforce:
    1. Session timeout (inactivity timeout)
    2. Absolute session timeout
    3. Password expiration
    4. Session revocation checks
    """

    def __init__(self, app):
        self.app = app
        # Paths that should skip security checks
        self.exempt_paths = [
            "/auth/login",
            "/auth/refresh",
            "/auth/password-policy",
            "/auth/reset-password-request",
            "/auth/reset-password-confirm",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/favicon.ico"
        ]

    async def __call__(self, request: Request, call_next):
        """Process the request and enforce security policies"""

        # Skip security checks for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Skip if no Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)

        # Extract token
        token = auth_header[7:]
        token_payload = decode_token(token)

        if not token_payload:
            return await call_next(request)

        # Get user_id and jti from token
        user_id = token_payload.get("sub")
        jti = token_payload.get("jti")

        if not user_id or not jti:
            return await call_next(request)

        # Get database session
        db: Session = next(get_db())

        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return await call_next(request)

            # Initialize security config
            security_config = SecurityConfigService(db)

            # Check if session exists and is valid
            session = db.query(UserSession).filter(
                UserSession.jti == jti,
                UserSession.user_id == str(user_id)
            ).first()

            if session:
                # Check if session was revoked
                if session.revoked_at:
                    logger.warning(f"Revoked session detected for user {user_id}, JTI: {jti}")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "Session has been revoked. Please log in again.",
                            "error_code": "SESSION_REVOKED"
                        }
                    )

                # Check session inactivity timeout
                session_timeout_min = security_config.get_config("session_timeout_minutes", user.tenant_id)
                if session_timeout_min and session_timeout_min > 0:
                    inactivity_limit = datetime.utcnow().timestamp() - (session_timeout_min * 60)
                    if session.last_activity.timestamp() < inactivity_limit:
                        # Revoke the session
                        session.revoked_at = datetime.utcnow()
                        db.commit()

                        logger.info(f"Session timed out due to inactivity for user {user_id}, JTI: {jti}")
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={
                                "detail": f"Session timed out due to inactivity ({session_timeout_min} minutes). Please log in again.",
                                "error_code": "SESSION_TIMEOUT"
                            }
                        )

                # Check absolute session timeout
                absolute_timeout_hours = security_config.get_config("session_absolute_timeout_hours", user.tenant_id)
                if absolute_timeout_hours and absolute_timeout_hours > 0:
                    absolute_limit = datetime.utcnow().timestamp() - (absolute_timeout_hours * 3600)
                    if session.created_at.timestamp() < absolute_limit:
                        # Revoke the session
                        session.revoked_at = datetime.utcnow()
                        db.commit()

                        logger.info(f"Session exceeded absolute timeout for user {user_id}, JTI: {jti}")
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={
                                "detail": f"Session exceeded maximum duration ({absolute_timeout_hours} hours). Please log in again.",
                                "error_code": "ABSOLUTE_TIMEOUT"
                            }
                        )

                # Update last activity timestamp
                session.last_activity = datetime.utcnow()
                db.commit()

            # Check password expiration (but allow grace logins)
            if user.password_expires_at and user.password_expires_at < datetime.utcnow():
                # Check if grace logins are exhausted
                if not user.grace_logins_remaining or user.grace_logins_remaining <= 0:
                    logger.warning(f"Password expired for user {user_id}, no grace logins remaining")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": "Your password has expired. Please change your password.",
                            "error_code": "PASSWORD_EXPIRED"
                        }
                    )
                else:
                    # Allow access but add warning header
                    response = await call_next(request)
                    response.headers["X-Password-Expiration-Warning"] = (
                        f"Password expired. {user.grace_logins_remaining} grace logins remaining."
                    )
                    return response

            # Check if password change is required
            if user.require_password_change:
                # Only allow access to password change endpoint
                if not request.url.path.startswith("/auth/change-password"):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": "You must change your password before continuing.",
                            "error_code": "PASSWORD_CHANGE_REQUIRED"
                        }
                    )

            # All checks passed, continue with request
            return await call_next(request)

        except Exception as e:
            logger.error(f"Error in security middleware: {e}")
            # On error, allow request to continue to prevent blocking legitimate requests
            return await call_next(request)
        finally:
            db.close()
