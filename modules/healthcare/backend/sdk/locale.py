"""
Healthcare SDK — Backend i18n framework.

T-HC-004

Translation files are loaded once at module startup into _TRANSLATIONS.
`t(locale, key, **kwargs)` never raises — missing keys fall back to en-US then key name.

Locale resolution precedence (highest priority first):
    1. Authenticated user profile locale
    2. Tenant default locale
    3. Platform default ("id-ID")
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_LOCALE = "id-ID"
FALLBACK_LOCALE = "en-US"
SUPPORTED_LOCALES = [DEFAULT_LOCALE, FALLBACK_LOCALE]

# Absolute path to the i18n directory (same package, sibling directory)
_I18N_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "i18n")

# Module-level cache: { locale: { key: translated_string } }
_TRANSLATIONS: dict[str, dict[str, str]] = {}


def _load_locale(locale: str) -> dict[str, str]:
    """Load a single locale JSON file. Returns empty dict on error."""
    path = os.path.join(_I18N_DIR, f"{locale}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("i18n file not found: %s", path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Malformed i18n file %s: %s", path, exc)
        return {}


def _load_all() -> None:
    """Load all supported locales into _TRANSLATIONS at module startup."""
    for locale in SUPPORTED_LOCALES:
        _TRANSLATIONS[locale] = _load_locale(locale)


# Load on import (module startup)
_load_all()


def resolve_locale(
    user_locale: Optional[str],
    tenant_locale: Optional[str],
) -> str:
    """
    Resolve the effective locale from the precedence chain:
        user_locale -> tenant_locale -> DEFAULT_LOCALE ("id-ID")

    Only supported locales are accepted; unsupported values fall through
    to the next level.
    """
    for candidate in (user_locale, tenant_locale, DEFAULT_LOCALE):
        if candidate and candidate in SUPPORTED_LOCALES:
            return candidate
    return DEFAULT_LOCALE


def t(locale: str, key: str, **kwargs: object) -> str:
    """
    Translate *key* into *locale*, interpolating any **kwargs.

    Fallback chain:
        1. locale translation file
        2. en-US translation file
        3. the key name itself (never raises)

    String interpolation uses str.format_map so callers pass named kwargs:
        t("id-ID", "auth.otp_sent", phone="+62812...")
    """
    translations = _TRANSLATIONS.get(locale, {})
    fallback = _TRANSLATIONS.get(FALLBACK_LOCALE, {})

    raw: Optional[str] = translations.get(key) or fallback.get(key)

    if raw is None:
        logger.warning("Missing i18n key %r for locale %r", key, locale)
        return key

    if not kwargs:
        return raw

    try:
        return raw.format_map(kwargs)
    except (KeyError, ValueError) as exc:
        logger.warning("i18n format error for key %r: %s", key, exc)
        return raw


__all__ = [
    "resolve_locale",
    "t",
    "SUPPORTED_LOCALES",
    "DEFAULT_LOCALE",
    "FALLBACK_LOCALE",
]
