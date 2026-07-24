"""Search endpoint — mounted at {API_PREFIX}/search (E2).

Full-text + filtered search over documents the caller may view. Gated by
dms:document:read:company; ACL visibility is applied on top.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import Principal, require_permission, tenant_session
from ..schemas.search import SearchResponse, SearchResult
from ..services.acl_service import AclService
from ..services.search_service import SearchService

router = APIRouter()


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
