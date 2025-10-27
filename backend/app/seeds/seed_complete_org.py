"""
Complete Organization Seed Data for Multi-Tenant Architecture
================================================================
Comprehensive seeding covering all organizational scenarios with proper multi-tenant support.

Run: python -m app.seeds.seed_complete_org
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.db import SessionLocal, engine
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.company import Company
from app.models.branch import Branch
from app.models.department import Department
from app.models.settings import UserSettings, TenantSettings
from app.core.auth import hash_password


# ============================================================================
# SEED DATA STRUCTURE
# ============================================================================

SEED_DATA = {
    # ========================================================================
    # SCENARIO 1: Tech Startup (Single Location, Flat Structure)
    # ========================================================================
    "tech_startup": {
        "tenant": {
            "code": "TECHSTART",
            "name": "TechStart Tenant",
            "subscription_tier": "premium",
            "max_companies": 1,
            "max_users": 50
        },
        "company": {
            "code": "TECHSTART",
            "name": "TechStart Innovations Inc.",
            "description": "Early-stage SaaS startup, single office, 25 employees"
        },
        "branches": [
            {
                "code": "HQ",
                "name": "San Francisco HQ",
                "description": "Main office and only location"
            }
        ],
        "departments": [
            {"code": "ENG", "name": "Engineering", "branch": "HQ"},
            {"code": "PROD", "name": "Product", "branch": "HQ"},
            {"code": "SALES", "name": "Sales & Marketing", "branch": "HQ"},
            {"code": "OPS", "name": "Operations", "branch": "HQ"},
        ],
        "users": [
            {"email": "ceo@techstart.com", "name": "John Founder", "is_superuser": False, "dept": "OPS"},
            {"email": "cto@techstart.com", "name": "Jane Engineer", "is_superuser": False, "dept": "ENG"},
            {"email": "dev1@techstart.com", "name": "Dev One", "is_superuser": False, "dept": "ENG"},
            {"email": "dev2@techstart.com", "name": "Dev Two", "is_superuser": False, "dept": "ENG"},
            {"email": "pm@techstart.com", "name": "Product Manager", "is_superuser": False, "dept": "PROD"},
        ]
    },

    # ========================================================================
    # SCENARIO 2: Medium Retail Chain (Multi-Location, Standard Hierarchy)
    # ========================================================================
    "retail_chain": {
        "tenant": {
            "code": "FASHIONHUB",
            "name": "FashionHub Tenant",
            "subscription_tier": "premium",
            "max_companies": 1,
            "max_users": 250
        },
        "company": {
            "code": "FASHIONHUB",
            "name": "FashionHub Retail Ltd.",
            "description": "Regional retail chain with 15 stores, 200 employees"
        },
        "branches": [
            {"code": "CORP", "name": "Corporate Office", "description": "Headquarters"},
            {"code": "NYC-01", "name": "Manhattan Flagship", "description": "Flagship store"},
            {"code": "NYC-02", "name": "Brooklyn Store", "description": "Brooklyn location"},
            {"code": "BOS-01", "name": "Boston Store", "description": "Boston location"},
            {"code": "DC", "name": "Distribution Center", "description": "Central warehouse"},
        ],
        "departments": [
            {"code": "EXEC", "name": "Executive", "branch": None},
            {"code": "HR", "name": "Human Resources", "branch": "CORP"},
            {"code": "FIN", "name": "Finance & Accounting", "branch": "CORP"},
            {"code": "IT", "name": "Information Technology", "branch": "CORP"},
            {"code": "STORE-MGT", "name": "Store Management", "branch": "NYC-01"},
            {"code": "SALES", "name": "Sales Floor", "branch": "NYC-01"},
            {"code": "STORE-MGT", "name": "Store Management", "branch": "BOS-01"},
            {"code": "SALES", "name": "Sales Floor", "branch": "BOS-01"},
            {"code": "WAREHOUSE", "name": "Warehouse Operations", "branch": "DC"},
        ],
        "users": [
            {"email": "ceo@fashionhub.com", "name": "CEO Fashion", "is_superuser": False, "dept": "EXEC", "branch": None},
            {"email": "cfo@fashionhub.com", "name": "CFO Money", "is_superuser": False, "dept": "FIN", "branch": "CORP"},
            {"email": "hr@fashionhub.com", "name": "HR Director", "is_superuser": False, "dept": "HR", "branch": "CORP"},
            {"email": "manager.nyc1@fashionhub.com", "name": "NYC Manager", "is_superuser": False, "dept": "STORE-MGT", "branch": "NYC-01"},
            {"email": "sales.nyc1@fashionhub.com", "name": "NYC Sales Rep", "is_superuser": False, "dept": "SALES", "branch": "NYC-01"},
        ]
    },

    # ========================================================================
    # SCENARIO 3: Healthcare Network (Complex Multi-Facility)
    # ========================================================================
    "healthcare": {
        "tenant": {
            "code": "MEDCARE",
            "name": "MedCare Tenant",
            "subscription_tier": "enterprise",
            "max_companies": 1,
            "max_users": 1000
        },
        "company": {
            "code": "MEDCARE",
            "name": "MedCare Health System",
            "description": "Regional healthcare network, 3 hospitals, 12 clinics"
        },
        "branches": [
            {"code": "HOSP-CENT", "name": "Central Hospital", "description": "Main hospital, 500 beds"},
            {"code": "HOSP-NORTH", "name": "North Hospital", "description": "Secondary hospital, 250 beds"},
            {"code": "CLINIC-01", "name": "Downtown Clinic", "description": "Primary care"},
            {"code": "ADMIN", "name": "Administrative Center", "description": "System administration"},
        ],
        "departments": [
            {"code": "EXEC", "name": "Executive Leadership", "branch": "ADMIN"},
            {"code": "HR", "name": "Human Resources", "branch": "ADMIN"},
            {"code": "ER", "name": "Emergency Room", "branch": "HOSP-CENT"},
            {"code": "ICU", "name": "Intensive Care Unit", "branch": "HOSP-CENT"},
            {"code": "NURSING", "name": "Nursing", "branch": "HOSP-CENT"},
            {"code": "PRIMARY-CARE", "name": "Primary Care", "branch": "CLINIC-01"},
        ],
        "users": [
            {"email": "ceo@medcare.com", "name": "CEO Healthcare", "is_superuser": False, "dept": "EXEC", "branch": "ADMIN"},
            {"email": "cmo@medcare.com", "name": "Chief Medical Officer", "is_superuser": False, "dept": "EXEC", "branch": "ADMIN"},
            {"email": "er.doc@medcare.com", "name": "ER Physician", "is_superuser": False, "dept": "ER", "branch": "HOSP-CENT"},
            {"email": "nurse.lead@medcare.com", "name": "Nursing Lead", "is_superuser": False, "dept": "NURSING", "branch": "HOSP-CENT"},
        ]
    },

    # ========================================================================
    # SCENARIO 4: Remote-First Tech Company
    # ========================================================================
    "remote_tech": {
        "tenant": {
            "code": "CLOUDWORK",
            "name": "CloudWork Tenant",
            "subscription_tier": "premium",
            "max_companies": 1,
            "max_users": 200
        },
        "company": {
            "code": "CLOUDWORK",
            "name": "CloudWork Solutions",
            "description": "Fully remote SaaS company, 150 employees worldwide"
        },
        "branches": [
            {"code": "VIRTUAL", "name": "Virtual Headquarters", "description": "No physical office"},
        ],
        "departments": [
            {"code": "ENG", "name": "Engineering", "branch": None},
            {"code": "PRODUCT", "name": "Product Management", "branch": None},
            {"code": "MARKETING", "name": "Marketing", "branch": None},
            {"code": "SALES", "name": "Sales", "branch": None},
        ],
        "users": [
            {"email": "ceo@cloudwork.com", "name": "CEO Remote", "is_superuser": False, "dept": "PRODUCT", "branch": None},
            {"email": "eng@cloudwork.com", "name": "VP Engineering", "is_superuser": False, "dept": "ENG", "branch": None},
            {"email": "dev1@cloudwork.com", "name": "Developer Global", "is_superuser": False, "dept": "ENG", "branch": None},
        ]
    },

    # ========================================================================
    # SCENARIO 5: Financial Services
    # ========================================================================
    "financial": {
        "tenant": {
            "code": "FINTECH",
            "name": "FinTech Tenant",
            "subscription_tier": "enterprise",
            "max_companies": 1,
            "max_users": 500
        },
        "company": {
            "code": "FINTECH",
            "name": "FinTech Capital Partners",
            "description": "Investment firm with strict compliance requirements"
        },
        "branches": [
            {"code": "HQ", "name": "Headquarters", "description": "Main office"},
            {"code": "NYC", "name": "New York Trading Floor", "description": "Trading operations"},
        ],
        "departments": [
            {"code": "TRADING", "name": "Trading", "branch": "NYC"},
            {"code": "COMPLIANCE", "name": "Compliance", "branch": "HQ"},
            {"code": "RISK", "name": "Risk Management", "branch": "HQ"},
            {"code": "IT", "name": "Technology", "branch": "HQ"},
        ],
        "users": [
            {"email": "ceo@fintech.com", "name": "CEO Finance", "is_superuser": False, "dept": "TRADING", "branch": "HQ"},
            {"email": "compliance@fintech.com", "name": "Chief Compliance Officer", "is_superuser": False, "dept": "COMPLIANCE", "branch": "HQ"},
            {"email": "trader@fintech.com", "name": "Senior Trader", "is_superuser": False, "dept": "TRADING", "branch": "NYC"},
        ]
    },
}


# ============================================================================
# GLOBAL SUPERUSER
# ============================================================================
SUPERUSER = {
    "email": "superadmin@system.com",
    "password": "SuperAdmin123!",
    "full_name": "System Super Administrator",
    "is_superuser": True,
    "is_active": True,
    "tenant_id": None
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_id():
    """Generate UUID as string."""
    return str(uuid.uuid4())


def seed_scenario(db: Session, scenario_key: str, scenario_data: dict):
    """Seed a complete organizational scenario with tenant."""
    print(f"\n{'='*70}")
    print(f"Seeding Scenario: {scenario_data['company']['name']}")
    print(f"{'='*70}")

    # 1. Create Tenant
    tenant_id = create_id()
    tenant_data = scenario_data['tenant']
    tenant = Tenant(
        id=tenant_id,
        code=tenant_data['code'],
        name=tenant_data['name'],
        subscription_tier=tenant_data.get('subscription_tier', 'free'),
        subscription_status='active',
        max_companies=tenant_data.get('max_companies', 10),
        max_users=tenant_data.get('max_users', 100),
        max_storage_gb=10,
        is_active=True,
        is_trial=False,
        created_at=datetime.utcnow()
    )
    db.add(tenant)
    db.flush()  # Ensure tenant ID is available
    print(f"✓ Tenant: {tenant.name} ({tenant.code})")

    # 2. Create Company
    company_id = create_id()
    company = Company(
        id=company_id,
        tenant_id=tenant_id,
        code=scenario_data['company']['code'],
        name=scenario_data['company']['name'],
        description=scenario_data['company'].get('description'),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(company)
    db.flush()
    print(f"  ✓ Company: {company.name} ({company.code})")

    # 3. Create Branches
    branch_map = {}
    for branch_data in scenario_data['branches']:
        branch_id = create_id()
        branch = Branch(
            id=branch_id,
            tenant_id=tenant_id,
            company_id=company_id,
            code=branch_data['code'],
            name=branch_data['name'],
            description=branch_data.get('description'),
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(branch)
        branch_map[branch_data['code']] = branch_id
        print(f"    ✓ Branch: {branch.name} ({branch.code})")

    db.flush()

    # 4. Create Departments
    dept_map = {}
    for dept_data in scenario_data['departments']:
        dept_id = create_id()
        branch_code = dept_data.get('branch')
        branch_id = branch_map.get(branch_code) if branch_code else None

        dept_key = f"{dept_data['code']}_{branch_code if branch_code else 'GLOBAL'}"

        department = Department(
            id=dept_id,
            tenant_id=tenant_id,
            company_id=company_id,
            branch_id=branch_id,
            code=dept_data['code'],
            name=dept_data['name'],
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(department)
        dept_map[dept_key] = dept_id

        branch_name = f" @ {branch_code}" if branch_code else " (Company-wide)"
        print(f"      ✓ Department: {dept_data['name']}{branch_name}")

    db.flush()

    # 5. Create Users
    for user_data in scenario_data['users']:
        user_id = create_id()

        # Resolve department and branch
        dept_code = user_data.get('dept')
        branch_code = user_data.get('branch')
        dept_key = f"{dept_code}_{branch_code if branch_code else 'GLOBAL'}"

        # If exact match not found, try without branch
        department_id = dept_map.get(dept_key)
        if not department_id:
            dept_key = f"{dept_code}_GLOBAL"
            department_id = dept_map.get(dept_key)

        branch_id = branch_map.get(branch_code) if branch_code else None

        user = User(
            id=user_id,
            email=user_data['email'],
            hashed_password=hash_password("password123"),
            full_name=user_data['name'],
            is_active=True,
            is_superuser=user_data.get('is_superuser', False),
            is_verified=True,
            tenant_id=tenant_id,
            default_company_id=company_id,
            branch_id=branch_id,
            department_id=department_id,
            created_at=datetime.utcnow()
        )
        db.add(user)

        # Create user settings
        user_settings = UserSettings(
            id=create_id(),
            user_id=user_id,
            theme="light",
            language="en",
            timezone="UTC",
            density="normal",
            created_at=datetime.utcnow()
        )
        db.add(user_settings)

        print(f"        ✓ User: {user_data['name']} ({user_data['email']})")

    # 6. Create Tenant Settings
    tenant_settings = TenantSettings(
        id=create_id(),
        tenant_id=tenant_id,
        tenant_name=company.name,
        primary_color="#6366f1",
        secondary_color="#8b5cf6",
        created_at=datetime.utcnow()
    )
    db.add(tenant_settings)

    db.commit()
    print(f"✓ Scenario '{scenario_data['company']['name']}' completed!")


def seed_superuser(db: Session):
    """Create global superuser."""
    print(f"\n{'='*70}")
    print("Creating Global Superuser")
    print(f"{'='*70}")

    # Check if superuser exists
    existing = db.query(User).filter(User.email == SUPERUSER['email']).first()
    if existing:
        print("✓ Superuser already exists, skipping...")
        return

    user_id = create_id()
    user = User(
        id=user_id,
        email=SUPERUSER['email'],
        hashed_password=hash_password(SUPERUSER['password']),
        full_name=SUPERUSER['full_name'],
        is_active=SUPERUSER['is_active'],
        is_superuser=SUPERUSER['is_superuser'],
        is_verified=True,
        tenant_id=SUPERUSER['tenant_id'],
        created_at=datetime.utcnow()
    )
    db.add(user)

    user_settings = UserSettings(
        id=create_id(),
        user_id=user_id,
        theme="dark",
        language="en",
        timezone="UTC",
        density="compact",
        created_at=datetime.utcnow()
    )
    db.add(user_settings)

    db.commit()
    print(f"✓ Superuser created: {SUPERUSER['email']}")
    print(f"  Password: {SUPERUSER['password']}")


def clear_all_data(db: Session):
    """Clear all existing data (use with caution!)."""
    print("\n⚠️  Clearing all existing data...")

    # Order matters due to foreign keys
    db.query(UserSettings).delete()
    db.query(TenantSettings).delete()
    db.query(User).delete()
    db.query(Department).delete()
    db.query(Branch).delete()
    db.query(Company).delete()
    db.query(Tenant).delete()

    db.commit()
    print("✓ All data cleared!")


def print_summary(db: Session):
    """Print seeding summary."""
    print(f"\n{'='*70}")
    print("SEEDING SUMMARY")
    print(f"{'='*70}")

    tenants = db.query(Tenant).count()
    companies = db.query(Company).count()
    branches = db.query(Branch).count()
    departments = db.query(Department).count()
    users = db.query(User).count()

    print(f"Tenants:     {tenants}")
    print(f"Companies:   {companies}")
    print(f"Branches:    {branches}")
    print(f"Departments: {departments}")
    print(f"Users:       {users}")
    print(f"{'='*70}\n")


def print_test_credentials():
    """Print test credentials."""
    print(f"\n{'='*70}")
    print("TEST CREDENTIALS")
    print(f"{'='*70}\n")

    print("SUPERUSER (Cross-tenant access):")
    print(f"  Email:    {SUPERUSER['email']}")
    print(f"  Password: {SUPERUSER['password']}")
    print()

    print("TENANT USERS (Password: password123 for all):")
    print()

    for scenario_key, scenario_data in SEED_DATA.items():
        print(f"{scenario_data['company']['name']}:")
        print(f"  Tenant Code: {scenario_data['tenant']['code']}")
        for user in scenario_data['users'][:3]:
            print(f"  - {user['email']}")
        if len(scenario_data['users']) > 3:
            print(f"  ... and {len(scenario_data['users']) - 3} more users")
        print()

    print(f"{'='*70}\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main seeding function."""
    print("\n" + "="*70)
    print("MULTI-TENANT ORGANIZATION SEED")
    print("="*70)
    print("\nThis will seed 5 organizational scenarios:")
    print("  • Tech Startup")
    print("  • Retail Chain")
    print("  • Healthcare Network")
    print("  • Remote-First Tech")
    print("  • Financial Services")
    print("\n" + "="*70)

    response = input("\nDo you want to clear existing data? (yes/no): ").strip().lower()
    clear_data = response == 'yes'

    db = SessionLocal()

    try:
        if clear_data:
            clear_all_data(db)

        # Seed superuser
        seed_superuser(db)

        # Seed all scenarios
        for scenario_key, scenario_data in SEED_DATA.items():
            try:
                seed_scenario(db, scenario_key, scenario_data)
            except Exception as e:
                print(f"\n❌ Error seeding {scenario_key}: {str(e)}")
                import traceback
                traceback.print_exc()
                db.rollback()
                continue

        # Print summary
        print_summary(db)
        print_test_credentials()

        print("✓ All scenarios seeded successfully!")
        print("\nYou can now:")
        print("  1. Start the API server: uvicorn app.main:app --reload")
        print("  2. Test with credentials above")
        print("  3. Explore multi-tenant isolation")

    except Exception as e:
        print(f"\n❌ Seeding failed: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
