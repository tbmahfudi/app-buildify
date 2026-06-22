"""
GET /api/v1/modules/healthcare/i18n/{locale}

Serves static translation JSON for the healthcare module.
Public endpoint — no authentication required.
Falls back to id-ID if the requested locale file is missing.

T-HC-008 / ADR-HC-004
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/healthcare/i18n",
    tags=["healthcare-i18n"],
)

_I18N_DIR = Path(__file__).parent / "i18n"
_SUPPORTED_LOCALES = {"id-ID", "en-US"}
_DEFAULT_LOCALE = "id-ID"

# In-memory cache: locale -> translation dict
_cache: dict[str, dict] = {}


def _load_locale(locale: str) -> dict:
    """Load and cache a locale JSON file. Returns {} on any error."""
    if locale in _cache:
        return _cache[locale]

    path = _I18N_DIR / f"{locale}.json"
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        _cache[locale] = data
        return data
    except FileNotFoundError:
        logger.warning("i18n: locale file not found: %s", path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("i18n: invalid JSON in %s: %s", path, exc)
        return {}


@router.get(
    "/{locale}",
    summary="Get healthcare i18n translations",
    response_class=JSONResponse,
    responses={
        200: {"description": "Translation key-value map"},
        404: {"description": "Locale not available and default fallback also missing"},
    },
)
async def get_translations(locale: str) -> JSONResponse:
    """
    Return the translation JSON for the requested locale.

    - If the locale is supported and its file exists, return it directly.
    - If the locale is not in SUPPORTED_LOCALES or the file is missing,
      fall back to id-ID.
    - Cache-Control: public, max-age=3600 (1 hour CDN/browser caching).
    """
    # Normalise and validate to prevent path traversal
    locale = locale.strip()
    if locale not in _SUPPORTED_LOCALES:
        logger.info("i18n: unsupported locale '%s', falling back to %s", locale, _DEFAULT_LOCALE)
        locale = _DEFAULT_LOCALE

    data = _load_locale(locale)
    if not data and locale != _DEFAULT_LOCALE:
        data = _load_locale(_DEFAULT_LOCALE)

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No translation file available for locale '{locale}'",
        )

    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=3600"},
    )
