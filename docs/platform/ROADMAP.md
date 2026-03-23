# Platform Roadmap

This document tracks the release history of the Flex Component Library and the planned feature roadmap for the App-Buildify platform.

---

## Release History

### v1.0.0 — 2024-10-30 (Current)

**Initial production release.**

#### Foundation
- `BaseComponent` — lifecycle management for all components
- `FlexResponsive` — breakpoint detection singleton
- Event system — `emit()` / `on()` for component communication
- `ui-utils` — toast notifications, loading spinners

#### Layout Components
- `FlexStack` — vertical/horizontal linear layout
- `FlexGrid` — responsive column grid
- `FlexContainer` — max-width centered wrapper
- `FlexSection` — full-width page section
- `FlexSidebar` — collapsible navigation sidebar
- `FlexCluster` — horizontal wrapping group
- `FlexToolbar` — sticky/fixed header and footer bars
- `FlexMasonry` — masonry/Pinterest-style grid
- `FlexSplitPane` — resizable split panels

#### UI Components
- `FlexCard` — card container with header/body/footer slots
- `FlexModal` — accessible modal dialog
- `FlexTabs` — tab navigation
- `FlexDataGrid` — sortable, filterable data table
- `FlexBadge` — label badges
- `FlexStepper` — step progress indicator

**Bundle size**: Core ~12KB gzipped | Full library ~38KB gzipped

---

### v0.3.0 — 2024-10-28

Phase 2 complete: `FlexContainer`, `FlexSection`, `FlexSidebar`

---

### v0.2.0 — 2024-10-26

Foundation MVP: `BaseComponent`, `FlexResponsive`, `FlexStack`, `FlexGrid`, `FlexCard`, `FlexModal`, `FlexTabs`

---

### v0.1.0 — 2024-10-24

Initial prototype — internal proof of concept

---

## Current Component Status

The following components are **fully implemented** in the codebase (`frontend/assets/js/components/`):

### Form Components (Implemented — not in original roadmap)

| Component | File | Status |
|-----------|------|--------|
| `FlexInput` | `flex-input.js` | ✅ Implemented |
| `FlexSelect` | `flex-select.js` | ✅ Implemented |
| `FlexCheckbox` | `flex-checkbox.js` | ✅ Implemented |
| `FlexRadio` | `flex-radio.js` | ✅ Implemented |
| `FlexTextarea` | `flex-textarea.js` | ✅ Implemented |
| `FlexAccordion` | `flex-accordion.js` | ✅ Implemented |
| `FlexBreadcrumb` | `flex-breadcrumb.js` | ✅ Implemented |
| `FlexTooltip` | `flex-tooltip.js` | ✅ Implemented |
| `FlexPagination` | `flex-pagination.js` | ✅ Implemented |

### Additional UI Components (Implemented)

| Component | File | Status |
|-----------|------|--------|
| `FlexAlert` | `flex-alert.js` | ✅ Implemented |
| `FlexButton` | `flex-button.js` | ✅ Implemented |
| `FlexDrawer` | `flex-drawer.js` | ✅ Implemented |
| `FlexDropdown` | `flex-dropdown.js` | ✅ Implemented |
| `FlexSpinner` | `flex-spinner.js` | ✅ Implemented |
| `FlexTable` | `flex-table.js` | ✅ Implemented |

---

## Planned / Not Yet Implemented

The following were planned in Phase 4 documentation but **do not exist** in the current codebase:

| Component | Priority | Description |
|-----------|----------|-------------|
| `FlexDatepicker` | High | Date/datetime picker with calendar UI |
| `FlexFileUpload` | High | File drag-and-drop upload with preview |
| `FlexForm` | High | Form container with validation orchestration |
| `FlexNotification` | Medium | Toast/notification system (distinct from ui-utils) |
| `FlexProgress` | Medium | Progress bar and circular progress indicator |

### Platform Features (Documented, Not Implemented)

| Feature | Specification | Notes |
|---------|--------------|-------|
| Prometheus monitoring | TECHNICAL_SPECIFICATION.md | `prometheus-client` in requirements.txt but no config or scraping endpoint wired up |
| TypeScript definitions | CHANGELOG.md roadmap | No `.d.ts` files exist |
| 2FA / Multi-factor auth | FUNCTIONAL_SPECIFICATION.md | Described as "short-term" enhancement |
| SSO / SAML | FUNCTIONAL_SPECIFICATION.md | Described as future integration |
| AI/ML features | FUNCTIONAL_SPECIFICATION.md | Long-term roadmap item |
| White-label theming | FUNCTIONAL_SPECIFICATION.md | Long-term roadmap item |
| Module marketplace | FUNCTIONAL_SPECIFICATION.md | Described but UI not implemented |
| Subscription tier enforcement | FUNCTIONAL_SPECIFICATION.md | Tiers defined (Free/Basic/Premium/Enterprise) but not enforced in code |
| Cloud storage integration | FUNCTIONAL_SPECIFICATION.md | S3/GCS mentioned, not implemented |
| Webhooks | FUNCTIONAL_SPECIFICATION.md | Listed as integration capability, not implemented |
| Storybook component explorer | CHANGELOG.md roadmap | Not set up |

---

## v1.1.0 — Planned

- `FlexDatepicker` — date/datetime picker
- `FlexFileUpload` — file upload with drag-and-drop
- `FlexForm` — form container with full validation
- `FlexProgress` — progress bars
- TypeScript definitions (`.d.ts`) for all components
- Unit tests for all components (Vitest)

## v1.2.0 — Planned

- `FlexNotification` — toast/notification system
- Dropdown menu improvements
- Theme system (light/dark/custom)
- CSS custom property tokens
- Component Storybook

## v2.0.0 — Future

- Virtual scrolling for large datasets
- Framework adapters (React, Vue wrappers)
- Design system integration
- Accessibility audit tooling

---

## Platform Feature Roadmap

### Short-term

- Two-factor authentication (TOTP/SMS)
- Advanced report scheduling
- Webhook outbound integration
- Prometheus metrics endpoint (`/metrics`)

### Medium-term

- Visual form builder (drag-and-drop)
- Document generation (PDF templates)
- Module marketplace UI
- Subscription tier enforcement

### Long-term

- SSO / SAML / OAuth2 provider
- AI-assisted data modeling
- White-label theming engine
- Mobile application (PWA or native)
