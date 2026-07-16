"""
Seed script: provision a shared_saas module's declared end-user RBAC (ADR-012 D4).

Reads the module's manifest, and if it declares ``tenancy.mode = shared_saas``, creates
the declared end-user role + group **in the shared SaaS tenant** (plus any declared
permissions, which must be namespaced to the module). Idempotent and additive: re-running
is a no-op, and the legacy per-clinic groups/roles are never touched (D6).

**This command is the source of truth** for provisioning, not the ``post_install`` hook
(ADR-012 Resolution Q2). The hook fires only from ``POST /modules/register``, swallows its
own failures, and runs with an unscoped session — so it calls this best-effort, while the
command is what an operator can run deterministically and re-run safely.

Run inside the container:
    docker exec app_buildify_backend python3 /app/scripts/seed_module_rbac.py healthcare

All shared_saas modules at once:
    docker exec app_buildify_backend python3 /app/scripts/seed_module_rbac.py --all

Dry run (report what would change, write nothing):
    docker exec app_buildify_backend python3 /app/scripts/seed_module_rbac.py --all --dry-run
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.module_system.tenancy import is_shared_saas, validate_tenancy_block  # noqa: E402
from app.services.module_rbac_service import provision_end_user_rbac  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_module_rbac")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    os.environ.get(
        "SQLALCHEMY_DATABASE_URL",
        "postgresql+psycopg2://appuser:apppass@localhost:5432/appdb",
    ),
)

# /app/modules in the container; ../../modules from this file in a checkout.
_MODULES_ROOT = Path(
    os.environ.get("MODULES_ROOT")
    or (Path("/modules") if Path("/modules").is_dir() else Path(__file__).resolve().parents[2] / "modules")
)


def _load_manifest(module_name: str) -> dict:
    path = _MODULES_ROOT / module_name / "manifest.json"
    if not path.is_file():
        raise SystemExit(f"manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _discover_modules() -> list:
    if not _MODULES_ROOT.is_dir():
        raise SystemExit(f"modules root not found: {_MODULES_ROOT}")
    return sorted(p.name for p in _MODULES_ROOT.iterdir() if (p / "manifest.json").is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision module end-user RBAC (ADR-012 D4)")
    parser.add_argument("module", nargs="?", help="Module name (e.g. healthcare)")
    parser.add_argument("--all", action="store_true", help="Every shared_saas module found")
    parser.add_argument("--dry-run", action="store_true", help="Report only; write nothing")
    args = parser.parse_args()

    if not args.module and not args.all:
        parser.error("give a module name or --all")

    names = _discover_modules() if args.all else [args.module]

    engine = create_engine(DATABASE_URL)
    session = sessionmaker(bind=engine)()
    exit_code = 0
    try:
        for name in names:
            manifest = _load_manifest(name)

            # Refuse to provision from a manifest that would be rejected at registration:
            # the namespace rule is what stops a module granting its end users someone
            # else's permissions, and this path writes RBAC directly.
            errors = validate_tenancy_block(manifest)
            if errors:
                logger.error("%s: invalid tenancy block -- refusing to provision:", name)
                for e in errors:
                    logger.error("  - %s", e)
                exit_code = 1
                continue

            if not is_shared_saas(manifest):
                logger.info("%s: per_tenant module -- nothing to provision", name)
                continue

            if args.dry_run:
                rbac = manifest["tenancy"]["end_user_rbac"]
                logger.info(
                    "%s: WOULD provision role=%s group=%s permissions=%s into the shared tenant",
                    name,
                    rbac.get("role"),
                    rbac.get("group"),
                    rbac.get("permissions") or [],
                )
                continue

            result = provision_end_user_rbac(session, manifest, commit=True)
            logger.info(
                "%s: provisioned role=%s group=%s in tenant=%s",
                name,
                result["role_code"],
                result["group_code"],
                result["tenant_id"],
            )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
