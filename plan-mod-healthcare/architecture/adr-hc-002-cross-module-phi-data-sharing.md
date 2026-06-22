---
artifact_id: adr-hc-002
type: adr
module: healthcare
status: Accepted
producer: B1 Software Architect
upstream: [vision-02, research-02, BACKLOG.md, adr-hc-001, adr-006-sdk-surface-db-and-dependencies]
created: 2026-06-21
---

# ADR-HC-002 — Cross-Module PHI Data Sharing

## Status

Accepted

## Context

The Healthcare Module Suite is a family of related modules:

```
healthcare (base)
  ├─ healthcare_scheduling
  ├─ healthcare_billing
  ├─ healthcare_pharmacy
  └─ healthcare_lab
```

Each sub-module is a separate FastAPI service (following arch-00-platform §2) with its own
Alembic version table. All sub-modules depend on the base `healthcare` module being active.

Sub-modules need to read **Patient** and **Encounter** records that are owned by the base
`healthcare` module. Specific use-cases:

| Sub-module | PHI data needed | Trigger |
|-----------|-----------------|---------|
| `healthcare_scheduling` | Patient demographics (name, phone) for booking confirmation | Appointment creation |
| `healthcare_pharmacy` | Patient ID, Encounter ID, prescribing Doctor ID | Prescription creation |
| `healthcare_lab` | Patient ID, Encounter ID, ordering Doctor ID | Lab order creation |
| `healthcare_billing` | Patient ID, Encounter ID, service codes, provider ID | Invoice generation |

Two candidate patterns exist:
1. **Healthcare Internal SDK** (`modules/healthcare/sdk/`) — sub-modules call Python functions
   that query the shared PostgreSQL database directly, scoped by `tenant_id` + `branch_id`.
2. **Internal REST API** — sub-modules call `GET /api/v1/modules/healthcare/patients/{id}` over
   HTTP, treating the base module as a service.

**PHI audit requirement** (vision-02, epic-01 Story 1.6.1): every cross-module PHI read must
generate an audit log entry with `(event_type, actor_id, tenant_id, branch_id, resource_type,
resource_id, timestamp, ip, source_module)`.

## Decision

### D1 — Healthcare Internal SDK (in-process Python, shared DB)

Sub-modules access Patient and Encounter data via the **Healthcare Internal SDK**
(`modules/healthcare/sdk/`), not via HTTP. The SDK exposes read-only query functions that:

1. Accept `(tenant_id, branch_id, patient_id | encounter_id)` — always fully scoped.
2. Use `healthcare_branch_session` (ADR-HC-001) to enforce ORM-level + DB RLS isolation.
3. Write an audit log entry to the shared `audit_log` table before returning data.

```
modules/healthcare/sdk/
  branch_scope.py          # BranchScopeListener + healthcare_branch_session (ADR-HC-001)
  phi_audit.py             # write_phi_read_audit(event_type, actor, tenant, branch, resource, source_module)
  patient_reader.py        # get_patient(tenant_id, branch_id, patient_id) -> PatientReadDTO
  encounter_reader.py      # get_encounter(tenant_id, branch_id, encounter_id) -> EncounterReadDTO
  __init__.py              # exports all public symbols
```

Sub-module import pattern:

```python
# Inside healthcare_pharmacy service
from modules.healthcare.sdk import get_patient, get_encounter, write_phi_read_audit

patient = get_patient(tenant_id=tid, branch_id=bid, patient_id=pid)
# audit log written inside get_patient() automatically
```

**Return types are read-only DTOs** (Pydantic models, not SQLAlchemy ORM objects). Sub-modules
receive a snapshot; they cannot mutate base-module records through the SDK.

The SDK import rule mirrors ADR-006: sub-modules may import `from modules.healthcare.sdk` but
never from `modules.healthcare.backend.app` directly. The CI linting gate
(`tools/lint/no_direct_backend_import.py`) is extended to also reject
`from modules.healthcare.backend` imports.

### D2 — Mandatory Audit Log on Every PHI Read

`get_patient()` and `get_encounter()` call `write_phi_read_audit()` internally before returning
data. Sub-module callers cannot skip the audit. The audit record schema:

```
audit_log row:
  event_type      = "phi.read"
  actor_id        = current_user.id (passed by caller)
  tenant_id       = tenant_id
  branch_id       = branch_id
  resource_type   = "patient" | "encounter"
  resource_id     = patient_id | encounter_id
  source_module   = "healthcare_pharmacy" | "healthcare_lab" | ... (caller declares)
  timestamp       = utcnow()
  ip              = request IP (passed by caller)
  metadata_json   = {"purpose": "prescription_creation", ...}
```

The `audit_log` table is append-only (ADR-HC-001 §D4; epic-01 Story 1.6.1 AC).

### D3 — Internal REST API is NOT used for PHI reads

The HTTP-based approach is rejected (see Alternatives). It remains available for
**non-PHI** inter-module queries (e.g. a sub-module checking whether a module is active for a
tenant), but PHI reads go through the SDK.

## Consequences

### Positive
- **No HTTP latency or serialization overhead** for PHI reads — critical on appointment booking
  and prescription creation paths (target: p95 < 200 ms per ADR-HC NFRs).
- **Audit is non-bypassable** — it is inside the SDK function, not a caller responsibility.
- **DTO isolation** — base module internal model can change without affecting sub-modules as
  long as DTO shape is preserved.
- **Consistent with platform SDK pattern** — mirrors `modules/sdk/` → `modules/healthcare/sdk/`
  layering, familiar to module authors.

### Negative
- **Shared database coupling** — sub-modules and base module share PostgreSQL; schema changes to
  `patients` or `encounters` tables require coordinated migration. Mitigation: DTO interface is
  the contract; internal ORM model changes that preserve the DTO are safe.
- **SDK surface must be maintained** — any new sub-module data need requires an SDK PR; this is
  intentional (same rationale as ADR-006 surface control).
- **Sub-modules must be co-deployed with base module** — in-process SDK calls require the
  healthcare base module code to be importable. This is already a product constraint (base
  module must be active for any sub-module to work).

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Internal REST API for PHI reads | HTTP adds 10–50 ms latency per call; requires auth token forwarding or service-to-service key; audit hook is harder to guarantee (caller could skip it). No benefit given co-deployment constraint. |
| Sub-modules import `healthcare.backend.app` directly | Violates ADR-006 isolation contract; couples sub-module release cycle to base module internals. |
| Event-sourced PHI projection (read models per sub-module) | Premature complexity for v1 scale; eventual consistency complicates PHI audit trail. Revisit if sub-modules are ever deployed as separate services. |

## Reference Map

| File | Relevance |
|------|-----------|
| `modules/sdk/dependencies.py` | Platform SDK pattern this healthcare SDK mirrors |
| `modules/sdk/db.py` | Base, GUID — shared by healthcare SDK |
| `plan/architecture/adr-006-sdk-surface-db-and-dependencies.md` | SDK isolation contract and CI linting gate |
| `plan-mod-healthcare/architecture/adr-hc-001.md` | `BranchScopeListener` and `healthcare_branch_session` |
| `plan-mod-healthcare/epics/epic-01-base-healthcare.md` | Stories 1.3.1, 1.6.1 — PHI data model and audit ACs |
| `plan-mod-healthcare/vision/vision-02.md` | Guardrail 1 (PHI isolation), Guardrail 3 (audit on by default) |
