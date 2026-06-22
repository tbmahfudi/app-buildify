"""
Healthcare — Backend locale wiring.

T-HC-017

GET /api/v1/modules/healthcare/i18n/{locale}
    Public; no auth; serves translation JSON from modules/healthcare/i18n/{locale}.json
    Falls back to id-ID; Cache-Control: public, max-age=3600

GET /api/v1/modules/healthcare/i18n-overrides/{locale}
    Auth: Clinic Owner; returns tenant-specific overrides from hc_i18n_overrides

PUT /api/v1/modules/healthcare/i18n-overrides/{locale}/{key}
    Auth: Clinic Owner; upsert override
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCI18nOverride
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-i18n"],
)

SUPPORTED_LOCALES = {"id-ID", "en-US"}
FALLBACK_LOCALE = "id-ID"

# Resolve i18n directory relative to this file's module location
_I18N_DIR = Path(__file__).parent / "i18n"


def _load_base_translations(locale: str) -> dict[str, Any]:
    """Load translations from disk; fall back to id-ID if locale file missing."""
    locale_file = _I18N_DIR / f"{locale}.json"
    if not locale_file.exists():
        locale_file = _I18N_DIR / f"{FALLBACK_LOCALE}.json"
    if not locale_file.exists():
        return {}
    with locale_file.open("r", encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/i18n/{locale}",
    summary="Get base translations for a locale (public, cached)",
)
async def get_translations(locale: str):
    if locale not in SUPPORTED_LOCALES:
        locale = FALLBACK_LOCALE

    translations = _load_base_translations(locale)

    response_body = json.dumps(translations, ensure_ascii=False)
    return Response(
        content=response_body,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get(
    "/i18n-overrides/{locale}",
    summary="Get tenant translation overrides (Clinic Owner)",
)
async def get_i18n_overrides(
    locale: str,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(HCRole.clinic_owner)),
):
    if locale not in SUPPORTED_LOCALES:
        raise HTTPException(status_code=400, detail=f"Unsupported locale: {locale}")

    overrides = (
        db.query(HCI18nOverride)
        .filter(
            HCI18nOverride.tenant_id == str(current_user.tenant_id),
            HCI18nOverride.locale == locale,
        )
        .all()
    )

    return {row.translation_key: row.translation_value for row in overrides}


class I18nOverrideUpsert(BaseModel):
    value: str


@router.put(
    "/i18n-overrides/{locale}/{key}",
    summary="Upsert a tenant translation override (Clinic Owner)",
)
async def upsert_i18n_override(
    locale: str,
    key: str,
    payload: I18nOverrideUpsert,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(HCRole.clinic_owner)),
):
    if locale not in SUPPORTED_LOCALES:
        raise HTTPException(status_code=400, detail=f"Unsupported locale: {locale}")

    existing = (
        db.query(HCI18nOverride)
        .filter(
            HCI18nOverride.tenant_id == str(current_user.tenant_id),
            HCI18nOverride.locale == locale,
            HCI18nOverride.translation_key == key,
        )
        .first()
    )

    if existing:
        existing.translation_value = payload.value
        existing.updated_at = datetime.utcnow()
    else:
        override = HCI18nOverride(
            tenant_id=str(current_user.tenant_id),
            locale=locale,
            translation_key=key,
            translation_value=payload.value,
        )
        db.add(override)

    db.commit()
    return {"locale": locale, "key": key, "value": payload.value}
