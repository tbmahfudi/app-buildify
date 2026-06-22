"""
Healthcare SDK — OTP generation and verification.

T-HC-002

OTP keys in Redis:
    otp:{phone}              — the 6-digit code, TTL 10 min
    otp_attempts:{phone}     — attempt counter, TTL 10 min
    otp_cooldown:{phone}     — resend cooldown lock, TTL 60 s

Error shape is intentionally consistent — never reveals whether a phone is registered.
"""
from __future__ import annotations

import os
import secrets
import string
from typing import Optional

OTP_TTL = 600          # 10 minutes in seconds
COOLDOWN_TTL = 60      # 60 seconds resend cooldown
MAX_ATTEMPTS = 5       # max verification attempts per phone per OTP_TTL window


def _get_redis():
    """
    Return a synchronous redis.Redis client.

    Uses REDIS_URL env var (same source as the platform RedisClient).
    Raises RuntimeError if Redis is not configured — OTP requires Redis.
    """
    try:
        import redis
    except ImportError as exc:
        raise RuntimeError(
            "redis-py is required for OTP functionality. "
            "Install it with: pip install redis"
        ) from exc

    url = os.environ.get("REDIS_URL", "")
    if not url:
        raise RuntimeError(
            "REDIS_URL environment variable is not set. "
            "OTP functionality requires Redis."
        )
    return redis.from_url(url, decode_responses=True, socket_connect_timeout=2)


def _otp_key(phone: str) -> str:
    return f"otp:{phone}"


def _attempts_key(phone: str) -> str:
    return f"otp_attempts:{phone}"


def _cooldown_key(phone: str) -> str:
    return f"otp_cooldown:{phone}"


def generate_otp(phone: str) -> str:
    """
    Generate a 6-digit OTP for the given phone number, store it in Redis,
    and return the code.

    Raises:
        ValueError: if the phone is currently in the 60-second resend cooldown.
        RuntimeError: if Redis is unavailable or not configured.
    """
    r = _get_redis()

    # Enforce resend cooldown
    if r.exists(_cooldown_key(phone)):
        raise ValueError(
            "OTP request too frequent. Please wait before requesting a new code."
        )

    code = "".join(secrets.choice(string.digits) for _ in range(6))

    pipe = r.pipeline()
    pipe.set(_otp_key(phone), code, ex=OTP_TTL)
    # Reset attempt counter on new OTP generation
    pipe.delete(_attempts_key(phone))
    # Set resend cooldown
    pipe.set(_cooldown_key(phone), "1", ex=COOLDOWN_TTL)
    pipe.execute()

    return code


def verify_otp(phone: str, code: str) -> bool:
    """
    Verify a 6-digit OTP for the given phone number.

    - Returns True and deletes the OTP key on success.
    - Returns False on mismatch (incrementing the attempt counter).
    - Raises ValueError if max attempts are exceeded (consistent error shape).

    The error messages are intentionally generic to prevent user enumeration.
    """
    r = _get_redis()

    # Check attempt count BEFORE validating the code
    attempts_key = _attempts_key(phone)
    attempts_raw: Optional[str] = r.get(attempts_key)
    attempts = int(attempts_raw) if attempts_raw else 0

    if attempts >= MAX_ATTEMPTS:
        raise ValueError(
            "Verification failed. Please request a new OTP."
        )

    stored_code: Optional[str] = r.get(_otp_key(phone))

    if stored_code is None:
        # OTP expired or never issued — increment attempts to rate-limit probing
        pipe = r.pipeline()
        pipe.incr(attempts_key)
        pipe.expire(attempts_key, OTP_TTL)
        pipe.execute()
        return False

    if stored_code != code:
        pipe = r.pipeline()
        pipe.incr(attempts_key)
        pipe.expire(attempts_key, OTP_TTL)
        pipe.execute()
        return False

    # Success — delete OTP and attempt counter (cooldown stays until it expires)
    pipe = r.pipeline()
    pipe.delete(_otp_key(phone))
    pipe.delete(attempts_key)
    pipe.execute()
    return True


__all__ = ["generate_otp", "verify_otp", "OTP_TTL", "COOLDOWN_TTL", "MAX_ATTEMPTS"]
