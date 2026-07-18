"""
Security regression — the clinic_owner sentinel is Company-fenced (ADR-HC-010).

Pins the fix for a CONFIRMED cross-company account-takeover: `get_caller_hc_role`'s
owner sentinel (branch_id IS NULL) used to match on tenant+user only, so an owner of ANY
clinic authorized as owner for ANY other Company's clinic just by passing its branch_id
(reachable via routes_household.staff_link_account -> force-relink a foreign patient's
account email -> takeover). Company is the isolation boundary under the shared SaaS tenant,
so an owner sentinel must only grant owner for branches in the owner's OWN Company.

Runs the REAL SQL in `get_caller_hc_role` against an in-memory SQLite DB (no full module
load, no live stack), so it exercises the actual query — not a Python re-implementation.

Run:
    python -m pytest modules/healthcare/backend/tests/test_hc_role_company_fence.py -q
"""
import importlib.util
import os
import sys
import types

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

_HERE = os.path.dirname(os.path.abspath(__file__))
_PERM_PATH = os.path.normpath(os.path.join(_HERE, "..", "sdk", "hc_permissions.py"))

TENANT = "5aa50000-shared-saas"
CA = "company-A"      # HealthPoint
CB = "company-B"      # MedCare
BR_A1 = "branch-A1"   # HealthPoint Main
BR_A2 = "branch-A2"   # a 2nd HealthPoint branch (same Company)
BR_B1 = "branch-B1"   # MedCare Main
USER_OWNER_A = "user-owner-A"
USER_OWNER_B = "user-owner-B"
USER_MGR_B1 = "user-mgr-B1"
USER_BADSENTINEL = "user-badsentinel"  # owner sentinel with NULL company_id (malformed)


def _load_perms():
    for name in ("modules", "modules.sdk"):
        if name not in sys.modules:
            m = types.ModuleType(name)
            m.__path__ = []
            sys.modules[name] = m
    dep = types.ModuleType("modules.sdk.dependencies")
    dep.tenant_scoped_session = lambda: None
    dep.get_current_user = lambda: None
    sys.modules["modules.sdk.dependencies"] = dep

    spec = importlib.util.spec_from_file_location("hc_perms_under_test", _PERM_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hc_perms_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


perms = _load_perms()


def _db():
    engine = create_engine("sqlite://")
    with engine.begin() as c:
        c.execute(text(
            "CREATE TABLE hc_branches (id TEXT PRIMARY KEY, tenant_id TEXT, platform_company_id TEXT)"
        ))
        c.execute(text(
            "CREATE TABLE hc_branch_staff (id TEXT PRIMARY KEY, tenant_id TEXT, branch_id TEXT, "
            "company_id TEXT, user_id TEXT, role TEXT, status TEXT, is_active BOOLEAN)"
        ))
        for bid, comp in ((BR_A1, CA), (BR_A2, CA), (BR_B1, CB)):
            c.execute(text("INSERT INTO hc_branches VALUES (:i,:t,:c)"),
                      {"i": bid, "t": TENANT, "c": comp})
        rows = [
            # owner sentinels (branch_id NULL) fenced by company_id
            ("s1", TENANT, None, CA, USER_OWNER_A, "clinic_owner", "active", True),
            ("s2", TENANT, None, CB, USER_OWNER_B, "clinic_owner", "active", True),
            # malformed sentinel: NULL company_id must fail closed
            ("s3", TENANT, None, None, USER_BADSENTINEL, "clinic_owner", "active", True),
            # branch-specific manager row for a single B branch
            ("s4", TENANT, BR_B1, None, USER_MGR_B1, "branch_manager", "active", True),
        ]
        for r in rows:
            c.execute(text(
                "INSERT INTO hc_branch_staff VALUES (:id,:t,:b,:c,:u,:r,:s,:a)"
            ), dict(zip(("id", "t", "b", "c", "u", "r", "s", "a"), r)))
    return sessionmaker(bind=engine)()


def _role(db, user, branch):
    r = perms.get_caller_hc_role(db=db, user_id=user, tenant_id=TENANT, branch_id=branch)
    return r.value if r is not None else None


# --- the regression: cross-company owner access is denied --------------------

def test_owner_denied_on_foreign_company_branch():
    db = _db()
    # THE bug: owner of Company A must NOT be owner of Company B's clinic.
    assert _role(db, USER_OWNER_A, BR_B1) is None
    assert _role(db, USER_OWNER_B, BR_A1) is None


# --- legitimate owner access is preserved ------------------------------------

def test_owner_allowed_on_own_company_branches():
    db = _db()
    assert _role(db, USER_OWNER_A, BR_A1) == "clinic_owner"
    # same Company, different branch — the "owner of all my branches" case must still work
    assert _role(db, USER_OWNER_A, BR_A2) == "clinic_owner"
    assert _role(db, USER_OWNER_B, BR_B1) == "clinic_owner"


def test_no_branch_context_reports_owner():
    db = _db()
    # "are you an owner at all?" — no branch to fence against
    assert _role(db, USER_OWNER_A, None) == "clinic_owner"


def test_malformed_sentinel_null_company_fails_closed():
    db = _db()
    assert _role(db, USER_BADSENTINEL, BR_A1) is None
    assert _role(db, USER_BADSENTINEL, BR_B1) is None
    assert _role(db, USER_BADSENTINEL, None) == "clinic_owner"  # no-branch path unchanged


def test_branch_specific_role_still_resolves():
    db = _db()
    assert _role(db, USER_MGR_B1, BR_B1) == "branch_manager"
    # ...but only for their own branch
    assert _role(db, USER_MGR_B1, BR_A1) is None


def test_unknown_user_has_no_role():
    db = _db()
    assert _role(db, "nobody", BR_A1) is None
