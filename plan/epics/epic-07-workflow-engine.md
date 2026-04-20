# Epic 7 — Workflow Engine

> Business process state machines that control entity lifecycle transitions, approval routing, and multi-step process orchestration.

---

## Feature 7.1 — Workflow Design `[DONE]`

### Story 7.1.1 — Workflow Definition Creation `[DONE]`

#### Backend
*As an API, I want to create workflow definitions with states, transitions, and trigger types, so that business processes can be modeled as state machines.*
- `POST /api/v1/workflows` accepts `{name, label, entity_id, trigger_type, canvas_data, trigger_conditions?}`
- `canvas_data` JSONB stores nodes (states) and edges (transitions) with positions for visual rendering
- Trigger types: `manual`, `automatic` (on entity field change), `scheduled`
- Workflow is versioned; `version` increments on each publish

#### Frontend
*As a tenant administrator on the workflows page, I want to open a visual workflow designer with a canvas where I can drag states and draw transitions between them, so that I can model business processes without writing code.*
- Route: `#/nocode/workflows` renders the workflows list; "New Workflow" button navigates to `#/nocode/workflows/new`
- Workflow designer page: split-pane layout — left panel = state/action palette; center = canvas; right panel = selected element properties
- Canvas: drag a "State" card from the palette to add a new state; draw a transition by clicking a state's output port and dragging to another state
- State properties panel (when a state is selected): State Name, Label, Color, Entry Actions, Exit Actions
- Transition properties panel (when a transition is selected): Transition Name, Required Role (who can trigger it), Conditions (field-value rules), Actions to execute
- "Save Draft" button (auto-saves canvas_data); "Publish" button makes the workflow active
- Top toolbar: zoom controls, "Undo" / "Redo" (10-step history), "Fit to screen"

---

### Story 7.1.2 — State Machine Transitions `[DONE]`

#### Backend
*As an API, I want to execute workflow transitions on entity records, so that records move through defined process states with permission and condition checks.*
- `POST /api/v1/workflows/{workflow_id}/records/{record_id}/transition` accepts `{transition_id, reason?}`
- Checks: user has the required role for this transition; current state matches the transition's `from_state`; `trigger_conditions` evaluate to true
- On success: updates `workflow_instance.current_state`; records the transition in `workflow_execution_log`
- Invalid transitions return 400 with `INVALID_STATE_TRANSITION` and `{current_state, allowed_transitions: []}`

#### Frontend
*As a user viewing an entity record that has an active workflow, I want to see the current workflow state prominently and click action buttons for each available transition, so that advancing the process is obvious and one-click.*
- Record detail page header shows: current state chip (colored per state config) + workflow progress bar (showing all states with the current one highlighted)
- "Actions" section below the header: one button per available transition for the current user (buttons hidden for transitions the user lacks permission for)
- Each action button shows the transition label (e.g. "Submit for Approval", "Approve", "Reject")
- Clicking a transition that requires a reason opens a `FlexModal` with a mandatory "Reason / Comment" textarea
- After transition: state chip animates to the new state; action buttons update; a toast confirms "Status changed to [New State]"

---

### Story 7.1.3 — Approval Workflows `[DONE]`

#### Backend
*As an API, I want transitions to support approval steps where designated users must approve before the transition completes, so that multi-stage review processes are enforced.*
- Transition config: `requires_approval: true`, `approver_roles: [role_id]`, `approval_mode: "any_one" | "all"`
- On initiating an approval transition: record enters `awaiting_approval` sub-state; approval requests created in `workflow_approvals` for each required approver
- `POST /api/v1/workflows/approvals/{id}/approve` and `/reject` advance or revert the transition

#### Frontend
*As a manager with pending approvals, I want a dedicated "My Approvals" page that lists all records awaiting my action, so that I can review and approve without searching through entity lists.*
- Route: `#/approvals` renders a list of pending approval requests grouped by workflow name
- Each item shows: record summary (first 3 field values), entity name, submitted by, submitted at, "days waiting" badge (amber > 2 days, red > 5 days)
- "Approve" and "Reject" buttons on each item; clicking either opens a comments modal
- Approve: transitions record to the next state; item removed from list with a green fade-out
- Reject: transitions record back to the previous state; item removed with a red fade-out
- "View Record" link opens the full record detail page in a new tab
- Approval count badge shown on the `#/approvals` menu item in the sidebar navigation

---

## Feature 7.2 — Workflow Execution and Monitoring `[DONE]`

### Story 7.2.1 — Workflow Execution History `[DONE]`

#### Backend
*As an API, I want to return the full transition history for a record, so that auditors can trace the complete workflow lifecycle.*
- `GET /api/v1/workflows/{workflow_id}/records/{record_id}/history` returns `[{from_state, to_state, transitioned_by, transitioned_at, reason, duration_in_state}]`
- Entries are immutable; no updates or deletes on `workflow_execution_log`

#### Frontend
*As an auditor viewing a record's workflow history tab, I want a timeline that shows each state transition with who did it, when, and any comments, so that I can reconstruct the approval process for compliance purposes.*
- Record detail page "Workflow History" tab shows a vertical timeline
- Each timeline node: state change arrow (from → to), actor name + avatar, timestamp, optional reason/comment in a quote block
- Duration badge on each state showing how long the record stayed in that state (e.g. "Stayed 2 days 4 hrs")
- "Download History" button exports the timeline as a PDF for compliance filing
- Superadmin / auditor role can see all transitions; regular users see only their own if restricted

---

### Story 7.2.2 — Active Workflow Monitoring `[DONE]`

#### Backend
*As an API, I want to return counts of records grouped by current workflow state, so that dashboards can show workflow pipeline health.*
- `GET /api/v1/workflows/{workflow_id}/state-counts` returns `{state_name: count}` for all active workflow instances
- Overdue records: `GET /api/v1/workflows/{workflow_id}/overdue?sla_hours=48` returns instances stuck in a state beyond the SLA

#### Frontend
*As a manager on the workflow monitoring page, I want to see a Kanban-style view of how many records are in each workflow state, with overdue items highlighted in red, so that I can spot bottlenecks at a glance.*
- Route: `#/nocode/workflows/{id}/monitor` renders a Kanban board
- Each column = one workflow state; column header shows state name + record count chip
- Records shown as mini-cards (first 2 field values + created date); overdue cards have a red border and a "⚠ X days overdue" badge
- Clicking a card opens the record detail page in a drawer (no full navigation)
- "SLA Threshold" dropdown (24h / 48h / 72h / custom) in the page header updates which records are flagged as overdue
- Auto-refreshes every 60 seconds; a "Last updated X seconds ago" label with a manual refresh button
