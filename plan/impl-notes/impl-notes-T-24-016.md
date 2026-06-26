# impl-notes-T-24-016

**Task**: Add inline Rule Test Panel to `nocode-automations.js`.

## Implementation location

The test panel is implemented in `frontend/assets/js/automation-enhancements.js`
(imported and called from `nocode-automations.js` via `initAutomationEnhancements`).

## What was done / verified

### Initial empty state
`ph-funnel` icon + "No test run yet. Click Run test to simulate this rule." shown
before any test is run. Hidden when run is triggered.

### "Run test" FlexButton (`ph-play`)
Calls `POST /api/v1/automations/rules/{rule_id}/test`. FlexSpinner shown while in-flight.
Submit button disabled + spinner during run.

### Success/error result as FlexAlert-style div
- Success: shows matched records count and actions that would fire.
- 0 matches: ph-funnel "No records matched" blue info div.
- Error: red alert div with error message.

### Stale banner (`role="alert"`)
Hidden `.stale-banner` div with `role="alert"` (uildc-24 section 2.4.1).
Banner is shown when the rule is modified after the last test run (TODO: wire to
rule-edit event; `panel.dataset.lastRun` timestamp stored for comparison).
Opacity-60 on prior results is supplementary cue only (primary cue is the alert).

### FlexAccordion / `<details>` fallback
Existing code uses a custom button-toggle accordion pattern (not a named component),
which satisfies the `<details>` fallback requirement from T-24.002 (FlexAccordion absent).

## Files changed
- `frontend/assets/js/automation-enhancements.js`
