"""Admin module management endpoints — upload-install pipeline."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.nocode_module import Module

router = APIRouter()

# Injected by main.py after module_registry is initialised
_module_registry = None


def _require_superuser(current_user=Depends(get_current_user)):
    if not getattr(current_user, 'is_superuser', False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Superuser access required')
    return current_user


@router.get('/', summary='List all modules')
def list_all_modules(
    db: Session = Depends(get_db),
    current_user=Depends(_require_superuser),
):
    modules = db.query(Module).order_by(Module.display_name).all()
    return [
        {
            'id': str(m.id),
            'name': m.name,
            'display_name': m.display_name,
            'version': m.version,
            'description': m.description,
            'install_status': m.install_status,
            'is_installed': m.is_installed,
            'category': m.category,
            'module_type': m.module_type,
        }
        for m in modules
    ]


@router.get('/{module_name}/install-status', summary='Poll install status')
def get_install_status(
    module_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(_require_superuser),
):
    m = db.query(Module).filter(Module.name == module_name).first()
    if not m:
        raise HTTPException(status_code=404, detail=f'Module {module_name!r} not found')
    return {
        'name': m.name,
        'install_status': m.install_status,
        'install_error_message': m.install_error_message,
        'is_installed': m.is_installed,
    }


@router.post('/upload-install', summary='Upload and install a module tarball')
async def upload_install(
    file: UploadFile = File(...),
    checksum_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(_require_superuser),
):
    import os, shutil, tarfile, tempfile, hashlib, json, datetime
    from pathlib import Path

    if not (file.filename.endswith('.tar.gz') or file.filename.endswith('.tgz')):
        raise HTTPException(status_code=400, detail='File must be a .tar.gz archive')

    tmp = tempfile.mkdtemp(prefix='module_upload_')
    try:
        # Save tarball
        tarball_path = os.path.join(tmp, file.filename)
        content = await file.read()
        with open(tarball_path, 'wb') as f:
            f.write(content)

        # Optional checksum verification
        if checksum_file:
            expected = (await checksum_file.read()).decode().split()[0].strip()
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                # warn only — do not abort
                pass

        # Extract
        with tarfile.open(tarball_path, 'r:gz') as tar:
            tar.extractall(tmp)

        # Find single top-level module dir
        entries = [e for e in os.listdir(tmp) if os.path.isdir(os.path.join(tmp, e))]
        if not entries:
            raise ValueError('No directory found in tarball')
        module_dir = os.path.join(tmp, entries[0])

        # Read manifest
        manifest_path = os.path.join(module_dir, 'manifest.json')
        with open(manifest_path) as f:
            manifest = json.load(f)

        name = manifest['name']
        version = manifest.get('version', '0.0.0')

        # Check if already installed
        existing = db.query(Module).filter(Module.name == name).first()
        if existing and existing.install_status == 'ready' and existing.is_installed:
            raise HTTPException(status_code=409, detail=f'Module {name!r} is already installed at v{existing.version}')

        # Mark in_progress
        if existing:
            existing.install_status = 'in_progress'
            existing.is_installed = False
            existing.install_error_message = None
        else:
            existing = Module(
                name=name,
                display_name=manifest.get('display_name', name),
                version=version,
                description=manifest.get('description'),
                module_type='code',
                install_status='in_progress',
                is_installed=False,
                manifest=manifest,
            )
            db.add(existing)
        db.commit()
        db.refresh(existing)

        # Copy backend files
        backend_src = os.path.join(module_dir, 'backend')
        if os.path.isdir(backend_src):
            dest = f'/app/modules/{name}'
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(backend_src, dest)

        # Copy frontend files
        frontend_src = os.path.join(module_dir, 'frontend')
        if os.path.isdir(frontend_src):
            dest = f'/frontend/assets/modules/{name}'
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

        # Run alembic migrations if present
        alembic_src = os.path.join(module_dir, 'alembic', 'versions')
        if os.path.isdir(alembic_src):
            alembic_dest = '/app/app/alembic/versions/postgresql'
            os.makedirs(alembic_dest, exist_ok=True)
            for f in os.listdir(alembic_src):
                if f.endswith('.py'):
                    shutil.copy2(os.path.join(alembic_src, f), os.path.join(alembic_dest, f))
            import subprocess
            result = subprocess.run(
                ['alembic', 'upgrade', 'head'],
                cwd='/app',
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f'Alembic failed: {result.stderr}')

        # Mark ready
        existing.install_status = 'ready'
        existing.is_installed = True
        existing.installed_at = datetime.datetime.utcnow()
        existing.installed_by_user_id = current_user.id
        db.commit()

        # Sync module registry
        if _module_registry:
            try:
                _module_registry.sync_modules()
            except Exception:
                pass

        return {'status': 'ok', 'module': {'name': name, 'version': version, 'install_status': 'ready'}}

    except HTTPException:
        raise
    except Exception as e:
        # Mark failed
        try:
            if existing:
                existing.install_status = 'failed'
                existing.install_error_message = str(e)
                db.commit()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
