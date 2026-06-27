# Epic 24 -- Smoke Checklist (Frontend Capability Surfacing)

> Run on a live dev stack (`docker compose up`) by D1 before test-report-24 sign-off.
> Capture reset links via MailHog (app_buildify_mailhog). Tick each box; note defects inline.
> Cross-references: test-plan-24.md (TC-24-M*), epic-24 ACs, uildc-24 sections.

## Pre-flight
- [ ] Dev stack up: backend, frontend, postgres, redis, mailhog all healthy
- [ ] Logged in as a tenant-admin with at least one entity, one automation rule, one scheduled job, and one builder page with >=2 versions

## Story 24.2.1 -- Password Strength UX (T-24.011)
- [ ] Forgot-password request view submits and shows "Check your inbox" confirmation
- [ ] Reset link captured from MailHog; opening confirm view loads new-password field
- [ ] **SECURITY**: token removed from `window.location.hash` immediately on load (history.replaceState)
- [ ] Weak password -> red bar, failing rules ph-x-circle/red, submit disabled
- [ ] Strong password -> all rules ph-check-circle/green, bar green, submit enabled
- [ ] Each rule item has `aria-label="{rule}: {passed|not met}"`
- [ ] Change Password (Settings -> Security) has strength meter; submit gated end-to-end
- [ ] Fail-open: block `/auth/password-policy` -> field stays usable, no JS crash
- [ ] Missing/expired token -> FlexAlert "Reset link has expired" + "Request new link"; password fields hidden

## Story 24.3.1 -- Data Model Publish UX (T-24.015)
- [ ] Toolbar shows status FlexBadge + "Preview changes" + "Publish" (disabled when clean)
- [ ] "Preview changes" opens diff modal: add table green, remove table red
- [ ] Destructive rows: border-l-4 border-red-500 + ph-warning icon in field-name cell
- [ ] "Publish now" -> status badge updates WITHOUT full page reload + success toast
- [ ] Modal: role=dialog, aria-modal=true, aria-labelledby set; Escape closes unless publishing
- [ ] Drag handle (ph-dots-six-vertical) reorders fields; entity marked dirty
- [ ] Alt+ArrowUp / Alt+ArrowDown reorders; aria-live announces "Field {name} moved to position {n} of {total}"
- [ ] Empty entity -> ph-table icon + "No fields yet" + "Add first field" primary button

## Stories 24.4.1 / 24.4.2 -- Automation Visibility (T-24.021)
- [ ] Rule Test Panel "Run test" success -> success FlexAlert
- [ ] Rule Test Panel error case -> error FlexAlert
- [ ] **SECURITY/UX**: edit rule after test -> stale banner with `role=alert`; prior results opacity-60
- [ ] Pre-run empty state: ph-funnel "No test run yet"
- [ ] Execution History tab loads; columns Started/Status/Duration/Trigger; Status badge `aria-label="Status: {value}"`
- [ ] Pagination page size 25 works; ph-clock empty state when none
- [ ] Date-range + status filter narrows results
- [ ] Row click opens Execution Detail drawer (payload/result/error); Escape closes; focus trapped
- [ ] Keyboard: row Enter opens drawer; ArrowUp/ArrowDown navigate

## Story 24.5.1 -- Scheduler Log Viewer (T-24.024)
- [ ] "History" (ph-clock-clockwise) opens drawer for the CORRECT job
- [ ] Execution list loads; row click populates log pane
- [ ] Log colours: ERROR/CRITICAL red-400, WARN/WARNING yellow-400, default green-400
- [ ] `<pre role="log" aria-live="polite">`; each line own `<span>`
- [ ] Escape closes drawer; focus trapped; aria-modal set
- [ ] **Constraint**: FlexSplitPane(direction=vertical) NOT used (FlexStack + CSS resize handle)

## Story 24.6.1 -- Builder Version History (T-24.029)
- [ ] "History" ghost button opens Version History drawer (right, 320px)
- [ ] Version list items: `aria-label="Version {N}, saved {relative time} by {author}"`; ph-files empty state
- [ ] Preview opens FlexModal(xl); canvas `pointer-events: none`; aria-modal/aria-labelledby; Escape closes
- [ ] Restore -> inline confirm row; ALL other Restore buttons disabled + opacity-50; focus on "Yes, restore"
- [ ] Cancel returns focus to triggering button
- [ ] "Yes, restore" -> success toast + canvas reloads

## Story 24.7.1 -- Dev Tool Cleanup (T-24.031)
- [ ] Removed routes absent from production nav (flex-layout-sandbox, builder-showcase, components-showcase, datatable, debug-financial-module)
- [ ] Direct-URL to each removed route -> dev-banner guard (not broken page)
- [ ] No JS console errors on initial load after deletions

## Sign-off
- [ ] All boxes ticked or defects logged with IDs
- [ ] Integration suite green (after DEF-24-A import fix) -- see test-plan-24.md section 2
- [ ] test-report-24.md updated
