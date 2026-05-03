---
artifact_id: adr-003
type: adr
producer: Software Architect (B1)
consumers: [Backend Engineer, DevOps, Tech Lead, C1, C2, C3, D3]
upstream: [arch-platform, adr-001-deployment-modes, adr-002-monolith-service-boundaries, epic-11-module-system, epic-19-infrastructure-deployment]
downstream: [arch-01-deployment-topology]
status: Proposed
created: 2026-05-03
updated: 2026-05-03
---

# ADR-003 — Microservices: Decomposition Strategy

## Status

Proposed.

## Context

ADR-001 established `DEPLOYMENT_MODE=distributed` as the microservices shape. ADR-002 defined the six domain slices inside the monolith. This ADR answers the next question: **when the platform runs in distributed mode, which slices become independent services, how many containers does an operator run, and what contract governs each service's external surface?**

The decomposition must satisfy four constraints derived from the vision and platform architecture:

1. **Tenant isolation must be preserved across service boundaries** — every service independently verifies the JWT-embedded `tenant_id`; no service trusts another service's tenant assertion without proof.
2. **The `BaseModule` contract (ADR-001) is frozen** — new modules plug in without changing core services.
3. **Operational simplicity must not collapse** — the monolith default exists for a reason; distributed mode should add containers only where independent scaling or team autonomy justifies the cost.
4. **The existing event bus must be the only cross-service async channel** — no direct service-to-service HTTP calls for domain events (only synchronous facade calls via gateway for query-like cross-service data needs).

The current state of the codebase provides two reference points:
- `docker-compose.yml` already runs `core-platform:8000` and `financial-module:9001` as separate containers.
- `infra/nginx/nginx.conf` already routes `/api/v1/financial/*` to `financial-module:9001` and `/api/v1/*` to `core_platform:8000`.
- The financial module already registers itself with the core via `register_with_core_platform()` (`modules/financial/backend/app/main.py:24-79`).

The gap: there is no documented decomposition map, no port registry, and no rule about which slices from ADR-002 stay in the core process vs. become their own service.

## Decision

In `distributed` mode, decompose the platform into **three layers of services**:

### Layer 1 — Core Platform (always present)

One service containing domains D1 (Identity & Access), D2 (Organisation), D3 (NoCode Platform), D4 (Process), D5 (Insights), and D6 (Platform Services). Port: 8000.

Rationale: these six domains share the tenant/company/branch/department data model tightly. Splitting them early offers no scaling advantage and significantly increases inter-service latency for queries that today are intra-process (e.g. dashboard rendering that fetches entity data). They stay together until a domain's scale or team-ownership justifies extraction (see "Future extractions" below).

### Layer 2 — Module Services (one per enabled module)

Each domain module (Financial, and future HR/CRM/Inventory) runs as its own FastAPI service. Port assignments are declared in the module's `manifest.json` under a new `service.port` field, allocated from a reserved range (9001–9099). Each module service:
- Owns its own database (`DATABASE_STRATEGY=separate`, its own PostgreSQL database or schema as configured).
- Has its own Alembic version table (`{module_name}_alembic_version`).
- Registers with the core at startup via `register_with_core_platform()` with exponential-backoff retry.
- Validates the JWT independently using the shared `JWT_SECRET_KEY` env var — it does **not** proxy auth through the core.
- Publishes and subscribes to the shared event bus for cross-domain notifications.

Current modules and their assigned ports:

| Module | Port | Database | Nginx location |
|--------|------|----------|----------------|
| `financial` | 9001 | `buildify_financial` (separate) or `buildify` (shared) | `/api/v1/financial/` |
| `hr` *(planned)* | 9002 | `buildify_hr` | `/api/v1/hr/` |
| `crm` *(planned)* | 9003 | `buildify_crm` | `/api/v1/crm/` |
| `inventory` *(planned)* | 9004 | `buildify_inventory` | `/api/v1/inventory/` |

### Layer 3 — Infrastructure Services (shared)

| Service | Port | Role |
|---------|------|------|
| `postgres` | 5432 | Shared host; each service connects to its own DB or schema |
| `redis` | 6379 | JWT blacklist + cache; shared across all services |
| `api-gateway` (Nginx) | 80/443 | TLS termination, routing, rate limiting |

### Decomposition rules

1. **New modules are always Layer 2.** No module code enters the core-platform image.
2. **A core domain slice may be extracted to Layer 2 only with a new ADR** that justifies the operational cost and defines the inter-service contract.
3. **Port allocation** is owned by this ADR. New modules must register their port in `manifest.json:service.port` and in the Nginx config before shipping.
4. **Database ownership**: in `distributed` mode, `DATABASE_STRATEGY=separate` is the default for module services. The core-platform uses the `buildify` database. Each module uses `buildify_{module_name}`.
5. **Auth delegation**: every service validates JWTs independently. The `MODULE_API_KEY` is only for service-to-service administrative calls (module registration), not for request auth.

### Container topology in distributed mode

```
                        Browser / API client
                               │
                               ▼
              ┌────────────────────────────────┐
              │   api-gateway (Nginx)  :80/443  │
              │   rate-limit 100r/s, TLS, CORS  │
              └─────┬──────────┬───────┬────────┘
                    │          │       │
          ┌─────────▼──┐  ┌────▼───┐  ┌▼──────────────┐
          │core-platform│  │financial│  │ hr / crm / .. │
          │   :8000     │  │  :9001  │  │  :9002+       │
          │ D1+D2+D3+   │  │own DB   │  │ own DB        │
          │ D4+D5+D6    │  │own alembic│ │own alembic   │
          └──────┬──────┘  └────┬────┘  └──────┬────────┘
                 │              │               │
                 └──────┬───────┘───────────────┘
                        │
              ┌──────────┴──────────────┐
              │  postgres :5432          │
              │  redis    :6379          │
              │  (shared infrastructure)│
              └─────────────────────────┘
```

### Future core-platform extractions (candidate order)

These are **not** decided here — each requires its own ADR:

| Candidate | Trigger for extraction |
|-----------|----------------------|
| Notification Service (D6 subset) | When email/SMS volume requires a dedicated worker pool separate from request handling |
| Scheduler Service (D4 subset) | When cron/job volume causes scheduler-thread starvation in the core process |
| Reporting Service (D5 subset) | When report export jobs (CSV/PDF) cause p95 latency spikes in the main request path |
| NoCode Runtime (D3 subset) | When dynamic entity CRUD for one tenant needs horizontal scaling independent of the core |

## Consequences

### Positive

- **Independent deployability**: a bug in the financial module can be patched and redeployed without touching the core.
- **Independent scaling**: a financially-heavy tenant can scale the financial service horizontally without scaling the core.
- **Team autonomy**: a module team owns their service end-to-end (code, migrations, observability).
- **Fault isolation**: a crashing module service does not bring down core authentication or NoCode.

### Negative

- **Operational cost**: distributed mode requires running 3+ containers (core + 1 per enabled module + infra). Small operators pay this tax even if they only use the core platform.
- **JWT secret sharing**: every service needs `JWT_SECRET_KEY`. Rotation requires coordinated restart of all services. Mitigation: future ADR for asymmetric JWT (RS256) so modules only need the public key.
- **Cross-service queries**: a dashboard widget that aggregates financial + NoCode entity data requires either a gateway aggregation layer or the core calling the module's API — adding a network hop and a failure surface.
- **Event bus load-bearing**: the PostgreSQL LISTEN/NOTIFY event bus (`backend/app/core/event_bus/`) must be production-ready before distributed mode is declared stable. Currently the financial module subscriber is a stub (`modules/financial/backend/app/core/event_handler.py:43-47`).

## Implementation checklist

- [ ] Add `service.port` field to `manifest.json` schema (validated by `backend/validate_module_manifest.py`).
- [ ] Wire `DEPLOYMENT_MODE=distributed` guard in `backend/app/main.py:70-76` (per ADR-001 §Implementation step 2).
- [ ] Finish LISTEN/NOTIFY subscriber in `modules/financial/backend/app/core/event_handler.py`.
- [ ] Update `infra/docker-compose.prod.yml` to add Compose profile `distributed` with all module services.
- [ ] Document port registry in `docs/platform/SERVICES.md`.
- [ ] Add Nginx location block template for new modules in `infra/nginx/nginx.conf`.

## Alternatives considered

- **One service per domain slice (D1–D6 all separate)**: maximum isolation, maximum operational cost. Six core services + N module services for a typical deployment. Rejected — benefits don't justify the overhead at current team and tenant scale. Revisit at 10+ modules or 100+ tenants.
- **Strangler-fig extraction (decompose organically as needed)**: attractive but requires explicit trigger criteria. This ADR provides those criteria (see "Future core-platform extractions") so the strangler fig has a roadmap rather than being purely reactive.
- **Service mesh (Istio/Linkerd) for cross-service auth**: full mTLS between services. Rejected — too heavy for the current operator profile (single Docker Compose host). Add when Kubernetes is the target platform.

## Related artifacts

- `plan/architecture/adr-001-deployment-modes.md` — establishes `DEPLOYMENT_MODE` switch.
- `plan/architecture/adr-002-monolith-service-boundaries.md` — domain slices this ADR decomposes.
- `plan/architecture/adr-004-inter-service-communication.md` — event bus and cross-service call rules.
- `plan/architecture/arch-01-deployment-topology.md` — full C4 view of both modes.
- `modules/financial/manifest.json` — reference module manifest; needs `service.port` field added.
- `modules/financial/backend/app/main.py` — module registration at startup.
- `infra/nginx/nginx.conf` — gateway routing; needs per-module location blocks.
- `backend/app/core/event_bus/` — event bus implementation.
- `backend/validate_module_manifest.py` — manifest validator; needs `service.port` schema rule.
