# impl-notes-T-24-011 -- QA: Password Strength UX (Story 24.2.1)

**Owner**: D1 QA Engineer
**Status**: DONE
**Depends on**: T-24.007, T-24.010

## Deliverables
- Integration tests: backend/tests/integration/test_epic24_auth_password.py
  (TC-24-001 password-policy public + schema; TC-24-002 reset-request enumeration safety
  with identical-message assertion; TC-24-003 reset-confirm invalid/missing token -> 4xx).
- Manual runbook: test-plan-24.md section 3 (TC-24-M01..M04).
- Smoke items: smoke_checklist_24.md "Story 24.2.1".

## Coverage notes
- Endpoints are pre-existing (arch-24 section 5); automated coverage is contract-level
  (auth, schema, enumeration safety, no-5xx). UI-only behaviour is manual.
- **Security item**: history.replaceState token clear (arch-24 3.1) is verified manually
  in TC-24-M01 step 2 -- inspect window.location.hash immediately after confirm-view load.
- **Fail-open**: TC-24-M03 blocks /auth/password-policy and confirms the indicator does
  not permanently block submit and does not crash.
- Rule icon states (ph-circle / ph-x-circle / ph-check-circle) and aria-labels verified
  manually (TC-24-M01 steps 3-5) -- not assertable at the API layer.

## Blocker
- DEF-24-A: app.main import fails (pre-existing T-22 modules.py / module_db_provisioner.py
  regressions, outside Epic 24 scope). Test files pass py_compile; re-run to green after fix.
