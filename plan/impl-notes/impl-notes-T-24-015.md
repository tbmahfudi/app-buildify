# impl-notes-T-24-015 -- QA: Data Model Publish UX (Story 24.3.1)

**Owner**: D1 QA Engineer
**Status**: DONE
**Depends on**: T-24.013, T-24.014

## Deliverables
- Integration tests: backend/tests/integration/test_epic24_data_model.py
  (TC-24-004 preview-migration auth + 404 + no-5xx; TC-24-005 publish auth + 404 +
  missing-body handling).
- Manual runbook: test-plan-24.md section 4 (TC-24-M05..M11).
- Smoke items: smoke_checklist_24.md "Story 24.3.1".

## Coverage notes
- preview-migration and publish need a real DataModelService over SQLite, so automated
  coverage is structural (auth guard, request shape, 404 guard, no-5xx). Diff content,
  badge-update-without-reload, and toolbar wiring are manual.
- Destructive-field affordance (border-l-4 border-red-500 + ph-warning, uildc-24 2.3.2)
  verified in TC-24-M06.
- Drag-reorder persistence + dirty-marking: TC-24-M09. Keyboard reorder with aria-live
  announcement "Field {name} moved to position {n} of {total}": TC-24-M10.
- Empty state (ph-table + "No fields yet" + "Add first field"): TC-24-M11.

## Blocker
- DEF-24-A (see test-plan-24.md section 2): pre-existing T-22 import regression blocks
  collection. Test file passes py_compile; re-run to green after fix.
