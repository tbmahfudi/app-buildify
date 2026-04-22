# Example 1 — List Page (User Management)

This example shows all 6 notation types applied to a standard list page with a toolbar, data grid, and slide-out drawer form.

---

```markdown
#### Frontend
*As a tenant administrator on the users page, I want to invite users, see the full user
list, and manage each user's status from a single page.*

- Route: `#/users` → `users.html` + `users.js`
- Layout: FlexStack(direction=vertical) > page-header, content-area
  - page-header: FlexToolbar — "Users" title | FlexBreadcrumb | "Invite User" FlexButton(primary)
  - content-area: FlexSection — filter bar | FlexDataGrid

- FlexDataGrid(server-side, sortable, selectable) — user list via GET /users
  - columns: Name, Email, Role (FlexBadge), Status (FlexBadge, clickable), Last Login, Actions
  - row action: Edit (pencil, opens FlexDrawer) | Deactivate (toggle) | Delete (trash, confirm modal)
  - bulk action: Deactivate Selected | Export CSV (visible when rows selected)

- FlexDrawer(position=right, size=md) — "Invite User" form, triggered by toolbar button
  - fields: Full Name (FlexInput, required) | Email (FlexInput, type=email, blur duplicate-check) | Role (FlexSelect, multiple) | Status (FlexCheckbox, default=active)
  - footer: Cancel | Save User (primary, spinner on submit)
  - on success: drawer closes; new row at top of grid with FlexBadge(color=success) "New" fading after 3s

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

- States:
  - loading: FlexDataGrid shows 8-row skeleton while GET /users resolves
  - empty: illustration + "No users yet" + "Invite your first user" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load users. Retry?" above the grid

- Responsive:
  - md−: Actions column collapses to per-row "⋮" FlexDropdown; grid shows Name, Email, Status, Actions only
  - sm−: grid switches to card-per-row layout with Name, Status badge, and "⋮" menu
```

---

## Notation types used

| # | Type | Used? | Notes |
|---|------|-------|-------|
| 1 | Page Layout Block | Yes | `FlexStack` root with 2 zones |
| 2 | Zone Notation | Yes | `page-header` and `content-area` described |
| 3 | Component Spec | Yes | `FlexDataGrid` and `FlexDrawer` specified |
| 4 | Responsive Notation | Yes | Tablet and mobile breakpoints |
| 5 | State Notation | Yes | loading, empty, error |
| 6 | Interaction Notation | Yes | 10 interactions covering full user journey |
