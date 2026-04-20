# App-Buildify — Full System Backlog

> **Structure**: Epic → Feature → Story  
> **Platform**: Multi-tenant NoCode/LowCode enterprise app builder (FastAPI + Vanilla JS)

## Status Legend

| Tag | Meaning |
|-----|---------|
| `[DONE]` | Fully implemented in the codebase |
| `[IN-PROGRESS]` | Partially implemented or has known bugs |
| `[OPEN]` | Documented gap — design exists, code does not |
| `[PLANNED]` | Roadmap item — no code or design yet |

---

## Summary Table

| # | Epic | Status |
|---|------|--------|
| 1 | Authentication & Identity Management | Mostly DONE; 2FA/SSO PLANNED |
| 2 | Multi-Tenancy & Organization Management | Mostly DONE; Tiers PLANNED |
| 3 | User Management | DONE |
| 4 | RBAC & Permissions | Mostly DONE; Entity Perms OPEN |
| 5 | NoCode Entity Designer | Mixed DONE/OPEN |
| 6 | Dynamic CRUD & API Layer | Mostly DONE; Bulk OPEN |
| 7 | Workflow Engine | DONE |
| 8 | Automation Rules | DONE; Webhooks PLANNED |
| 9 | Dashboard & Analytics | DONE |
| 10 | Reporting | DONE |
| 11 | Module System | Mostly DONE; Marketplace PLANNED |
| 12 | Financial Module | DONE; AP/Budget PLANNED |
| 13 | Security & Compliance | Mostly DONE; Prometheus/Tests OPEN |
| 14 | Notification System | Arch DONE; Delivery OPEN/PLANNED |
| 15 | Flex Component Library | Core DONE; 5 Components PLANNED |
| 16 | Internationalization | DONE; Module i18n PLANNED |
| 17 | Settings & Configuration | DONE; White-Label PLANNED |
| 18 | Developer Experience & Module SDK | Partial DONE; Guide PLANNED |
| 19 | Infrastructure & Deployment | Mostly DONE; CI/CD PLANNED |
| 20 | Mobile & Progressive Web App | PLANNED |

---

## EPIC 1 — Authentication & Identity Management

> Secure multi-method authentication: credential login, token lifecycle, MFA, and SSO. Foundation for all other epics.

---

### Feature 1.1 — Email/Password Login `[DONE]`

#### Story 1.1.1 — User Login with JWT Tokens `[DONE]`
*As a user, I want to log in with my email and password and receive access and refresh tokens, so that I can authenticate all subsequent API requests without re-entering credentials.*
- `POST /auth/login` accepts `{email, password}` and returns `{access_token, refresh_token, user}`
- Access token expires in 30 min; refresh token expires in 7 days (both configurable)
- JWT payload contains `sub`, `tenant_id`, `exp`, `iat`, `jti`
- Invalid credentials → 401; locked account → 423; rate-limited → 429

#### Story 1.1.2 — Token Refresh `[DONE]`
*As a user, I want my session to silently renew before it expires, so that I am not logged out unexpectedly mid-work.*
- `POST /auth/refresh` accepts a valid refresh token and returns a new access token
- Frontend auto-retries with refresh token on 401 response
- Expired refresh tokens return 401 and force re-login
- Refresh tokens are rotated on use to prevent replay attacks

#### Story 1.1.3 — Logout and Token Revocation `[DONE]`
*As a user, I want my session tokens invalidated immediately on logout, so that stolen tokens cannot be reused.*
- `POST /auth/logout` adds the token `jti` to the Redis blacklist with remaining-TTL expiry
- Every authenticated request checks the blacklist; revoked `jti` → 401
- Session record in `user_sessions` marked inactive on logout
- Audit log records the logout event with IP and user-agent

#### Story 1.1.4 — Password Reset Flow `[DONE]`
*As a user who forgot their password, I want to receive a reset link and set a new password, so that I can regain account access.*
- `POST /auth/forgot-password` creates a `password_reset_token` record and queues a notification
- `POST /auth/reset-password` accepts a valid token + new password
- Reset tokens expire after a configurable TTL (default 1 hour) and are single-use
- New password is validated against the tenant's active password policy before acceptance

#### Story 1.1.5 — Password Strength Check API `[DONE]`
*As a frontend developer, I want a real-time password strength endpoint, so that users see strength feedback while typing.*
- `POST /auth/strength-check` accepts `{password}` and returns a strength score and list of unmet rules
- `GET /auth/password-requirements` returns the current tenant's policy rules for display in the UI
- Frontend renders a strength meter using the score (0–100) returned by the endpoint

---

### Feature 1.2 — Session Management `[DONE]`

#### Story 1.2.1 — Idle and Absolute Session Timeouts `[DONE]`
*As a security administrator, I want sessions to expire after inactivity and after a hard maximum, so that unattended terminals cannot be exploited.*
- Idle timeout (default 30 min) and absolute timeout (default 8 h) configurable in `SecurityPolicy`
- Each authenticated request refreshes the idle timeout timestamp on the session record
- Requests after timeout → 401 with `SESSION_EXPIRED` error code
- Frontend shows "Session expired" message and redirects to login

#### Story 1.2.2 — Concurrent Session Limits `[DONE]`
*As a tenant administrator, I want to cap how many simultaneous sessions each user can have, so that shared credentials are detected and controlled.*
- `max_concurrent_sessions` configurable in `SecurityPolicy` (default: 3)
- New login exceeding the limit terminates the oldest session or rejects login (configurable)
- `single_session_mode = true` terminates all prior sessions on new login
- Active sessions are visible in the user's session management UI

#### Story 1.2.3 — Session Listing and Forced Termination `[DONE]`
*As a user, I want to see all my active sessions and revoke any I don't recognize, so that I can respond to unauthorized access immediately.*
- `GET /users/me/sessions` returns active sessions with device hint, IP, and last-seen timestamp
- `DELETE /users/me/sessions/{id}` terminates a specific session (adds `jti` to Redis blacklist)
- `DELETE /users/me/sessions` terminates all sessions except the current one
- All session termination actions are audit-logged

---

### Feature 1.3 — Password Policy Engine `[DONE]`

#### Story 1.3.1 — Configurable Password Strength Rules `[DONE]`
*As a tenant administrator, I want to enforce minimum password complexity requirements, so that users are forced to choose secure passwords.*
- Policy supports: `min_length`, `max_length`, `require_uppercase`, `require_lowercase`, `require_digit`, `require_special_char`
- Optionally blocks common passwords and username-as-password
- Validation runs on create, reset, and change; returns specific failure message per violated rule
- Per-tenant policy overrides platform defaults; superadmin manages platform defaults

#### Story 1.3.2 — Password History and Rotation `[DONE]`
*As a security administrator, I want users to be unable to reuse recent passwords, so that password rotation policies are effective.*
- Last N password hashes stored in `password_history` table (N configurable, default 5)
- On password change, each stored hash is bcrypt-checked; match → validation error
- `expiration_days` (default 90) triggers expiry; `expiration_warning_days` (default 14) shows a banner
- `grace_logins` (default 3) allows login after expiry with a forced-change prompt

#### Story 1.3.3 — Account Lockout (Progressive and Fixed) `[DONE]`
*As a security administrator, I want failed login attempts to trigger account lockout, so that brute-force attacks are blocked.*
- After `max_attempts` (default 5) consecutive failures, the account is locked
- `lockout_type = "progressive"` doubles duration per successive lockout; `"fixed"` applies a constant duration
- `login_attempts` table records each attempt with IP, user-agent, timestamp, and outcome
- Failed-attempt counter resets after `reset_attempts_after_min` (default 60 min) with no failures

---

### Feature 1.4 — Two-Factor Authentication `[PLANNED]`

#### Story 1.4.1 — TOTP Setup and Enrollment `[PLANNED]`
*As a user, I want to enroll an authenticator app as a second factor, so that my account is protected even if my password is compromised.*
- `POST /auth/2fa/setup/totp` generates a TOTP secret and returns a QR code URI
- User confirms enrollment by submitting a valid TOTP code; server stores the secret
- 8 single-use backup recovery codes generated at enrollment time
- `is_2fa_enabled` flag on user record set to `true` after confirmed enrollment

#### Story 1.4.2 — TOTP Login Verification `[PLANNED]`
*As a user with 2FA enabled, I want to be prompted for my authenticator code after my password, so that both factors are required.*
- Successful password login with 2FA enabled returns an intermediate `mfa_challenge_token` (not full tokens)
- `POST /auth/2fa/verify` accepts `{mfa_challenge_token, code}` and issues full tokens on valid code
- Challenge token expires in 5 minutes
- Three consecutive failed TOTP attempts invalidate the challenge and require re-login

#### Story 1.4.3 — SMS Second Factor `[PLANNED]`
*As a user without an authenticator app, I want to receive a one-time code via SMS, so that I can still use two-factor authentication.*
- Tenant admin enables SMS 2FA via `NotificationConfig` SMS provider settings
- `POST /auth/2fa/setup/sms` registers and verifies a phone number
- `POST /auth/2fa/send-sms` sends a 6-digit OTP via the configured SMS adapter
- OTP expires in 10 minutes, is single-use, and rate-limited to 5 per hour per user

#### Story 1.4.4 — 2FA Policy Enforcement per Tenant `[PLANNED]`
*As a tenant administrator, I want to mandate 2FA for all users in my tenant, so that I meet our security compliance requirements.*
- `require_2fa` flag in `SecurityPolicy` forces enrollment on next login for all tenant users
- Users without 2FA enrolled are redirected to the enrollment flow after password authentication
- Grace period configurable (e.g. 7 days to enroll before access is blocked)
- Superadmin can exempt specific users from the mandate

---

### Feature 1.5 — SSO / SAML / OAuth2 `[PLANNED]`

#### Story 1.5.1 — SAML 2.0 Service Provider Integration `[PLANNED]`
*As an enterprise tenant administrator, I want to configure a SAML Identity Provider, so that employees log in with corporate credentials without a separate password.*
- Admin uploads or pastes IdP metadata XML via the settings UI
- Platform acts as a SAML SP; generates SP metadata at `/auth/saml/metadata`
- Successful SAML assertion creates or updates the local user record (JIT provisioning)
- Attribute mapping configurable: IdP attributes → `email`, `full_name`, `role` fields

#### Story 1.5.2 — OAuth2/OIDC Provider Login `[PLANNED]`
*As a user, I want to log in using Google, Microsoft, or another OAuth2 provider, so that I don't need a separate password.*
- Platform supports OAuth2 Authorization Code flow with PKCE
- Google Workspace and Microsoft Entra are pre-configured providers
- Tenant admin can register custom OIDC providers with `client_id`, `client_secret`, `discovery_url`
- On first OAuth login, a local user record is created and linked to the OAuth identity

#### Story 1.5.3 — SSO Session Synchronization `[PLANNED]`
*As a tenant administrator, I want IdP-initiated logout to automatically log users out of the platform, so that central session revocation is honored.*
- SAML Single Logout (SLO) request from IdP invalidates the corresponding platform session
- Platform-initiated logout can optionally send an SLO request to the IdP
- Session audit log records the SSO provider as the logout initiator

---

## EPIC 2 — Multi-Tenancy & Organization Management

> Fully isolated multi-tenant architecture with a four-level org hierarchy: Tenant → Company → Branch → Department.

---

### Feature 2.1 — Tenant Lifecycle Management `[DONE]`

#### Story 2.1.1 — Tenant Provisioning `[DONE]`
*As a platform superadmin, I want to create new tenant organizations, so that clients can be onboarded independently.*
- `POST /org/tenants` creates a tenant with `name`, `slug`, `domain`, and initial admin user
- Tenant `slug` is unique platform-wide and used in API scoping
- Creating a tenant seeds default roles, security policy, and notification config
- `tenant.created` event published to the event bus for module initialization hooks

#### Story 2.1.2 — Tenant Settings and Branding `[DONE]`
*As a tenant administrator, I want to configure my organization's name, logo, and color theme, so that the platform presents a consistent brand.*
- `TenantSettings` stores `tenant_name`, `logo_url`, `primary_color`, `secondary_color`, `theme_config`
- Settings applied at runtime to the frontend via the settings API
- Tenant admin can update branding without superadmin involvement
- Color tokens from `theme_config` override CSS custom properties platform-wide for that tenant

#### Story 2.1.3 — Tenant Suspension and Deactivation `[DONE]`
*As a superadmin, I want to suspend a tenant without deleting data, so that billing issues can be handled while preserving records.*
- Tenant `is_active = false` causes all authenticated requests from that tenant to return 403
- Suspension does not delete any data; reactivation restores full access
- Superadmin audit log records suspension and reactivation events with reason
- Suspended tenants receive a configurable notification

---

### Feature 2.2 — Organization Hierarchy `[DONE]`

#### Story 2.2.1 — Company Management `[DONE]`
*As a tenant administrator, I want to create and manage multiple companies within my tenant, so that I can represent distinct legal entities or subsidiaries.*
- `POST /org/companies` creates a company with `name`, `code`, `currency`, `timezone`, `fiscal_year_start`
- `company.created` event published to the event bus
- Users can be granted access to multiple companies within the same tenant
- Company-scoped RBAC permissions limit data visibility to each company

#### Story 2.2.2 — Branch Management `[DONE]`
*As a company administrator, I want to create branches, so that I can scope data to physical or virtual locations.*
- `POST /org/branches` creates a branch under a company with optional `parent_branch_id` for hierarchy
- RBAC scopes can be set at company or branch level independently
- Data queries with `scope=branch` automatically filter to the current user's branch context

#### Story 2.2.3 — Department Management `[DONE]`
*As a company administrator, I want to organize users into departments, so that department-level data access can be enforced.*
- `POST /org/departments` creates a department under a branch with a `manager_user_id`
- Users belong to exactly one department but can be granted cross-department data access
- Department hierarchy appears in the org chart UI

#### Story 2.2.4 — User-Company Access Control `[DONE]`
*As a tenant administrator, I want to grant users access to specific companies, so that multi-company tenants maintain data isolation.*
- `user_company_access` junction table controls which companies each user can access
- Users without access to a company receive 403 on any company-scoped resource
- Users can switch active company from the UI without re-logging in
- Audit log records company access grant/revoke actions

---

### Feature 2.3 — Subscription Tier Enforcement `[PLANNED]`

#### Story 2.3.1 — Subscription Tier Model `[PLANNED]`
*As a platform operator, I want each tenant to have an assigned subscription tier, so that feature access and usage limits are enforced programmatically.*
- `subscription_tier` field on `Tenant` model: `free`, `basic`, `premium`, `enterprise`
- Tier definitions stored as configuration specifying: max users, max modules, max entities, API rate limit
- `TenantTierMiddleware` intercepts requests and enforces limits before route handlers
- Exceeding a limit returns 402 (Payment Required) with a descriptive upgrade message

#### Story 2.3.2 — User and Module Limits per Tier `[PLANNED]`
*As a platform operator, I want free-tier tenants capped at a defined user and module count, so that resource usage is monetizable.*
- `POST /users` on a tenant at their user cap returns 402 with `TIER_LIMIT_EXCEEDED`
- Enabling a module that exceeds the tier limit is blocked with an upgrade prompt
- Usage vs. limits visible to tenant admin in a "Usage" settings page

#### Story 2.3.3 — API Rate Limits per Tier `[PLANNED]`
*As a platform operator, I want API rate limits to scale with subscription tier, so that free-tier tenants cannot degrade performance for paid tenants.*
- SlowAPI reads the tenant's tier from JWT or DB: Free 60 rpm / Basic 300 / Premium 1000 / Enterprise unlimited
- Rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) returned on every response
- HTTP 429 body includes a tier upgrade suggestion

---

## EPIC 3 — User Management

> Full lifecycle management of user accounts: CRUD, profiles, group membership, and cross-company access.

---

### Feature 3.1 — User CRUD `[DONE]`

#### Story 3.1.1 — User Creation by Admin `[DONE]`
*As a tenant administrator, I want to create user accounts, so that organization members can access the platform with appropriate roles.*
- `POST /users` creates a user with `email`, `full_name`, `password`, `tenant_id`, optional role assignments
- Email must be unique within a tenant; password hashed with bcrypt
- Welcome notification queued on user creation (subject to notification delivery config)
- Superadmin can create users in any tenant; tenant admin only in their own tenant

#### Story 3.1.2 — User Profile Management `[DONE]`
*As a user, I want to update my own profile information, so that my name, timezone, and language preference are current.*
- `PUT /users/me` allows updating `full_name`, `phone`, `timezone`, `language`, `avatar_url`
- `PUT /users/{id}` restricted to tenant admin or superadmin
- Language change reflected in UI immediately without re-login

#### Story 3.1.3 — User Activation and Deactivation `[DONE]`
*As a tenant administrator, I want to deactivate a user without deleting their account, so that access is revoked while audit history is preserved.*
- `PATCH /users/{id}/status` toggles `is_active`; deactivated users cannot log in (401)
- All active sessions of a deactivated user are terminated immediately via Redis blacklist
- Audit log records deactivation with the acting admin's identity

#### Story 3.1.4 — Admin-Initiated Password Reset `[DONE]`
*As a tenant administrator, I want to force-reset a user's password, so that I can handle account recovery requests.*
- `POST /users/{id}/reset-password` generates a reset token and queues a reset email
- Superadmin can force password reset on any user across all tenants
- All admin password reset actions are audit-logged

---

### Feature 3.2 — User Groups and Teams `[DONE]`

#### Story 3.2.1 — Group Creation and Membership `[DONE]`
*As a tenant administrator, I want to create user groups and assign members, so that I can manage role assignments at scale.*
- `POST /rbac/groups` creates a group with `name`, `description`, `tenant_id`
- `POST /rbac/groups/{id}/members` adds users to a group
- A user can belong to multiple groups; effective permissions are the union of all group roles
- Group membership changes take effect on the next authenticated request

#### Story 3.2.2 — Group Role Assignment `[DONE]`
*As a tenant administrator, I want to assign roles to groups, so that access management scales with organization size.*
- `POST /rbac/groups/{id}/roles` assigns roles to a group
- Removing a role from a group removes it from all group members immediately
- Permission evaluation path: user direct roles → group roles (union of all)

---

## EPIC 4 — RBAC & Permissions

> Fine-grained Role-Based Access Control with `resource:action:scope` permission model, wildcard support, and enforcement at API and UI layers.

---

### Feature 4.1 — Role Management `[DONE]`

#### Story 4.1.1 — System and Custom Role Definitions `[DONE]`
*As a tenant administrator, I want to create custom roles with specific permission sets, so that I can model my organization's actual job functions.*
- `POST /rbac/roles` creates a tenant-scoped role with a `name` and `description`
- System roles (`SuperAdmin`, `TenantAdmin`, `CompanyAdmin`, `Manager`, `User`) are seeded and immutable
- Custom roles can be cloned from system roles as a starting point
- Role names are unique within a tenant

#### Story 4.1.2 — Permission Assignment to Roles `[DONE]`
*As a tenant administrator, I want to attach specific permissions to roles, so that role holders receive exactly the access they need.*
- `POST /rbac/roles/{id}/permissions` assigns permissions by permission ID (bulk array supported)
- `DELETE /rbac/roles/{id}/permissions/{perm_id}` removes a single permission
- Permission changes take effect on the next authenticated request for all role holders

#### Story 4.1.3 — User Role Assignment `[DONE]`
*As a tenant administrator, I want to assign roles to individual users, so that they gain the permissions defined by those roles.*
- `POST /rbac/users/{id}/roles` assigns roles to a user; a user can hold multiple direct roles
- Role assignment is scoped: a tenant admin cannot assign roles from other tenants
- All role assignment actions are audit-logged

---

### Feature 4.2 — Permission Engine `[DONE]`

#### Story 4.2.1 — Permission Format and Wildcard Matching `[DONE]`
*As a developer, I want permissions to support wildcard matching, so that broad access can be granted without enumerating every action.*
- Permission format: `resource:action:scope` (e.g. `financial:invoices:create:company`)
- Wildcards supported at any segment: `*:*:platform`, `users:*:tenant`, `data:read:*`
- `require_permission(code)` dependency evaluates wildcard matches correctly
- `*:*:platform` supersedes all other permission checks (superadmin wildcard)

#### Story 4.2.2 — Scope Hierarchy Enforcement `[DONE]`
*As a developer, I want the RBAC system to automatically scope data to the user's organizational level, so that users cannot access data outside their boundary.*
- Scope hierarchy: `platform > tenant > company > branch > department`
- `_get_org_context()` injects the correct WHERE clause into all queries based on user scope
- Scope context derived from the JWT payload and session — never from request parameters

#### Story 4.2.3 — Frontend RBAC Filtering `[DONE]`
*As a frontend developer, I want a `hasPermission()` utility that reflects the current user's permissions, so that UI elements are shown or hidden based on access rights.*
- `hasPermission('resource:action:scope')` returns boolean using the current session's permission list
- Full permission list loaded once at login and cached in-memory; refreshed on token renewal
- Menu items, action buttons, and routes are filtered before rendering; hidden elements are not in the DOM

#### Story 4.2.4 — Per-Entity Permission Enforcement `[OPEN]`
*As a security architect, I want per-entity RBAC enforced on the dynamic data API, so that custom entities can have access rules independent of global RBAC.*
- `EntityDefinition.permissions` JSONB `{role: [actions]}` evaluated in `DynamicEntityService` before CRUD
- When `permissions` is null, global RBAC is the sole check
- Unauthorized access returns 403 with `ENTITY_PERMISSION_DENIED` error code
- Dynamic data router uses `Depends(require_permission("{entity_name}:read:tenant"))` for GET and appropriate verbs for mutations

---

## EPIC 5 — NoCode Entity Designer

> Visual interface for designing custom database tables (entities) with fields, relationships, constraints, and lifecycle management.

---

### Feature 5.1 — Entity Lifecycle Management `[DONE]`

#### Story 5.1.1 — Entity Creation `[DONE]`
*As a tenant administrator, I want to create a custom entity with a name and description, so that my business can track custom data objects without writing code.*
- `POST /data-model/entities` creates an entity in `draft` status with `name`, `label`, `plural_label`, `icon`, `category`
- Draft entities are invisible to the runtime data API until published
- Entity creation is recorded in the audit log
- `entity_type` can be `custom`, `virtual`, or `system`

#### Story 5.1.2 — Entity Publishing and Migration `[DONE]`
*As a tenant administrator, I want to publish my entity design so that a real database table is created and records can be stored.*
- `POST /data-model/entities/{id}/publish` triggers DDL execution via Alembic
- Status transitions: `draft → migrating → published` (or back to `draft` on failure)
- Write operations during `migrating` status return 503; reads return last valid model
- Migration failure returns error details and reverts status to `draft`

#### Story 5.1.3 — Entity Archival `[DONE]`
*As a tenant administrator, I want to archive obsolete entities without losing historical data, so that the data model can evolve cleanly.*
- `POST /data-model/entities/{id}/archive` transitions status to `archived`
- Archived entities return 404 from the dynamic data API
- Archive is blocked if other published entities have active FK relationships to this entity
- Archival is reversible by republishing

#### Story 5.1.4 — Virtual Entity (PostgreSQL View Mapping) `[DONE]`
*As a developer, I want to map existing PostgreSQL views to entities, so that complex SQL queries are accessible through the standard API.*
- `entity_type = "virtual"` and `table_name = "<view_name>"` maps the entity to an existing DB view
- `meta_data.view_sql` can contain a `CREATE OR REPLACE VIEW` statement executed during migration
- `POST`, `PUT`, `DELETE` on virtual entities return 405 Method Not Allowed
- `GET` list, single-record, metadata, and aggregate endpoints all work on virtual entities

#### Story 5.1.5 — Entity Versioning (Record History) `[OPEN]`
*As a tenant administrator, I want entities with `is_versioned = true` to keep a history of record changes, so that I can audit data modifications over time.*
- `update_record()` inserts the previous row into a `{entity_name}_versions` shadow table before applying updates
- `GET /dynamic-data/{entity}/records/{id}/versions` returns change history in reverse chronological order
- Version records include `changed_by`, `changed_at`, and a diff of modified fields
- Reports default to querying the current version; `include_versions=true` exposes history

---

### Feature 5.2 — Field System `[DONE / OPEN]`

#### Story 5.2.1 — Field Types and Constraints `[DONE]`
*As a tenant administrator, I want to define fields with various data types and validation constraints, so that data quality is enforced at the schema level.*
- Supported `field_type` values: `text`, `number`, `decimal`, `boolean`, `date`, `datetime`, `email`, `phone`, `url`, `select`, `multi_select`, `relationship`, `lookup`, `calculated`, `uuid`, `json`
- Constraints: `is_required`, `is_unique`, `is_indexed`, `max_length`, `min_length`, `max_value`, `min_value`, `precision`, `decimal_places`
- Constraints enforced at both DB level (DDL) and service layer (`_validate_and_prepare_data()`)
- `is_system` fields cannot be deleted by tenant admin

#### Story 5.2.2 — Select/Enum Fields with Allowed Values `[OPEN]`
*As a tenant administrator, I want to define a fixed list of acceptable values for a field, so that data entry is constrained to predefined options.*
- `allowed_values` JSONB schema: `[{"value": "active", "label": "Active", "label_i18n": {...}}]`
- Pydantic validator on `FieldDefinitionCreate` rejects non-conforming shapes for `select`/`enum` types
- `_validate_and_prepare_data()` enforces value membership; error includes the allowed list
- `allowed_values` exposed in `GET /dynamic-data/{entity}/metadata` response

#### Story 5.2.3 — Calculated Fields `[DONE]`
*As a tenant administrator, I want fields whose values are computed from other fields, so that derived data is always consistent without application logic.*
- `is_calculated = true` and `calculation_formula` (e.g. `{unit_price} * {quantity}`) generates a `GENERATED ALWAYS AS ... STORED` PostgreSQL column
- `{field_name}` tokens replaced with column names during DDL generation
- Calculated fields are filterable and sortable; flagged as read-only in metadata response
- Clients cannot submit values for calculated fields; service ignores or rejects them

#### Story 5.2.4 — Custom Validation Rules `[OPEN]`
*As a tenant administrator, I want to define custom field validation rules beyond built-in constraints, so that business-specific rules are enforced on data entry.*
- `validation_rules` JSONB schema: `[{"type": "regex", "pattern": "^[A-Z]", "message": "Must start with uppercase"}]`
- Supported rule types: `regex`, `min_length`, `max_length`, `min_value`, `max_value`
- `validate_value()` in `FieldTypeMapper` iterates and applies all rules
- Validation failures include the rule type in the structured error response

#### Story 5.2.5 — Cascading Field Dependencies `[OPEN]`
*As a tenant administrator, I want lookup fields to filter options based on a parent field value, so that dependent dropdowns work correctly (e.g. City filtered by Country).*
- `depends_on_field` and `filter_expression` on `FieldDefinition` define the dependency
- Server-side: lookup options API applies the expression as a WHERE clause when `depends_on_field` is set
- Metadata endpoint exposes `depends_on_field` so the frontend can wire cascading dropdowns
- Changing the parent field value clears the dependent field value in form mode

---

### Feature 5.3 — Relationships and Lookups `[DONE]`

#### Story 5.3.1 — Foreign Key Relationship Fields `[DONE]`
*As a tenant administrator, I want relationship fields that point to records in another entity, so that normalized data can be associated without custom SQL.*
- Relationship field defines `ref_entity_name`, `ref_field`, `relationship_type` (`many-to-one`, `one-to-many`, `many-to-many`)
- DDL generates a proper PostgreSQL FK constraint with configurable `ON DELETE` behavior
- `GET /dynamic-data/{entity}/records?expand=customer_id` inlines related records as `customer_id_data` (no N+1)
- Expand depth is limited to 1 level

#### Story 5.3.2 — Relationship Traversal Endpoint `[OPEN]`
*As a frontend developer, I want to retrieve all related records for a given record in one API call, so that related-record panels can be built without complex joins.*
- `GET /dynamic-data/{entity}/records/{id}/{relationship}` returns paginated related records
- Supports `page`, `page_size`, `sort_by`, `filters`, `search` consistent with `list_records`
- Soft-deleted target records excluded unless `include_deleted=true`
- Org-scope filters applied to the target entity's records

#### Story 5.3.3 — Lookup Fields `[DONE]`
*As a tenant administrator, I want dropdown fields that reference records from any entity, so that users select standardized values rather than typing free text.*
- Lookup field config stores `lookup_entity`, `value_field`, `label_field`
- `GET /lookups/{name}` returns filtered options with search/filter parameters for large option sets
- Lookup fields rendered as searchable dropdowns in auto-generated forms

---

### Feature 5.4 — Soft Delete `[OPEN]`

#### Story 5.4.1 — Soft Delete Implementation `[OPEN]`
*As a tenant administrator, I want deleted records to be soft-deleted by default, so that accidental deletions can be recovered and audit trails remain complete.*
- When `supports_soft_delete = true`, `DELETE` sets `deleted_at` timestamp instead of hard delete
- `list_records()` automatically applies `WHERE deleted_at IS NULL` for soft-delete entities
- `GET /dynamic-data/{entity}/records/{id}` for a soft-deleted record returns 404
- `include_deleted=true` parameter allows viewing soft-deleted records (admin only)
- Aggregate queries also exclude soft-deleted records from counts and sums by default

---

## EPIC 6 — Dynamic CRUD & API Layer

> Auto-generated REST API for all published entities with filtering, sorting, searching, pagination, aggregation, and bulk operations.

---

### Feature 6.1 — Standard CRUD Operations `[DONE]`

#### Story 6.1.1 — Record Create, Read, Update, Delete `[DONE]`
*As a developer, I want auto-generated CRUD endpoints for every published entity, so that I can build frontend pages without writing custom backend code.*
- `POST /dynamic-data/{entity}/records` creates a record, validates against field definitions
- `GET /dynamic-data/{entity}/records/{id}` returns a single record; 404 if not found or soft-deleted
- `PUT /dynamic-data/{entity}/records/{id}` updates a record; calculated and system fields are ignored
- `DELETE /dynamic-data/{entity}/records/{id}` deletes or soft-deletes based on entity config
- List response uses standard envelope `{items, total, page, page_size, pages}`

#### Story 6.1.2 — Filtering, Sorting, Searching, Pagination `[DONE]`
*As a frontend developer, I want to filter, sort, search, and paginate entity records via query parameters, so that large datasets are manageable.*
- `?filters={"operator":"AND","conditions":[...]}` applies structured filters (operator key required)
- `?sort_by=field_name&sort_order=asc` applies sorting; defaults to entity's `default_sort_field`
- `?search=term` applies full-text search across the entity's searchable fields
- `?page=1&page_size=20` paginates; response includes `total` and `pages`

#### Story 6.1.3 — Structured Validation Error Responses `[IN-PROGRESS]`
*As a frontend developer, I want per-field validation error details in the API response, so that I can highlight exactly which fields failed and why.*
- On validation failure (400), API returns `{"detail": "...", "errors": [{"field": "email", "message": "..."}]}`
- `base-service.js` attaches `error.errors` to the thrown error object
- `dynamic-form.js` `showFieldErrors(errors)` maps each `{field, message}` to its input element
- `entity-manager.js` `saveRecord()` calls `form.showFieldErrors(error.errors)` when present

---

### Feature 6.2 — Aggregation API `[DONE]`

#### Story 6.2.1 — Server-Side GROUP BY Analytics `[DONE]`
*As a dashboard builder, I want to run aggregation queries against any entity without SQL, so that KPI widgets and charts are powered by live data.*
- `GET /dynamic-data/{entity}/aggregate?group_by=status&metrics=[{"field":"amount","function":"sum"}]`
- Supported functions: `count`, `sum`, `avg`, `min`, `max`, `count_distinct`; `COUNT(*)` via `field="*"`
- `date_trunc` + `date_field` parameters enable time-series grouping by `hour/day/week/month/quarter/year`
- Org-scope isolation applies identically to `list_records`

#### Story 6.2.2 — Aggregation Hints in Entity Metadata `[OPEN]`
*As a dashboard widget builder, I want the entity metadata to include hints about which fields are aggregatable, so that widget UIs can auto-populate axis and metric selectors.*
- `table_config` JSONB schema defined: `{columns: [{field, label, visible, sortable, filterable, aggregatable, aggregate_functions, format}]}`
- `aggregatable: true` and `aggregate_functions` auto-populated for numeric field types
- `format` auto-derived from `field_type` and `prefix`/`suffix` hints (e.g. `$` prefix → `format: "currency"`)
- `GET /dynamic-data/{entity}/metadata` includes `table_config` in the response

---

### Feature 6.3 — Bulk Operations `[OPEN]`

#### Story 6.3.1 — Bulk Create (CSV Import) `[OPEN]`
*As a tenant administrator, I want to import records from a CSV file, so that I can migrate existing data without manual entry.*
- `POST /dynamic-data/{entity}/records/bulk` with `{"records": [...]}` creates multiple records in a single transaction
- Frontend "Import" button accepts CSV; column mapping UI maps CSV headers to entity fields via metadata
- Response includes `created`, `failed`, and `errors` arrays (partial success supported)
- Import limited to 1000 records per request

#### Story 6.3.2 — Bulk Update and Bulk Delete `[OPEN]`
*As a power user, I want to select multiple records and update a field or delete them all at once, so that batch data corrections are efficient.*
- `PUT /dynamic-data/{entity}/records/bulk` accepts `{"records": [{id, ...fields}]}` and updates each
- `DELETE /dynamic-data/{entity}/records/bulk` accepts `{"ids": [...]}` and soft-deletes each
- `FlexTable` `bulkAction` event connected in `entity-manager.js` to call the appropriate bulk method
- Bulk action toolbar appears above the table when rows are selected
- Audit log records bulk operations with count and summary

---

## EPIC 7 — Workflow Engine

> Business process state machines that control entity lifecycle transitions, approval routing, and multi-step process orchestration.

---

### Feature 7.1 — Workflow Design `[DONE]`

#### Story 7.1.1 — Workflow Definition Creation `[DONE]`
*As a tenant administrator, I want to define a workflow for an entity by specifying states and transitions, so that business processes are enforced consistently.*
- `POST /workflows` creates a `WorkflowDefinition` with `name`, `label`, `entity_id`, `trigger_type`, `canvas_data`
- Canvas data stores nodes (states) and edges (transitions) including positions for visual rendering
- Trigger types: `manual`, `automatic`, `scheduled`
- Workflow is versioned; `version` increments on publish

#### Story 7.1.2 — State Machine Transitions `[DONE]`
*As a user, I want to advance a record through workflow states by clicking action buttons, so that business process steps are tracked and enforced.*
- Permitted transitions evaluated based on record's current state and user's permissions
- Invalid transitions return 400 with `INVALID_STATE_TRANSITION` error code
- State transitions can have entry/exit actions (e.g. send notification, trigger automation)
- `trigger_conditions` JSONB specifies automatic transition criteria

#### Story 7.1.3 — Approval Workflows `[DONE]`
*As a manager, I want certain workflow transitions to require my approval before proceeding, so that significant changes are reviewed before taking effect.*
- Transition config specifies `required_approvers` (by role or user)
- Approval request creates a task/notification for each approver
- Record enters an `awaiting_approval` sub-state during the approval process
- Rejection returns the record to the previous state with a rejection reason

---

### Feature 7.2 — Workflow Execution and Monitoring `[DONE]`

#### Story 7.2.1 — Workflow Execution History `[DONE]`
*As an auditor, I want to see the full transition history of a record, so that I can reconstruct how a business process unfolded.*
- `GET /workflows/{entity_id}/records/{record_id}/history` returns all state transitions
- Each record includes `from_state`, `to_state`, `transitioned_by`, `transitioned_at`, `reason`
- Workflow history is immutable once written
- History included in the entity audit log

#### Story 7.2.2 — Active Workflow Monitoring `[DONE]`
*As a manager, I want a dashboard of records currently in each workflow state, so that bottlenecks and stuck approvals are visible.*
- `GET /workflows/{workflow_id}/state-counts` returns record counts grouped by current state
- Records stuck in `awaiting_approval` beyond a configurable SLA period are flagged
- Overdue items shown with visual indicators in the workflow monitor UI

---

## EPIC 8 — Automation Rules

> Event-driven and scheduled automation rules that trigger actions (notifications, API calls, field updates, webhooks) when configurable conditions are met.

---

### Feature 8.1 — Automation Rule Configuration `[DONE]`

#### Story 8.1.1 — Database Event Triggers `[DONE]`
*As a tenant administrator, I want automation rules to fire when records are created, updated, or deleted, so that downstream processes are triggered automatically.*
- Automation rule config: `trigger_type = "database_event"`, `entity_id`, `event_type` (`create`/`update`/`delete`/`any`)
- Event bus (`EventPublisher`) publishes the event after the operation
- `trigger_conditions` JSONB specifies which field values activate the rule
- Matching automation rules evaluated by `AutomationService` asynchronously

#### Story 8.1.2 — Scheduled Triggers `[DONE]`
*As a tenant administrator, I want automation rules to run on a schedule, so that periodic tasks happen without manual intervention.*
- `trigger_type = "scheduled"`, `schedule_type` (`cron`/`interval`/`one_time`), `cron_expression`
- `SchedulerEngine` evaluates due jobs from `scheduler_jobs` table and executes them
- Job execution history stored in `scheduler_job_runs` with `status`, `started_at`, `completed_at`, `output`
- Scheduler config is hierarchical: system → tenant → company → branch

#### Story 8.1.3 — Automation Actions `[DONE]`
*As a tenant administrator, I want to define what happens when an automation rule fires, so that triggered actions match business needs without custom code.*
- Supported action types: `send_notification`, `update_field`, `create_record`, `call_webhook`, `run_workflow_transition`, `call_api`
- Actions configured as a JSONB array; multiple actions per rule executed in order
- Action failures logged and do not roll back the triggering event unless configured
- `max_retries` and `retry_delay_seconds` configurable per action

---

### Feature 8.2 — Webhook Outbound Integration `[PLANNED]`

#### Story 8.2.1 — Webhook Endpoint Registration `[PLANNED]`
*As a tenant administrator, I want to register external URLs as webhook recipients, so that external systems are notified of platform events.*
- `POST /webhooks` registers a webhook with `url`, `events` array, `secret`, and `is_active`
- Webhook URLs pass a validation challenge before activation
- Multiple webhooks per tenant/event combination supported
- Stored in `webhooks` table with per-tenant isolation

#### Story 8.2.2 — Webhook Delivery and Retry `[PLANNED]`
*As a tenant administrator, I want failed webhook deliveries retried automatically, so that transient network errors don't cause missed events.*
- Webhooks delivered asynchronously via the automation action system
- HTTP 2xx = success; any other response triggers retry with exponential backoff (1s, 5s, 30s, 5m, 30m, 1h)
- After all retries fail, the endpoint is auto-disabled and admin notified
- `GET /webhooks/{id}/deliveries` returns delivery attempt history with request/response bodies

#### Story 8.2.3 — Webhook Payload Signing `[PLANNED]`
*As a webhook recipient developer, I want payloads signed with HMAC-SHA256, so that I can verify events genuinely originate from the platform.*
- Every webhook POST includes `X-Signature: sha256=<hmac>` header using the webhook's configured secret
- Signing algorithm: HMAC-SHA256 over the raw request body
- `PUT /webhooks/{id}/rotate-secret` issues a new secret; both old and new signatures included during a 24-hour transition window

---

## EPIC 9 — Dashboard & Analytics

> Visual dashboard builder with KPI cards, charts, report tables, and live data from any published entity or module.

---

### Feature 9.1 — Dashboard Builder `[DONE]`

#### Story 9.1.1 — Dashboard Creation and Layout `[DONE]`
*As a tenant administrator, I want to create dashboards with a visual grid layout, so that I can design information screens tailored to each role.*
- `POST /dashboards` creates a dashboard with `name`, `layout_type` (`grid`/`freeform`/`responsive`), `theme`
- Dashboards support multiple pages; each page has an independent widget canvas
- Dashboard associated with `tenant_id` and optionally a `module_id`
- Dashboard designer at `#/dashboards/new` uses a 4-step wizard (metadata → pages → widgets → filters)

#### Story 9.1.2 — KPI Widget Configuration `[DONE]`
*As a dashboard designer, I want to add KPI cards that display a single aggregated metric, so that key business numbers are visible at a glance.*
- `WidgetType.KPI_CARD` config requires: `entity_name`, `metric_field`, `metric_function` (`sum`/`count`/`avg`), optional filters
- Widget displays value with configurable `label`, `prefix`, `suffix`, `decimal_places`
- Trend indicator shows delta vs. prior period when `compare_period` is configured
- Data fetched from the aggregate API (`GET /dynamic-data/{entity}/aggregate`)

#### Story 9.1.3 — Chart Widget Configuration `[DONE]`
*As a dashboard designer, I want to add bar, line, pie, and area charts, so that trends and distributions are visualized.*
- Supported chart types: `bar`, `line`, `pie`, `donut`, `area`, `scatter`, `gauge`, `funnel`, `heatmap`
- Config: `entity_name`, `x_axis_field`, `y_axis_metric`, `group_by`, optional `date_trunc`
- Charts support auto-refresh intervals: 30s, 1m, 5m, 15m, 30m, 1h, or none
- Chart data fetched from the aggregate API

#### Story 9.1.4 — Dashboard Sharing and Access Control `[DONE]`
*As a manager, I want to share dashboards with my team, so that everyone sees the same operational view.*
- Dashboard `visibility`: `private`, `tenant`, `company`, or `public`
- Dashboard owner can share with specific users or roles via an access list
- RBAC permission `dashboards:read:company` required to view; `dashboards:write:tenant` to create/edit
- Shared dashboards appear in recipient's list with a "shared" indicator

---

### Feature 9.2 — Dashboard Interactivity `[DONE]`

#### Story 9.2.1 — Global Filter Panel `[DONE]`
*As a dashboard viewer, I want to apply filters that cascade to all widgets, so that I can explore data without navigating individual widget settings.*
- `WidgetType.FILTER_PANEL` provides date range pickers and dimension selectors
- Filter changes broadcast a filter-change event; all data widgets re-fetch with the new filter applied
- Filter state persisted in the URL so filtered views can be bookmarked and shared
- Individual widgets can opt out of global filters

#### Story 9.2.2 — Widget Drill-Down `[DONE]`
*As a dashboard viewer, I want to click on a chart segment or KPI to see the underlying records, so that I can investigate anomalies without leaving the dashboard.*
- Clicking a chart element or KPI opens a drawer with the list of records matching that segment's filters
- Drill-down uses `list_records` with the same filters as the widget but without aggregation
- Drill-down list supports pagination, sorting, and search
- Deep-link from drill-down to the full entity record page is available

---

### Feature 9.3 — Materialized Views and Performance `[DONE]`

#### Story 9.3.1 — Materialized View Support `[DONE]`
*As a developer, I want dashboard widgets to query materialized views for pre-aggregated data, so that complex analytics are fast on large datasets.*
- `ProcedureService.refresh_materialized_view(view_name)` available for manual and scheduled refresh
- Virtual entities can point to materialized views (`entity_type = "virtual"`, `table_name = mv_name`)
- Dashboard widgets backed by materialized view virtual entities use the same API as regular entities
- Scheduler job type `data_sync` can be configured to refresh materialized views on a schedule

---

## EPIC 10 — Reporting

> Report designer for tabular, summary, cross-tab, and chart reports with parameterization, scheduling, and multi-format export.

---

### Feature 10.1 — Report Designer `[DONE]`

#### Story 10.1.1 — Report Definition Creation `[DONE]`
*As a tenant administrator, I want to design tabular reports by selecting an entity and fields, so that I can produce structured data outputs without SQL.*
- `POST /reports` creates a `ReportDefinition` with `report_type` (`tabular`/`summary`/`crosstab`/`metric`/`chart`), `entity_id`, and column config
- Column config supports `aggregation_type` (`sum`/`avg`/`count`/`min`/`max`/`none`) per column
- Report supports `filters`, `sort_by`, `group_by` configuration
- Report designer at `#/reports/new` uses a 6-step wizard (metadata → data source → query → columns → parameters → visualization)

#### Story 10.1.2 — Report Parameters `[DONE]`
*As a report user, I want to supply parameters when running a report, so that the same report definition produces different outputs based on my selections.*
- Parameter types: `string`, `integer`, `decimal`, `date`, `datetime`, `boolean`, `lookup`, `multi_select`
- Parameters defined with `name`, `label`, `type`, `default_value`, `is_required`
- `POST /reports/{id}/run` accepts parameter values and applies them to the report query
- Date parameters support relative values: `today`, `this_week`, `this_month`, `last_30_days`

#### Story 10.1.3 — Report Export `[DONE]`
*As a report user, I want to export report results to PDF, Excel, and CSV, so that I can share reports with stakeholders outside the platform.*
- `POST /reports/{id}/export?format=pdf` generates and returns a file download
- Supported formats: `pdf`, `excel_formatted`, `excel_raw`, `csv`, `json`, `html`
- PDF export preserves tenant branding (logo, colors) when configured
- Large reports (> 50,000 rows) use async export with a downloadable result link

---

### Feature 10.2 — Report Scheduling `[DONE]`

#### Story 10.2.1 — Scheduled Report Delivery `[DONE]`
*As a manager, I want reports generated and emailed to me on a schedule, so that I receive regular operational updates without manually running reports.*
- `POST /scheduler/jobs` with `job_type = "report_generation"` creates a scheduled report job
- Schedule supports cron expression, interval, or one-time execution
- Generated report queued for delivery via notification system (email subject to SMTP config)
- Failed report generation retried up to `max_retries` times; admin notified on persistent failure

#### Story 10.2.2 — Report Job History and Monitoring `[DONE]`
*As a tenant administrator, I want to see a history of scheduled report runs, so that I can diagnose delivery failures.*
- `GET /scheduler/jobs/{id}/runs` returns all execution attempts with `status`, `started_at`, `completed_at`, `output`, `error`
- Failed runs include the error message (truncated for security)
- Monitoring dashboard shows jobs by next-run time and recent status

---

## EPIC 11 — Module System

> Pluggable architecture for extending the platform with code-delivered (FastAPI microservice) and nocode (user-designed) modules.

---

### Feature 11.1 — Module Registry and Activation `[DONE]`

#### Story 11.1.1 — Module Registration `[DONE]`
*As a module developer, I want to register my module by posting a manifest, so that it becomes available for tenants to activate.*
- `POST /modules/register` accepts a `manifest.json` with `name`, `display_name`, `version`, `module_type`, `api_prefix`, `permissions`, `menu_items`, `routes`
- Registered module appears in the catalog with `status = "available"`
- Module registration is idempotent: re-registering the same `name` + `version` updates the existing record

#### Story 11.1.2 — Per-Tenant Module Activation `[DONE]`
*As a tenant administrator, I want to enable a registered module for my organization, so that my users gain access to its features.*
- `POST /modules/{id}/activate` with `tenant_id` creates a `ModuleActivation` record
- On activation, module menus injected into the core menu tree; routes added to the hash-based router
- Module permissions available for assignment in the RBAC system
- `company.created` event triggers module-specific initialization hooks defined in the manifest

#### Story 11.1.3 — Module Dependency Management `[DONE]`
*As a module developer, I want to declare dependencies on other modules, so that activation is blocked if dependencies are missing.*
- `ModuleDependency` records `module_id`, `depends_on_module_id`, `version_constraint` (semver range)
- Activation with unmet dependencies returns 409 with list of missing/incompatible dependencies
- Deactivating a module with active dependents is blocked unless `force=true`

---

### Feature 11.2 — Module Marketplace UI `[PLANNED]`

#### Story 11.2.1 — Module Catalog Browse `[PLANNED]`
*As a tenant administrator, I want to browse available modules in a marketplace interface, so that I can discover and evaluate modules before enabling them.*
- Module marketplace page at `#/modules/marketplace` lists all available modules
- Filter by `category`, `module_type`, `is_installed`; search by name/description
- Each module card shows: icon, name, description, version, author, category, activation status
- Module detail modal shows full description, permissions required, and dependencies

#### Story 11.2.2 — One-Click Module Activation from Marketplace `[PLANNED]`
*As a tenant administrator, I want to activate a module directly from the marketplace UI, so that I do not need to use the API.*
- "Activate" button calls `POST /modules/{id}/activate` for the current tenant
- Activation progress shown with a spinner; success/failure displayed inline
- After activation, module menu items appear in navigation without a page reload
- Required permissions prompt shown before activation if new permissions need to be assigned

---

### Feature 11.3 — NoCode Module Builder `[DONE]`

#### Story 11.3.1 — User-Designed Module Creation `[DONE]`
*As a tenant administrator, I want to package entities, workflows, and dashboards into a named module, so that it can be reused across companies within my tenant.*
- `POST /nocode-modules` creates a `Module` record with `module_type = "nocode"` and a unique `table_prefix`
- Module designer UI at `#/nocode/modules` lists nocode modules with status and entity count
- Entities, workflows, automations, and dashboards can be associated with a module via `module_id`
- Publishing a nocode module makes it available for activation in other companies

#### Story 11.3.2 — Module Template Export and Import `[DONE]`
*As a platform superadmin, I want to export a module as a template package and import it to other tenants, so that best-practice configurations are distributed without manual setup.*
- `POST /nocode-modules/{id}/export` generates a ZIP of entity definitions, field definitions, workflows, and dashboard configs
- `POST /nocode-modules/import` accepts a ZIP and creates the module under the target tenant
- Import is idempotent: re-running the same package updates existing definitions rather than creating duplicates
- Import logs a summary of created/updated/skipped items

---

## EPIC 12 — Financial Module

> Production-ready double-entry bookkeeping: Chart of Accounts, customers, invoicing with workflow, payments, journal entries, tax management, and six standard financial reports.

---

### Feature 12.1 — Chart of Accounts `[DONE]`

#### Story 12.1.1 — Hierarchical Account Structure `[DONE]`
*As a finance manager, I want to set up a hierarchical Chart of Accounts, so that my organization's finances are organized according to accounting principles.*
- `POST /financial/accounts` creates an account with `code`, `name`, `account_type` (`asset`/`liability`/`equity`/`revenue`/`expense`), `parent_account_id`
- Account tree is unlimited in depth; each node inherits the type from its root
- `POST /financial/accounts/setup/default` seeds a 50-account standard chart template
- `GET /financial/accounts/hierarchy` returns the full tree structure

#### Story 12.1.2 — Account Balance Tracking `[DONE]`
*As an accountant, I want to see the current balance of any account at any point in time, so that I can verify financial positions without running a full report.*
- `GET /financial/accounts/{id}/balance?as_of=2025-12-31` returns debit/credit balance as of the given date
- Balance computed from posted journal entries only (draft and voided entries excluded)
- Normal balance direction respected per account type (debit normal vs. credit normal)

---

### Feature 12.2 — Invoicing with Workflow `[DONE]`

#### Story 12.2.1 — Invoice Creation and Posting `[DONE]`
*As a billing administrator, I want to create invoices, add line items, and post them to the general ledger, so that revenue is recognized in accounting.*
- `POST /financial/invoices` creates an invoice in `DRAFT` status with `customer_id`, `invoice_date`, `due_date`, `line_items`, `tax_rate_id`
- `POST /financial/invoices/{id}/post` transitions to `POSTED` and auto-generates double-entry journal entries
- Invoice number auto-generated with configurable prefix and sequence per company
- Line items include `description`, `quantity`, `unit_price`, `account_id`, `tax_amount`

#### Story 12.2.2 — Invoice Workflow States `[DONE]`
*As a finance manager, I want invoices to move through defined states, so that the status of all receivables is always clear.*
- Lifecycle: `DRAFT → POSTED → PARTIALLY_PAID → PAID → VOID`
- `POST /financial/invoices/{id}/void` voids an invoice and creates reversal journal entries
- Status transitions enforced: a draft invoice cannot be directly voided
- Voided invoices retained for audit with `voided_at` timestamp and `void_reason`

#### Story 12.2.3 — Payment Recording and Allocation `[DONE]`
*As an accountant, I want to record customer payments and allocate them against invoices, so that outstanding balances are accurately tracked.*
- `POST /financial/payments` records a payment with `customer_id`, `amount`, `payment_date`, `payment_method`, `reference`
- `POST /financial/payments/{id}/allocate` allocates payment amounts against invoices
- Partial allocation → invoice status `PARTIALLY_PAID`; full allocation → `PAID`
- `GET /financial/payments/unallocated` returns payments with unallocated balance > 0

---

### Feature 12.3 — Double-Entry Journal Entries `[DONE]`

#### Story 12.3.1 — Manual Journal Entry Posting `[DONE]`
*As an accountant, I want to post manual journal entries with balanced debits and credits, so that adjusting entries and corrections can be made.*
- `POST /financial/journal-entries` creates a journal with `date`, `description`, `reference`, `line_items`
- `POST /financial/journal-entries/{id}/post` validates balance (total debits = total credits) before posting
- Unbalanced entries return 400 with `UNBALANCED_JOURNAL_ENTRY`
- `POST /financial/journal-entries/{id}/reverse` creates a reversal entry with negated amounts

---

### Feature 12.4 — Financial Reports `[DONE]`

#### Story 12.4.1 — Standard Financial Report Suite `[DONE]`
*As a CFO, I want to generate standard financial reports on demand, so that the organization's financial health can be assessed quickly.*
- `GET /financial/reports/trial-balance?as_of=2025-12-31` — all accounts with debit/credit totals
- `GET /financial/reports/balance-sheet?as_of=2025-12-31` — assets, liabilities, equity
- `GET /financial/reports/income-statement?from=2025-01-01&to=2025-12-31` — revenues and expenses
- `GET /financial/reports/aged-receivables?as_of=2025-12-31` — outstanding invoices by aging bucket (0-30, 31-60, 61-90, 90+ days)
- `GET /financial/reports/cash-flow?from=...&to=...` — operating/investing/financing activities
- `GET /financial/reports/account-ledger/{id}?from=...&to=...` — all transactions for a specific account

#### Story 12.4.2 — Tax Rate Management `[DONE]`
*As a finance administrator, I want to configure multiple tax rates for different jurisdictions, so that invoices apply correct tax calculations automatically.*
- `POST /financial/tax-rates` creates a tax rate with `name`, `rate` (percentage), `account_id`, `is_compound`
- `POST /financial/tax-rates/calculate` returns the tax amount for a given `subtotal` and `tax_rate_id`
- Multiple tax rates can be applied to a single invoice line item
- Archived tax rates cannot be applied to new invoices but remain visible on historical invoices

---

### Feature 12.5 — Financial Module Planned Enhancements `[PLANNED]`

#### Story 12.5.1 — Vendor Management and Accounts Payable `[PLANNED]`
*As an accountant, I want to manage vendor records and track bills, so that the platform covers the full payables cycle.*
- Vendor model with `name`, `code`, `tax_id`, `payment_terms`, `default_expense_account_id`
- `POST /financial/bills` creates an AP bill with workflow mirroring the invoice module
- `GET /financial/reports/aged-payables` — outstanding bills grouped by aging bucket
- AP journal entries use the accounts payable liability account automatically

#### Story 12.5.2 — Bank Reconciliation `[PLANNED]`
*As an accountant, I want to reconcile bank statement transactions against GL entries, so that accounting records match actual bank activity.*
- `POST /financial/bank-accounts` registers a bank account mapped to a GL cash account
- Bank statement CSV import maps transactions to the reconciliation workspace
- Matched transactions flagged; unmatched items require manual assignment to GL entries
- Reconciliation report shows matched, unmatched, and outstanding items

#### Story 12.5.3 — Budget Management `[PLANNED]`
*As a department manager, I want to define budgets by account and period, so that actual vs. budget variance reports are available.*
- `POST /financial/budgets` creates a budget per `fiscal_year`, `company_id`, with line items per `account_id` and `period`
- `GET /financial/reports/budget-variance?year=2025` compares actuals to budget by period and account
- Budget approval workflow: draft → submitted → approved
- Budget figures editable only before the period start date (or by finance admin override)

---

## EPIC 13 — Security & Compliance

> Platform-level and per-tenant security hardening: audit logging, sensitive operation re-authentication, security headers, rate limiting, and compliance controls.

---

### Feature 13.1 — Audit Logging `[DONE]`

#### Story 13.1.1 — Comprehensive Audit Trail `[DONE]`
*As a compliance officer, I want every significant action recorded in an audit log with actor, timestamp, and before/after values, so that I can reconstruct what happened and demonstrate regulatory compliance.*
- All authentication events, RBAC changes, and data operations are logged
- Each entry includes: `event_type`, `actor_user_id`, `tenant_id`, `resource_type`, `resource_id`, `action`, `changes` (before/after JSON diff), `ip_address`, `user_agent`, `timestamp`
- Audit logs are append-only; no UPDATE or DELETE permitted on `audit_logs` by application code
- `GET /audit?event_type=...&actor_id=...&from=...&to=...` supports filtered queries

#### Story 13.1.2 — Entity-Level Audit Logging `[DONE]`
*As a tenant administrator, I want all writes to entities with `is_audited = true` to appear in the audit log, so that custom data changes are traceable.*
- `create_record`, `update_record`, and `delete_record` on audited entities write to `audit_logs`
- Update entries include a JSON diff of changed fields only (not the entire record)
- Audit entries reference `entity_name` and `record_id` so the specific record can be located
- Audit log viewer in the UI shows human-readable summaries of audit entries

---

### Feature 13.2 — Security Policies `[DONE]`

#### Story 13.2.1 — Per-Tenant Security Policy Configuration `[DONE]`
*As a tenant administrator, I want to set security policies specific to my organization, so that I can meet my compliance requirements without affecting other tenants.*
- `SecurityPolicy` records are per-tenant; superadmin manages the platform default policy
- Tenant policy overrides platform defaults; if no tenant policy exists, platform defaults apply
- `PUT /admin/security/policies/{tenant_id}` allows superadmin to update any tenant's policy
- Policy changes take effect on the next login attempt; existing sessions are not immediately affected

#### Story 13.2.2 — Sensitive Operation Re-Authentication `[DONE]`
*As a security administrator, I want users to re-enter their password before performing sensitive operations, so that session hijacking cannot cause irreversible damage.*
- Sensitive operations tagged in the backend with a `require_reauth` flag
- If the current token was issued more than `reauth_window_minutes` ago, API returns 403 with `REAUTH_REQUIRED`
- Frontend prompts for password confirmation; on success, issues a short-lived `reauth_token` for one operation
- Re-authentication events are audit-logged

#### Story 13.2.3 — Security Headers Middleware `[DONE]`
*As a security engineer, I want standard security headers on all responses, so that common browser-based attacks (XSS, clickjacking, MIME sniffing) are mitigated.*
- `SecurityMiddleware` adds: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Strict-Transport-Security`, `Referrer-Policy`
- CSP allows only same-origin scripts and styles plus explicitly configured external sources (Tailwind CDN, Phosphor icons)

#### Story 13.2.4 — Rate Limiting `[DONE]`
*As a platform operator, I want API rate limiting enforced per IP, so that abuse and brute-force attacks are slowed.*
- SlowAPI-based per-IP rate limiting: login endpoints 10 req/min; general API 100 req/min
- Rate limit responses return HTTP 429 with `Retry-After` header
- Rate limits configurable via `RATE_LIMIT_PER_MINUTE` environment variable

---

### Feature 13.3 — Prometheus Metrics `[PLANNED]`

#### Story 13.3.1 — Prometheus `/metrics` Endpoint `[PLANNED]`
*As a DevOps engineer, I want a Prometheus-compatible `/metrics` endpoint, so that platform health can be monitored with standard observability tooling.*
- `prometheus-client` (already in `requirements.txt`) wired up and mounted at `/metrics`
- Core metrics: `http_requests_total` (by method, path, status), `http_request_duration_seconds`, `db_pool_size`, `active_sessions_total`, `notification_queue_length`
- `/metrics` protected: accessible only from whitelisted IPs or with a bearer token
- A Prometheus scrape service added to `infra/docker-compose.dev.yml`

#### Story 13.3.2 — Grafana Dashboard Template `[PLANNED]`
*As a DevOps engineer, I want a pre-built Grafana dashboard, so that I can visualize health metrics without building dashboards from scratch.*
- `infra/grafana/` contains a Grafana dashboard JSON provisioning file
- Dashboard panels include: request rate, error rate, p50/p95/p99 latency, active sessions, DB pool utilization
- Grafana service added to `infra/docker-compose.dev.yml` alongside Prometheus
- Dashboard auto-provisions on first Grafana start via the provisioning directory

---

### Feature 13.4 — Test Coverage `[IN-PROGRESS]`

#### Story 13.4.1 — Backend Unit and Integration Test Suite `[IN-PROGRESS]`
*As a developer, I want comprehensive backend tests covering authentication, RBAC, dynamic entity CRUD, and the financial module, so that regressions are caught before production.*
- Backend `tests/` targets 80% line coverage using `pytest` and `pytest-asyncio`
- Unit tests cover: `DynamicQueryBuilder`, `PasswordValidator`, `AutomationService`, `WorkflowService`, `ReportService`
- Integration tests cover: full auth flow, RBAC permission evaluation, dynamic entity lifecycle, financial invoice cycle
- Tests run in CI on every push to `main` and `develop` branches

#### Story 13.4.2 — Frontend Component Test Coverage `[IN-PROGRESS]`
*As a frontend developer, I want Vitest tests for all Flex components, so that UI regressions are caught during development.*
- Currently tested: `FlexAccordion`, `FlexCheckbox`, `FlexInput`, `FlexRadio`, `BaseComponent`
- New tests needed for: layout components (FlexStack, FlexGrid, FlexSidebar), UI components (FlexModal, FlexTable, FlexDataGrid), form components (FlexSelect, FlexTextarea)
- Vitest coverage thresholds (80% statements/functions/lines, 75% branches) enforced in CI

---

## EPIC 14 — Notification System

> Queue-based notification delivery for system events via email, SMS, webhook, and in-app channels.

---

### Feature 14.1 — Notification Queue `[DONE]`

#### Story 14.1.1 — Notification Queuing Architecture `[DONE]`
*As a developer, I want all notification sends queued asynchronously, so that authentication and data operations are not slowed by delivery latency.*
- `NotificationService.queue_notification()` creates a `NotificationQueue` record with `status=pending`
- Queue supports `priority` (1–10), `scheduled_for`, `max_attempts`, `delivery_method`
- Background worker polls the queue, attempts delivery, and updates `status` to `sent`, `failed`, or `retrying`
- Failed deliveries retried up to `max_attempts` with exponential backoff

#### Story 14.1.2 — Notification Configuration per Tenant `[DONE]`
*As a tenant administrator, I want to configure which notification types are enabled and by which method, so that users receive relevant communications through their preferred channel.*
- `NotificationConfig` has per-type enable/disable toggles and `methods` array for each type
- Supported types: `account_locked`, `password_expiring`, `password_changed`, `password_reset`, `login_from_new_device`
- `tenant_id = NULL` in `NotificationConfig` represents the platform default; tenant config overrides it

---

### Feature 14.2 — Email Delivery `[OPEN]`

#### Story 14.2.1 — SMTP Email Delivery Adapter `[OPEN]`
*As a tenant administrator, I want email notifications actually sent, so that users receive password reset links, lockout alerts, and workflow notifications.*
- `NotificationConfig` SMTP settings (`smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `email_from`) used by the delivery worker
- Delivery worker implements actual SMTP send using `aiosmtplib`
- `POST /settings/notifications/test-email` sends a test email to verify SMTP config
- Delivery errors (connection refused, auth failure) caught, logged, and queue entry marked for retry

#### Story 14.2.2 — Email Template System `[OPEN]`
*As a tenant administrator, I want branded email templates for each notification type, so that emails reflect our organization's visual identity.*
- Default HTML templates exist for: `account_locked`, `password_expiring`, `password_reset`, `welcome_user`, `workflow_approval_request`
- Templates support variables: `{{user_name}}`, `{{tenant_name}}`, `{{action_url}}`, `{{expiry_date}}`
- Tenant admin can customize subject line and body via the settings UI
- Fallback to plain-text templates if HTML rendering fails

---

### Feature 14.3 — SMS and Push Delivery `[PLANNED]`

#### Story 14.3.1 — SMS Delivery via Provider `[PLANNED]`
*As a tenant administrator, I want to deliver OTPs and alerts via SMS, so that users with phone-based 2FA and mobile-first workflows are supported.*
- `NotificationConfig` SMS settings support Twilio as initial provider
- SMS delivery worker calls the provider API for each queued SMS notification
- SMS length limits (160 chars) handled; longer messages split or truncated
- `POST /settings/notifications/test-sms` sends a test SMS to the admin's registered phone

#### Story 14.3.2 — In-App Notification Center `[PLANNED]`
*As a user, I want to see a list of in-app notifications (approvals, alerts, reminders) in the navigation bar, so that I don't miss important events while working.*
- Notification bell icon in the top nav shows an unread count badge
- Clicking opens a dropdown listing the 10 most recent notifications with timestamp and action link
- `GET /notifications/me?unread=true` returns unread notifications for the current user
- `POST /notifications/{id}/read` marks a notification as read; `POST /notifications/read-all` clears the unread count

---

## EPIC 15 — Flex Component Library

> Zero-dependency vanilla JS Web Components library forming the UI foundation for all platform pages and module frontends.

---

### Feature 15.1 — Layout Components `[DONE]`

#### Story 15.1.1 — Layout Component Suite `[DONE]`
*As a frontend developer, I want layout primitives that compose into complex page structures, so that page layouts are built declaratively without custom CSS.*
- All 9 layout components implemented: `FlexStack`, `FlexGrid`, `FlexContainer`, `FlexSection`, `FlexSidebar`, `FlexCluster`, `FlexToolbar`, `FlexMasonry`, `FlexSplitPane`
- Components use CSS custom properties for spacing, sizing, and breakpoint behavior
- `FlexResponsive` singleton provides breakpoint detection; layout components react to breakpoint changes
- Semantic HTML and ARIA roles used throughout

#### Story 15.1.2 — UI Component Suite `[DONE]`
*As a frontend developer, I want UI primitives ready to use, so that interactive page elements are consistent across the platform.*
- All 16 UI components implemented: `FlexCard`, `FlexModal`, `FlexTabs`, `FlexDataGrid`, `FlexTable`, `FlexBadge`, `FlexStepper`, `FlexAlert`, `FlexButton`, `FlexDrawer`, `FlexDropdown`, `FlexSpinner`, `FlexAccordion`, `FlexBreadcrumb`, `FlexTooltip`, `FlexPagination`
- `FlexModal` and `FlexDrawer` trap focus correctly (WCAG 2.1 §2.4.3)
- `FlexTable` emits `bulkAction` event with selected rows when checkbox selection is used
- Full bundle ~38 KB gzipped

#### Story 15.1.3 — Form Component Suite `[DONE]`
*As a frontend developer, I want standard form input components that validate and emit change events consistently, so that forms are built with uniform UX patterns.*
- All 5 form components implemented: `FlexInput`, `FlexSelect`, `FlexCheckbox`, `FlexRadio`, `FlexTextarea`
- Each component supports `name`, `value`, `disabled`, `required`, `error` attributes
- `change` event emitted with `{name, value}` payload on every value change
- Error state sets `aria-invalid="true"` and renders an inline error message

---

### Feature 15.2 — Planned Components `[PLANNED]`

#### Story 15.2.1 — FlexDatepicker Component `[PLANNED]`
*As a form builder, I want a date/datetime picker component, so that users can select dates through a calendar UI rather than typing ISO strings.*
- `<flex-datepicker>` supports `type` attribute: `date` or `datetime`
- Calendar popup opens on input focus; `value` always in ISO 8601 format
- Keyboard navigation: arrow keys move day selection, Enter confirms, Escape closes
- `min` and `max` attributes disable out-of-range dates

#### Story 15.2.2 — FlexFileUpload Component `[PLANNED]`
*As a form builder, I want a file upload component with drag-and-drop and preview, so that entity records can have file attachments.*
- `<flex-file-upload>` supports drag-and-drop and click-to-browse
- `accept` attribute restricts file types; `max-size` attribute rejects oversized files before upload
- Preview thumbnails shown for image files; file icon + name for other types
- Multiple file upload supported when `multiple` attribute is set

#### Story 15.2.3 — FlexForm Component `[PLANNED]`
*As a frontend developer, I want a form container that orchestrates validation across all child inputs, so that form submission and error display are handled consistently.*
- `<flex-form>` wraps any combination of Flex form components
- `form.validate()` returns an array of `{field, message}` errors from all child components
- `form.showFieldErrors(errors)` maps API validation errors to matching child components
- `submit` event emitted only if `validate()` returns no errors

#### Story 15.2.4 — FlexNotification Component `[PLANNED]`
*As a frontend developer, I want a toast notification component, so that success, error, warning, and info messages are shown with consistent styling.*
- `<flex-notification>` renders toast messages in a configurable screen position
- `type` attribute: `success`, `error`, `warning`, `info`
- Auto-dismiss after `duration` ms (default 5000); persistent notifications have `dismissible` attribute
- Maximum 5 concurrent notifications; oldest dismissed when limit is reached
- Uses `role="alert"` with `aria-live="polite"` or `"assertive"` based on type

#### Story 15.2.5 — FlexProgress Component `[PLANNED]`
*As a frontend developer, I want a progress bar and circular progress indicator, so that long-running operations have visual feedback.*
- `<flex-progress>` supports `type` attribute: `bar` or `circular`
- `value` (0–100) and `indeterminate` attribute shows animation without a known value
- `label` attribute shows a text description below the bar
- Color controlled by CSS custom properties, inheriting from tenant theme

---

### Feature 15.3 — Developer Experience for the Library `[PLANNED]`

#### Story 15.3.1 — TypeScript Definitions `[PLANNED]`
*As a TypeScript developer consuming the Flex library, I want `.d.ts` type declaration files, so that I get autocomplete and type checking when using components.*
- Each component has a corresponding `.d.ts` file exported from the package
- Types cover: constructor options, public methods, event payload shapes, attribute names
- Type definitions pass `tsc --strict --noEmit` without errors

#### Story 15.3.2 — Storybook Component Explorer `[PLANNED]`
*As a designer or developer, I want an interactive Storybook explorer, so that I can browse and test component variations without running the full platform.*
- Storybook configured in repo with `npm run storybook` command
- Every implemented component has at least one Story showing its default state
- A11y addon configured to run accessibility checks on each Story automatically

---

## EPIC 16 — Internationalization (i18n)

> Full multi-language support using i18next with lazy-loaded namespace JSON files and runtime language switching.

---

### Feature 16.1 — Multi-Language Support `[DONE]`

#### Story 16.1.1 — Language Loading and Runtime Switching `[DONE]`
*As a user, I want to switch the application language from the settings page, so that I can use the platform in my preferred language.*
- Supported languages: `en`, `de`, `es`, `fr`, `id`
- Language persisted to `localStorage` and applied on next page load
- `i18next.changeLanguage(lang)` reloads all UI strings dynamically without a full page refresh
- Language files loaded lazily per namespace (`common.json`, `pages.json`, `menu.json`)

#### Story 16.1.2 — Translation Namespace Coverage `[DONE]`
*As a translator, I want all user-visible strings organized in namespace JSON files, so that I can add or update translations without modifying JavaScript source code.*
- `common.json` covers: all UI action labels (Save, Cancel, Delete, Confirm, Loading, etc.)
- `pages.json` covers: all page-specific labels and form field labels
- `menu.json` covers: all navigation menu item labels
- Missing translation keys fall back to `en` (i18next fallback language configured)

#### Story 16.1.3 — Adding a New Language `[DONE]`
*As a developer, I want a documented process for adding a new language, so that expanding language support is straightforward.*
- Create `frontend/assets/i18n/<code>/` with the three namespace files
- Add the code to `supportedLngs` in `i18n.js` and to the language dropdown in `settings.js`
- A translation completeness check script identifies untranslated keys

---

### Feature 16.2 — Module and Dynamic Content i18n `[PLANNED]`

#### Story 16.2.1 — Module i18n Namespace Registration `[PLANNED]`
*As a module developer, I want to register my module's i18n namespace with the platform, so that module UI strings are translated consistently.*
- Module manifest includes an `i18n` section with `namespace` name and `locales_path`
- On module activation, the platform loads the module's locale files from its frontend directory
- Module translates labels using `t('module_name:key')` pattern
- Missing module translations fall back to English without errors

#### Story 16.2.2 — Entity and Field Label i18n `[PLANNED]`
*As a tenant administrator designing a multi-language deployment, I want entity and field labels to be translatable, so that the custom data model is fully localized.*
- `EntityDefinition` and `FieldDefinition` support a `label_i18n` JSONB field: `{"en": "Invoice", "de": "Rechnung"}`
- Metadata API returns the localized label based on `Accept-Language` header or user language preference
- Entity designer UI allows entering labels for each configured language
- Falls back to the base `label` field if a translation for the current language is not defined

---

## EPIC 17 — Settings & Configuration

> User-level preferences (theme, language, timezone) and system-level settings (security policies, notification configs) with a layered override model.

---

### Feature 17.1 — User Settings `[DONE]`

#### Story 17.1.1 — User Preferences `[DONE]`
*As a user, I want to set my preferred theme, language, timezone, and display density, so that the platform fits my personal workflow.*
- `UserSettings` stores: `theme` (`light`/`dark`), `language`, `timezone`, `density` (`compact`/`normal`/`comfortable`)
- Settings page at `#/settings` provides a UI for each preference
- Changes saved to `user_settings` table and applied immediately without re-login
- Custom `preferences` JSON field allows extensible storage for feature-specific user settings

#### Story 17.1.2 — Dark/Light Theme Switching `[DONE]`
*As a user, I want to switch between light and dark mode, so that I can use the platform comfortably in different lighting conditions.*
- `theme-manager.js` applies the theme by toggling a class on `<html>` or updating CSS custom properties
- Theme persists across page reloads via `UserSettings.theme`
- All Flex components and page styles respect the active theme
- System preference (`prefers-color-scheme`) used as the default on first visit

---

### Feature 17.2 — Tenant and System Settings `[DONE]`

#### Story 17.2.1 — Tenant Branding Configuration `[DONE]`
*As a tenant administrator, I want to set my company's name, logo, and brand colors, so that users experience a consistent brand identity.*
- `TenantSettings.primary_color`, `secondary_color`, `logo_url`, `tenant_name` applied at the application level
- CSS custom property tokens updated from `theme_config` JSON on page load
- Logo appears in the navigation sidebar replacing the default platform logo
- Branding changes visible to all tenant users without them needing to refresh

#### Story 17.2.2 — System Configuration (Superadmin) `[DONE]`
*As a superadmin, I want to manage platform-level settings, so that defaults apply to all tenants unless overridden.*
- Platform default security policy managed via `PUT /admin/security/policies/default`
- Default notification config (`tenant_id = NULL`) applies to tenants without their own config
- Platform-level feature flags gate experimental features for all tenants

#### Story 17.2.3 — Menu Management `[DONE]`
*As a tenant administrator, I want to customize the navigation menu items, so that my users see only the relevant sections for their work.*
- Menu management UI at `#/settings/menu-management` allows CRUD on menu items
- Drag-drop hierarchy ordering for parent-child menu relationships
- Icon selection with color customization per menu item
- Menu changes apply to all users within the tenant immediately

---

### Feature 17.3 — White-Label Theming `[PLANNED]`

#### Story 17.3.1 — CSS Custom Property Token System `[PLANNED]`
*As a platform operator, I want a comprehensive CSS token system, so that visual customization is applied uniformly across all components.*
- All Flex components use CSS custom properties for color, spacing, typography, border-radius, and shadow
- Token naming follows a semantic pattern: `--flex-color-primary`, `--flex-spacing-md`, `--flex-radius-base`
- Token values set at `:root` and overrideable per-tenant via `theme_config` JSON in `TenantSettings`
- A token reference guide published in the component documentation

#### Story 17.3.2 — Full White-Label Branding `[PLANNED]`
*As an enterprise tenant, I want to fully replace the platform's brand with my own, so that end-users see only our brand.*
- `TenantSettings` supports `custom_app_name`, `favicon_url`, `login_background_url`, `login_logo_url`
- Login page reads these settings before rendering
- Browser tab title uses `custom_app_name`
- All platform vendor name references in the UI replaced dynamically

---

## EPIC 18 — Developer Experience & Module SDK

> Tools, conventions, and documentation enabling third-party developers to build and distribute modules on the platform.

---

### Feature 18.1 — Module Development SDK `[DONE / PARTIAL]`

#### Story 18.1.1 — Module Manifest Specification `[DONE]`
*As a module developer, I want a clear manifest format to declare my module's identity, permissions, and integration points, so that my module integrates cleanly.*
- `manifest.json` schema documented: `name`, `display_name`, `version`, `module_type`, `category`, `api_prefix`, `permissions[]`, `menu_items[]`, `routes[]`, `event_subscriptions[]`, `dependencies[]`
- Manifest validation on `POST /modules/register` returns structured errors for schema violations
- Versioning follows semver; `major_version` bump requires superadmin approval for existing activations

#### Story 18.1.2 — Base Module Class `[DONE]`
*As a module developer, I want a `BaseModule` class to subclass, so that authentication, RBAC, and event bus integration are inherited automatically.*
- `BaseModule` provides: JWT auth dependency injection, permission checking helper, event publisher access, tenant context extraction
- Module developer subclasses `BaseModule` and overrides `get_router()` to return their FastAPI router
- `BaseModule` handles tenant isolation for DB queries automatically

#### Story 18.1.3 — Event Bus Integration for Modules `[DONE]`
*As a module developer, I want to subscribe to platform events and publish my own events, so that my module reacts to platform changes.*
- `EventPublisher.publish(event_type, payload, tenant_id)` available from the base module
- Event subscription declared in `manifest.json` under `event_subscriptions`
- `EventSubscriber` polls for new events by type and delivers them to the module's handler
- Financial module demonstrates the pattern: publishes `financial.invoice.created` and consumes `tenant.created`

---

### Feature 18.2 — API Documentation and Developer Tooling `[DONE / PLANNED]`

#### Story 18.2.1 — Swagger/OpenAPI Interactive Documentation `[DONE]`
*As a developer, I want interactive API documentation at `/docs`, so that I can explore and test endpoints without writing code.*
- FastAPI auto-generates OpenAPI 3.0 spec for all routes
- Swagger UI at `/docs`; Redoc at `/redoc`
- All routes have `summary`, `tags`, and response model annotations
- Authentication can be tested via the "Authorize" button in Swagger UI

#### Story 18.2.2 — API Reference Documentation `[DONE]`
*As a developer integrating with the platform, I want a human-readable API reference, so that I understand all endpoints, parameters, and response shapes.*
- `docs/backend/API_REFERENCE.md` documents all router groups with example requests and responses
- Response envelope shape documented: `{items, total, page, page_size, pages}`
- A note states that Swagger UI at `/api/docs` is always the authoritative source

#### Story 18.2.3 — Module Development Guide `[PLANNED]`
*As a third-party developer, I want a step-by-step guide to building, testing, and publishing a module, so that I can extend the platform without understanding its full internals.*
- Guide covers: directory structure, manifest format, `BaseModule` subclassing, Alembic migrations, frontend page integration, event bus usage, testing
- A minimal "Hello World" module provided as a starter template in `modules/example/`
- Guide documents how to run the module locally alongside the core platform using a Docker Compose override file
- Guide covers module versioning, upgrade path, and backward-compatible API changes

#### Story 18.2.4 — Seed and Example Data Scripts `[DONE]`
*As a developer, I want seed scripts that populate a realistic dataset, so that I can develop against representative data without manual setup.*
- 30+ seed files in `backend/app/seeds/` covering: admin users, tenants, companies, roles, permissions, entity templates
- `make seed` command runs all seeds in correct dependency order
- Financial module seed creates a default chart of accounts for each seeded company
- Seed scripts are idempotent: re-running does not create duplicates

---

## EPIC 19 — Infrastructure & Deployment

> Docker-based containerization, Nginx reverse proxy, database migrations, CI/CD pipeline, cloud storage, and production hardening.

---

### Feature 19.1 — Docker and Container Setup `[DONE / OPEN]`

#### Story 19.1.1 — Development Docker Compose `[DONE]`
*As a developer, I want a single `docker-compose up` command to start the complete development environment, so that onboarding takes minutes.*
- `docker-compose.yml` starts: `postgres`, `redis`, `backend`, `financial-module`, `frontend`, `nginx`
- All services have health checks configured
- Volume mounts enable hot-reload for backend and frontend
- `make docker-up` is the documented command; `make docker-logs` tails all service logs

#### Story 19.1.2 — Production Docker Compose `[OPEN]`
*As a DevOps engineer, I want a production-ready Docker Compose file, so that I can deploy to a server with minimal manual configuration.*
- `infra/docker-compose.prod.yml` uses tagged image references from the container registry
- No bind-mount volumes; data stored in named volumes
- Health check dependencies configured (backend waits for postgres and redis to be healthy)
- Environment variable file (`--env-file .env.prod`) configured

#### Story 19.1.3 — Nginx Routing Configuration `[DONE]`
*As a DevOps engineer, I want Nginx to correctly route requests to the appropriate backend service, so that the single-origin frontend can reach all APIs.*
- `/api/v1/financial/*` proxied to `financial-module:9001`
- `/api/` proxied to `backend:8000`
- `/modules/<name>/<file>` serves module frontend static assets
- `/*` falls back to `index.html` for SPA hash routing
- Gzip compression enabled for JS, CSS, and JSON responses

---

### Feature 19.2 — Database Migrations `[DONE]`

#### Story 19.2.1 — Alembic Migration Management `[DONE]`
*As a developer, I want Alembic to manage all schema changes, so that database upgrades are reproducible and reversible.*
- `alembic upgrade head` applies all pending migrations; `alembic downgrade -1` reverts one
- Migrations run automatically at application startup (lifespan handler in `main.py`)
- Migration files committed to git and reviewed like application code
- 70+ migration files in `versions/postgresql/` covering all platform tables

#### Story 19.2.2 — Module-Specific Alembic Setup `[DONE]`
*As a module developer, I want my module to have its own Alembic environment, so that module schema changes are managed independently.*
- Each code module has a `backend/alembic/` directory with its own `env.py` and `alembic.ini`
- `docker-compose exec financial-module alembic upgrade head` documented for module migrations
- Module migrations can reference core tables with `op.create_foreign_key()` targeting the shared DB

---

### Feature 19.3 — Cloud Storage Integration `[PLANNED]`

#### Story 19.3.1 — S3-Compatible File Storage `[PLANNED]`
*As a platform administrator, I want file attachments stored in S3-compatible object storage, so that the database is not burdened with binary data.*
- A `StorageService` abstracts file upload/download operations over S3-compatible APIs (AWS S3, MinIO, GCS)
- Config via `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `PUT /files/upload-url` generates a presigned URL for client-side direct upload
- `GET /files/{key}` generates a presigned download URL valid for a configurable TTL

#### Story 19.3.2 — Entity Record Attachments API `[PLANNED]`
*As a developer, I want a standard API for attaching files to any entity record, so that the `supports_attachments` flag on `EntityDefinition` is fully functional.*
- `POST /dynamic-data/{entity}/records/{id}/attachments` accepts a file key and creates an attachment metadata record
- `GET /dynamic-data/{entity}/records/{id}/attachments` returns all attachments for a record
- `DELETE /dynamic-data/{entity}/records/{id}/attachments/{attachment_id}` removes the attachment
- `FlexFileUpload` component uses the presigned URL for upload and stores the resulting file key

---

### Feature 19.4 — CI/CD Pipeline `[PLANNED]`

#### Story 19.4.1 — GitHub Actions CI Pipeline `[PLANNED]`
*As a developer, I want automated CI checks on every pull request, so that code quality and test coverage are enforced before merging.*
- `.github/workflows/ci.yml` runs on every PR to `main` and `develop`
- Jobs: Python lint (`ruff`), backend tests (`pytest`), frontend lint, frontend tests (`vitest`), coverage thresholds
- PR is blocked if any job fails
- Test results and coverage reports uploaded as workflow artifacts

#### Story 19.4.2 — GitHub Actions CD Pipeline `[PLANNED]`
*As a DevOps engineer, I want automated container image builds and pushes on merge to main, so that deployments are triggered by code rather than manual processes.*
- `.github/workflows/cd.yml` builds and pushes `app-backend`, `app-frontend`, and `financial-module` images to GHCR
- Images tagged with both commit SHA and `latest`
- Production `docker-compose.prod.yml` references `ghcr.io/{org}/{image}:${TAG}`
- Deployment workflow dispatches a webhook or SSH command to restart services on the production server

---

## EPIC 20 — Mobile & Progressive Web App

> PWA capability for offline-first access and native-like mobile experience.

---

### Feature 20.1 — Progressive Web App (PWA) `[PLANNED]`

#### Story 20.1.1 — PWA Manifest and Service Worker `[PLANNED]`
*As a mobile user, I want to install the platform as an app on my phone, so that I can access it quickly from the home screen.*
- `manifest.webmanifest` defines app name, icons (192px and 512px), theme color, and `display: standalone`
- A service worker registered and caches the application shell (HTML, CSS, core JS bundle)
- The app is installable in Chrome and Safari (passes Lighthouse PWA audit)

#### Story 20.1.2 — Offline Access for Key Pages `[PLANNED]`
*As a field worker with unreliable connectivity, I want to view recently accessed data while offline, so that I am not blocked when network is unavailable.*
- Service worker caches last-fetched responses for dashboard, active entity lists, and user profile
- When offline, the app shows a banner "You are offline — showing cached data"
- Write operations (create/update/delete) queued offline and synced when connectivity resumes
- Conflicts between queued offline changes and server state surfaced for manual resolution

#### Story 20.1.3 — Mobile-Responsive UI `[PLANNED]`
*As a mobile user, I want all platform pages to be usable on a small screen, so that I can complete common tasks from my phone without a desktop.*
- All page layouts use `FlexResponsive` breakpoints; sidebar collapses to a hamburger menu on mobile
- Data tables switch to card layout on screens narrower than 768px
- Form inputs are touch-friendly (minimum 44px tap targets per WCAG 2.5.5)
- Critical user journeys (view dashboard, approve workflow, read audit log) tested on mobile viewport

---

## Backlog Statistics

| Metric | Count |
|--------|-------|
| Total Epics | 20 |
| Total Features | 62 |
| Total Stories | 160 |
| Stories marked `[DONE]` | ~85 |
| Stories marked `[IN-PROGRESS]` | ~6 |
| Stories marked `[OPEN]` | ~28 |
| Stories marked `[PLANNED]` | ~41 |

---

*Generated from codebase analysis of `tbmahfudi/app-buildify` on branch `claude/create-system-backlog-nAwCn`.*
