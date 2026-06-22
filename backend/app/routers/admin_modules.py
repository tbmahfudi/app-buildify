"""
Admin Module Management API Endpoints

Provides REST API for superuser-level module management:
- Upload and install a module tarball
- List all modules in the catalog
- Poll install status of a module
"""

from __future__ import annotations

import hashlib
import json
import logging
import time

import requests
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_superuser
from app.core.module_system.loader import ModuleLoader
from app.models.nocode_module import Module
from app.models.user import User

logger = logging.getLogger(__name__)

HOST_PROJECT_ROOT = os.environ.get('HOST_PROJECT_ROOT', '/home/mahfudi/app-buildify')

router = APIRouter(tags=["admin-modules"])

# Lazily resolved — set from main.py the same way modules_router.module_registry is set
_module_registry = None


def _get_registry():
    """Return the global ModuleRegistryService, or raise 503 if not initialised."""
    if _module_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Module system not initialized",
        )
    return _module_registry


# ---------------------------------------------------------------------------
# GET /  — list all modules in the catalog
# ---------------------------------------------------------------------------

@router.get("/")
async def list_all_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
):
    """
    List all modules from the DB with catalog fields.

    Requires superuser.
    """
    modules = db.query(Module).all()
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "display_name": m.display_name,
            "version": m.version,
            "description": m.description,
            "install_status": m.install_status,
            "is_installed": m.is_installed,
            "category": m.category,
            "module_type": m.module_type,
        }
        for m in modules
    ]


# ---------------------------------------------------------------------------
# GET /{module_name}/install-status  — poll install status
# ---------------------------------------------------------------------------

@router.get("/{module_name}/install-status")
async def get_install_status(
    module_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
):
    """
    Return the install status for a named module.

    Requires superuser.
    """
    module = db.query(Module).filter(Module.name == module_name).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_name}' not found",
        )
    return {
        "name": module.name,
        "install_status": module.install_status,
        "install_error_message": module.install_error_message,
        "is_installed": module.is_installed,
    }


# ---------------------------------------------------------------------------
# POST /upload-install  — upload a tarball and install it
# ---------------------------------------------------------------------------

@router.post("/upload-install", status_code=status.HTTP_200_OK)
async def upload_and_install_module(
    file: UploadFile = File(...),
    checksum_file: Optional[UploadFile] = File(None),
    deploy_mode: str = Form("auto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
):
    """
    Upload a .tar.gz module tarball and install it.

    Mirrors the 8-step manage.sh pipeline:
    1. Save tarball to temp dir
    2. Verify SHA256 checksum (optional — warns if missing)
    3. Extract and locate single top-level module directory
    4. Read and validate manifest.json against JSON schema
    5. Check for existing ready installation (409 if found)
    6. Set install_status=in_progress in DB
    7. Copy backend/ files (branched: sub-module vs top-level)
    8. Copy frontend/ files (branched: sub-module vs top-level)
    9. Run alembic migrations
    10. Set install_status=ready
    11. Sync module registry
    12. Clean up temp dir

    Requires superuser.
    """
    # ---- validate filename ------------------------------------------------
    filename = file.filename or ""
    if not filename.endswith(".tar.gz"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a .tar.gz archive",
        )

    tmp_dir = Path(tempfile.mkdtemp(prefix="module_upload_"))
    tarball_path = tmp_dir / filename

    try:
        # Step 1 — save tarball
        content = await file.read()
        tarball_path.write_bytes(content)

        # Step 2 — optional checksum verification
        if checksum_file is not None:
            checksum_content = (await checksum_file.read()).decode().strip()
            sha256_actual = hashlib.sha256(content).hexdigest()
            # SHA256SUMS format: "<hash>  <filename>" or just "<hash>"
            expected_hash = checksum_content.split()[0].lower()
            if sha256_actual != expected_hash:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SHA256 checksum mismatch: expected {expected_hash}, got {sha256_actual}",
                )
            logger.info(f"Checksum verified for {filename}")
        else:
            logger.warning(f"No checksum file provided for {filename} — skipping verification")

        # Step 3 — extract and find top-level module dir
        extract_dir = tmp_dir / "extracted"
        extract_dir.mkdir()
        try:
            with tarfile.open(tarball_path, "r:gz") as tf:
                tf.extractall(extract_dir)
        except tarfile.TarError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract tarball: {exc}",
            )

        top_level = [p for p in extract_dir.iterdir() if p.is_dir()]
        if len(top_level) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Tarball must contain exactly one top-level directory, "
                    f"found {len(top_level)}: {[p.name for p in top_level]}"
                ),
            )
        module_dir = top_level[0]

        # Step 4 — read and validate manifest
        manifest_path = module_dir / "manifest.json"
        if not manifest_path.exists():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="manifest.json not found in module directory",
            )
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid manifest.json: {exc}",
            )

        loader = ModuleLoader(module_dir)
        valid, err = loader.validate_manifest(manifest)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Manifest validation failed: {err}",
            )

        module_name: str = manifest["name"]
        module_version: str = manifest.get("version", "1.0.0")

        # Step 5 — check for existing ready installation
        existing = db.query(Module).filter(Module.name == module_name).first()
        if existing and existing.install_status == "ready" and existing.is_installed:
            loc = f"inside '{existing.parent_module_id}'" if existing.parent_module_id else "as top-level"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Module '{module_name}' is already installed {loc} at v{existing.version}",
            )

        # Step 6 — set install_status=in_progress
        from app.models.base import generate_uuid

        if existing:
            db_module = existing
        else:
            db_module = Module(
                id=generate_uuid(),
                name=module_name,
                display_name=manifest.get("display_name", module_name),
                module_type="code",
                version=module_version,
                description=manifest.get("description"),
                category=manifest.get("category"),
                manifest=manifest,
            )
            db.add(db_module)

        db_module.install_status = "in_progress"
        db_module.install_error_message = None
        db.commit()
        db.refresh(db_module)

        # Steps 7 & 8 — copy backend/frontend files
        # Branch order: standalone > sub-module > top-level embedded
        deploy_config = manifest.get("deployment", {})
        manifest_mode = deploy_config.get("mode", "embedded")
        effective_mode = deploy_mode if deploy_mode != "auto" else manifest_mode

        parent_module_name = manifest.get("parent_module")  # None for top-level

        if effective_mode == "standalone" and not parent_module_name:
            # Standalone: spin up its own Docker container
            port = deploy_config.get("port")
            if not port or not (9002 <= int(port) <= 9099):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Standalone modules must declare deployment.port (9002-9099) in manifest",
                )
            port = int(port)
            all_ready = db.query(Module).filter(Module.install_status == "ready").all()
            for cm in all_ready:
                if cm.manifest and cm.manifest.get("deployment", {}).get("port") == port:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Port {port} already claimed by module '{cm.name}'",
                    )
            _install_standalone(module_dir, module_name, module_version, port, db_module, db)
        elif parent_module_name:
            # Sub-module: inject into parent service directory instead of creating new
            parent = db.query(Module).filter(
                Module.name == parent_module_name,
                Module.is_installed == True,
                Module.install_status == "ready",
            ).first()
            if not parent:
                raise HTTPException(
                    status_code=409,
                    detail=f"Parent module '{parent_module_name}' is not installed. Install it first.",
                )
            # Copy backend files into parent's directory as a sub-directory
            backend_src = os.path.join(module_dir, "backend")
            if os.path.isdir(backend_src):
                dest = f"/app/modules/{parent_module_name}/{module_name}"
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(backend_src, dest)
            # Copy frontend into parent's frontend directory
            frontend_src = os.path.join(module_dir, "frontend")
            if os.path.isdir(frontend_src):
                dest = f"/frontend/assets/modules/{parent_module_name}/{module_name}"
                os.makedirs(dest, exist_ok=True)
                for item in os.listdir(frontend_src):
                    s = os.path.join(frontend_src, item)
                    d = os.path.join(dest, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
            # Set parent_module_id on the Module record
            db_module.parent_module_id = parent.id
        else:
            # Top-level module: copy into own service directory
            backend_src = os.path.join(module_dir, "backend")
            if os.path.isdir(backend_src):
                dest = f"/app/modules/{module_name}"
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(backend_src, dest)
            frontend_src = os.path.join(module_dir, "frontend")
            if os.path.isdir(frontend_src):
                dest = f"/frontend/assets/modules/{module_name}"
                os.makedirs(dest, exist_ok=True)
                for item in os.listdir(frontend_src):
                    s = os.path.join(frontend_src, item)
                    d = os.path.join(dest, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)

        # Step 9 — alembic migrations (standalone runs its own inside _install_standalone)
        if effective_mode != "standalone":
            _run_alembic()

        # Step 10 — mark ready
        db_module.install_status = "ready"
        db_module.is_installed = True
        db_module.installed_at = datetime.now(timezone.utc)
        db_module.version = module_version
        db_module.display_name = manifest.get("display_name", module_name)
        db_module.description = manifest.get("description")
        db_module.manifest = manifest
        db.commit()
        db.refresh(db_module)

        # Step 11 — sync module registry
        try:
            registry = _get_registry()
            registry.sync_modules()
            logger.info(f"Module registry synced after installing '{module_name}'")
        except HTTPException:
            logger.warning("Module registry not available for sync — skipping")
        except Exception as sync_exc:
            logger.warning(f"Registry sync failed (non-fatal): {sync_exc}")

        # Step 12 — clean up temp dir
        shutil.rmtree(tmp_dir, ignore_errors=True)

        return {
            "status": "ok",
            "module": {
                "name": module_name,
                "version": module_version,
                "install_status": "ready",
            },
        }

    except HTTPException:
        # Mark failed in DB if we have a module name from the manifest parse
        _mark_failed(db, locals().get("module_name"), locals().get("db_module"), str("Upload or validation error"))
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    except Exception as exc:
        logger.error(f"Module upload-install failed: {exc}", exc_info=True)
        module_name_local = locals().get("module_name")
        db_module_local = locals().get("db_module")
        _mark_failed(db, module_name_local, db_module_local, str(exc))
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Module installation failed: {exc}",
        )



def _install_standalone(
    module_dir: Path,
    name: str,
    version: str,
    port: int,
    db_module,
    db,
) -> None:
    """Install a module as its own Docker service."""
    host_root = HOST_PROJECT_ROOT

    # Copy backend
    backend_src = module_dir / "backend"
    if backend_src.is_dir():
        dest = Path(host_root) / "modules" / name / "backend"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(backend_src, dest)

    # Copy frontend
    frontend_src = module_dir / "frontend"
    if frontend_src.is_dir():
        dest = Path("/frontend/assets/modules") / name
        dest.mkdir(parents=True, exist_ok=True)
        for item in frontend_src.iterdir():
            d = dest / item.name
            if item.is_dir():
                if d.exists():
                    shutil.rmtree(d)
                shutil.copytree(item, d)
            else:
                shutil.copy2(item, d)

    # Write compose file on the host
    compose_path = Path(host_root) / "infra" / "modules" / f"{name}-compose.yml"
    compose_path.parent.mkdir(parents=True, exist_ok=True)
    compose_path.write_text(
        f"services:\n"
        f"  {name}:\n"
        f"    container_name: app_buildify_{name}\n"
        f"    build:\n"
        f"      context: ../../modules/{name}/backend\n"
        f"      dockerfile: Dockerfile\n"
        f"    ports:\n"
        f"      - \"{port}:{port}\"\n"
        f"    environment:\n"
        f"      SQLALCHEMY_DATABASE_URL: postgresql+psycopg2://appuser:apppass@postgres:5432/appdb\n"
        f"      MODULE_NAME: {name}\n"
        f"      MODULE_PORT: {port}\n"
        f"      PLATFORM_API_URL: http://backend:8000\n"
        f"    networks:\n"
        f"      - app_buildify_default\n"
        f"    depends_on:\n"
        f"      - postgres\n"
        f"\n"
        f"networks:\n"
        f"  app_buildify_default:\n"
        f"    external: true\n"
    )

    # Write nginx conf
    nginx_conf = Path(host_root) / "infra" / "nginx" / "modules" / f"{name}.conf"
    nginx_conf.parent.mkdir(parents=True, exist_ok=True)
    nginx_conf.write_text(
        f"location ~ ^/api/(v[0-9]+)/{name}/(.*)$ {{\n"
        f"    proxy_pass http://{name}-module:{port}/api/$1/{name}/$2$is_args$args;\n"
        f"    proxy_http_version 1.1;\n"
        f"    proxy_set_header Host $http_host;\n"
        f"    proxy_set_header X-Real-IP $remote_addr;\n"
        f"    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
        f"    proxy_set_header X-Forwarded-Proto $scheme;\n"
        f"}}\n"
    )

    # Alembic before container starts
    _run_alembic()

    # Start the container
    subprocess.run(
        ["docker", "compose", "-f", str(compose_path), "-p", f"app_buildify_{name}", "up", "-d", "--build"],
        check=True,
        timeout=300,
    )
    logger.info(f"Started standalone container for module '{name}' on port {port}")

    # Reload nginx
    subprocess.run(
        ["docker", "exec", "app_buildify_frontend", "nginx", "-s", "reload"],
        check=True,
        timeout=30,
    )

    # Health poll (120s)
    health_url = f"http://localhost:{port}/health"
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            r = requests.get(health_url, timeout=3)
            if r.status_code < 500:
                logger.info(f"Module '{name}' healthy on port {port}")
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    raise RuntimeError(f"Module '{name}' did not become healthy within 120s at {health_url}")


def _run_alembic() -> None:
    """Run alembic upgrade head against the platform database."""
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed (exit {result.returncode}):\n{result.stderr}"
        )
    logger.info("Alembic migrations completed")


def _mark_failed(
    db: Session,
    module_name: Optional[str],
    db_module,
    error_message: str,
) -> None:
    """Helper: set install_status=failed on the DB record if we have one."""
    try:
        if db_module is not None:
            db_module.install_status = "failed"
            db_module.install_error_message = error_message[:2000]
            db.commit()
        elif module_name:
            existing = db.query(Module).filter(Module.name == module_name).first()
            if existing:
                existing.install_status = "failed"
                existing.install_error_message = error_message[:2000]
                db.commit()
    except Exception as mark_exc:
        logger.warning(f"Could not mark module as failed in DB: {mark_exc}")
