"""
Seed script: Multi-clinic MedCare + single-clinic HealthPoint tenant.

Idempotent — re-running will not duplicate rows.

Run inside container:
    docker exec app_buildify_backend python3 /app/scripts/seed_clinic_tenants.py

Or directly with WSL DB access using env var DATABASE_URL.
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    os.environ.get(
        "SQLALCHEMY_DATABASE_URL",
        "postgresql+psycopg2://appuser:apppass@localhost:5432/appdb",
    ),
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def upsert_tenant(db, *, name: str, code: str, subscription_tier: str = "basic") -> str:
    """Return tenant id, creating if not present (match on code)."""
    row = db.execute(
        text("SELECT id FROM tenants WHERE code = :code"),
        {"code": code},
    ).fetchone()
    if row:
        print(f"  [tenant] EXISTS  {name} ({code}) -> {row[0]}")
        return str(row[0])
    tid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO tenants (id, name, code, subscription_tier, subscription_status,
                                 max_companies, max_users, max_storage_gb,
                                 current_companies, current_users, current_storage_gb,
                                 is_active, is_trial, created_at)
            VALUES (:id, :name, :code, :tier, 'active',
                    10, 500, 10, 0, 0, 0,
                    TRUE, FALSE, NOW())
            """
        ),
        {"id": tid, "name": name, "code": code, "tier": subscription_tier},
    )
    print(f"  [tenant] CREATED {name} ({code}) -> {tid}")
    return tid


def get_or_create_company(db, *, tenant_id: str, name: str) -> str:
    """Return company id for the tenant, creating if needed."""
    row = db.execute(
        text("SELECT id FROM companies WHERE tenant_id = :tid LIMIT 1"),
        {"tid": tenant_id},
    ).fetchone()
    if row:
        return str(row[0])
    cid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO companies (id, tenant_id, name, code, is_active, created_at)
            VALUES (:id, :tid, :name, :code, TRUE, NOW())
            """
        ),
        {"id": cid, "tid": tenant_id, "name": name, "code": name[:10].upper().replace(" ", "")},
    )
    print(f"  [company] CREATED {name} -> {cid}")
    return cid


def upsert_branch(db, *, company_id: str, tenant_id: str, code: str,
                  name: str, city: str) -> str:
    """Return branch id (unique per company+code)."""
    row = db.execute(
        text("SELECT id FROM branches WHERE company_id = :cid AND code = :code"),
        {"cid": company_id, "code": code},
    ).fetchone()
    if row:
        print(f"    [branch] EXISTS  {name} ({code}) -> {row[0]}")
        return str(row[0])
    bid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO branches (id, company_id, tenant_id, code, name, city,
                                  is_active, is_headquarters, created_at)
            VALUES (:id, :cid, :tid, :code, :name, :city,
                    TRUE, FALSE, NOW())
            """
        ),
        {"id": bid, "cid": company_id, "tid": tenant_id,
         "code": code, "name": name, "city": city},
    )
    print(f"    [branch] CREATED {name} ({code}) -> {bid}")
    return bid


def upsert_user(db, *, email: str, full_name: str, password: str,
                tenant_id: str, branch_id: str, roles: str) -> str:
    """Return user id (unique per email)."""
    row = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()
    if row:
        print(f"      [user] EXISTS  {email} -> {row[0]}")
        return str(row[0])
    uid = str(uuid.uuid4())
    hpw = hash_password(password)
    db.execute(
        text(
            """
            INSERT INTO users (id, email, hashed_password, full_name,
                               is_active, is_superuser, is_verified,
                               tenant_id, branch_id, roles,
                               failed_login_attempts, require_password_change,
                               created_at)
            VALUES (:id, :email, :hpw, :name,
                    TRUE, FALSE, TRUE,
                    :tid, :bid, :roles,
                    0, FALSE, NOW())
            """
        ),
        {"id": uid, "email": email, "hpw": hpw, "name": full_name,
         "tid": tenant_id, "bid": branch_id, "roles": roles},
    )
    print(f"      [user] CREATED {email} -> {uid}")
    return uid


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed():
    db = SessionLocal()
    try:
        print("\n=== SEEDING clinic tenants ===\n")

        # ------------------------------------------------------------------ #
        # Tenant 1 — MedCare (EXISTING)
        # ------------------------------------------------------------------ #
        MEDCARE_TENANT_ID = "50f10a52-66ad-4c38-a0b2-6015db8dd42c"
        print("[MedCare] Using existing tenant", MEDCARE_TENANT_ID)

        # Get or create a company for MedCare
        medcare_company_id = get_or_create_company(
            db, tenant_id=MEDCARE_TENANT_ID, name="MedCare Health System"
        )

        clinics = [
            {"code": "MC-001", "name": "MedCare Central Clinic", "city": "Jakarta",
             "manager_email": "manager.mc001@medcare.com",
             "staff_email":   "staff.mc001@medcare.com"},
            {"code": "MC-002", "name": "MedCare North Clinic",   "city": "Jakarta",
             "manager_email": "manager.mc002@medcare.com",
             "staff_email":   "staff.mc002@medcare.com"},
            {"code": "MC-003", "name": "MedCare South Clinic",   "city": "Bogor",
             "manager_email": "manager.mc003@medcare.com",
             "staff_email":   "staff.mc003@medcare.com"},
        ]

        for c in clinics:
            print(f"\n  Branch: {c['name']}")
            branch_id = upsert_branch(
                db,
                company_id=medcare_company_id,
                tenant_id=MEDCARE_TENANT_ID,
                code=c["code"],
                name=c["name"],
                city=c["city"],
            )
            suffix = c["code"].replace("-", "").lower()
            upsert_user(
                db,
                email=c["manager_email"],
                full_name=f"Manager {c['code']}",
                password="password123",
                tenant_id=MEDCARE_TENANT_ID,
                branch_id=branch_id,
                roles="clinic_manager",
            )
            upsert_user(
                db,
                email=c["staff_email"],
                full_name=f"Staff {c['code']}",
                password="password123",
                tenant_id=MEDCARE_TENANT_ID,
                branch_id=branch_id,
                roles="clinic_staff",
            )

        # ------------------------------------------------------------------ #
        # Tenant 2 — HealthPoint Clinic (NEW)
        # ------------------------------------------------------------------ #
        print("\n[HealthPoint] Creating new tenant ...")
        hp_tenant_id = upsert_tenant(
            db, name="HealthPoint Clinic", code="healthpoint", subscription_tier="basic"
        )

        hp_company_id = get_or_create_company(
            db, tenant_id=hp_tenant_id, name="HealthPoint Clinic"
        )

        print("\n  Branch: HealthPoint Main Clinic")
        hp_branch_id = upsert_branch(
            db,
            company_id=hp_company_id,
            tenant_id=hp_tenant_id,
            code="HP-001",
            name="HealthPoint Main Clinic",
            city="Bandung",
        )

        hp_users = [
            ("admin@healthpoint.com",   "Admin HealthPoint",   "tenant_admin"),
            ("manager@healthpoint.com", "Manager HealthPoint", "clinic_manager"),
            ("staff1@healthpoint.com",  "Staff 1 HealthPoint", "clinic_staff"),
            ("staff2@healthpoint.com",  "Staff 2 HealthPoint", "clinic_staff"),
        ]
        for email, name, role in hp_users:
            upsert_user(
                db,
                email=email,
                full_name=name,
                password="password123",
                tenant_id=hp_tenant_id,
                branch_id=hp_branch_id,
                roles=role,
            )

        db.commit()
        print("\n=== SEED COMPLETE — committed ===\n")

        # ------------------------------------------------------------------ #
        # Verification summary
        # ------------------------------------------------------------------ #
        print("=== VERIFICATION ===")
        rows = db.execute(
            text(
                """
                SELECT t.name AS tenant, COUNT(b.id) AS branches
                FROM tenants t
                LEFT JOIN branches b ON b.tenant_id = t.id
                WHERE t.id IN (:mid, :hid)
                GROUP BY t.name
                """
            ),
            {"mid": MEDCARE_TENANT_ID, "hid": hp_tenant_id},
        ).fetchall()
        for r in rows:
            print(f"  {r[0]}: {r[1]} branch(es)")

        rows = db.execute(
            text(
                """
                SELECT t.name AS tenant, COUNT(u.id) AS users
                FROM tenants t
                LEFT JOIN users u ON u.tenant_id = t.id
                WHERE t.id IN (:mid, :hid)
                GROUP BY t.name
                """
            ),
            {"mid": MEDCARE_TENANT_ID, "hid": hp_tenant_id},
        ).fetchall()
        for r in rows:
            print(f"  {r[0]}: {r[1]} user(s)")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
