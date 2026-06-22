# D1 Backend Re-verification

Audited by: D1 QA Engineer
Date: 2026-06-22
Repo: /home/mahfudi/app-buildify/modules/healthcare/

## Fix Status

| Fix ID | Status | Notes |
|--------|--------|-------|
| FIX-BE-002 | PASS | modules/sdk/dependencies.py re-exports decode_token (line 11). patient_auth.py imports decode_token from modules.sdk.dependencies — no backend.app import present. |
| FIX-BE-001 | PASS | Two consent GET endpoints exist: GET /patients/me/consents (lines 100-106) using get_current_patient, and GET /branches/{branch_id}/patients/{patient_id}/consents (lines 148-156) using get_current_user. Broken staff_roles == ["patient"] heuristic is gone. |
| FIX-BE-003 | PASS | routes_appointments.py line 189 calls write_phi_read_audit() in the patient appointment list endpoint. |
| FIX-BE-004 | PASS | routes_patients.py calls write_phi_read_audit() at lines 130 and 177, covering both new consent endpoints. |
| FIX-BE-005 | PARTIAL FAIL | contact_phone: Optional[str] = None in schemas/public.py is correct. @limiter.limit("60/minute") decorators are applied syntactically to clinic search/profile endpoints. However the limiter object in routes_public.py is a freshly constructed local Limiter instance — it is never assigned to app.state.limiter and SlowAPIMiddleware is not added. SlowAPI reads request.app.state.limiter at runtime; this limiter will not intercept requests. Decorators are syntactically present but functionally inert. |
| FIX-BE-006 | PASS | routes_appointments.py calls write_event_audit() at lines 78, 143, 271, 332, and 395. The list_available_slots endpoint is covered. |

## New Issues Found

### ISSUE-BE-007 — Rate limiter not wired to FastAPI app (routes_public.py)

**Severity:** High — declared rate limits are silently unenforced.

**Detail:** routes_public.py lines 17-32 create a local Limiter(key_func=get_remote_address) instance. SlowAPI's @limiter.limit() decorator works by reading request.app.state.limiter at request-dispatch time via SlowAPIMiddleware. Because this local instance is never assigned to app.state and no middleware is added, all three @limiter.limit("60/minute") decorators on the public endpoints are no-ops.

The platform already has a correctly configured limiter at backend/app/core/rate_limiter.py (assigned to app.state.limiter in main.py line 226). However importing directly from backend.app would re-introduce the sandbox violation fixed in FIX-BE-002.

**Recommended fix:** Re-export the platform limiter from modules/sdk/dependencies.py (alongside decode_token), then import it in routes_public.py from modules.sdk.dependencies. This keeps the sandbox boundary intact and uses the single shared, registered limiter instance.

## Overall verdict: FAIL

FIX-BE-005 is incomplete: the rate-limiting decorators are present syntactically but the local Limiter instance is never registered with the FastAPI application, so limits are not enforced at runtime. All other fixes (FIX-BE-001, FIX-BE-002, FIX-BE-003, FIX-BE-004, FIX-BE-006) are verified correct and complete. The final sweep confirms zero remaining backend.app imports in the healthcare module.
