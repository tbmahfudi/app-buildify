"""MFA login challenge (ADR-HC-009 D3).

The half-authenticated state between "password was correct" and "fully logged in".

When a user with an active MFA factor logs in, we do **not** issue access/refresh
tokens. We mint a short-lived, single-purpose ``mfa_challenge`` JWT and dispatch an
OTP; only ``POST /auth/mfa/verify`` trades that token + the code for real tokens.

Two properties matter and are enforced here:

* **The challenge token is not an access token.** It carries ``type:
  "mfa_challenge"``, and every normal auth path rejects a token whose ``type`` is
  not ``access``. So a half-authenticated caller cannot reach any protected route
  — including the healthcare ``from-platform`` bridge — by waving it around.
* **It is single-use.** The JWT's ``jti`` is registered in Redis when minted and
  deleted when consumed, so a captured token cannot be replayed even inside its
  5-minute window. Redis (not the DB) because this is short-lived, high-churn
  state that should expire on its own — same reasoning as the OTP codes it guards.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import jwt
from sqlalchemy.orm import Session

from app.core.auth import ALGORITHM
from app.core.config import SECRET_KEY
from app.models.user import User
from app.models.user_mfa_factor import UserMFAFactor
from app.routers import otp
from app.services import mfa_service

logger = logging.getLogger(__name__)

# D3: "~5-minute TTL". Long enough to read an SMS/email, short enough to bound replay.
CHALLENGE_TTL_SECONDS = 300

TOKEN_TYPE = "mfa_challenge"

_REDIS_PREFIX = "mfa:challenge:"


class ChallengeError(Exception):
    """The challenge token is missing, malformed, expired, or already used."""


def _redis_key(jti: str) -> str:
    return f"{_REDIS_PREFIX}{jti}"


def mask_target(factor_type: str, target: str) -> str:
    """A recognizable but non-disclosing hint: ``j***n@example.com`` / ``+62****789``.

    The user needs to know *where* the code went; an attacker who has only the
    password must not learn the full address/number from the login response.
    """
    if not target:
        return ""
    if factor_type == "email_otp" and "@" in target:
        local, _, domain = target.partition("@")
        if len(local) <= 2:
            masked_local = local[0] + "*" if local else "*"
        else:
            masked_local = f"{local[0]}***{local[-1]}"
        return f"{masked_local}@{domain}"
    # phone: keep the last 3 digits only
    tail = target[-3:]
    return f"{'*' * max(len(target) - 3, 0)}{tail}"


def create_challenge(
    db: Session,
    user: User,
    *,
    ip: Optional[str] = None,
) -> Tuple[str, List[UserMFAFactor], UserMFAFactor]:
    """Mint a single-use challenge token and dispatch an OTP to the user's factor.

    Returns ``(mfa_token, active_factors, dispatched_factor)``. The OTP goes to the
    first active factor; the full list is returned so the response can advertise
    the available methods (D3 ``methods``).

    Raises ``ChallengeError`` if the user has no active factor — callers must only
    reach here after :func:`mfa_service.has_active_factor`.
    """
    factors = mfa_service.list_active_factors(db, user.id)
    if not factors:
        raise ChallengeError("User has no active MFA factor")

    target_factor = factors[0]
    channel = mfa_service.channel_for_factor(target_factor.factor_type)

    # Reuses the S4 OTP service: purpose="mfa" keeps this in its own rate-limit
    # bucket, and the per-target/account/IP daily caps (R6) apply unchanged.
    otp.send_otp(
        channel=channel,
        target=target_factor.target,
        purpose="mfa",
        tenant_code=str(user.tenant_id) if user.tenant_id else "platform",
        account_id=str(user.id),
        ip=ip,
    )

    jti = str(uuid.uuid4())
    now = datetime.utcnow()
    token = jwt.encode(
        {
            "sub": str(user.id),
            "type": TOKEN_TYPE,
            "jti": jti,
            "factor_id": str(target_factor.id),
            "iat": now,
            "exp": now + timedelta(seconds=CHALLENGE_TTL_SECONDS),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    # Register for single-use. If Redis is down we fail the login rather than
    # silently degrade to a replayable token.
    otp.get_redis().setex(_redis_key(jti), CHALLENGE_TTL_SECONDS, str(user.id))

    return token, factors, target_factor


def validate_challenge(token: str) -> Tuple[str, str, str]:
    """Check a challenge token without spending it. Returns ``(user_id, factor_id, jti)``.

    Raises ``ChallengeError`` if the token is malformed, the wrong ``type``, expired,
    or already redeemed.

    Note what this deliberately does *not* do: it does not burn the token on a wrong
    code. Limiting code guesses is the OTP service's attempt-lockout job (R7/R9);
    burning here as well would mean a single typo costs the user another SMS and a
    fresh login — spending real money (R6) to duplicate a control we already have.
    The token is spent by :func:`burn_challenge` once the code is actually correct,
    which is the replay that D3's "single-use" exists to stop.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise ChallengeError("Invalid or expired challenge")

    if payload.get("type") != TOKEN_TYPE:
        # An access/refresh token must never be usable as a challenge.
        raise ChallengeError("Invalid or expired challenge")

    jti = payload.get("jti")
    user_id = payload.get("sub")
    factor_id = payload.get("factor_id")
    if not jti or not user_id or not factor_id:
        raise ChallengeError("Invalid or expired challenge")

    if not otp.get_redis().exists(_redis_key(jti)):
        # Already redeemed, or expired out of Redis.
        raise ChallengeError("Invalid or expired challenge")

    return str(user_id), str(factor_id), str(jti)


def burn_challenge(jti: str) -> bool:
    """Spend the token so it cannot be redeemed twice (D3 single-use).

    Returns True if this caller was the one that spent it. DEL is atomic, so of two
    concurrent verifies holding the same token only one can win the exchange.
    """
    return otp.get_redis().delete(_redis_key(jti)) == 1
