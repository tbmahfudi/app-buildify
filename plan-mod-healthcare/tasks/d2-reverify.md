# D2 Re-verification

Reviewer: D2 (automated re-check, 2026-06-22)
Context: Verifying C4 fixes against findings in d2-code-review.md

| Finding | Status | Notes |
|---------|--------|-------|
| CR-001 Double commit in pharmacy | FAIL | create_prescription (line 508) has two db.commit() calls: line 585 (after INSERTs) and line 598 (after audit write). Audit event is written post-commit then committed again. Should be: write audit before first commit, then single commit. |
| CR-002 Stock adjust race condition | PASS | adjust_stock path (lines 388-418): uses FOR UPDATE lock then SET stock_quantity = stock_quantity + :adj (atomic arithmetic). Dispense path (lines 742-764) also uses FOR UPDATE lock; uses computed new_stock variable but lock prevents concurrent reads so race is closed. |
| CR-003 Partial results marking order as resulted | PASS | Lines 801-811: counts total_lines and resulted_lines, sets order status to "resulted" only when resulted_lines >= total_lines and total_lines > 0, otherwise "processing". Correct guard present. |
| CR-004 Hardcoded actor_id="staff" | PASS | grep returns 0 matches in routes_lab.py. |
| CR-005 SET LOCAL string interpolation | PASS | No SET LOCAL or f-string SET in branch_scope.py. Lines 164-165 use SELECT set_config('app.tenant_id', :val, true) parameterised calls. Comment lines mention SET LOCAL descriptively but do not execute it. |
| CR-010 finalize/void missing tenant filter | PASS | Both finalize_invoice and void_invoice call _fetch_invoice(db, invoice_id, branch_id, tenant_id) first (validates ownership) then UPDATE with WHERE id=:id AND tenant_id=:tid AND branch_id=:bid. Full tenant+branch filter present in both. |
| CR-014 Missing unique constraint | PASS | Migration hcs_001_scheduling_tables.py lines 60-61: op.create_unique_constraint("uq_hcs_slot_provider_datetime", ...) present. |
| CR-015 Slot query tenant filter | PASS | routes_appointments.py lines 68-71: query has WHERE s.tenant_id=:tid AND s.branch_id=:bid. Comment explicitly marks the CR-015 fix. |
| CR-008/CR-009 N+1 queries | PASS | No for-in-db.query or for-in-prescriptions patterns found in routes_pharmacy.py. |

## Remaining open items

### CR-001 -- Double commit in create_prescription (FAIL -- not fixed)

In routes_pharmacy.py, function create_prescription (line 508):

- line 585: db.commit()         # commits INSERT header + lines
- ...        write_event_audit() # audit written AFTER commit -- not atomic with data
- line 598: db.commit()         # second commit for audit row alone

Risk: If the process crashes between lines 585 and 598, the prescription exists in the DB but has no audit trail. The two-commit pattern was the original finding (CR-001) -- C4 appears to have fixed other functions but missed this one.

Fix: Move write_event_audit(...) to before the first db.commit() and remove the second db.commit(). Single commit makes the prescription data and audit atomic.

## Verdict: PARTIAL

7 of 8 checked findings are PASS. CR-001 is NOT fixed in create_prescription. All other MAJOR and BLOCKER findings (CR-002, CR-003, CR-004, CR-005, CR-010, CR-014, CR-015) are confirmed resolved. CR-008/CR-009 N+1 patterns are gone.

Action required: C4 must fix the double commit in create_prescription before this module is cleared for merge.
