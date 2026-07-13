"""TenantModuleDatabase SQLAlchemy ORM model -- Epic 22.4.1 (TD-3)

Table created by migration pg_tenant_module_databases.py.
FK and CHECK constraints added by pg_tenant_module_db_constraints.py (TD-1/TD-2).

NOT marked __tenant_scoped__ -- provisioning and cleanup scripts need
cross-tenant visibility via with_admin_cross_tenant_scope().
"""

from sqlalchemy import Column, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from .base import GUID, Base, generate_uuid


class TenantModuleDatabase(Base):
    """
    Registry of per-tenant per-module physical databases.

    One row per (tenant, module) pair. Created when a tenant enables a
    module that uses DATABASE_STRATEGY=per_tenant. Lifecycle managed by
    the provisioning service (T-22.013/T-22.014) and cleanup service
    (T-22.018/T-22.019).
    """

    __tablename__ = "tenant_module_databases"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Tenant reference (FK enforced by pg_tenant_module_db_constraints migration)
    tenant_id = Column(GUID, nullable=False)

    # Module reference (FK enforced by pg_tenant_module_db_constraints migration)
    module_id = Column(GUID, nullable=False)

    # Physical database name, e.g. "{tenant_id}_{module_id}"
    db_name = Column(String(255), nullable=False)

    # Secrets-manager reference -- never a raw DSN.
    # Supported formats:
    #   vault:<path>
    #   env:<VAR_NAME>
    #   arn:aws:secretsmanager:<region>:<account>:secret:<name>
    connection_secret_ref = Column(Text, nullable=True)

    # Lifecycle status -- values enforced by CHECK constraint in migration TD-2.
    # Valid values: provisioning | ready | failed | archived
    status = Column(String(30), nullable=False, server_default="provisioning")

    # Populated when status=failed; cleared on successful retry.
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "module_id",
            name="uq_tenant_module_databases_tenant_module",
        ),
        Index("ix_tenant_module_databases_tenant_id", "tenant_id"),
        Index("ix_tenant_module_databases_module_id", "module_id"),
    )
