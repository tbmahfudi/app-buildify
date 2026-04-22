# Notation Types 5 & 6 — State Notation and Interaction Notation

## 5. State Notation

Describes what renders in each significant UI state.

```
- States:
  - loading: [skeleton / spinner description]
  - empty: [illustration + CTA description]
  - error: FlexAlert(type=error) "[message]" + [recovery action]
  - [custom]: [description]
```

### Standard states

| State | When to document |
|-------|-----------------|
| `loading` | Required for any page that fetches API data |
| `empty` | Required — what shows when the data set is empty |
| `error` | Required — API failure or network error |
| `no-permission` | When the page is reachable but the user lacks access |
| `draft` | When a resource has a distinct draft vs. published state |
| `readonly` | When a normally-editable page can be locked |
| `conflict` | When optimistic updates can collide |
| any custom | Only when the story explicitly requires distinct UI treatment |

### Rules

- `loading` + `empty` + `error` are required for all data-fetching pages.
- Name Flex components explicitly: `FlexAlert(type=error)`, `8-row skeleton`, not vague prose like "a spinner shows".
- Custom states appear only when the page renders something visually distinct — not just a different API response.

### Example

```
- States:
  - loading: FlexDataGrid shows 8-row skeleton while GET /users resolves
  - empty: illustration + "No users yet" + "Invite your first user" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load users. Retry?" above the grid
  - no-permission: FlexAlert(type=warning) "You do not have access to manage users."
```

---

## 6. Interaction Notation

Describes all user actions on the page and their outcomes. Distinct from State Notation (what renders) and Component Spec (structure). Use it to make explicit what the user **can do** and **what happens**.

```
- Interactions:
  - [action verb] [target]: [effect]
  - [action verb] [target]: [effect] → [next step]
  - keyboard [Key / Ctrl+Key]: [effect]
  - drag [source] onto [target]: [effect]
```

### Action verbs

`click` · `hover` · `focus` · `blur` · `type` · `select` · `drag` · `drop` · `scroll` · `swipe` · `long-press` · `keyboard`

### Effect patterns

| Pattern | Syntax |
|---------|--------|
| Navigation | `→ navigates to #/path` |
| API call | `→ GET/POST/PUT/DELETE /endpoint → [result]` |
| UI open | `→ opens FlexModal(size=sm)` / `→ opens FlexDrawer(position=right)` |
| UI close | `→ closes FlexDrawer` / `→ closes FlexModal` |
| State change | `→ [component] enters [state-name] state` |
| Toast / alert | `→ FlexAlert(type=success) "Saved"` |
| Chained | `→ [immediate effect] → [subsequent effect]` |

### Rules

- List **every meaningful user action**, not just the happy path.
- Chain multi-step flows with `→`.
- Group by area when the page has many interaction zones.
- List keyboard shortcuts and accessibility actions explicitly when they exist.
- **Do NOT duplicate** interactions already covered by `on [trigger]:` inside a Component Spec — use Interaction Notation for page-level or cross-component flows.

### Example (list page)

```
- Interactions:
  - click "Invite User" button: opens FlexDrawer(position=right) invite form
  - click row: navigates to `#/users/{id}`
  - hover row: reveals Edit | Deactivate | Delete action icons
  - click Status badge: opens FlexModal(size=sm) confirm → PATCH /users/{id}/status
  - click Delete icon: FlexModal "Delete [Name]? This cannot be undone." → DELETE /users/{id} → row fades out
  - type in search bar: debounced 300ms → GET /users?search=[term] → grid refreshes
  - click column header: toggles sort asc/desc → GET /users?sort=[col]&order=[dir]
  - select rows + click bulk action: acts on all selected; deselects rows after completion
  - keyboard Escape: closes open drawer or modal
  - keyboard Tab: moves focus through rows; Enter opens focused row
```

### Example (canvas page)

```
- Interactions:
  - drag State card from palette onto canvas: creates state node at drop position → properties panel opens
  - click state node: selects it (highlighted border) → properties panel shows state config
  - drag from state output port to another state: draws a transition arrow → properties panel switches to transition config
  - double-click state node label: inline rename input; Enter confirms; Escape cancels
  - click canvas background: deselects all; properties panel closes
  - keyboard Delete (node selected): removes node → FlexModal confirm if node has active records
  - keyboard Ctrl+Z: undo last action (up to 10 steps)
  - keyboard Ctrl+Y: redo
  - keyboard Ctrl+S: triggers Save Draft
  - scroll with Ctrl held: zooms canvas in/out
  - middle-mouse drag or two-finger pan: pans the canvas
  - navigate away with unsaved changes: dirty-state guard FlexModal "Leave without saving?"
```
