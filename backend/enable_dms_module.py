"""
Enable the DMS (Document Management) module for one or more tenants.

DMS is a *standalone* module (its API runs in its own container and self-registers
its manifest with the core platform on startup). Standalone modules are activated
per-tenant by inserting a TenantModule (module_activations) row directly — the same
path used by enable_financial_module.py — rather than the filesystem-loader-based
`/module-registry/enable` endpoint (which only works for in-process modules that
ship a backend `module.py`).

Usage (run inside the backend container):
    docker exec app_buildify_backend python enable_dms_module.py TECHSTART
    docker exec app_buildify_backend python enable_dms_module.py TECHSTART HEALTHPOINT
"""
import sys
import uuid
from datetime import datetime

from app.core.db import SessionLocal
from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.tenant import Tenant

MODULE_NAME = "dms"


def enable_for_tenant(db, module, tenant_code: str) -> bool:
    tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
    if not tenant:
        print(f"❌ Tenant '{tenant_code}' not found")
        return False

    tm = (
        db.query(TenantModule)
        .filter(TenantModule.tenant_id == tenant.id, TenantModule.module_id == module.id)
        .first()
    )
    if tm:
        if not tm.is_enabled:
            tm.is_enabled = True
            tm.enabled_at = datetime.utcnow()
            db.commit()
            print(f"✅ Enabled DMS for {tenant_code} ({tenant.name})")
        else:
            print(f"✅ DMS already enabled for {tenant_code} ({tenant.name})")
    else:
        tm = TenantModule(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant.id),
            module_id=str(module.id),
            is_enabled=True,
            configuration={},
            enabled_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(tm)
        db.commit()
        print(f"✅ Enabled DMS for {tenant_code} ({tenant.name})")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python enable_dms_module.py TENANT_CODE [TENANT_CODE ...]")
        sys.exit(1)
    tenant_codes = [c.upper() for c in sys.argv[1:]]

    db = SessionLocal()
    try:
        module = db.query(ModuleRegistry).filter(ModuleRegistry.name == MODULE_NAME).first()
        if not module:
            print(f"❌ Module '{MODULE_NAME}' is not registered. Start the dms-module "
                  f"container so it self-registers with the core platform, then retry.")
            sys.exit(1)
        print(f"✅ Found registered module: {module.display_name} v{module.version}")

        ok = 0
        for code in tenant_codes:
            if enable_for_tenant(db, module, code):
                ok += 1
        print(f"\nEnabled for {ok}/{len(tenant_codes)} tenant(s).")
        print("Reload the SPA — the DMS route (#/dms/documents) will now register.")
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
