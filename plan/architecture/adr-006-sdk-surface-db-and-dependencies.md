# ADR-006: SDK Surface Expansion — Database Base and FastAPI Dependencies

**Date:** 2026-06-20
**Status:** Accepted
**Deciders:** Platform team

---

## Context

Modules need to define SQLAlchemy models that inherit the platform `Base`
(so Alembic migrations see them) and to use the platform's FastAPI dependency
functions (`tenant_scoped_session`, `get_current_user`, `has_permission`) in
their route handlers.

Before this ADR the only sanctioned import was `from modules.sdk import …`,
but `sdk/__init__.py` did not expose any DB or dependency symbols.  Module
authors were either copying platform internals into their modules or, worse,
importing directly from `backend.app` — violating the isolation contract.

---

## Decision

Introduce two thin re-export modules inside `modules/sdk/`:

1. **`modules/sdk/db.py`** — re-exports `Base`, `GUID`, `generate_uuid` from
   `backend.app.models.base`.
2. **`modules/sdk/dependencies.py`** — re-exports `tenant_scoped_session`,
   `get_current_user`, `has_permission` from
   `backend.app.core.dependencies`.

Both modules are added to `modules/sdk/__init__.py` and its `__all__` so that
module authors can write:

```python
from modules.sdk import Base, tenant_scoped_session, has_permission
```

or the more explicit:

```python
from modules.sdk.db import Base, GUID, generate_uuid
from modules.sdk.dependencies import tenant_scoped_session, get_current_user, has_permission
```

No module may import from `backend.app` directly.  This rule is enforced by a
CI linting gate (`tools/lint/no_direct_backend_import.py`).

---

## Consequences

### Positive

- **SDK-only rule is now enforceable end-to-end.** Modules can write fully
  idiomatic SQLAlchemy models and FastAPI routes without ever touching
  `backend.app`.
- **Platform can refactor internals** (rename classes, move modules) without
  touching module code, as long as SDK re-exports are updated.
- **Template scaffold is self-contained** — new module authors have working
  examples that compile and pass the linting gate.

### Negative

- **SDK maintainers must keep re-exports in sync** with platform internals.
  If `backend.app.models.base` is refactored, `modules/sdk/db.py` must be
  updated in the same PR or modules will break at import time.
- **Surface area grows.** Every symbol added to the SDK is an implicit promise
  to maintain it.  SDK additions should require a short ADR note or PR
  description explaining the need.

---

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Let modules import `backend.app` directly | Breaks isolation; couples module release cycle to platform internals |
| Copy-paste base classes into each module | Breaks Alembic (multiple `Base` instances); maintenance nightmare |
| Generate per-module base via factory function | Complexity with no benefit given the single-Base Alembic setup |
