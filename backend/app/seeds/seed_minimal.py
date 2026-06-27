"""
Minimal Seed — Platform Superadmin Only
=======================================
Seeds nothing but the global superadmin (sysadmin) account. No sample tenants,
companies, branches, users, or RBAC groups.

The superadmin bypasses RBAC permission checks (is_superuser), so this is enough
to log in and operate a clean system. Use this when you want an empty platform
with just an admin account, instead of the full demo dataset seeded by
`app.seeds.seed_complete_org`.

Run: python -m app.seeds.seed_minimal
"""

from app.core.db import SessionLocal
from app.seeds.seed_complete_org import seed_superuser, SUPERUSER


def main():
    """Seed only the global superadmin. Idempotent — safe to re-run."""
    print("\n" + "=" * 70)
    print("MINIMAL SEED — SUPERADMIN ONLY")
    print("=" * 70)

    db = SessionLocal()
    try:
        seed_superuser(db)  # idempotent; commits internally
        print("\n" + "=" * 70)
        print("✓ Minimal seed complete.")
        print(f"  Superadmin: {SUPERUSER['email']} / {SUPERUSER['password']}")
        print("  (No sample tenants/users — superadmin bypasses RBAC.)")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"\n❌ Minimal seed failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
