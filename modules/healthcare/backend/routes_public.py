"""
Healthcare — Public clinic search and profile APIs.

T-HC-022  GET /api/v1/clinics/search              (PUBLIC)
T-HC-023  GET /api/v1/clinics/{slug}               (PUBLIC)
          GET /api/v1/clinics/{slug}/branches/{branch_id}  (PUBLIC)

No PHI is returned from any endpoint in this file.
FIX-BE-005: Redis-based 60 req/IP/min rate limiting implemented.
"""
from __future__ import annotations

import os
import time
from typing import Dict, List, Optional, Tuple

import redis as _redis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session
from app.core.dependencies import get_db as _platform_get_db
from modules.healthcare.schemas.public import (
    ClinicPublicProfile,
    ClinicSearchItem,
    ClinicSearchResponse,
    PublicBranchDetail,
    PublicProviderSummary,
)
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id


# ---------------------------------------------------------------------------
# Rate limiting dependency
# ---------------------------------------------------------------------------

def _get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return _redis.from_url(url, decode_responses=True)


async def _public_rate_limit(request: Request):
    """60 requests per minute per IP for public endpoints."""
    ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:public:{ip}:{int(time.time() // 60)}"
    try:
        r = _get_redis()
        count = r.incr(key)
        if count == 1:
            r.expire(key, 60)
        if count > 60:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    except HTTPException:
        raise
    except Exception:
        pass  # fail open — don't block requests if Redis is unavailable


router = APIRouter(tags=["healthcare-public"])


def _get_public_db():
    """Unauthenticated plain DB session for public (no-auth) endpoints."""
    yield from _platform_get_db()

# ---------------------------------------------------------------------------
# Module-level caches
# ---------------------------------------------------------------------------
# Simple dict cache with 60-second TTL for search results
# Key: (specialty, city, name, page, page_size) -> (timestamp, result)
_search_cache: Dict[Tuple, Tuple[float, ClinicSearchResponse]] = {}
_SEARCH_CACHE_TTL = 60  # seconds

# 5-minute per-slug cache for public profiles
# Key: slug -> (timestamp, ClinicPublicProfile | None)
_profile_cache: Dict[str, Tuple[float, Optional[ClinicPublicProfile]]] = {}
_PROFILE_CACHE_TTL = 300  # 5 minutes


# ---------------------------------------------------------------------------
# T-HC-022 — Clinic search
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/clinics/search",
    response_model=ClinicSearchResponse,
    summary="Search public clinic directory (public, no PHI)",
)
async def clinic_search(
    request: Request,
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(_get_public_db),
    _rl: None = Depends(_public_rate_limit),
) -> ClinicSearchResponse:
    """
    Search the public clinic directory.

    Returns non-PHI clinic metadata only: name, slug, specialty_tags,
    city, average_rating, online_booking, branch_count.

    Page size is capped at 50.
    Results cached 60 seconds in-process.
    """
    cache_key: Tuple = (specialty, city, name, page, page_size)
    now = time.time()

    cached = _search_cache.get(cache_key)
    if cached and (now - cached[0]) < _SEARCH_CACHE_TTL:
        return cached[1]

    offset = (page - 1) * page_size

    # Build WHERE clauses — all filters on non-PHI columns only. Company directory is opt-in
    # (companies.public_listing) and per-branch public_visible (ADR-HC-010 D6); scoped to the
    # shared SaaS tenant so results are grouped by CLINIC (Company), not the shared tenant.
    where_parts = [
        "b.deleted_at IS NULL", "b.status = 'active'", "b.public_visible = true",
        "c.public_listing = true", "c.is_active = true", "c.tenant_id = :saas",
    ]
    params: dict = {"limit": page_size, "offset": offset, "saas": hc_shared_tenant_id()}

    if specialty:
        where_parts.append("b.specialty_tags::text ILIKE :specialty")
        params["specialty"] = f"%{specialty}%"
    if city:
        where_parts.append("b.address_city ILIKE :city")
        params["city"] = f"%{city}%"
    if name:
        where_parts.append("(c.name ILIKE :name OR b.branch_name ILIKE :name)")
        params["name"] = f"%{name}%"

    where_sql = " AND ".join(where_parts)

    # Count query — distinct Companies (clinics)
    count_sql = f"""
        SELECT COUNT(DISTINCT c.id)
        FROM hc_branches b
        JOIN companies c ON c.id = b.platform_company_id
        WHERE {where_sql}
    """
    total: int = db.execute(text(count_sql), params).scalar() or 0

    # Main query — group by Company to aggregate branch_count + avg_rating; slug = companies.code
    rows_sql = f"""
        SELECT
            c.id                                   AS company_id,
            c.name                                 AS clinic_name,
            MIN(c.code)                            AS slug,
            MIN(b.address_city)                    AS city,
            COALESCE(
                AVG(cr.rating) FILTER (WHERE cr.status = 'approved'),
                NULL
            )                                      AS average_rating,
            BOOL_OR(b.online_booking)              AS online_booking,
            COUNT(DISTINCT b.id)                   AS branch_count,
            COALESCE(
                array_agg(DISTINCT elem) FILTER (WHERE elem IS NOT NULL),
                ARRAY[]::text[]
            )                                      AS specialty_tags
        FROM hc_branches b
        JOIN companies c ON c.id = b.platform_company_id
        LEFT JOIN hc_clinic_reviews cr ON cr.branch_id = b.id
        LEFT JOIN LATERAL jsonb_array_elements_text(
            COALESCE(b.appointment_types, '[]'::jsonb)
        ) AS elem ON true
        WHERE {where_sql}
        GROUP BY c.id, c.name
        ORDER BY clinic_name ASC
        LIMIT :limit OFFSET :offset
    """
    rows = db.execute(text(rows_sql), params).fetchall()

    items = [
        ClinicSearchItem(
            clinic_name=row.clinic_name,
            slug=row.slug or "",
            specialty_tags=list(row.specialty_tags) if row.specialty_tags else [],
            city=row.city or "",
            average_rating=float(row.average_rating) if row.average_rating else None,
            online_booking=bool(row.online_booking),
            branch_count=int(row.branch_count),
        )
        for row in rows
    ]

    result = ClinicSearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )

    _search_cache[cache_key] = (now, result)
    return result


# ---------------------------------------------------------------------------
# epic-20 Feature 20.4 — PHI-free clinic directory (logged-out chooser feed)
# The single cross-Company public read surface (ADR-HC-010 D6). Opt-in only.
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/clinics",
    summary="Public clinic directory — opt-in Companies + their public branches (no PHI)",
    tags=["healthcare-public"],
)
async def clinic_directory(
    request: Request,
    db: Session = Depends(_get_public_db),
    _rl: None = Depends(_public_rate_limit),
):
    """Return the PHI-free clinic chooser feed: every Company that opted into the public
    directory (companies.public_listing), with its public-visible clinic sites. Under the shared
    SaaS tenant this is the only place clinics are listed across Companies; it exposes no PHI."""
    rows = db.execute(
        text(
            """
            SELECT c.code AS slug, c.name AS clinic_name, c.city AS company_city,
                   b.id AS branch_id, b.branch_name, b.address_city, b.online_booking
            FROM companies c
            LEFT JOIN hc_branches b
                   ON b.platform_company_id = c.id
                  AND b.public_visible = true AND b.deleted_at IS NULL AND b.status = 'active'
            WHERE c.public_listing = true AND c.is_active = true AND c.tenant_id = :saas
            ORDER BY c.name ASC, b.branch_name ASC
            """
        ),
        {"saas": hc_shared_tenant_id()},
    ).fetchall()

    clinics: dict = {}
    for r in rows:
        c = clinics.setdefault(r.slug, {
            "slug": r.slug, "clinic_name": r.clinic_name,
            "city": r.company_city or "", "branches": [],
        })
        if r.branch_id:
            c["branches"].append({
                "branch_id": str(r.branch_id),
                "branch_name": r.branch_name,
                "city": r.address_city or "",
                "online_booking": bool(r.online_booking),
            })
    items = list(clinics.values())
    return {"clinics": items, "total": len(items)}


# ---------------------------------------------------------------------------
# T-HC-023 — Public clinic profile
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/clinics/{slug}",
    response_model=ClinicPublicProfile,
    summary="Public clinic profile with branches and providers (public, no PHI)",
)
async def clinic_public_profile(
    request: Request,
    slug: str,
    db: Session = Depends(_get_public_db),
    _rl: None = Depends(_public_rate_limit),
) -> ClinicPublicProfile:
    """
    Return public profile for a clinic identified by slug.

    Includes all active branches.
    Providers: name + specialty ONLY (no license_number, no PHI).
    Cached 5 minutes per slug.
    """
    return _get_profile(slug=slug, branch_id=None, db=db)


@router.get(
    "/api/v1/clinics/{slug}/branches/{branch_id}",
    response_model=PublicBranchDetail,
    summary="Single branch public detail with providers (public, no PHI)",
)
async def clinic_branch_public(
    request: Request,
    slug: str,
    branch_id: str,
    db: Session = Depends(_get_public_db),
    _rl: None = Depends(_public_rate_limit),
) -> PublicBranchDetail:
    """
    Return public detail for a specific branch of a clinic.

    Providers: name + specialty ONLY — no license_number, no PHI.
    """
    profile = _get_profile(slug=slug, branch_id=branch_id, db=db)
    for branch in profile.branches:
        if branch.branch_id == branch_id:
            return branch
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Branch not found.",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_profile(
    slug: str,
    branch_id: Optional[str],
    db: Session,
) -> ClinicPublicProfile:
    """Fetch (or return cached) public profile for the given slug."""
    now = time.time()
    cached = _profile_cache.get(slug)
    if cached and (now - cached[0]) < _PROFILE_CACHE_TTL and cached[1] is not None:
        return cached[1]

    # Company lookup by code (slug = Company code, ADR-HC-010 D6). Only Companies that opted
    # into the public directory (public_listing) are publicly resolvable, under the shared tenant.
    company_row = db.execute(
        text(
            "SELECT id, name "
            "FROM companies "
            "WHERE UPPER(code) = UPPER(:slug) AND tenant_id = :saas "
            "AND public_listing = true AND is_active = true "
            "LIMIT 1"
        ),
        {"slug": slug, "saas": hc_shared_tenant_id()},
    ).fetchone()

    if company_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found.",
        )

    company_id = str(company_row[0])
    clinic_name = company_row[1]

    # Branches query — the Company's clinic sites (hc_branches.platform_company_id), public-visible only.
    branch_filter = "AND b.id = :bid" if branch_id else ""
    branch_params: dict = {"cid": company_id}
    if branch_id:
        branch_params["bid"] = branch_id

    branch_rows = db.execute(
        text(
            f"SELECT b.id, b.branch_name, b.address_city, b.address_street, "
            f"       b.contact_phone, b.online_booking "
            f"FROM hc_branches b "
            f"WHERE b.platform_company_id = :cid AND b.public_visible = true "
            f"AND b.deleted_at IS NULL AND b.status = 'active' "
            f"{branch_filter} "
            f"ORDER BY b.branch_name ASC"
        ),
        branch_params,
    ).fetchall()

    # Average rating (non-PHI aggregation) across the Company's branches
    rating_row = db.execute(
        text(
            "SELECT AVG(cr.rating) "
            "FROM hc_clinic_reviews cr "
            "JOIN hc_branches b ON cr.branch_id = b.id "
            "WHERE b.platform_company_id = :cid AND cr.status = 'approved'"
        ),
        {"cid": company_id},
    ).fetchone()
    avg_rating = float(rating_row[0]) if rating_row and rating_row[0] else None

    # Specialty tags (aggregate from appointment_types — non-PHI)
    tag_rows = db.execute(
        text(
            "SELECT DISTINCT elem "
            "FROM hc_branches b, "
            "     jsonb_array_elements_text(COALESCE(b.appointment_types, '[]'::jsonb)) AS elem "
            "WHERE b.platform_company_id = :cid AND b.deleted_at IS NULL"
        ),
        {"cid": company_id},
    ).fetchall()
    specialty_tags = [r[0] for r in tag_rows if r[0]]

    # Build branch details with providers (name + specialty ONLY — no PHI)
    branches: List[PublicBranchDetail] = []
    for br in branch_rows:
        br_id = str(br[0])

        # Providers: name + specialty only — explicitly exclude license_number and all PHI
        prov_rows = db.execute(
            text(
                "SELECT p.display_name, p.specialty "
                "FROM hc_providers p "
                "WHERE p.branch_id = :bid "
                "AND p.is_active = true "
                "ORDER BY p.display_name ASC"
            ),
            {"bid": br_id},
        ).fetchall()

        providers = [
            PublicProviderSummary(
                name=prov[0] or "",
                specialty=prov[1] or "",
            )
            for prov in prov_rows
        ]

        branches.append(
            PublicBranchDetail(
                branch_id=br_id,
                branch_name=br[1],
                address_city=br[2],
                address_street=br[3],
                contact_phone=br[4],
                online_booking=bool(br[5]),
                providers=providers,
            )
        )

    profile = ClinicPublicProfile(
        clinic_name=clinic_name,
        slug=slug,
        specialty_tags=specialty_tags,
        city=branches[0].address_city if branches else "",
        average_rating=avg_rating,
        branches=branches,
    )

    _profile_cache[slug] = (now, profile)
    return profile

# ---------------------------------------------------------------------------
# T-HC-PUBLIC-SLOTS — Available slots (PUBLIC, no auth required)
# GET /api/v1/public/clinics/{tenant_code}/branches/{branch_id}/slots?date=YYYY-MM-DD
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/public/clinics/{tenant_code}/branches/{branch_id}/slots",
    summary="List available slots for a branch (public, no auth)",
    tags=["healthcare-public"],
)
async def get_available_slots_public(
    tenant_code: str,
    branch_id: str,
    date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(_get_public_db),
):
    """
    Returns available appointment slots for a branch on a given date.
    No authentication required.
    Only returns slots with status='available'.
    """
    # Resolve the clinic by Company code (ADR-HC-010 D6 — the {tenant_code} path segment is now
    # the Company slug). Slots live on the shared SaaS tenant, isolated per clinic by the branch.
    company_row = db.execute(
        text(
            "SELECT id, tenant_id FROM companies "
            "WHERE UPPER(code) = UPPER(:code) AND tenant_id = :saas AND is_active = true LIMIT 1"
        ),
        {"code": tenant_code, "saas": hc_shared_tenant_id()},
    ).fetchone()
    if company_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found.",
        )
    company_id = str(company_row[0])
    tenant_id = str(company_row[1])

    # Verify the branch is one of that Company's clinic sites.
    branch_row = db.execute(
        text(
            "SELECT id FROM hc_branches "
            "WHERE id = :bid AND platform_company_id = :cid AND deleted_at IS NULL LIMIT 1"
        ),
        {"bid": branch_id, "cid": company_id},
    ).fetchone()
    if branch_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found.",
        )

    rows = db.execute(
        text(
            """
            SELECT
                s.id              AS id,
                p.display_name    AS provider_name,
                p.specialty       AS provider_specialty,
                s.start_time      AS start_time,
                s.end_time        AS end_time,
                s.appointment_type
            FROM hcs_appointment_slots s
            JOIN hc_providers p ON p.id = s.provider_id
            WHERE s.tenant_id = :tid
              AND s.branch_id  = :bid
              AND s.slot_date  = :dt
              AND s.status     = 'available'
            ORDER BY s.start_time
            """
        ),
        {"tid": tenant_id, "bid": branch_id, "dt": date},
    ).fetchall()

    return [
        {
            "id": str(row.id),
            "provider_name": row.provider_name or "",
            "provider_specialty": row.provider_specialty or "",
            "start_time": str(row.start_time),
            "end_time": str(row.end_time),
            "appointment_type": row.appointment_type,
        }
        for row in rows
    ]
