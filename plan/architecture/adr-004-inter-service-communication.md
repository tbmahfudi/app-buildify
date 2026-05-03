---
artifact_id: adr-004
type: adr
producer: Software Architect (B1)
consumers: [Backend Engineer, DevOps, Tech Lead, C1, C2, C3, D3]
upstream: [arch-platform, adr-001-deployment-modes, adr-002-monolith-service-boundaries, adr-003-microservices-decomposition]
downstream: [arch-01-deployment-topology]
status: Proposed
created: 2026-05-03
updated: 2026-05-03
---

# ADR-004 — Inter-Service Communication in Distributed Mode

## Status

Proposed.

## Context

ADR-003 defines the service decomposition for distributed mode. It mandates that "the event bus must be the only cross-service async channel" and that "no direct service-to-service HTTP calls are permitted for domain events." This ADR specifies the full communication contract so engineers know which pattern to use for every cross-service interaction category.

Three interaction categories arise in the current and anticipated platform:

1. **Request-scoped queries**: a service needs data from another service in order to construct a response to an end-user request. Example: the core's Dashboard API wants to include a financial KPI for a tenant that has the financial module enabled.
2. **Domain events (fire-and-forget)**: a service signals that something happened, and other interested services react. Example: financial module publishes `financial.invoice.paid` → core workflow engine triggers an automation rule.
3. **Administrative / lifecycle calls**: a module service registers itself with the core at startup; the core calls a module to check health or retrieve its permission list.

The current codebase provides two partial implementations:
- **Event bus** (`backend/app/core/event_bus/publisher.py`, `subscriber.py`): PostgreSQL LISTEN/NOTIFY with a fallback polling table. Publisher is implemented; subscriber is real in the core but is a stub in the financial module (`modules/financial/backend/app/core/event_handler.py:43-47`).
- **Module registration via HTTP**: `modules/financial/backend/app/main.py:24-79` calls `POST /api/v1/modules/register` on the core at startup.

No pattern is defined for request-scoped cross-service queries. Without a rule, engineers will either: (a) duplicate data across databases, (b) make undocumented direct HTTP calls between services, or (c) avoid implementing cross-module features.

## Decision

Three canonical communication patterns, one for each interaction category:

---

### Pattern 1 — Request-scoped: Gateway-mediated composition (BFF / aggregation at the API gateway or core)

When an end-user request requires data from a module service, the **core-platform** acts as the aggregator. It makes an authenticated HTTP call to the module's internal API using the `MODULE_API_KEY` and the request's `tenant_id` and `X-Company-ID` headers, merges the response, and returns a unified payload to the client.

```
Client → Nginx → core-platform:8000
                      │
                      ├─ own DB query (entities, workflows, …)
                      │
                      └─ HTTP GET financial-module:9001/api/v1/financial/summary
                              (headers: MODULE_API_KEY, X-Tenant-Id, X-Company-Id)
                              │
                              └─ financial DB query → response
```

Rules:
- Only the **core-platform** may make aggregation calls to module services. Module services never call each other directly.
- Calls use the internal Docker network hostname (`financial-module:9001`), not the public Nginx route.
- The `MODULE_API_KEY` authenticates service-to-service calls; user JWT is forwarded as-is so the module can perform its own tenant/permission checks.
- Aggregation calls are **synchronous and bounded**: 2-second timeout, no retry beyond one. If a module is down, the core returns a partial response with a `degraded_services` field in the envelope; it does not fail the entire response.
- Cross-service aggregation is a last resort. Prefer publishing a periodic summary event and caching it in the core's `WidgetDataCache` (`backend/app/services/dashboard_service.py`) over making a live call per dashboard render.

---

### Pattern 2 — Domain events: PostgreSQL LISTEN/NOTIFY event bus

All async cross-service notifications use the event bus at `backend/app/core/event_bus/`.

**Publishing** (any service):
```python
from app.core.event_bus.publisher import get_event_publisher

publisher = get_event_publisher(db_session)
await publisher.publish(
    event_type="financial.invoice.paid",
    payload={"invoice_id": str(invoice_id), "amount": amount},
    tenant_id=tenant_id,
    company_id=company_id,
)
```

**Subscribing** (any service):

Each service subscribes to the event bus at startup using the `EventSubscriber` class (`backend/app/core/event_bus/subscriber.py`). Module services must copy (not import) the subscriber implementation into their own codebase to avoid a compile-time dependency on the core. The shared contract is the **wire format** (JSON envelope), not the Python class.

Wire format (stored in `platform_events` unlogged table and sent as the NOTIFY payload):

```json
{
  "event_id": "<uuid>",
  "event_type": "financial.invoice.paid",
  "tenant_id": "<uuid>",
  "company_id": "<uuid>",
  "user_id": "<uuid>",
  "event_source": "financial-module",
  "payload": { "invoice_id": "…", "amount": 1000.00 },
  "created_at": "2026-05-03T12:00:00Z",
  "schema_version": "1"
}
```

Rules:
- Event types follow the namespace pattern `{module}.{aggregate}.{verb}` (e.g. `financial.invoice.paid`, `core.workflow.completed`).
- Events are **at-least-once** (the polling fallback guarantees delivery; idempotency is the consumer's responsibility).
- Events carry only IDs and a minimal payload; consumers re-query their own DB for full records. No PII in event payloads.
- The subscriber stub in `modules/financial/backend/app/core/event_handler.py:43-47` **must be replaced** before distributed mode is declared production-ready (tracked as a 🔴 gap in `arch-platform.md §9 risk #14`).

---

### Pattern 3 — Administrative / lifecycle: Authenticated REST on internal network

Module-to-core administrative calls (registration, health check, permission sync) use direct HTTP on the internal Docker network with `MODULE_API_KEY` authentication. These calls are not routed through Nginx.

Current examples:
- `POST /api/v1/modules/register` — financial module calls this at startup (`modules/financial/backend/app/main.py:24-79`).
- `GET /api/v1/modules/{name}/health` — orchestrator or core calls this for readiness gates.

Rules:
- Only lifecycle / administrative operations use this channel. No domain data.
- Core → module administrative calls (e.g. "disable module for tenant") are published via Pattern 2 (event bus) so the module reacts asynchronously. The core does not wait for acknowledgement.

---

### Decision summary table

| Interaction | Pattern | Transport | Sync? | Auth |
|-------------|---------|-----------|-------|------|
| Dashboard widget pulling financial KPI | Pattern 1 (gateway aggregation) | HTTP (internal network) | Yes | MODULE_API_KEY + user JWT |
| Invoice paid → trigger workflow | Pattern 2 (event bus) | PostgreSQL NOTIFY | No | none (internal bus) |
| Module registers with core at boot | Pattern 3 (admin REST) | HTTP (internal network) | Yes | MODULE_API_KEY |
| Module subscribes to core domain events | Pattern 2 (event bus) | PostgreSQL LISTEN | No | none (internal bus) |

## Consequences

### Positive

- **No hidden coupling**: the three patterns are exhaustive; an engineer who needs a new cross-service interaction always has a clear home.
- **Graceful degradation**: Pattern 1 mandates partial-response semantics; a failing module never crashes the core.
- **Event replay**: Pattern 2's fallback polling table (`platform_events`) provides a replayable log — useful for debugging and for a new module subscriber catching up after downtime.

### Negative

- **Stub must be finished**: Pattern 2 is hollow until `modules/financial/backend/app/core/event_handler.py` is completed. This is the single highest-risk gap for distributed mode readiness.
- **Aggregation latency**: Pattern 1 adds at least one network round-trip to dashboard rendering. Caching (WidgetDataCache) is the mitigation; engineers must populate the cache proactively.
- **PostgreSQL as broker**: LISTEN/NOTIFY is not durable across Postgres restart (in-memory queue). The fallback polling table provides durability for the reliable path; engineers must not assume NOTIFY alone is sufficient.
- **Module service port registry**: Pattern 3 admin calls use hardcoded service hostnames. These must be discoverable via the manifest's `service.host` and `service.port` fields (defined in ADR-003) rather than hardcoded strings.

## Alternatives considered

- **gRPC for all cross-service calls**: strongly-typed contracts, efficient binary protocol. Rejected — requires gRPC codegen tooling, a proto schema registry, and client stubs in every service. Overhead for current team size; revisit at ≥ 5 modules.
- **RabbitMQ / Kafka for events**: production-grade broker with durable queues. Rejected — adds a new infrastructure dependency (another container, another failure point) when the PostgreSQL event bus already provides at-least-once delivery via the polling fallback. Revisit when event volume exceeds PostgreSQL NOTIFY limits (~8KB payload, ~1k msg/s throughput).
- **Direct HTTP module-to-module calls (any-to-any)**: simplest to implement per feature, worst for coupling. Rejected — creates a mesh that is impossible to reason about and breaks the "module services never call each other" rule from ADR-003.
- **Shared Redis pub/sub**: lighter than PostgreSQL LISTEN/NOTIFY with less boilerplate. Rejected — Redis is already used for JWT blacklist and cache; mixing it with event routing creates unclear operational boundaries. Also: Redis pub/sub has no durability.

## Related artifacts

- `plan/architecture/adr-001-deployment-modes.md` — establishes distributed mode.
- `plan/architecture/adr-003-microservices-decomposition.md` — service topology this ADR constrains.
- `plan/architecture/arch-01-deployment-topology.md` — full system view.
- `backend/app/core/event_bus/publisher.py` — Pattern 2 publish implementation.
- `backend/app/core/event_bus/subscriber.py` — Pattern 2 subscribe implementation (copy into modules).
- `modules/financial/backend/app/core/event_handler.py` — 🔴 stub that must be replaced (lines 43-47).
- `modules/financial/backend/app/main.py` — Pattern 3 admin registration (lines 24-79).
- `backend/app/services/dashboard_service.py` — WidgetDataCache (Pattern 1 caching mitigation).
- `infra/nginx/nginx.conf` — Pattern 1 internal routing and module location blocks.
