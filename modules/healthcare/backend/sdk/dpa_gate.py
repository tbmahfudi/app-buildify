"""
Healthcare SDK — DPA gate dependency.

T-HC-019

require_dpa: FastAPI dependency that checks hc_patient_consents for
consent_type="clinic_dpa" scoped to the calling tenant.  Raises HTTP 403
with a localised message if the DPA record is missing.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.sdk.locale import t


def require_dpa(
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
) -> None:
    """
    FastAPI dependency — verify the tenant has accepted the DPA.

    Queries hc_patient_consents for:
        consent_type = 'clinic_dpa'
        entity_id    = tenant_id          (stored in patient_id column for DPA rows)
        status       = 'active'

    Raises HTTP 403 with a localised message if missing.
    """
    tenant_id: str = str(current_user.tenant_id)
    locale: str = getattr(current_user, "locale", "id-ID") or "id-ID"

    row = db.execute(
        text(
            "SELECT id FROM hc_patient_consents "
            "WHERE tenant_id = :tid "
            "AND consent_type = 'clinic_dpa' "
            "AND status = 'active' "
            "LIMIT 1"
        ),
        {"tid": tenant_id},
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t(locale, "error.dpa_required"),
        )


__all__ = ["require_dpa"]
