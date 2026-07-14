import logging
import os
import random
import smtplib
import threading
import uuid
from email.message import EmailMessage
from typing import Optional

import redis
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
_redis: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


router = APIRouter(prefix="/api/v1/otp", tags=["otp"])

# ADR-011 S4 added ``mfa`` — MFA factor enroll/verify runs in its own bucket
# (sec-review-011 R6: distinct purpose so MFA can't share/deplete another flow's cap).
ALLOWED_PURPOSES = {"patient_registration", "patient_login", "staff_2fa", "password_reset", "mfa"}
# Delivery channels. Each keeps a *separate* rate/cost bucket (R6) so an SMS flood
# can't exhaust the email budget or vice-versa.
ALLOWED_CHANNELS = {"phone", "email"}

OTP_TTL = 600  # 10 min
COOLDOWN_TTL = 60  # 1 min between resends
MAX_ATTEMPTS = 5
TOKEN_TTL = 300  # 5 min one-time token
# R6: hard daily caps to bound SMS/email spend + enrollment abuse. Separate
# buckets per delivery target, per account, and per source IP.
DAILY_CAP = int(os.environ.get("OTP_DAILY_CAP", "10"))  # per target
ACCOUNT_DAILY_CAP = int(os.environ.get("OTP_ACCOUNT_DAILY_CAP", "20"))  # per account
IP_DAILY_CAP = int(os.environ.get("OTP_IP_DAILY_CAP", "30"))  # per source IP
DAILY_TTL = 24 * 3600


class OtpSendRequest(BaseModel):
    phone: str
    purpose: str
    tenant_code: str


class OtpVerifyRequest(BaseModel):
    phone: str
    purpose: str
    tenant_code: str
    code: str


class OtpSendResponse(BaseModel):
    message: str
    resend_after: int


class OtpVerifyResponse(BaseModel):
    verified: bool
    otp_token: Optional[str] = None


def _code_key(purpose: str, channel: str, tenant_code: str, target: str) -> str:
    return f"otp:code:{purpose}:{channel}:{tenant_code}:{target}"


def _attempts_key(purpose: str, channel: str, tenant_code: str, target: str) -> str:
    return f"otp:attempts:{purpose}:{channel}:{tenant_code}:{target}"


def _cooldown_key(purpose: str, channel: str, tenant_code: str, target: str) -> str:
    return f"otp:cooldown:{purpose}:{channel}:{tenant_code}:{target}"


def _daily_key(scope: str, ident: str) -> str:
    # Per-scope daily spend counter (R6). scope in {"target", "acct", "ip"}.
    return f"otp:daily:{scope}:{ident}"


def _over_daily_cap(r, scope: str, ident: str, cap: int) -> bool:
    return int(r.get(_daily_key(scope, ident)) or 0) >= cap


def _bump_daily(r, scope: str, ident: str) -> None:
    # Increment the counter; set the 24h window TTL only when first created.
    if r.incr(_daily_key(scope, ident)) == 1:
        r.expire(_daily_key(scope, ident), DAILY_TTL)


def _token_key(token: str) -> str:
    return f"otp:token:{token}"


def send_otp(
    *,
    channel: str,
    target: str,
    purpose: str,
    tenant_code: str,
    account_id: Optional[str] = None,
    ip: Optional[str] = None,
) -> int:
    """Generate + dispatch a one-time code to ``target`` over ``channel``.

    Importable core used by both the HTTP endpoints and the platform MFA router
    (ADR-011 S4). Enforces the resend cooldown and the daily caps
    (sec-review-011 R6) — separate buckets per **target**, per **account**, and
    per source **IP** when those are supplied — stores the code in Redis with an
    attempt counter (R7), and fires the message off-thread. The account/IP caps
    are what stop an authenticated caller from fanning codes out to many
    arbitrary targets (spam / cost-amplification). Raises ``HTTPException``
    (400/429) on invalid input or a limit hit. Returns the resend cooldown (s).
    """
    if purpose not in ALLOWED_PURPOSES:
        raise HTTPException(status_code=400, detail=f"Unknown purpose '{purpose}'")
    if channel not in ALLOWED_CHANNELS:
        raise HTTPException(status_code=400, detail=f"Unknown channel '{channel}'")

    r = get_redis()
    cooldown_key = _cooldown_key(purpose, channel, tenant_code, target)
    if r.exists(cooldown_key):
        ttl = r.ttl(cooldown_key)
        raise HTTPException(status_code=429, detail=f"Please wait {ttl}s before requesting another OTP")

    # R6 — hard daily caps, checked before minting. Separate buckets so one axis
    # can't deplete another: per target, per account, per source IP.
    over = HTTPException(status_code=429, detail="Daily verification-code limit reached; try again tomorrow")
    if _over_daily_cap(r, "target", f"{channel}:{target}", DAILY_CAP):
        raise over
    if account_id and _over_daily_cap(r, "acct", str(account_id), ACCOUNT_DAILY_CAP):
        raise over
    if ip and _over_daily_cap(r, "ip", str(ip), IP_DAILY_CAP):
        raise over

    code = f"{random.randint(0, 999999):06d}"
    code_key = _code_key(purpose, channel, tenant_code, target)
    attempts_key = _attempts_key(purpose, channel, tenant_code, target)

    pipe = r.pipeline()
    pipe.set(code_key, code, ex=OTP_TTL)
    pipe.set(cooldown_key, "1", ex=COOLDOWN_TTL)
    pipe.delete(attempts_key)
    pipe.execute()

    _bump_daily(r, "target", f"{channel}:{target}")
    if account_id:
        _bump_daily(r, "acct", str(account_id))
    if ip:
        _bump_daily(r, "ip", str(ip))

    _dispatch(channel, target, code, purpose)
    # R7 — never log the code or the raw target.
    logger.info("OTP sent purpose=%s channel=%s tenant=%s", purpose, channel, tenant_code)
    return COOLDOWN_TTL


def verify_otp(*, channel: str, target: str, purpose: str, tenant_code: str, code: str) -> str:
    """Verify a code previously sent by :func:`send_otp`; return a one-time token.

    Generic failure messages + a per-target attempt counter with lockout (R7).
    On success consumes the code and issues an opaque token (5 min TTL) the caller
    can exchange for a privileged action. Raises ``HTTPException`` on
    invalid/expired/incorrect codes or once the attempt cap is hit.
    """
    if purpose not in ALLOWED_PURPOSES:
        raise HTTPException(status_code=400, detail=f"Unknown purpose '{purpose}'")
    if channel not in ALLOWED_CHANNELS:
        raise HTTPException(status_code=400, detail=f"Unknown channel '{channel}'")

    r = get_redis()
    code_key = _code_key(purpose, channel, tenant_code, target)
    attempts_key = _attempts_key(purpose, channel, tenant_code, target)

    stored_code = r.get(code_key)
    if not stored_code:
        raise HTTPException(status_code=400, detail="OTP expired or not found")

    attempts = int(r.get(attempts_key) or 0)
    if attempts >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many incorrect attempts; request a new OTP")

    if code != stored_code:
        r.incr(attempts_key)
        r.expire(attempts_key, OTP_TTL)
        raise HTTPException(status_code=400, detail="Incorrect OTP code")

    # Correct -- consume code, issue one-time token
    r.delete(code_key)
    r.delete(attempts_key)

    token = str(uuid.uuid4())
    token_key = _token_key(token)
    token_value = f"{channel}:{target}:{tenant_code}:{purpose}"
    r.set(token_key, token_value, ex=TOKEN_TTL)

    logger.info("OTP verified purpose=%s channel=%s tenant=%s", purpose, channel, tenant_code)
    return token


@router.post("/send", response_model=OtpSendResponse)
async def send_otp_endpoint(body: OtpSendRequest):
    resend_after = send_otp(
        channel="phone", target=body.phone, purpose=body.purpose, tenant_code=body.tenant_code
    )
    return OtpSendResponse(message="OTP sent", resend_after=resend_after)


@router.post("/verify", response_model=OtpVerifyResponse)
async def verify_otp_endpoint(body: OtpVerifyRequest):
    token = verify_otp(
        channel="phone",
        target=body.phone,
        purpose=body.purpose,
        tenant_code=body.tenant_code,
        code=body.code,
    )
    return OtpVerifyResponse(verified=True, otp_token=token)


def _dispatch(channel: str, target: str, code: str, purpose: str) -> None:
    """Fire-and-forget delivery on the appropriate channel."""
    if channel == "email":
        threading.Thread(target=_dispatch_email, args=(target, code, purpose), daemon=True).start()
    else:
        threading.Thread(target=_dispatch_message, args=(target, code, purpose), daemon=True).start()


def _dispatch_message(phone: str, code: str, purpose: str) -> None:
    """Fire-and-forget: try WhatsApp, fall back to SMS, log if both unavailable."""
    wa_url = os.environ.get("WHATSAPP_API_URL")
    sms_url = os.environ.get("SMS_GATEWAY_URL")
    message = f"Your verification code is {code}. Valid for 10 minutes. Do not share it."

    if wa_url:
        try:
            import httpx

            token = os.environ.get("WHATSAPP_API_TOKEN", "")
            resp = httpx.post(
                wa_url,
                json={"to": phone, "message": message},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if resp.status_code < 300:
                logger.info("WhatsApp OTP dispatched")
                return
            logger.warning(f"WhatsApp returned {resp.status_code}; falling back to SMS")
        except Exception as e:
            logger.warning(f"WhatsApp dispatch failed: {e}; falling back to SMS")

    if sms_url:
        try:
            import httpx

            resp = httpx.post(sms_url, json={"to": phone, "text": message}, timeout=10)
            if resp.status_code < 300:
                logger.info("SMS OTP dispatched")
                return
            logger.warning(f"SMS gateway returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"SMS dispatch failed: {e}")

    logger.warning("No SMS/WhatsApp provider configured; phone OTP not delivered")


def _dispatch_email(email: str, code: str, purpose: str) -> None:
    """Fire-and-forget email OTP via SMTP (ADR-002-smtp; MailHog in dev).

    Reads the same env SMTP config as the notification worker
    (``SMTP_HOST``/``SMTP_PORT``/``SMTP_USER``/``SMTP_PASSWORD``/``SMTP_FROM``/
    ``SMTP_USE_TLS``). The code is never logged (R7).
    """
    host = os.environ.get("SMTP_HOST")
    if not host:
        logger.warning("No SMTP_HOST configured; email OTP not delivered (purpose=%s)", purpose)
        return

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", "no-reply@example.com")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = sender
    msg["To"] = email
    msg.set_content(f"Your verification code is {code}. Valid for 10 minutes. Do not share it.")

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if use_tls and user:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        logger.info("Email OTP dispatched (purpose=%s)", purpose)
    except Exception as e:
        logger.warning("Email OTP dispatch failed: %s", e)
