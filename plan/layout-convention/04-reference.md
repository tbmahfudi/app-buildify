# Reference: Component Library, Cheat Sheets, and Pattern Map

## Flex Component Quick Reference

### Layout components (page root choices)

`FlexStack` `FlexGrid` `FlexContainer` `FlexSection` `FlexSidebar` `FlexCluster` `FlexToolbar` `FlexMasonry` `FlexSplitPane`

### UI components

`FlexModal` `FlexDrawer` `FlexTable` `FlexDataGrid` `FlexTabs` `FlexStepper` `FlexPagination` `FlexAlert` `FlexBadge` `FlexCard` `FlexButton` `FlexTooltip` `FlexAccordion` `FlexDropdown` `FlexBreadcrumb`

### Form components

`FlexInput` `FlexSelect` `FlexTextarea` `FlexCheckbox` `FlexRadio` `FlexDatepicker`[PLANNED] `FlexFileUpload`[PLANNED] `FlexForm`[PLANNED]

---

## Interaction Cheat Sheet

```
- Interactions:
  - click [target]: [effect]
  - hover [target]: [what reveals / changes]
  - focus [target]: [tooltip shown / helper text appears]
  - blur [target]: [inline validation fires]
  - type in [input]: debounced Xms → [API call or filter]
  - select [option in FlexSelect]: [effect]
  - drag [item] onto [target]: [drop effect]
  - scroll [direction] on [area]: [zoom / pan / infinite-load]
  - keyboard [Key / Ctrl+Key]: [effect]
  - keyboard Escape: closes modal / drawer / dropdown
  - [action] on success: [happy-path effect]
  - [action] on error: FlexAlert(type=error) "[message]" + [recovery option]
```

---

## State Cheat Sheet

```
- States:
  - loading: [N-row skeleton / full-page spinner]
  - empty: [illustration] + "[message]" + [CTA FlexButton]
  - error: FlexAlert(type=error) "[message]" + [Retry link / button]
  - no-permission: FlexAlert(type=warning) "[message]"
  - draft: [what renders in draft mode vs. posted mode]
  - readonly: [inputs disabled / FlexAlert(type=info) "[context]"]
  - conflict: [merge prompt or override option]
```

---

## Common Pattern Map

| Page Type | Root Layout | Primary Component |
|-----------|-------------|-------------------|
| List / table page | `FlexStack(direction=vertical)` | `FlexDataGrid(server-side)` |
| Full-page form | `FlexGrid(columns=2)` | `FlexInput` / `FlexSelect` fields |
| Overlay form | `FlexModal` or `FlexDrawer` | `fields:` notation |
| Tabbed detail | `FlexStack(direction=vertical)` | `FlexTabs` + `tabs:` notation |
| Multi-step wizard | `FlexSplitPane` > stepper, preview | `FlexStepper` + `steps:` notation |
| Designer / canvas | `FlexSplitPane` > palette, canvas, properties | Canvas surface + `FlexDrawer` properties |
| Confirmation dialog | `FlexModal(size=sm)` | `footer: Cancel \| Confirm` |
| Settings page | `FlexSidebar` > section-nav, content | `FlexTabs` or anchored sections |
| Dashboard | `FlexGrid(columns=N, responsive)` | `FlexCard` + chart embeds |

---

## Notation Type Decision Tree

```
Does the story have a page route?
  YES → write Page Layout Block (#1) and Zone Notation (#2)

Does the page have a major data grid, modal, drawer, tabs, or stepper?
  YES → write Component Spec (#3) for each (max 4)

Does the page have a real mobile or tablet experience?
  YES → write Responsive Notation (#4)

Does the page fetch data from an API?
  YES → write State Notation (#5) with at minimum: loading, empty, error

Does the page have user-initiated actions beyond form submission?
  YES → write Interaction Notation (#6)
```
