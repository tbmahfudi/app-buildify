"""Search endpoint — mounted at {API_PREFIX}/search (E2).

Full-text + filtered search over documents the caller may view. Gated by
dms:document:read:company; ACL visibility is applied on top.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import Principal, require_permission, tenant_session
from ..models.saved_search import DmsSavedSearch
from ..schemas.search import (
    SavedSearchCreate,
    SavedSearchListResponse,
    SavedSearchResponse,
    SearchResponse,
    SearchResult,
)
from ..services.acl_service import AclService
from ..services.search_service import SearchService

router = APIRouter()

_READ = require_permission("dms:document:read:company")


@router.get("", response_model=SearchResponse)
async def search(
    q: Optional[str] = Query(None, description="Full-text query (filename, tags, metadata)"),
    tag: Optional[str] = Query(None, description="Match a single tag exactly"),
    author: Optional[str] = Query(None, description="uploaded_by user id"),
    type: Optional[str] = Query(None, description="content-type prefix, e.g. 'image/' or 'application/pdf'"),
    folder_id: Optional[str] = Query(None, description="Scope to a folder"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort: str = Query("relevance", pattern="^(relevance|name|date|size)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    is_admin = principal.has_permission("dms:document:delete:company")
    results, total = await SearchService.search(
        db, tenant_id=principal.tenant_id, user_id=principal.user_id,
        group_ids=group_ids, is_admin=is_admin, q=q, tag=tag, author=author,
        content_type_prefix=type, folder_id=folder_id, date_from=date_from,
        date_to=date_to, sort=sort, page=page, page_size=page_size,
    )
    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        total=total, page=page, page_size=page_size,
    )


# --- saved searches (per user) ----------------------------------------------
@router.get("/saved", response_model=SavedSearchListResponse)
async def list_saved(
    principal: Principal = Depends(_READ),
    db: AsyncSession = Depends(tenant_session),
):
    rows = (
        await db.execute(
            select(DmsSavedSearch).where(
                DmsSavedSearch.tenant_id == principal.tenant_id,
                DmsSavedSearch.user_id == principal.user_id,
            ).order_by(DmsSavedSearch.created_at.desc())
        )
    ).scalars().all()
    return SavedSearchListResponse(saved=[SavedSearchResponse.model_validate(r) for r in rows])


@router.post("/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved(
    body: SavedSearchCreate,
    principal: Principal = Depends(_READ),
    db: AsyncSession = Depends(tenant_session),
):
    row = DmsSavedSearch(
        id=uuid.uuid4(), tenant_id=principal.tenant_id, user_id=principal.user_id,
        name=body.name.strip(), params=body.params or {},
    )
    db.add(row)
    await db.flush()
    return SavedSearchResponse.model_validate(row)


@router.delete("/saved/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved(
    saved_id: str,
    principal: Principal = Depends(_READ),
    db: AsyncSession = Depends(tenant_session),
):
    row = await db.scalar(
        select(DmsSavedSearch).where(
            DmsSavedSearch.id == saved_id,
            DmsSavedSearch.tenant_id == principal.tenant_id,
            DmsSavedSearch.user_id == principal.user_id,
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Saved search not found")
    await db.delete(row)
    await db.flush()
