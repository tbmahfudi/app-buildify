# Notation Types 3 & 4 — Component Spec and Responsive Notation

## 3. Component Spec Notation

Specifies a major UI component with its key attributes and behaviors.

```
- [FlexComponent](attr=val, attr=val) — [purpose]
  - columns: Col1, Col2(badge), Col3, Actions
  - fields: Name (FlexInput, required) | Role (FlexSelect, multiple)
  - tabs: Tab1 | Tab2 | Tab3
  - steps: 1. Step | 2. Step | 3. Step
  - row action: Edit | Delete (confirm modal)
  - on [trigger]: [effect]
```

### Sub-keys by component type

| Component | Sub-keys to use |
|-----------|----------------|
| `FlexDataGrid` / `FlexTable` | `columns:`, `row action:`, `bulk action:`, `on row-change:` |
| `FlexModal` / `FlexDrawer` | `fields:`, `footer:`, `on success:`, `on error:` |
| `FlexTabs` | `tabs:` |
| `FlexStepper` | `steps:` |
| `FlexForm` | `fields:`, `on submit:` |
| Any | `on [trigger]: [effect]` |

### `on [trigger]: [effect]` patterns

- `on success: drawer closes; new row appears at top of grid`
- `on row-change: summary panel totals recalculate instantly`
- `on blur: inline duplicate-email check`
- `on confirm: POST /endpoint → redirect to detail`

### Rules

- Use Component Spec for `FlexDataGrid`, `FlexModal`, `FlexDrawer`, `FlexTabs`, `FlexStepper`, `FlexForm`.
- **Skip** full specs for ambient components (`FlexAlert`, `FlexBadge`, `FlexButton`, `FlexBreadcrumb`) — describe them inline inside Layout or Interaction lines.
- **1–4 Component Specs per story maximum.** More = story is too large.
- Attributes in parentheses are for things that affect behaviour or appearance meaningfully (`server-side`, `sortable`, `size=md`, `position=right`). Skip cosmetic or default attrs.

### Example

```
- FlexDataGrid(server-side, sortable, selectable) — user list via GET /users
  - columns: Name, Email, Role (FlexBadge), Status (FlexBadge, clickable), Last Login, Actions
  - row action: Edit (opens FlexDrawer) | Deactivate (toggle) | Delete (confirm modal)
  - bulk action: Deactivate Selected | Export CSV (visible when rows selected)

- FlexDrawer(position=right, size=md) — "Invite User" form
  - fields: Full Name (FlexInput, required) | Email (FlexInput, type=email, blur duplicate-check) | Role (FlexSelect, multiple) | Status (FlexCheckbox, default=active)
  - footer: Cancel | Save User (primary, spinner on submit)
  - on success: drawer closes; new row appears at top of grid with FlexBadge(color=success) "New" fading after 3s
```

---

## 4. Responsive Notation

Describes layout changes at specific breakpoints. The **default is `lg+` (desktop)**.

```
- Responsive:
  - lg+: [desktop-only changes]
  - md−: [tablet changes relative to desktop default]
  - sm−: [mobile changes]
```

### Breakpoints

| Token | Min-width | Common target |
|-------|-----------|---------------|
| `xs` | 0 px | very small mobile |
| `sm` | 640 px | mobile landscape |
| `md` | 768 px | tablet |
| `lg` | 1024 px | small desktop (default) |
| `xl` | 1280 px | large desktop |

Suffix `+` = "this width and above"; suffix `−` = "this width and below".

### Rules

- Required **only** for pages with a genuine mobile/tablet experience.
- Skip for superadmin-only pages, designer/canvas pages, or any page explicitly scoped to desktop only.
- Describe changes **relative to the desktop default** — don't repeat what stays the same.
- Use inline shorthand (see Zone Notation) when only one zone changes.

### Example

```
- Responsive:
  - md−: Actions column collapses to per-row "⋮" FlexDropdown; grid shows Name, Email, Status, Actions only
  - sm−: grid switches to card-per-row layout with Name, Status badge, and "⋮" menu
```

```
- Responsive:
  - lg+: FlexSplitPane three-region layout (palette | canvas | properties)
  - md−: palette collapses to FlexDrawer toggled by toolbar "Palette" button; properties become bottom FlexDrawer
  - sm−: canvas-only; palette and properties via floating action buttons
```
