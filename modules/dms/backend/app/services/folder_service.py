"""Folder business logic (E1 F1.3): nested, tenant-scoped folders."""

import uuid
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import Document
from ..models.folder import Folder


class FolderError(Exception):
    """Raised for folder rule violations (mapped to HTTP 4xx by the router)."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class FolderService:
    @staticmethod
    async def get(db: AsyncSession, *, tenant_id: str, folder_id: str) -> Optional[Folder]:
        return await db.scalar(
            select(Folder).where(
                Folder.id == folder_id,
                Folder.tenant_id == tenant_id,
                Folder.is_active.is_(True),
            )
        )

    @staticmethod
    async def _require(db: AsyncSession, *, tenant_id: str, folder_id: str) -> Folder:
        folder = await FolderService.get(db, tenant_id=tenant_id, folder_id=folder_id)
        if not folder:
            raise FolderError("Folder not found", 404)
        return folder

    @staticmethod
    async def create(
        db: AsyncSession, *, tenant_id: str, user_id: Optional[str], name: str,
        parent_id: Optional[str],
    ) -> Folder:
        if parent_id is not None:
            await FolderService._require(db, tenant_id=tenant_id, folder_id=parent_id)
        folder = Folder(
            id=uuid.uuid4(), tenant_id=tenant_id, name=name.strip(),
            parent_id=parent_id, created_by=user_id, is_active=True,
        )
        db.add(folder)
        try:
            await db.flush()
        except IntegrityError:
            raise FolderError("A folder with that name already exists here", 409)
        return folder

    @staticmethod
    async def list(
        db: AsyncSession, *, tenant_id: str, parent_id: Optional[str]
    ) -> List[Folder]:
        cond = and_(
            Folder.tenant_id == tenant_id,
            Folder.is_active.is_(True),
            Folder.parent_id == parent_id if parent_id is not None
            else Folder.parent_id.is_(None),
        )
        rows = (
            await db.execute(select(Folder).where(cond).order_by(Folder.name))
        ).scalars().all()
        return list(rows)

    @staticmethod
    async def rename(
        db: AsyncSession, *, tenant_id: str, folder_id: str, name: str
    ) -> Folder:
        folder = await FolderService._require(db, tenant_id=tenant_id, folder_id=folder_id)
        folder.name = name.strip()
        try:
            await db.flush()
        except IntegrityError:
            raise FolderError("A folder with that name already exists here", 409)
        return folder

    @staticmethod
    async def _is_descendant(
        db: AsyncSession, *, tenant_id: str, folder_id: str, maybe_ancestor_id: str
    ) -> bool:
        """True if maybe_ancestor_id is folder_id or one of its ancestors."""
        cur: Optional[str] = maybe_ancestor_id
        seen = set()
        while cur is not None and cur not in seen:
            if str(cur) == str(folder_id):
                return True
            seen.add(cur)
            row = await db.scalar(
                select(Folder.parent_id).where(
                    Folder.id == cur, Folder.tenant_id == tenant_id
                )
            )
            cur = str(row) if row else None
        return False

    @staticmethod
    async def move(
        db: AsyncSession, *, tenant_id: str, folder_id: str, new_parent_id: Optional[str]
    ) -> Folder:
        folder = await FolderService._require(db, tenant_id=tenant_id, folder_id=folder_id)
        if new_parent_id is not None:
            await FolderService._require(db, tenant_id=tenant_id, folder_id=new_parent_id)
            # A folder cannot become its own descendant's child.
            if await FolderService._is_descendant(
                db, tenant_id=tenant_id, folder_id=folder_id, maybe_ancestor_id=new_parent_id
            ):
                raise FolderError("Cannot move a folder into itself or its descendant", 400)
        folder.parent_id = new_parent_id
        try:
            await db.flush()
        except IntegrityError:
            raise FolderError("A folder with that name already exists there", 409)
        return folder

    @staticmethod
    async def delete(db: AsyncSession, *, tenant_id: str, folder_id: str) -> None:
        folder = await FolderService._require(db, tenant_id=tenant_id, folder_id=folder_id)
        # Only empty folders may be deleted (no active subfolders or documents).
        child_folders = await db.scalar(
            select(func.count()).select_from(Folder).where(
                Folder.tenant_id == tenant_id,
                Folder.parent_id == folder_id,
                Folder.is_active.is_(True),
            )
        )
        child_docs = await db.scalar(
            select(func.count()).select_from(Document).where(
                Document.tenant_id == tenant_id,
                Document.folder_id == folder_id,
                Document.is_active.is_(True),
            )
        )
        if (child_folders or 0) > 0 or (child_docs or 0) > 0:
            raise FolderError("Folder is not empty", 409)
        folder.is_active = False
        await db.flush()
