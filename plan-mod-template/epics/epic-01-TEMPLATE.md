---
artifact_id: epic-01-TEMPLATE
type: epic
module: TEMPLATE
producer: A3 Product Owner
status: open
created: YYYY-MM-DD
---

# Epic 1 — Core TEMPLATE Functionality

> One-paragraph summary of what this epic delivers and why.

---

## Feature 1.1 — Example Feature `[OPEN]`

### Story 1.1.1 — Example Story `[OPEN]`

*As a [user type], I want [capability] so that [benefit].*

#### Backend
- Endpoint: `GET /api/v1/modules/TEMPLATE/example`
- Returns: `{items: [], total: int}`
- Requires: tenant scope, `TEMPLATE:read` permission

#### Frontend
- Route: `#/modules/TEMPLATE`
- Component: `FlexTable` with columns [...]
- Empty state: "No items yet" with a Create button

#### Acceptance Criteria
- [ ] Endpoint returns 200 with empty list for a fresh tenant
- [ ] Table renders with correct columns
- [ ] Empty state is shown when there are no items
