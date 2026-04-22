# Example 3 — Canvas / Designer Page (Workflow Designer)

This example shows a drag-and-drop visual designer with a resizable split-pane, a draggable node palette, an SVG canvas, and a slide-in properties panel.

---

```markdown
#### Frontend
*As a tenant administrator, I want a visual workflow designer with a drag-and-drop canvas
to model business process states and transitions without writing code.*

- Route: `#/nocode/workflows/{id}/edit` → `workflow-designer.html` + `workflow-designer-page.js`
- Layout: FlexSplitPane(initial-split=20%) > palette, canvas
  - palette: FlexStack(direction=vertical, gap=sm) — toolbar-row | draggable-items
    - toolbar-row: FlexToolbar — title | Save Draft | Publish (primary) | Undo | Redo | Fit Screen
    - draggable-items: "State" card | "Transition" card | helper action cards
  - canvas: FlexContainer(fill) — SVG drag-drop surface; state nodes; transition arrows
  - (on selection) FlexDrawer(position=right, size=sm, overlay=false) — properties panel
    - state selected: State Name (FlexInput) | Color (picker) | Entry/Exit Actions (FlexAccordion)
    - transition selected: Name (FlexInput) | Required Role (FlexSelect) | Conditions (FlexAccordion)

- FlexModal(size=sm) — Publish confirm, triggered by Publish button
  - footer: Cancel | Publish Workflow (FlexButton, variant=primary)
  - on confirm: POST /workflows/{id}/publish → toolbar badge updates to "Published"

- FlexModal(size=sm) — dirty-navigation guard
  - triggered: on any route change when canvas has unsaved changes
  - footer: Stay | Leave without saving
  - on confirm (Leave): discards changes and navigates away

- Interactions:
  - drag State card from palette onto canvas: creates state node at drop position → properties panel opens
  - click state node: selects it (highlighted border) → properties panel shows state config
  - drag from state output port to another state: draws a transition arrow → properties panel switches to transition config
  - double-click state node label: inline rename input; Enter confirms; Escape cancels
  - click canvas background: deselects all; properties panel closes
  - click transition arrow: selects it → properties panel shows transition config
  - drag placed state node: repositions on canvas; connected arrows follow
  - keyboard Delete (node selected): removes node → FlexModal confirm if node has active workflow records
  - keyboard Ctrl+Z: undo last action (up to 10 steps)
  - keyboard Ctrl+Y: redo
  - keyboard Ctrl+S: triggers Save Draft
  - scroll with Ctrl held: zooms canvas in/out
  - middle-mouse drag or two-finger pan: pans the canvas
  - click "Publish": opens confirm FlexModal → POST /workflows/{id}/publish → badge updates
  - navigate away with unsaved changes: dirty-state guard FlexModal "Leave without saving?"

- States:
  - empty-canvas: centered hint card "Drag a State from the palette to start"
  - saving: toolbar Save button shows spinner; canvas interactions remain enabled
  - published: Publish button replaced by FlexBadge(color=success) "Published" + "Create New Version" button
  - readonly: nodes non-draggable; FlexAlert(type=info) "Viewing published version" pinned at top

- Responsive:
  - lg+: FlexSplitPane three-region layout (palette | canvas | properties drawer inline)
  - md−: palette collapses to FlexDrawer toggled by toolbar "Palette" button; properties become bottom FlexDrawer
  - sm−: canvas-only view; palette and properties accessible via floating action buttons
```

---

## Notation types used

| # | Type | Used? | Notes |
|---|------|-------|-------|
| 1 | Page Layout Block | Yes | `FlexSplitPane` with palette and canvas zones |
| 2 | Zone Notation | Yes | Two-level nesting inside palette; conditional drawer zone |
| 3 | Component Spec | Yes | Two `FlexModal` instances specified separately |
| 4 | Responsive Notation | Yes | All three breakpoints — desktop default is three-pane |
| 5 | State Notation | Yes | empty-canvas, saving, published, readonly |
| 6 | Interaction Notation | Yes | 15 interactions covering drag, select, keyboard, zoom, guard |
