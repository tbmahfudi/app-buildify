# Backend API E2E suite (live container, black-box)

These tests hit the **running** API over HTTP — no app imports, no TestClient.
They verify the deployed artifact: routing, middleware, auth, RBAC, DB, JSON.

## Run

```bash
# 1. bring the stack up (from repo root)
./manage.sh start postgres

# 2. run the suite inside the backend container (has pytest + httpx)
docker exec app_buildify_backend python -m pytest tests/e2e --confcutdir=tests/e2e -v
```

`--confcutdir=tests/e2e` is **required** — it stops pytest loading the
in-process `tests/conftest.py`, which is a separate (and currently broken on
this image) harness.

From any host that can reach the API instead of `docker exec`:

```bash
E2E_BASE_URL=http://localhost:8000 python -m pytest tests/e2e -v
```

## Configuration (env vars)

| Var | Default |
|-----|---------|
| `E2E_BASE_URL` | `http://localhost:8000` |
| `E2E_SU_EMAIL` / `E2E_SU_PASSWORD` | `superadmin@system.com` / `SuperAdmin123!` |
| `E2E_USER_EMAIL` / `E2E_USER_PASSWORD` | `ceo@techstart.com` / `password123` |

## Fixtures (conftest.py)

- `su` — auto-reauthenticating superadmin client.
- `user` — auto-reauthenticating low-privilege tenant client (for authz tests).
- `anon` — unauthenticated client (for 401/403 negative cases).
- `ephemeral(creds)` — context-manager login that **logs out on exit** (use for
  auth-flow tests so they don't evict the shared session under
  `max_concurrent_sessions=3`).
- `unique(prefix)` — collision-free name factory.

## Layout

```
test_health.py             health, openapi, 404
test_auth.py               exhaustive auth router (9 ops)
test_smoke_all_routers.py  OpenAPI-driven GET sweep across all 23 routers
```

Add deep per-router files (`test_rbac.py`, `test_org.py`, …) following the
coverage matrix in `tests/test-plans/test-plan-e2e-api.md`.
Known 5xx defects are tracked as `xfail(strict=True)` with a `DEF-NNN` reason.
