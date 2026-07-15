"""Trusted-device store (ADR-HC-009 D4).

A browser that has already cleared an MFA challenge can be "remembered" so the
second factor is skipped for a bounded window. The security property that makes
this safe to persist:

    the raw device secret is NEVER stored server-side — only its HMAC.

The secret is minted here, handed to the browser in a signed HttpOnly cookie, and
never written to the database. A dump of ``user_trusted_devices`` therefore yields
no replayable material: an attacker would still need the victim's cookie. This
mirrors how we treat passwords, and is why ``device_hash`` is an HMAC (keyed with
SECRET_KEY) rather than a bare digest — a stolen table cannot be brute-forced
offline without also stealing the key.
"""

import hmac
import logging
import secrets
from datetime import datetime, timedelta
from hashlib import sha256
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import SECRET_KEY
from app.models.user import User
from app.models.user_trusted_device import UserTrustedDevice

logger = logging.getLogger(__name__)

# Name of the cookie carrying the raw device secret.
COOKIE_NAME = "tdid"

# D4: 30-day window. Overridable per-tenant via security config (see _window_days).
DEFAULT_TRUST_DAYS = 30

# Entropy for the device secret. 32 bytes url-safe ≈ 43 chars — far beyond guessable.
_SECRET_BYTES = 32


def _hash_secret(raw_secret: str) -> str:
    """HMAC-SHA256 the device secret with the app key.

    Keyed (not plain sha256) so that a leaked table is useless without SECRET_KEY.
    """
    return hmac.new(SECRET_KEY.encode("utf-8"), raw_secret.encode("utf-8"), sha256).hexdigest()


def window_days(db: Session, user: User) -> int:
    """Trust window in days — tenant security config, falling back to D4's 30."""
    try:
        from app.core.security_config import SecurityConfigService

        configured = SecurityConfigService(db).get_config("mfa_trusted_device_days", user.tenant_id)
        if configured:
            return int(configured)
    except Exception as e:  # noqa: BLE001 — config is best-effort; never block login on it
        logger.debug(f"trusted-device window lookup failed, using default: {e}")
    return DEFAULT_TRUST_DAYS


def _label_from_user_agent(user_agent: Optional[str]) -> Optional[str]:
    """Best-effort human hint for the security screen ("Chrome on Windows").

    Deliberately coarse: this is a recognition aid for the user, not a fingerprint,
    and we do not want to store a full UA string as a tracking vector.
    """
    if not user_agent:
        return None
    ua = user_agent.lower()
    browser = next(
        (name for token, name in (
            ("edg/", "Edge"), ("opr/", "Opera"), ("chrome", "Chrome"),
            ("firefox", "Firefox"), ("safari", "Safari"),
        ) if token in ua),
        "Browser",
    )
    os_name = next(
        (name for token, name in (
            ("windows", "Windows"), ("android", "Android"), ("iphone", "iOS"),
            ("ipad", "iOS"), ("mac os", "macOS"), ("linux", "Linux"),
        ) if token in ua),
        None,
    )
    return f"{browser} on {os_name}" if os_name else browser


def is_trusted(db: Session, user: User, raw_secret: Optional[str]) -> bool:
    """True if this cookie secret maps to a live trust for this user.

    Matching is scoped to ``user`` so a cookie minted for one account can never
    suppress the challenge on another. Updates ``last_used_at`` on a hit.
    """
    if not raw_secret:
        return False

    device_hash = _hash_secret(raw_secret)
    now = datetime.utcnow()

    row = (
        db.query(UserTrustedDevice)
        .filter(
            UserTrustedDevice.user_id == str(user.id),
            UserTrustedDevice.device_hash == device_hash,
            UserTrustedDevice.revoked_at.is_(None),
            UserTrustedDevice.expires_at > now,
        )
        .first()
    )

    if row is None:
        return False

    # Sliding last_used_at — observability only; does not extend the window.
    try:
        row.last_used_at = now
        db.commit()
    except Exception as e:  # noqa: BLE001 — never fail a login over a telemetry write
        logger.warning(f"failed to update last_used_at for trusted device {row.id}: {e}")
        db.rollback()

    return True


def remember_device(db: Session, user: User, user_agent: Optional[str] = None) -> str:
    """Mint a new device secret, store only its HMAC, and return the raw secret.

    The caller is responsible for putting the returned secret in an HttpOnly cookie.
    It is not recoverable afterwards.
    """
    raw_secret = secrets.token_urlsafe(_SECRET_BYTES)
    device_hash = _hash_secret(raw_secret)
    now = datetime.utcnow()

    row = UserTrustedDevice(
        user_id=str(user.id),
        device_hash=device_hash,
        label=_label_from_user_agent(user_agent),
        expires_at=now + timedelta(days=window_days(db, user)),
        last_used_at=now,
    )
    db.add(row)
    db.commit()

    return raw_secret


def list_devices(db: Session, user: User) -> List[UserTrustedDevice]:
    """Live trusts for the security screen, newest first."""
    return (
        db.query(UserTrustedDevice)
        .filter(
            UserTrustedDevice.user_id == str(user.id),
            UserTrustedDevice.revoked_at.is_(None),
            UserTrustedDevice.expires_at > datetime.utcnow(),
        )
        .order_by(UserTrustedDevice.created_at.desc())
        .all()
    )


def revoke_device(db: Session, user: User, device_id: str) -> bool:
    """Revoke one trust by id. Scoped to ``user`` so ids are not cross-user addressable."""
    row = (
        db.query(UserTrustedDevice)
        .filter(
            UserTrustedDevice.id == device_id,
            UserTrustedDevice.user_id == str(user.id),
            UserTrustedDevice.revoked_at.is_(None),
        )
        .first()
    )
    if row is None:
        return False

    row.revoked_at = datetime.utcnow()
    db.commit()
    return True


def revoke_all(db: Session, user: User) -> int:
    """Revoke every live trust for a user. Returns the number revoked.

    Called on password change/reset (sec-review-011 R8) and on MFA disable (D4) —
    a credential change must not leave a remembered browser able to skip MFA.
    """
    now = datetime.utcnow()
    rows = (
        db.query(UserTrustedDevice)
        .filter(
            UserTrustedDevice.user_id == str(user.id),
            UserTrustedDevice.revoked_at.is_(None),
        )
        .all()
    )
    for row in rows:
        row.revoked_at = now
    db.commit()
    return len(rows)
