"""
MFA factor service — platform-native second-factor enrollment (ADR-011 S4).

The DB-facing core behind ``/api/v1/mfa/*``. It owns the ``user_mfa_factors``
lifecycle (enroll pending → activate on a verified OTP round-trip → disable) so
the router stays thin and the OTP orchestration lives in one place. A factor is
never trusted as active until a real send→verify round-trip proves the user
controls the delivery target (sec-review-011 R5); this module only flips
``is_active`` from :func:`activate_factor`, which the router calls *after*
``otp.verify_otp`` succeeds.

No secret is stored here — only the delivery target + verification state; OTP
codes stay in the OTP service (R11 / ADR-011).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.user_mfa_factor import UserMFAFactor

# factor_type -> OTP delivery channel. ``factor_type`` is an open string in the
# model (TOTP reserved for later); the values enrollable *today* are these two.
_FACTOR_CHANNEL = {
    "phone_otp": "phone",
    "email_otp": "email",
}


class InvalidFactorError(ValueError):
    """Unknown ``factor_type`` or an empty/invalid delivery target."""


class FactorNotFoundError(Exception):
    """No factor with that id belongs to this user."""


class AlreadyEnrolledError(Exception):
    """An *active* factor with the same type+target already exists.

    The user has nothing to do; the caller should surface a benign "already
    enrolled" outcome rather than re-sending a code.
    """


def channel_for_factor(factor_type: str) -> str:
    """Map a ``factor_type`` to its OTP channel, or raise ``InvalidFactorError``."""
    try:
        return _FACTOR_CHANNEL[factor_type]
    except KeyError:
        raise InvalidFactorError(
            f"Unsupported factor_type '{factor_type}'; expected one of {sorted(_FACTOR_CHANNEL)}"
        )


def normalize_target(factor_type: str, target: str) -> str:
    """Trim + canonicalize a delivery target for its channel.

    Emails are lower-cased so ``A@B.com`` and ``a@b.com`` are one factor (and the
    unique constraint holds). Raises ``InvalidFactorError`` on an empty or
    obviously malformed target — full validation is the delivery channel's job.
    """
    channel = channel_for_factor(factor_type)
    target = (target or "").strip()
    if not target:
        raise InvalidFactorError("A delivery target (phone or email) is required")

    if channel == "email":
        target = target.lower()
        if "@" not in target or target.startswith("@") or target.endswith("@"):
            raise InvalidFactorError("Enter a valid email address")
    else:  # phone
        digits = target.lstrip("+")
        if not digits.isdigit() or len(digits) < 6:
            raise InvalidFactorError("Enter a valid phone number")
    return target


def list_factors(db: Session, user_id: str) -> List[UserMFAFactor]:
    """All MFA factors enrolled by a user, newest first."""
    return (
        db.query(UserMFAFactor)
        .filter(UserMFAFactor.user_id == str(user_id))
        .order_by(UserMFAFactor.created_at.desc())
        .all()
    )


def get_factor(db: Session, user_id: str, factor_id: str) -> Optional[UserMFAFactor]:
    """Fetch one factor, scoped to its owner (never leak another user's factor)."""
    return (
        db.query(UserMFAFactor)
        .filter(UserMFAFactor.id == str(factor_id), UserMFAFactor.user_id == str(user_id))
        .first()
    )


def get_or_create_pending_factor(
    db: Session, *, user_id: str, factor_type: str, target: str
) -> Tuple[UserMFAFactor, str]:
    """Return an *inactive* factor to send an enrollment code to.

    Validates + normalizes input, then, keyed on the ``(user, type, target)``
    unique constraint:

    - an already-**active** factor → ``AlreadyEnrolledError`` (nothing to do);
    - an existing **pending** factor → reused (a re-enroll just re-sends a code);
    - otherwise a fresh ``is_active=False`` row is created.

    The row is created but *not* trusted — activation only happens later via
    :func:`activate_factor` once the OTP round-trip proves ownership (R5).
    Returns ``(factor, channel)``.
    """
    channel = channel_for_factor(factor_type)
    target = normalize_target(factor_type, target)

    existing = (
        db.query(UserMFAFactor)
        .filter(
            UserMFAFactor.user_id == str(user_id),
            UserMFAFactor.factor_type == factor_type,
            UserMFAFactor.target == target,
        )
        .first()
    )
    if existing is not None:
        if existing.is_active:
            raise AlreadyEnrolledError()
        return existing, channel

    factor = UserMFAFactor(
        user_id=str(user_id),
        factor_type=factor_type,
        target=target,
        is_active=False,
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    return factor, channel


def activate_factor(db: Session, factor: UserMFAFactor) -> UserMFAFactor:
    """Mark a factor active after a verified OTP round-trip (R5)."""
    factor.is_active = True
    factor.verified_at = datetime.utcnow()
    db.commit()
    db.refresh(factor)
    return factor


def disable_factor(db: Session, user_id: str, factor_id: str) -> bool:
    """Remove a user's factor. Returns ``False`` if it wasn't theirs / not found."""
    factor = get_factor(db, user_id, factor_id)
    if factor is None:
        return False
    db.delete(factor)
    db.commit()
    return True
