# UI Layout Description Convention (UILDC v1.0)

Standard for writing `#### Frontend` sections in product backlog stories.

## Sub-documents

| # | File | Contents |
|---|------|----------|
| 1 | [Page Layout & Zone Notation](layout-convention/01-page-layout-zone.md) | Notation types 1 & 2 — page skeleton and zone contents |
| 2 | [Component Spec & Responsive Notation](layout-convention/02-component-spec-responsive.md) | Notation types 3 & 4 — major components and breakpoints |
| 3 | [State & Interaction Notation](layout-convention/03-state-interactions.md) | Notation types 5 & 6 — UI states and user actions |
| 4 | [Reference & Cheat Sheet](layout-convention/04-reference.md) | Component library quick ref, cheat sheets, pattern map |
| 5 | [Example: List Page](layout-convention/05-example-list-page.md) | Full story example — User Management list |
| 6 | [Example: Form Page](layout-convention/06-example-form-page.md) | Full story example — Invoice Creation form |
| 7 | [Example: Canvas Page](layout-convention/07-example-canvas-page.md) | Full story example — Workflow Designer canvas |

## Quick Rules

- All 6 notation types are optional; use only the ones the story needs.
- Notation is written as nested bullet lists under `#### Frontend`.
- Desktop (`lg+`) is the default; only add `- Responsive:` if the page has a real mobile story.
- `loading` + `empty` + `error` states are required for every page that fetches data.
- `- Interactions:` covers page-level and cross-component user actions; `on [trigger]:` inside a Component Spec covers component-internal reactions.
- 1–4 Component Specs per story maximum; more means the story needs splitting.
