"""Async database layer for the DMS module.

Tenant isolation is enforced at the database via Postgres Row-Level Security.
Every request opens a transaction and sets the `app.tenant_id` GUC (matching the
platform convention used by the healthcare module); the RLS policies in
dms_001_base_tables then filter every row to the caller's tenant.
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from ..config import settings

# asyncpg driver
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_tenant_db(tenant_id: str) -> AsyncGenerator[AsyncSession, None]:
    """Yield a tenant-scoped session with the RLS GUC set for the transaction.

    Not a FastAPI dependency directly — call it from `tenant_session()` in
    security.py which resolves `tenant_id` from the authenticated principal.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tid, true)"),
                {"tid": str(tenant_id)},
            )
            yield session


async def get_untenanted_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session with NO tenant GUC — for cross-tenant lookups by an
    unguessable key (public share tokens), where the tenant is unknown until the
    row is found. Callers MUST scope every subsequent query by the tenant_id they
    read from that first row. RLS is bypassed by the DMS DB role anyway, so the
    code-level tenant filter is the real guard (see tenant_isolation notes).
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
