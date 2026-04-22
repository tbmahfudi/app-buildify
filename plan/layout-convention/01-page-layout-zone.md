# Notation Types 1 & 2 — Page Layout Block and Zone Notation

## 1. Page Layout Block

Declares the top-level page skeleton immediately after the route bullet.

```
- Route: `#/path` → `template.html` + `page.js`
- Layout: [RootComponent](attrs) > zone-a, zone-b, zone-c
  - zone-a: [Component] — contents | contents
  - zone-b: [Component] — contents
```

### Root layout component choices

| Component | Use case |
|-----------|----------|
| `FlexStack(direction=vertical)` | Top-to-bottom single-column pages |
| `FlexStack(direction=horizontal)` | Side-by-side two-panel pages |
| `FlexGrid(columns=N)` | Multi-column form or card layouts |
| `FlexSidebar(side=left\|right)` | Pages with a fixed sidebar and scrolling main area |
| `FlexSplitPane(initial-split=X%)` | Resizable two-pane designer / explorer pages |
| `FlexSection` | Standalone content section within a page |
| `FlexContainer(fill)` | Full-bleed canvas or map surface |
| `FlexToolbar` | Fixed top or bottom action bar |
| `FlexCluster` | Inline group of wrapping elements |

### Rules

- One root Flex layout component per page.
- Zone labels must be **semantic** (`palette`, `canvas`, `nav-panel`, `summary-panel`) — not generic (`left`, `col1`, `area2`).
- Put layout attributes in parentheses **only** when they materially affect macro structure (e.g. `direction=vertical`, `sidebar-width=300px`, `initial-split=20%`). Skip cosmetic attrs (padding, color).
- The `>` separator means "contains zones"; the zone list after it is just for orientation — the indented lines are the authoritative spec.

### Example

```
- Route: `#/users` → `users.html` + `users.js`
- Layout: FlexStack(direction=vertical) > page-header, content-area
  - page-header: FlexToolbar — "Users" title | FlexBreadcrumb | "Invite User" FlexButton(primary)
  - content-area: FlexSection — filter bar | FlexDataGrid
```

---

## 2. Zone Notation

Describes the contents of each named zone (indented under Layout).

```
  - [zone-label]: [Component](attrs) — [element A] | [element B]
    - [nested-zone]: [Component] — [contents]    ← max one extra nesting level
```

### Rules

- One line per zone.
- `|` separates sibling elements within a zone.
- Max **two levels** of nesting. If you need three, the story is too large — split it.
- When a zone's contents are a single well-known Flex component, name it directly: `- canvas: FlexContainer(fill) — SVG surface`.
- When a zone contains heterogeneous content, describe it with a layout component: `- header: FlexToolbar — [contents]`.

### Example (three-zone designer layout)

```
- Layout: FlexSplitPane(initial-split=20%) > palette, canvas
  - palette: FlexStack(direction=vertical, gap=sm) — toolbar-row | draggable-items
    - toolbar-row: FlexToolbar — title | Save Draft | Publish (primary) | Undo | Redo
    - draggable-items: "State" card | "Transition" card | helper cards
  - canvas: FlexContainer(fill) — SVG drag-drop surface; state nodes; transition arrows
  - (on selection) FlexDrawer(position=right, size=sm, overlay=false) — properties panel
```

### Inline breakpoint shorthand

When only one zone changes at a breakpoint, annotate it inline rather than adding a full `- Responsive:` block:

```
- Layout: FlexSidebar(side=left) > nav, main [md−: nav collapses to icon rail]
  - nav: FlexStack — logo | nav-links
  - main: FlexSection — page content
```
