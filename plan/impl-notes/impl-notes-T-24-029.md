# impl-notes-T-24-029 -- QA: Builder Version History (Story 24.6.1)

**Owner**: D1 QA Engineer
**Status**: DONE
**Depends on**: T-24.026, T-24.027

## Deliverables
- Integration tests: backend/tests/integration/test_epic24_builder.py (NEW)
  (TC-24-011 versions list auth + 403/404 + list shape; TC-24-012 version detail auth +
  403/404 + non-integer version -> 422; TC-24-013 restore auth + 400/403/404 +
  non-integer version -> 422).
- Manual runbook: test-plan-24.md section 7 (TC-24-M25..M30).
- Smoke items: smoke_checklist_24.md "Story 24.6.1".

## Coverage notes
- History toolbar button -> drawer open, version-item aria-labels
  ("Version {N}, saved {relative time} by {author}"), and ph-files empty state verified
  manually (TC-24-M25..M26).
- Preview modal with canvas pointer-events:none + Escape close: TC-24-M27.
- **Concurrent-restore prevention** (uildc-24 2.6): inline confirm row disables ALL other
  Restore buttons (opacity-50); focus moves to "Yes, restore"; Cancel returns focus to the
  triggering button -- TC-24-M28..M29. This is the security/UX-critical behaviour.
- Successful restore reloads canvas + success toast: TC-24-M30.

## Blocker
- DEF-24-A (see test-plan-24.md section 2). Test file passes py_compile; re-run after fix.
