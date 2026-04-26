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
- Route (list): `#/nocode/workflows` → `workflows.html` + `workflows-page.js`
- Route (designer): `#/nocode/workflows/new` and `#/nocode/workflows/{id}/edit` → `workflow-designer.html` + `workflow-designer-page.js`
- Layout (designer): FlexSplitPane(initial-split=20%) > palette, canvas
  - palette: FlexStack(direction=vertical, gap=sm) — toolbar-row | draggable-items
    - toolbar-row: FlexToolbar — workflow name | Save Draft | Publish (primary) | Undo | Redo | Fit Screen | zoom controls
    - draggable-items: "State" card | "Transition" card
  - canvas: FlexContainer(fill) — SVG drag-drop surface; state nodes; transition arrows
  - (on state selected) FlexDrawer(position=right, size=sm, overlay=false) — state properties
    - fields: State Name (FlexInput) | Label (FlexInput) | Color (picker) | Entry Actions (FlexAccordion) | Exit Actions (FlexAccordion)
  - (on transition selected) FlexDrawer(position=right, size=sm, overlay=false) — transition properties
    - fields: Transition Name (FlexInput) | Required Role (FlexSelect) | Conditions (FlexAccordion) | Actions (FlexAccordion)

- FlexModal(size=sm) — Publish confirm
  - footer: Cancel | Publish Workflow (primary)
  - on confirm: POST /workflows/{id}/publish → badge updates to FlexBadge(color=success) "Published"

- Interactions:
  - drag State card onto canvas: creates state node at drop position → state properties drawer opens
  - click state node: selects it → state properties drawer shows state config
  - drag from state output port to another state: draws transition arrow → transition properties drawer opens
  - double-click state node label: inline rename input; Enter confirms; Escape cancels
  - click canvas background: deselects all; properties drawer closes
  - drag placed state node: repositions; connected arrows follow
  - keyboard Delete (node selected): removes node → FlexModal confirm if node has active records
  - keyboard Ctrl+Z / Ctrl+Y: undo / redo (up to 10 steps)
  - keyboard Ctrl+S: triggers Save Draft
  - Ctrl+scroll: zooms canvas; two-finger pan / middle-mouse drag: pans canvas
  - navigate away with unsaved changes: dirty-state guard FlexModal "Leave without saving?"

- States:
  - empty-canvas: centered hint "Drag a State from the palette to start"
  - saving: Save Draft button shows spinner; canvas remains interactive
  - published: Publish button replaced by FlexBadge(color=success) "Published" + "Create New Version"
  - readonly: nodes non-draggable; FlexAlert(type=info) "Viewing published version" at top

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
- Route: `#/dynamic/{entity}/{id}` → record detail page (workflow section in header, shown when entity has an active workflow)
- Layout addition (workflow-aware detail page): FlexStack(direction=vertical) > workflow-header, actions-bar, field-values
  - workflow-header: FlexCluster — current state FlexBadge(color per state config) | workflow progress bar (all states, current highlighted)
  - actions-bar: FlexCluster — one FlexButton per available transition (hidden for transitions the user lacks permission for)

- FlexModal(size=sm) — transition reason, triggered by clicking a transition that requires a reason
  - fields: Reason / Comment (FlexTextarea, required)
  - footer: Cancel | Confirm Transition (primary)
  - on confirm: POST /workflows/{workflow_id}/records/{record_id}/transition → state chip animates to new state; actions-bar re-renders; toast "Status changed to [New State]"

- Interactions:
  - click transition button (no reason required): POST /workflows/{workflow_id}/records/{record_id}/transition immediately
  - click transition button (reason required): opens reason FlexModal(size=sm)
  - confirm transition: state chip animates to new state; actions-bar updates with new available transitions; toast shown

---

### Story 7.1.3 — Approval Workflows `[DONE]`

#### Backend
*As an API, I want transitions to support approval steps where designated users must approve before the transition completes, so that multi-stage review processes are enforced.*
- Transition config: `requires_approval: true`, `approver_roles: [role_id]`, `approval_mode: "any_one" | "all"`
- On initiating an approval transition: record enters `awaiting_approval` sub-state; approval requests created in `workflow_approvals` for each required approver
- `POST /api/v1/workflows/approvals/{id}/approve` and `/reject` advance or revert the transition

#### Frontend
*As a manager with pending approvals, I want a dedicated "My Approvals" page that lists all records awaiting my action, so that I can review and approve without searching through entity lists.*
- Route: `#/approvals` → `approvals.html` + `approvals-page.js`
- Layout: FlexStack(direction=vertical) > page-header, approvals-list
  - page-header: FlexToolbar — "My Approvals" title | approval count FlexBadge
  - approvals-list: FlexStack(gap=sm) — approval items grouped by workflow name (FlexSection per group)
    - each item: record summary (first 3 field values) | entity name | submitted by + at | "X days waiting" FlexBadge(color=amber >2d, color=danger >5d) | "View Record" link (opens new tab) | "Approve" FlexButton(primary) | "Reject" FlexButton(ghost, danger)

- FlexModal(size=sm) — approve/reject comments, triggered by either button
  - fields: Comment (FlexTextarea, optional for approve, required for reject)
  - footer: Cancel | Confirm (primary)
  - on approve confirm: POST /workflows/approvals/{id}/approve → item fades out green
  - on reject confirm: POST /workflows/approvals/{id}/reject → item fades out red

- Interactions:
  - click "Approve": opens comments FlexModal; confirm → item green fade-out
  - click "Reject": opens comments FlexModal (comment required); confirm → item red fade-out
  - click "View Record": opens record detail in new tab
  - sidebar nav "Approvals" menu item: shows live count FlexBadge (updates on page load)

- States:
  - loading: approval items show skeleton while GET /workflows/approvals resolves
  - empty: illustration + "No pending approvals" message

---

## Feature 7.2 — Workflow Execution and Monitoring `[DONE]`

### Story 7.2.1 — Workflow Execution History `[DONE]`

#### Backend
*As an API, I want to return the full transition history for a record, so that auditors can trace the complete workflow lifecycle.*
- `GET /api/v1/workflows/{workflow_id}/records/{record_id}/history` returns `[{from_state, to_state, transitioned_by, transitioned_at, reason, duration_in_state}]`
- Entries are immutable; no updates or deletes on `workflow_execution_log`

#### Frontend
*As an auditor viewing a record's workflow history tab, I want a timeline that shows each state transition with who did it, when, and any comments, so that I can reconstruct the approval process for compliance purposes.*
- Route: `#/dynamic/{entity}/{id}` → record detail page "Workflow History" tab

- FlexTabs addition — "Workflow History" tab (alongside Details, Related):
  - vertical timeline (GET /workflows/{workflow_id}/records/{record_id}/history)
  - each node: from-state → to-state arrow | actor avatar + name | timestamp | duration FlexBadge "Stayed X days Y hrs" | optional reason/comment in a quote block
  - "Download History" FlexButton(ghost) at top → exports timeline as PDF

- Interactions:
  - click "Workflow History" tab: GET /workflows/{workflow_id}/records/{record_id}/history → timeline renders
  - click "Download History": POST /workflows/{workflow_id}/records/{record_id}/history/export → PDF download

- States:
  - loading: timeline shows skeleton nodes while history resolves
  - empty: "No transitions recorded yet"
  - restricted (regular user): only transitions involving current user shown; FlexAlert(type=info) "Showing your transitions only"

---

### Story 7.2.2 — Active Workflow Monitoring `[DONE]`

#### Backend
*As an API, I want to return counts of records grouped by current workflow state, so that dashboards can show workflow pipeline health.*
- `GET /api/v1/workflows/{workflow_id}/state-counts` returns `{state_name: count}` for all active workflow instances
- Overdue records: `GET /api/v1/workflows/{workflow_id}/overdue?sla_hours=48` returns instances stuck in a state beyond the SLA

#### Frontend
*As a manager on the workflow monitoring page, I want to see a Kanban-style view of how many records are in each workflow state, with overdue items highlighted in red, so that I can spot bottlenecks at a glance.*
- Route: `#/nocode/workflows/{id}/monitor` → `workflow-monitor.html` + `workflow-monitor-page.js`
- Layout: FlexStack(direction=vertical) > page-header, kanban-board
  - page-header: FlexToolbar — workflow name | SLA Threshold (FlexSelect: 24h | 48h | 72h | custom) | "Last updated X seconds ago" label | Refresh FlexButton(ghost)
  - kanban-board: FlexGrid(columns=auto, gap=md) — one column per workflow state

- Kanban column per state:
  - header: state name + record count FlexBadge
  - body: FlexStack(gap=sm) — mini-card per record (first 2 field values + created date)
  - overdue mini-card: red border + FlexBadge(color=danger) "⚠ X days overdue"

- FlexDrawer(position=right, size=md) — record detail, triggered by clicking a mini-card
  - shows full record detail inline (no page navigation)

- Interactions:
  - change SLA Threshold: GET /workflows/{id}/overdue?sla_hours=X → overdue badges re-evaluate; board re-renders
  - click mini-card: opens record detail FlexDrawer(position=right)
  - click Refresh: manual GET /workflows/{id}/state-counts → board re-renders
  - auto-refresh: board polls every 60s; "Last updated X seconds ago" counter ticks

- States:
  - loading: kanban columns show skeleton cards
  - empty column: column shows "No records in this state"
  - error: FlexAlert(type=error) "Could not load workflow data. Retry?"
