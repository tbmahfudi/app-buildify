"""
Healthcare SDK — Branch access verification helper.

Internal module — not part of the public SDK surface.
Called by healthcare_branch_session to verify hc_branch_staff membership.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def verify_branch_access(
    db: Session,
    user_id: str,
    tenant_id: str,
    branch_id: str,
) -> bool:
    """
    Return True if the user has a row in hc_branch_staff for the given branch.

    Uses a raw SQL query so this works before any ORM models are imported
    (avoids circular imports in sdk/).

    The hc_branch_staff table is created by the healthcare Alembic migration.
    If the table does not exist yet (e.g. tests before migration), returns False.
    """
    try:
        result = db.execute(
            text(
                "SELECT 1 FROM hc_branch_staff "
                "WHERE user_id = :user_id "
                "AND tenant_id = :tenant_id "
                "AND branch_id = :branch_id "
                "LIMIT 1"
            ),
            {"user_id": user_id, "tenant_id": tenant_id, "branch_id": branch_id},
        )
        return result.fetchone() is not None
    except Exception:
        return False
