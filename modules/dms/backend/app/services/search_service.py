"""Full-text search over documents (E2).

Searches filename + tags + custom metadata (content/OCR extraction is deferred).
Ranked by ts_rank with an html <mark> snippet from ts_headline. Results are
ACL-filtered (a caller only sees documents they can at least *view*).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import Document
from .acl_service import AclService

# Cap the candidate set we rank+ACL-filter in one pass (MVP; tune if needed).
_CANDIDATE_CAP = 500

_SORTS = {
    "relevance": "rank DESC, created_at DESC",
    "name": "filename ASC",
    "date": "created_at DESC",
    "size": "size_bytes DESC",
}


class SearchService:
    @staticmethod
    async def search(
        db: AsyncSession, *, tenant_id: str, user_id: str, group_ids: List[str],
        is_admin: bool, q: Optional[str] = None, tag: Optional[str] = None,
        author: Optional[str] = None, content_type_prefix: Optional[str] = None,
        folder_id: Optional[str] = None, date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None, sort: str = "relevance",
        page: int = 1, page_size: int = 25,
    ) -> Tuple[List[Dict[str, Any]], int]:
        has_q = bool(q and q.strip())
        clauses = ["d.tenant_id = :tid", "d.is_active"]
        params: Dict[str, Any] = {"tid": tenant_id, "q": q or ""}
        if has_q:
            clauses.append("d.search_vector @@ query")
        if tag:
            clauses.append(":tag = ANY(d.tags)")
            params["tag"] = tag
        if author:
            clauses.append("d.uploaded_by = :author")
            params["author"] = author
        if content_type_prefix:
            clauses.append("d.content_type LIKE :ctype")
            params["ctype"] = content_type_prefix + "%"
        if folder_id:
            clauses.append("d.folder_id = :folder")
            params["folder"] = folder_id
        if date_from:
            clauses.append("d.created_at >= :dfrom")
            params["dfrom"] = date_from
        if date_to:
            clauses.append("d.created_at <= :dto")
            params["dto"] = date_to

        order = _SORTS.get(sort, _SORTS["relevance"])
        if sort == "relevance" and not has_q:
            order = _SORTS["date"]  # rank is 0 without a query

        sql = text(
            f"""
            SELECT d.id,
                   ts_rank(d.search_vector, query) AS rank,
                   ts_headline('english',
                       coalesce(d.filename,'') || ' ' || coalesce(array_to_string(d.tags,' '),''),
                       query,
                       'StartSel=<mark>,StopSel=</mark>,MaxWords=12,MinWords=3,ShortWord=2') AS snippet
            FROM dms_documents d, plainto_tsquery('english', :q) query
            WHERE {' AND '.join(clauses)}
            ORDER BY {order}
            LIMIT :cap
            """
        )
        params["cap"] = _CANDIDATE_CAP
        rows = (await db.execute(sql, params)).mappings().all()
        if not rows:
            return [], 0

        # Preserve ranked order while loading the ORM rows for ACL checks.
        order_index = {str(r["id"]): i for i, r in enumerate(rows)}
        meta = {str(r["id"]): r for r in rows}
        docs = (
            await db.execute(
                select(Document).where(Document.id.in_(list(order_index.keys())))
            )
        ).scalars().all()
        docs.sort(key=lambda d: order_index.get(str(d.id), 1 << 30))

        visible: List[Document] = []
        for d in docs:
            if await AclService.authorize_document(
                db, tenant_id=tenant_id, user_id=user_id, group_ids=group_ids,
                is_admin=is_admin, document=d, need="view",
            ):
                visible.append(d)

        total = len(visible)
        start = (page - 1) * page_size
        page_docs = visible[start:start + page_size]

        results: List[Dict[str, Any]] = []
        for d in page_docs:
            m = meta[str(d.id)]
            results.append({
                "id": d.id, "filename": d.filename, "folder_id": d.folder_id,
                "content_type": d.content_type, "size_bytes": d.size_bytes,
                "current_version": d.current_version, "tags": list(d.tags or []),
                "metadata": dict(d.doc_metadata or {}), "is_private": d.is_private,
                "uploaded_by": d.uploaded_by, "created_at": d.created_at,
                "updated_at": d.updated_at, "rank": float(m["rank"] or 0.0),
                "snippet": m["snippet"] if has_q else None,
            })
        return results, total
