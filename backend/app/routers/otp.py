import logging
import os
import random
import uuid
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

ALLOWED_PURPOSES = {"patient_registration", "patient_login", "staff_2fa", "password_reset"}
OTP_TTL = 600  # 10 min
COOLDOWN_TTL = 60  # 1 min between resends
MAX_ATTEMPTS = 5
TOKEN_TTL = 300  # 5 min one-time token


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


def _code_key(purpose: str, tenant_code: str, phone: str) -> str:
    return f"otp:code:{purpose}:{tenant_code}:{phone}"


def _attempts_key(purpose: str, tenant_code: str, phone: str) -> str:
    return f"otp:attempts:{purpose}:{tenant_code}:{phone}"


def _cooldown_key(purpose: str, tenant_code: str, phone: str) -> str:
    return f"otp:cooldown:{purpose}:{tenant_code}:{phone}"


def _token_key(token: str) -> str:
    return f"otp:token:{token}"


@router.post("/send", response_model=OtpSendResponse)
async def send_otp(body: OtpSendRequest):
    if body.purpose not in ALLOWED_PURPOSES:
        raise HTTPException(status_code=400, detail=f"Unknown purpose '{body.purpose}'")

    r = get_redis()
    cooldown_key = _cooldown_key(body.purpose, body.tenant_code, body.phone)
    if r.exists(cooldown_key):
        ttl = r.ttl(cooldown_key)
        raise HTTPException(status_code=429, detail=f"Please wait {ttl}s before requesting another OTP")

    code = f"{random.randint(0, 999999):06d}"
    code_key = _code_key(body.purpose, body.tenant_code, body.phone)
    attempts_key = _attempts_key(body.purpose, body.tenant_code, body.phone)

    pipe = r.pipeline()
    pipe.set(code_key, code, ex=OTP_TTL)
    pipe.set(cooldown_key, "1", ex=COOLDOWN_TTL)
    pipe.delete(attempts_key)
    pipe.execute()

    _send_otp_message(body.phone, code, body.purpose)
    logger.info(f"OTP sent to {body.phone} for purpose={body.purpose} tenant={body.tenant_code}")
    return OtpSendResponse(message="OTP sent", resend_after=COOLDOWN_TTL)


@router.post("/verify", response_model=OtpVerifyResponse)
async def verify_otp(body: OtpVerifyRequest):
    if body.purpose not in ALLOWED_PURPOSES:
        raise HTTPException(status_code=400, detail=f"Unknown purpose '{body.purpose}'")

    r = get_redis()
    code_key = _code_key(body.purpose, body.tenant_code, body.phone)
    attempts_key = _attempts_key(body.purpose, body.tenant_code, body.phone)

    stored_code = r.get(code_key)
    if not stored_code:
        raise HTTPException(status_code=400, detail="OTP expired or not found")

    attempts = int(r.get(attempts_key) or 0)
    if attempts >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many incorrect attempts; request a new OTP")

    if body.code != stored_code:
        r.incr(attempts_key)
        r.expire(attempts_key, OTP_TTL)
        raise HTTPException(status_code=400, detail="Incorrect OTP code")

    # Correct -- consume code, issue one-time token
    r.delete(code_key)
    r.delete(attempts_key)

    token = str(uuid.uuid4())
    token_key = _token_key(token)
    token_value = f"{body.phone}:{body.tenant_code}:{body.purpose}"
    r.set(token_key, token_value, ex=TOKEN_TTL)

    logger.info(f"OTP verified for {body.phone} purpose={body.purpose} tenant={body.tenant_code}")
    return OtpVerifyResponse(verified=True, otp_token=token)


def _send_otp_message(phone: str, code: str, purpose: str) -> None:
    """Fire-and-forget: try WhatsApp, fall back to SMS, log if both unavailable."""
    import threading

    threading.Thread(target=_dispatch_message, args=(phone, code, purpose), daemon=True).start()


def _dispatch_message(phone: str, code: str, purpose: str) -> None:
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
                logger.info(f"WhatsApp OTP sent to {phone}")
                return
            logger.warning(f"WhatsApp returned {resp.status_code}; falling back to SMS")
        except Exception as e:
            logger.warning(f"WhatsApp dispatch failed: {e}; falling back to SMS")

    if sms_url:
        try:
            import httpx

            resp = httpx.post(sms_url, json={"to": phone, "text": message}, timeout=10)
            if resp.status_code < 300:
                logger.info(f"SMS OTP sent to {phone}")
                return
            logger.warning(f"SMS gateway returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"SMS dispatch failed: {e}")

    logger.warning(f"No messaging provider configured; OTP code for {phone}: {code}")
