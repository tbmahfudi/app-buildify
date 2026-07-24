"""Row-level ACLs (E3): privacy flags, grants, inheritance and resolution.

Model: **default-open**. A folder/document is reachable by anyone holding the
coarse RBAC permission *unless* it — or any ancestor folder — is marked private.
For a restricted resource, access requires one of:
  - being the document owner (uploaded_by), or
  - holding the resource-type admin permission (checked by the caller), or
  - an ACL grant (view/edit/manage) to the user or one of their groups, on the
    document or any ancestor folder (grants inherit down the tree).

Capabilities are ordered view < edit < manage; a grant confers itself and below.
"""

from typing import List, Optional, Set

from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.acl import CAPABILITY_RANK, DmsAcl
from ..models.document import Document
from ..models.folder import Folder

VALID_RESOURCE_TYPES = {"folder", "document"}
VALID_PRINCIPAL_TYPES = {"user", "group"}
VALID_CAPABILITIES = set(CAPABILITY_RANK)


class AclError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class AclService:
    # -- helpers -------------------------------------------------------------
    @staticmethod
    async def user_group_ids(db: AsyncSession, user_id: str) -> List[str]:
        """The caller's group ids, read from the shared platform table."""
        rows = await db.execute(
            text("SELECT group_id FROM user_groups WHERE user_id = :uid"),
            {"uid": str(user_id)},
        )
        return [str(r[0]) for r in rows.fetchall()]

    @staticmethod
    async def ancestor_folder_ids(
        db: AsyncSession, *, tenant_id: str, folder_id: Optional[str]
    ) -> List[str]:
        """folder_id and every ancestor up to the root (self-first)."""
        out: List[str] = []
        seen: Set[str] = set()
        cur = folder_id
        while cur and str(cur) not in seen:
            seen.add(str(cur))
            out.append(str(cur))
            cur = await db.scalar(
                select(Folder.parent_id).where(
                    Folder.id == cur, Folder.tenant_id == tenant_id
                )
            )
            cur = str(cur) if cur else None
        return out

    @staticmethod
    async def _any_private(
        db: AsyncSession, *, tenant_id: str, folder_ids: List[str]
    ) -> bool:
        if not folder_ids:
            return False
        found = await db.scalar(
            select(Folder.id).where(
                Folder.tenant_id == tenant_id,
                Folder.id.in_(folder_ids),
                Folder.is_private.is_(True),
            ).limit(1)
        )
        return found is not None

    # -- resolution ----------------------------------------------------------
    @staticmethod
    async def is_restricted(
        db: AsyncSession, *, tenant_id: str, document: Document
    ) -> bool:
        if document.is_private:
            return True
        ancestors = await AclService.ancestor_folder_ids(
            db, tenant_id=tenant_id, folder_id=str(document.folder_id) if document.folder_id else None
        )
        return await AclService._any_private(db, tenant_id=tenant_id, folder_ids=ancestors)

    @staticmethod
    async def effective_capability(
        db: AsyncSession, *, tenant_id: str, user_id: str, group_ids: List[str],
        document: Document,
    ) -> Optional[str]:
        """Highest capability the principal has on the document via ACLs (self +
        inherited from ancestor folders), or None. Owner is handled by callers."""
        ancestors = await AclService.ancestor_folder_ids(
            db, tenant_id=tenant_id, folder_id=str(document.folder_id) if document.folder_id else None
        )
        principal_clauses = [and_(DmsAcl.principal_type == "user", DmsAcl.principal_id == user_id)]
        if group_ids:
            principal_clauses.append(
                and_(DmsAcl.principal_type == "group", DmsAcl.principal_id.in_(group_ids))
            )
        resource_clauses = [and_(DmsAcl.resource_type == "document", DmsAcl.resource_id == document.id)]
        if ancestors:
            resource_clauses.append(
                and_(DmsAcl.resource_type == "folder", DmsAcl.resource_id.in_(ancestors))
            )
        rows = (
            await db.execute(
                select(DmsAcl.capability).where(
                    DmsAcl.tenant_id == tenant_id,
                    or_(*resource_clauses),
                    or_(*principal_clauses),
                )
            )
        ).scalars().all()
        best = 0
        for cap in rows:
            best = max(best, CAPABILITY_RANK.get(cap, 0))
        if best == 0:
            return None
        return next(c for c, r in CAPABILITY_RANK.items() if r == best)

    @staticmethod
    async def authorize_document(
        db: AsyncSession, *, tenant_id: str, user_id: str, group_ids: List[str],
        is_admin: bool, document: Document, need: str,
    ) -> bool:
        """Whether the principal may perform an action needing `need` capability."""
        if not await AclService.is_restricted(db, tenant_id=tenant_id, document=document):
            return True  # not private -> coarse RBAC (already checked) governs
        if is_admin:
            return True
        if document.uploaded_by and str(document.uploaded_by) == str(user_id):
            return True
        cap = await AclService.effective_capability(
            db, tenant_id=tenant_id, user_id=user_id, group_ids=group_ids, document=document
        )
        if not cap:
            return False
        return CAPABILITY_RANK[cap] >= CAPABILITY_RANK[need]

    @staticmethod
    async def authorize_folder(
        db: AsyncSession, *, tenant_id: str, user_id: str, group_ids: List[str],
        is_admin: bool, folder_id: Optional[str], need: str,
    ) -> bool:
        """Whether the principal may act (needing `need`) on/within a folder.

        Root (folder_id is None) is never private. A folder is restricted if it
        or an ancestor is private; then owner(created_by)/admin/ACL grant applies.
        """
        if folder_id is None:
            return True
        ancestors = await AclService.ancestor_folder_ids(
            db, tenant_id=tenant_id, folder_id=folder_id
        )
        if not await AclService._any_private(db, tenant_id=tenant_id, folder_ids=ancestors):
            return True
        if is_admin:
            return True
        folder = await db.scalar(
            select(Folder).where(Folder.id == folder_id, Folder.tenant_id == tenant_id)
        )
        if folder is not None and folder.created_by and str(folder.created_by) == str(user_id):
            return True
        # Grants on this folder or any ancestor, to the user or a group.
        principal_clauses = [and_(DmsAcl.principal_type == "user", DmsAcl.principal_id == user_id)]
        if group_ids:
            principal_clauses.append(
                and_(DmsAcl.principal_type == "group", DmsAcl.principal_id.in_(group_ids))
            )
        rows = (
            await db.execute(
                select(DmsAcl.capability).where(
                    DmsAcl.tenant_id == tenant_id,
                    DmsAcl.resource_type == "folder",
                    DmsAcl.resource_id.in_(ancestors),
                    or_(*principal_clauses),
                )
            )
        ).scalars().all()
        best = max((CAPABILITY_RANK.get(c, 0) for c in rows), default=0)
        return best >= CAPABILITY_RANK[need]

    # -- management ----------------------------------------------------------
    @staticmethod
    async def set_privacy(
        db: AsyncSession, *, tenant_id: str, resource_type: str, resource_id: str,
        is_private: bool,
    ) -> None:
        if resource_type == "folder":
            obj = await db.scalar(
                select(Folder).where(Folder.id == resource_id, Folder.tenant_id == tenant_id,
                                     Folder.is_active.is_(True))
            )
        elif resource_type == "document":
            obj = await db.scalar(
                select(Document).where(Document.id == resource_id, Document.tenant_id == tenant_id,
                                       Document.is_active.is_(True))
            )
        else:
            raise AclError("Invalid resource type", 400)
        if not obj:
            raise AclError(f"{resource_type.title()} not found", 404)
        obj.is_private = is_private
        await db.flush()

    @staticmethod
    async def grant(
        db: AsyncSession, *, tenant_id: str, created_by: Optional[str], resource_type: str,
        resource_id: str, principal_type: str, principal_id: str, capability: str,
    ) -> DmsAcl:
        if resource_type not in VALID_RESOURCE_TYPES:
            raise AclError("Invalid resource type", 400)
        if principal_type not in VALID_PRINCIPAL_TYPES:
            raise AclError("Invalid principal type", 400)
        if capability not in VALID_CAPABILITIES:
            raise AclError("Invalid capability", 400)
        existing = await db.scalar(
            select(DmsAcl).where(
                DmsAcl.tenant_id == tenant_id,
                DmsAcl.resource_type == resource_type,
                DmsAcl.resource_id == resource_id,
                DmsAcl.principal_type == principal_type,
                DmsAcl.principal_id == principal_id,
            )
        )
        if existing:
            existing.capability = capability
            await db.flush()
            return existing
        import uuid
        acl = DmsAcl(
            id=uuid.uuid4(), tenant_id=tenant_id, resource_type=resource_type,
            resource_id=resource_id, principal_type=principal_type,
            principal_id=principal_id, capability=capability, created_by=created_by,
        )
        db.add(acl)
        await db.flush()
        return acl

    @staticmethod
    async def revoke(db: AsyncSession, *, tenant_id: str, acl_id: str) -> bool:
        acl = await db.scalar(
            select(DmsAcl).where(DmsAcl.id == acl_id, DmsAcl.tenant_id == tenant_id)
        )
        if not acl:
            return False
        await db.delete(acl)
        await db.flush()
        return True

    @staticmethod
    async def list_for_resource(
        db: AsyncSession, *, tenant_id: str, resource_type: str, resource_id: str
    ) -> List[DmsAcl]:
        rows = (
            await db.execute(
                select(DmsAcl).where(
                    DmsAcl.tenant_id == tenant_id,
                    DmsAcl.resource_type == resource_type,
                    DmsAcl.resource_id == resource_id,
                ).order_by(DmsAcl.created_at)
            )
        ).scalars().all()
        return list(rows)
