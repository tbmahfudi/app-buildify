# ADR-009 — OTP as a Platform Service

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-23 |
| **Deciders** | A3 (Product Owner), B1 (Software Architect) |
| **Supersedes** | — |

---

## Context

Phone-based OTP verification is a generic capability needed across multiple modules:
patient registration in the healthcare module, potential two-factor authentication for
staff portals, and future e-commerce checkout flows. Without a platform-owned OTP
service, each module that needs phone verification must:

- Manage its own Redis key schema for codes and attempt counters
- Implement its own rate-limiting and resend-cooldown logic
- Wire up and maintain its own SMS/WhatsApp adapter
- Define its own security policy (TTL, max attempts, code length)

This duplication creates inconsistent security guarantees across the platform and
multiplies the surface area that must be audited for vulnerabilities. A single
misconfiguration in one module's OTP logic could compromise tenant data.

---

## Decision

**OTP is a platform service. Modules never implement their own OTP logic.**

The platform exposes two endpoints:

- `POST /api/v1/otp/send`
- `POST /api/v1/otp/verify`

Modules call these endpoints with a `purpose` string that scopes the OTP to a specific
workflow. The platform owns all Redis key management, rate limiting, delivery adapters,
and security parameters.

---

## API Contract

### Send OTP

**Request**
```
POST /api/v1/otp/send
{
  "phone":       "+628123456789",
  "purpose":     "patient_registration",
  "tenant_code": "clinic_medcare"
}
```

**Response** `200 OK`
```json
{
  "message":      "OTP sent",
  "resend_after": 60
}
```

### Verify OTP

**Request**
```
POST /api/v1/otp/verify
{
  "phone":       "+628123456789",
  "purpose":     "patient_registration",
  "tenant_code": "clinic_medcare",
  "code":        "482910"
}
```

**Response** `200 OK`
```json
{
  "verified":  true,
  "otp_token": "a3f7c2d1-84e5-4b2a-9f6e-123456789abc"
}
```

### `otp_token` semantics

The `otp_token` returned on successful verification is a **single-use, 5-minute TTL**
proof-of-verification token. The calling module passes this token to its own downstream
endpoint (e.g. `POST /api/v1/modules/healthcare/patients/register`). That endpoint
calls the platform's token-consumption helper to validate and consume the token before
creating the resource. A consumed or expired token is rejected with `403 Forbidden`.

---

## Redis Key Schema

All keys are namespaced by `purpose`, `tenant_code`, and `phone` to prevent cross-module
and cross-tenant collisions.

| Key | Value | TTL |
|-----|-------|-----|
| `otp:code:{purpose}:{tenant_code}:{phone}` | The OTP code (6 digits) | 600 s |
| `otp:attempts:{purpose}:{tenant_code}:{phone}` | Attempt counter (integer) | 600 s |
| `otp:cooldown:{purpose}:{tenant_code}:{phone}` | Resend-block sentinel | 60 s |
| `otp:token:{uuid}` | `{phone}:{tenant_code}:{purpose}` (payload) | 300 s |

No database table is used. OTP state is entirely ephemeral and lives in Redis only.

---

## Delivery

OTP codes are delivered as follows:

1. **Primary — WhatsApp**: via `WHATSAPP_API_URL` + `WHATSAPP_API_TOKEN` environment
   variables. The platform messaging layer (`backend/app/core/messaging.py`) attempts
   WhatsApp first.
2. **Fallback — SMS**: via `SMS_GATEWAY_URL`. Used automatically if the WhatsApp
   delivery attempt returns a non-2xx response.

Module code never calls delivery adapters directly.

---

## Rate Limits

| Limit | Value | Scope |
|-------|-------|-------|
| Max verification attempts | 5 per 10 min | per `purpose:tenant_code:phone` |
| Resend cooldown | 60 s | per `purpose:tenant_code:phone` |
| nginx `limit_req_zone` | 5 req/min/IP | on `location /api/v1/otp/` |

Exceeding the attempt limit returns `429 Too Many Requests`. The resend cooldown is
enforced by the presence of `otp:cooldown:*` in Redis — the endpoint returns
`{ "error": "resend_cooldown", "resend_after": <remaining_seconds> }` while the key
exists.

---

## Consequences

### Positive

- Modules are simpler: no OTP code, no Redis key management, no delivery adapter wiring.
- Any future module that needs phone verification gets it for free by calling two endpoints.
- The platform owns the entire security surface for OTP — one audit covers all modules.
- Rate-limiting policy is consistent across modules and can be tightened globally in one place.

### Negative / constraints

- Modules cannot customise OTP code length, TTL, or delivery channel per-workflow.
  If a future module needs a materially different policy, a new `purpose` prefix or a
  platform configuration extension will be required.
- All OTP traffic flows through the platform service; a Redis outage disables OTP for
  all modules simultaneously.

---

## Implementation Checklist

- [ ] `backend/app/routers/otp.py` — implement `/send` and `/verify` endpoints
- [ ] `backend/app/core/messaging.py` — WhatsApp primary + SMS fallback delivery logic
- [ ] `backend/app/main.py` — register the OTP router
- [ ] `infra/nginx/app.conf` — add `limit_req_zone` and `limit_req` directives for
      `location ~ ^/api/v1/otp/`
- [ ] Platform SDK — expose `consume_otp_token(token, phone, tenant_code, purpose)`
      helper for module registration endpoints
- [ ] Docs — update `docs/modules/CREATING_A_MODULE.md` with OTP usage pattern
