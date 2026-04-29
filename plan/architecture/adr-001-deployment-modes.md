---
artifact_id: adr-001
type: adr
producer: Software Architect
consumers: [Backend Engineer, DevOps, Tech Lead]
upstream: [arch-platform, epic-11-module-system, epic-19-infrastructure-deployment]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
---

# ADR-001 — Deployment Modes: Monolith and Distributed

## Status

Accepted.

## Context

App-Buildify already runs in two shapes simultaneously, neither of which is canonical:

- **In-process module mounting** (monolith): the core platform's `lifespan` calls `module_registry.get_all_routers()` and does `app.include_router(router)` for every discovered module — see `backend/app/main.py:70-76`. The financial module's routers are then served from the core process at port 8000.
- **Standalone module service** (distributed): `modules/financial/backend/app/main.py:110-118` is a separate FastAPI app on port 9001 that calls `register_with_core_platform()` (lines 24-79, exponential backoff 2-32 s) over HTTP at boot. The Nginx gateway routes `/api/v1/financial/*` to this service (`infra/nginx/nginx.conf`).

Both code paths are alive. The ambiguity costs us:

- Module endpoints can be served from two places, with no guarantee they behave identically.
- `DATABASE_STRATEGY=shared|separate` is wired (`modules/financial/backend/app/config.py:23,79`) but undocumented and un-toggled — only `shared` is used.
- The Postgres LISTEN/NOTIFY event bus has a real implementation in `backend/app/core/event_bus/` and a stub in `modules/financial/backend/app/core/event_handler.py:43-47`. It exists for cross-module communication in distributed mode but has no canonical wiring.
- Operators have no single switch to choose a deployment shape.

The `BaseModule` ABC at `backend/app/core/module_system/base_module.py` already abstracts a module's surface (`get_router()`, `get_permissions()`, `get_models()`, lifecycle hooks `pre/post_install`, `pre/post_enable`, `pre/post_disable`, `pre/post_uninstall`). That contract is the right boundary; only the **transport** (in-process Python call vs. HTTP through the gateway) differs between modes.

## Decision

Support **both** deployment modes from a single codebase, controlled by one environment variable: `DEPLOYMENT_MODE`.

| `DEPLOYMENT_MODE` value | Behavior |
|-------------------------|----------|
| `monolith` (default) | Core process mounts every enabled module's router in-process. Module FastAPI services are not started. One Postgres database, one process. |
| `distributed` | Core process skips in-process router mounting. Each module runs as its own FastAPI service. Gateway routes `/api/v1/<module>/*` to the module service. Each module owns its own database (`DATABASE_STRATEGY=separate`). Cross-module communication uses the event bus. |

The `BaseModule` contract is the seam. Both modes consume it identically; modules need no code changes between modes.

## Consequences

### Positive

- **One artifact, two shapes.** Same image, same code, two deploy topologies.
- **Smooth growth path.** Start in `monolith` for dev and small tenants; switch to `distributed` when a module needs independent scaling or its own team.
- **Boundary stays honest.** Forcing every module through `BaseModule` means a module that secretly imports core-platform code can't run in `distributed`, surfacing leakage early.
- **Uses what's already built.** No new abstractions; just wires `DEPLOYMENT_MODE` into existing branches.

### Negative

- **Two test matrices.** Every module endpoint must be exercised in both modes.
- **Event bus becomes load-bearing in `distributed`.** The LISTEN/NOTIFY stub at `modules/financial/backend/app/core/event_handler.py:43-47` must be finished before `distributed` is production-ready (tracked as a 🔴 gap in `audit-11-module-system.md`).
- **Operators must understand the modes.** Documented in `/docs/deployment/`; default stays `monolith` so the simple path is the obvious one.

## Implementation

The decision is documented; the code change is small and goes into a follow-up PR. Sketch:

### 1. Settings

`backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    ...
    DEPLOYMENT_MODE: Literal["monolith", "distributed"] = "monolith"
```

### 2. Core lifespan branch

`backend/app/main.py:70-76`, current:

```python
for router in module_registry.get_all_routers():
    app.include_router(router)
```

Becomes:

```python
if settings.DEPLOYMENT_MODE == "monolith":
    for router in module_registry.get_all_routers():
        app.include_router(router)
# distributed: gateway routes module traffic to standalone services
```

### 3. Module standalone entry

`modules/<m>/backend/app/main.py` — already correct. The `register_with_core_platform()` retry loop already tolerates the core not being up first.

### 4. Database strategy

When `DEPLOYMENT_MODE=distributed`, modules default `DATABASE_STRATEGY=separate` (already implemented in `modules/financial/backend/app/config.py:23,79`). Each module gets its own Postgres database. Migrations stay independent thanks to per-module Alembic version tables (e.g. `financial_alembic_version`).

### 5. Event bus

In `distributed`, all inter-module communication MUST go through the event bus at `backend/app/core/event_bus/`. The stub at `modules/financial/backend/app/core/event_handler.py:43-47` must be replaced with a real subscriber loop using PostgreSQL LISTEN/NOTIFY. Design reference: `/docs/archive/POSTGRES_EVENT_BUS_DESIGN.md`.

### 6. Gateway

`infra/nginx/nginx.conf` is already correct. Each module gets a `location /api/v1/<m>/` block routing to `<m>:<port>`. In `monolith`, those upstreams resolve to the core service; in `distributed`, to each module's own container. (This is the one place the operator's compose file changes between modes.)

### 7. Compose profiles

`docker-compose.yml` — add Compose profiles so the same file serves both modes:

- Profile `monolith`: starts `postgres`, `redis`, `core-platform`, `api-gateway`, `frontend`. Modules are NOT started.
- Profile `distributed`: starts everything plus each module as its own service.

Operator command:
```bash
COMPOSE_PROFILES=monolith docker compose up      # default
COMPOSE_PROFILES=distributed docker compose up   # microservices
```

## Trace — same request in both modes

Request: `POST /api/v1/financial/invoices`

**Monolith:**
```
client → nginx :80 → core-platform :8000 (mounted financial router)
       → FinancialService → shared `buildify` DB
```

**Distributed:**
```
client → nginx :80 → financial-module :9001 (own router)
       → FinancialService → own `financial` DB
       → LISTEN/NOTIFY publishes `financial.invoice.created`
       → core's event-bus subscriber logs / triggers downstream workflows
```

Both routes work using only the files cited above; no code path is mode-specific beyond the single `if settings.DEPLOYMENT_MODE` guard.

## Migration path for existing operators

Today's setup is a hybrid: in-process mounting + standalone financial service running simultaneously. With this ADR shipped:

1. Default `DEPLOYMENT_MODE=monolith` is set; in-process mounting continues. The standalone financial service is no longer required and can be removed from `docker-compose.yml` for monolith deploys.
2. Operators who want independent module scaling set `DEPLOYMENT_MODE=distributed`, remove the in-process mount, and run module services per `infra/nginx/nginx.conf`.
3. No data migration is required; only the operator's compose file changes.

## Alternatives considered

- **Monolith-only.** Rejected: kills the financial module's ability to scale independently and forces a single team to own every module.
- **Distributed-only (force microservices).** Rejected: punitive for dev (need 6+ containers), and operationally heavy for small tenants.
- **Build-time switch (separate Docker images per mode).** Rejected: doubles CI cost and image surface for a runtime concern that has a clean toggle.

## Related artifacts

- `/plan/architecture/arch-platform.md` — system topology this ADR refines.
- `/plan/epics/epic-11-module-system.md` — module contract this ADR depends on.
- `/plan/epics/epic-19-infrastructure-deployment.md` — gateway and compose work that must absorb this decision.
- `/docs/archive/POSTGRES_EVENT_BUS_DESIGN.md` — event bus design that distributed mode finishes.
- `/plan/architecture/audits/audit-11-module-system.md` — captures the LISTEN/NOTIFY stub as a 🔴 gap.

## Decisions

- **`monolith` is the default** so the simplest path is the easiest path.
- **Event bus is mandatory in `distributed`** — no fallbacks to direct HTTP module-to-module calls.
- **`BaseModule` contract is frozen** as the deployment-mode abstraction; new modules must conform.

## Open Questions

- Should there be a third mode `hybrid` (some modules in-process, some standalone)? Held back: complicates the matrix; revisit if a real operator asks for it.
- Per-module port allocation in `distributed` — should manifests declare a `port`, or should an orchestrator assign them? Currently hard-coded (financial = 9001); needs a registration scheme before module 3.
