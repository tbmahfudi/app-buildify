"""
backend/app/core/tenant/module_db_provisioner.py
Per-tenant module database provisioner -- Epic 22, Feature 22.5, T-22.013.

NFR: provisioning must complete in <= 60 seconds (arch-22 section 9).

Responsibilities:
  * provision()    -- CREATE DATABASE, run Alembic migrations, persist row to
                      tenant_module_databases, update status to ready.
  * deprovision()  -- SET status=deprovisioning, DROP DATABASE, SET status=deprovisioned.

connection_secret_ref format (dev): env:MODULE_DB_{DB_NAME_UPPER}
In production this would be a Vault path or AWS Secrets Manager ARN.
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.tenant_module_database import TenantModuleDatabase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module registry: path to each module Alembic root.
# Extend when adding new tenant-scoped modules.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[5]  # app-buildify/

MODULE_ALEMBIC_DIRS: dict[str, Path] = {
    "financial": _REPO_ROOT / "modules" / "financial" / "backend",
    "healthcare": _REPO_ROOT / "modules" / "healthcare" / "backend",
}


def _get_postgres_admin_url() -> str:
    """Return a PostgreSQL DSN for admin commands, pointing at the postgres DB."""
    url = os.environ.get(
        "DATABASE_URL",
        os.environ.get(
            "SQLALCHEMY_DATABASE_URL",
            "postgresql://appuser:apppass@localhost:5432/appdb",
        ),
    )
    base = url.rsplit("/", 1)[0]
    return f"{base}/postgres"


class ModuleDBProvisioner:
    """Provisions and deprovisions per-tenant module databases.

    NFR: provisioning must complete in <= 60 seconds (arch-22 section 9).

    Usage::

        provisioner = ModuleDBProvisioner()
        secret_ref = await provisioner.provision(tenant_id, "financial")
        await provisioner.deprovision(tenant_id, "financial")

    The async methods delegate to synchronous implementations so they can be
    called from FastAPI background tasks without requiring asyncpg at this layer.
    """

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    async def provision(self, tenant_id: UUID, module_name: str) -> str:
        """Provision a per-tenant module database.

        Steps:
            1. Generate db_name: mod_{module_name}_{str(tenant_id)[:8]}
            2. INSERT tenant_module_databases row (status=provisioning).
               UNIQUE constraint prevents double-provisioning.
            3. CREATE DATABASE {db_name}.
            4. Run module Alembic migrations.
            5. Persist connection_secret_ref and set status=ready.

        Returns:
            connection_secret_ref e.g. env:MODULE_DB_MOD_FINANCIAL_A1B2C3D4.

        Raises:
            ValueError:   if module_name is unknown.
            RuntimeError: if CREATE DATABASE or migrations fail.
        """
        return self._provision_sync(tenant_id, module_name)

    async def deprovision(self, tenant_id: UUID, module_name: str) -> None:
        """Deprovision a per-tenant module database.

        Steps:
            1. Set status to deprovisioning.
            2. DROP DATABASE {db_name}.
            3. Set status to deprovisioned.

        Raises:
            ValueError:   if module_name is unknown.
            RuntimeError: if DROP DATABASE fails.
        """
        self._deprovision_sync(tenant_id, module_name)

    # -------------------------------------------------------------------
    # Synchronous implementation
    # -------------------------------------------------------------------

    def _provision_sync(self, tenant_id: UUID, module_name: str) -> str:
        """Synchronous implementation of provision()."""
        t_start = time.monotonic()
        db_name = self._make_db_name(tenant_id, module_name)
        connection_secret_ref = f"env:MODULE_DB_{db_name.upper()}"

        logger.info(
            "provisioner.provision.start tenant_id=%s module=%s db_name=%s",
            tenant_id, module_name, db_name,
        )

        db: Session = SessionLocal()
        row: Optional[TenantModuleDatabase] = None
        try:
            # Step 1: insert row in provisioning state (idempotent guard).
            row = TenantModuleDatabase(
                tenant_id=tenant_id,
                module_id=self._module_uuid(module_name),
                db_name=db_name,
                status="provisioning",
            )
            db.add(row)
            try:
                db.commit()
                db.refresh(row)
            except IntegrityError:
                # Row already exists -- idempotent; fetch it.
                db.rollback()
                row = (
                    db.query(TenantModuleDatabase)
                    .filter_by(tenant_id=tenant_id, db_name=db_name)
                    .one()
                )
                if row.status == "ready":
                    logger.info(
                        "provisioner.provision.already_ready db_name=%s", db_name
                    )
                    return row.connection_secret_ref or connection_secret_ref
                row.status = "provisioning"
                row.error_message = None
                db.commit()

            # Step 2: CREATE DATABASE.
            self._create_database(db_name)
            logger.info("provisioner.create_database.ok db_name=%s", db_name)

            # Step 3: Run Alembic migrations.
            self._run_migrations(module_name, db_name)
            logger.info("provisioner.migrations.ok db_name=%s", db_name)

            # Step 4: Persist secret ref and mark ready.
            row.connection_secret_ref = connection_secret_ref
            row.status = "ready"
            row.error_message = None
            db.commit()

            elapsed = time.monotonic() - t_start
            logger.info(
                "provisioner.provision.done db_name=%s elapsed_s=%.2f gate=%s",
                db_name, elapsed, "PASS" if elapsed <= 60 else "FAIL",
            )
            return connection_secret_ref

        except Exception as exc:
            elapsed = time.monotonic() - t_start
            logger.error(
                "provisioner.provision.failed db_name=%s elapsed_s=%.2f error=%s",
                db_name, elapsed, exc, exc_info=True,
            )
            if row is not None:
                try:
                    row.status = "failed"
                    row.error_message = str(exc)
                    db.commit()
                except Exception:
                    db.rollback()
            raise RuntimeError(
                f"Provisioning failed for {db_name} after {elapsed:.2f}s: {exc}"
            ) from exc
        finally:
            db.close()

    def _deprovision_sync(self, tenant_id: UUID, module_name: str) -> None:
        """Synchronous implementation of deprovision()."""
        db_name = self._make_db_name(tenant_id, module_name)
        logger.info(
            "provisioner.deprovision.start tenant_id=%s module=%s db_name=%s",
            tenant_id, module_name, db_name,
        )

        db: Session = SessionLocal()
        try:
            row = (
                db.query(TenantModuleDatabase)
                .filter_by(tenant_id=tenant_id, db_name=db_name)
                .one_or_none()
            )

            # Step 1: mark deprovisioning.
            if row is not None:
                row.status = "deprovisioning"
                db.commit()

            # Step 2: DROP DATABASE.
            self._drop_database(db_name)
            logger.info("provisioner.drop_database.ok db_name=%s", db_name)

            # Step 3: mark deprovisioned.
            if row is not None:
                row.status = "deprovisioned"
                db.commit()

            logger.info(
                "provisioner.deprovision.done tenant_id=%s db_name=%s",
                tenant_id, db_name,
            )
        except Exception as exc:
            logger.error(
                "provisioner.deprovision.failed db_name=%s error=%s", db_name, exc,
                exc_info=True,
            )
            db.rollback()
            raise RuntimeError(f"Deprovision failed for {db_name}: {exc}") from exc
        finally:
            db.close()

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _make_db_name(tenant_id: UUID, module_name: str) -> str:
        """Generate a deterministic Postgres-safe database name.

        Format: mod_{module_name}_{first 8 hex chars of tenant_id}
        Example: mod_financial_a1b2c3d4
        """
        short_id = str(tenant_id).replace("-", "")[:8]
        return f"mod_{module_name}_{short_id}"

    @staticmethod
    def _module_uuid(module_name: str) -> UUID:
        """Return a stable UUID-v5 for the module name.

        In production this would be a lookup against the modules table.
        For the prototype we derive a stable UUID from the name.
        """
        import uuid
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"module.{module_name}")

    @staticmethod
    def _build_admin_url() -> str:
        """Return the admin DSN with psql-compatible prefix."""
        raw = _get_postgres_admin_url()
        for prefix in ("postgresql+psycopg2://", "postgresql+asyncpg://"):
            if raw.startswith(prefix):
                raw = "postgresql://" + raw[len(prefix):]
                break
        return raw

    def _create_database(self, db_name: str) -> None:
        """Create the module database using psycopg2 (prefers) or psql (fallback)."""
        try:
            import psycopg2
            import psycopg2.errors  # noqa: F401
            admin_url = _get_postgres_admin_url()
            for prefix in ("postgresql+psycopg2://", "postgresql+asyncpg://"):
                if admin_url.startswith(prefix):
                    admin_url = "postgresql://" + admin_url[len(prefix):]
                    break
            conn = psycopg2.connect(admin_url)
            conn.autocommit = True
            cur = conn.cursor()
            try:
                cur.execute(f'CREATE DATABASE "{db_name}"')
            except Exception as exc:
                if "already exists" in str(exc):
                    logger.info(
                        "provisioner.create_database.already_exists db_name=%s", db_name
                    )
                else:
                    raise
            finally:
                conn.close()
        except ImportError:
            # psql CLI fallback.
            admin_url = self._build_admin_url()
            base = admin_url.rsplit("/", 1)[0]
            result = subprocess.run(
                ["psql", f"{base}/postgres", "-c", f'CREATE DATABASE "{db_name}"'],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0 and "already exists" not in result.stderr:
                raise RuntimeError(
                    f"CREATE DATABASE failed: {result.stderr.strip()}"
                )

    def _drop_database(self, db_name: str) -> None:
        """DROP DATABASE IF EXISTS, terminating active connections first."""
        try:
            import psycopg2
            admin_url = _get_postgres_admin_url()
            for prefix in ("postgresql+psycopg2://", "postgresql+asyncpg://"):
                if admin_url.startswith(prefix):
                    admin_url = "postgresql://" + admin_url[len(prefix):]
                    break
            conn = psycopg2.connect(admin_url)
            conn.autocommit = True
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()",
                    (db_name,),
                )
                cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            finally:
                conn.close()
        except ImportError:
            admin_url = self._build_admin_url()
            base = admin_url.rsplit("/", 1)[0]
            subprocess.run(
                ["psql", f"{base}/postgres", "-c",
                 f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                 f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid();"],
                capture_output=True, text=True, timeout=30,
            )
            result = subprocess.run(
                ["psql", f"{base}/postgres", "-c", f'DROP DATABASE IF EXISTS "{db_name}"'],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"DROP DATABASE failed: {result.stderr.strip()}")

    def _run_migrations(self, module_name: str, db_name: str) -> None:
        """Run alembic upgrade head for the module against the new database.

        DATABASE_URL env var is overridden to point at the new DB.
        Timeout is 55 s to stay within the 60 s NFR (arch-22 section 9).
        """
        module_dir = MODULE_ALEMBIC_DIRS.get(module_name)
        if module_dir is None:
            raise ValueError(
                f"Unknown module {module_name!r}. Known: {sorted(MODULE_ALEMBIC_DIRS)}"
            )
        if not module_dir.exists():
            raise ValueError(
                f"Module directory for {module_name!r} not found: {module_dir}"
            )

        admin_url = _get_postgres_admin_url()
        base = admin_url.rsplit("/", 1)[0]
        # Restore psycopg2 prefix for the module DB DSN.
        if "postgresql://" in base and "+psycopg2" not in base and "+asyncpg" not in base:
            base = base.replace("postgresql://", "postgresql+psycopg2://", 1)
        module_db_url = f"{base}/{db_name}"

        env = {
            **os.environ,
            "DATABASE_URL": module_db_url,
            "SQLALCHEMY_DATABASE_URL": module_db_url,
        }

        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            capture_output=True, text=True,
            timeout=55,  # 5 s headroom before the 60 s NFR boundary.
            cwd=str(module_dir),
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Alembic migrations failed for {module_name!r} against {db_name!r}:\n"
                f"{result.stderr}"
            )
        logger.debug(
            "provisioner.migrations.output module=%s db_name=%s stdout=%s",
            module_name, db_name, result.stdout[:500],
        )
