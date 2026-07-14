"""
Account service — platform-native user account creation (ADR-011).

The single place that mints a platform ``User`` for password-based registration
(patients first; the same primitive is reused for other roles later). Credential
handling is centralized here so no caller reimplements password hashing or policy
(sec-review-011 R2). Callers stay enumeration-safe by mapping ``AccountExistsError``
and success to the *same* outward response (sec-review-011 R1).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.core.password_validator import PasswordValidator
from app.core.security_config import PasswordPolicyConfig, SecurityConfigService, load_from_env
from app.models.user import User


class WeakPasswordError(Exception):
    """Raised when the password fails the platform strength policy (R2).

    Carries the human-readable policy errors so the caller can surface them
    (a 422 for the *registrant's own* new password is not an enumeration leak).
    """

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors) or "Password does not meet policy requirements")


class AccountExistsError(Exception):
    """Raised when the email/username is already taken.

    The caller MUST NOT surface this distinctly to an unauthenticated registrant
    (sec-review-011 R1) — map it to the same generic outcome as success.
    """


# Password-policy config keys that affect strength validation, mapped to the
# PasswordPolicyConfig attribute + a coercion. Mirrors GET /auth/password-policy.
_POLICY_KEYS = [
    ("password_min_length", "min_length", int),
    ("password_require_uppercase", "require_uppercase", bool),
    ("password_require_lowercase", "require_lowercase", bool),
    ("password_require_digit", "require_digit", bool),
    ("password_require_special_char", "require_special_char", bool),
    ("password_min_unique_chars", "min_unique_chars", int),
    ("password_allow_common", "allow_common", bool),
]


def load_password_policy(db: Session, tenant_id: Optional[str]) -> PasswordPolicyConfig:
    """Resolve the effective password policy for a tenant.

    Starts from the env-configured baseline and overlays any per-tenant DB config
    (the same source ``GET /auth/password-policy`` reads). Never raises — falls
    back to the baseline if the config service is unavailable.
    """
    base = load_from_env().password
    try:
        svc = SecurityConfigService(db)
        overrides = {}
        for key, attr, cast in _POLICY_KEYS:
            val = svc.get_config(key, tenant_id)
            if val is not None:
                overrides[attr] = cast(val)
        return base.model_copy(update=overrides) if overrides else base
    except Exception:  # pragma: no cover - defensive: policy load must not 500 registration
        return base


def create_patient_account(
    db: Session,
    *,
    tenant_id: str,
    email: str,
    password: str,
    full_name: str,
    username: Optional[str] = None,
    phone: Optional[str] = None,
    default_company_id: Optional[str] = None,
    policy: Optional[PasswordPolicyConfig] = None,
) -> User:
    """Create a login-capable platform ``User`` with ``role`` patient semantics.

    The returned user is active, has a policy-validated password, and is *not*
    email-verified yet (``is_verified=False``) — activation is a separate step
    (ADR-011 register flow). ``must_set_password`` is False because the registrant
    chose a password now (ADR-HC-009 D7 gate is only for legacy OTP backfills).

    Raises:
        WeakPasswordError: password fails policy (surface to the registrant).
        AccountExistsError: email/username already taken (caller keeps generic).
        ValueError: missing required input.
    """
    email_norm = (email or "").strip().lower()
    if not email_norm:
        raise ValueError("email is required")
    if not full_name or not full_name.strip():
        raise ValueError("full_name is required")

    effective_policy = policy if policy is not None else load_password_policy(db, tenant_id)
    is_valid, errors = PasswordValidator(effective_policy).validate_strength(
        password, user_email=email_norm, user_name=full_name
    )
    if not is_valid:
        raise WeakPasswordError(errors)

    user = User(
        email=email_norm,
        username=(username.strip() if username else None),
        hashed_password=hash_password(password),
        must_set_password=False,
        is_active=True,
        is_verified=False,
        full_name=full_name.strip(),
        phone=phone,
        tenant_id=tenant_id,
        default_company_id=default_company_id,
        password_changed_at=datetime.utcnow(),
    )

    # Insert inside a SAVEPOINT so a unique-violation (duplicate email/username)
    # rolls back only this insert, leaving the caller's outer transaction usable.
    try:
        with db.begin_nested():
            db.add(user)
            db.flush()
    except IntegrityError:
        raise AccountExistsError(email_norm) from None

    return user
