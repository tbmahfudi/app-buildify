"""
Healthcare SDK — hCaptcha adapter.

T-HC-003

Set HCAPTCHA_SECRET_KEY env var to your hCaptcha secret key.
Set HCAPTCHA_SECRET_KEY=test to bypass verification in CI/testing.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException, status

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"
_BYPASS_VALUE = "test"


def verify_hcaptcha(token: str) -> bool:
    """
    POST to hCaptcha verify API.

    Returns True on success, False on failure or network error.
    If HCAPTCHA_SECRET_KEY == "test", always returns True (CI bypass).
    """
    secret_key: str = os.environ.get("HCAPTCHA_SECRET_KEY", "")

    if not secret_key:
        # No key configured — fail closed (do not silently allow)
        return False

    if secret_key == _BYPASS_VALUE:
        # CI bypass mode
        return True

    try:
        import urllib.parse
        import urllib.request

        data = urllib.parse.urlencode({
            "secret": secret_key,
            "response": token,
        }).encode("ascii")

        req = urllib.request.Request(
            HCAPTCHA_VERIFY_URL,
            data=data,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            import json as _json
            body = _json.loads(resp.read().decode("utf-8"))
            return bool(body.get("success", False))
    except Exception:
        # Network error or unexpected response — fail closed
        return False


def require_captcha(
    x_captcha_token: Optional[str] = Header(None, alias="X-Captcha-Token"),
) -> None:
    """
    FastAPI dependency — validates hCaptcha token from X-Captcha-Token header.

    Raises HTTP 422 if the token is missing or verification fails.

    Usage::

        @router.post("/patients/register")
        async def register(
            payload: RegisterRequest,
            _=Depends(require_captcha),
        ):
            ...
    """
    if not x_captcha_token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="X-Captcha-Token header is required",
        )

    if not verify_hcaptcha(x_captcha_token):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Security verification failed. Please try again.",
        )


__all__ = [
    "verify_hcaptcha",
    "require_captcha",
    "HCAPTCHA_VERIFY_URL",
]
