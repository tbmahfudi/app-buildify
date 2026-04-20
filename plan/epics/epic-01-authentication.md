# Epic 1 — Authentication & Identity Management

> Secure multi-method authentication: credential login, token lifecycle, MFA, and SSO.

---

## Feature 1.1 — Email/Password Login `[DONE]`

### Story 1.1.1 — User Login with JWT Tokens `[DONE]`

#### Backend
*As an API, I want to authenticate users by email/password and issue JWT tokens, so that clients can authorize subsequent requests.*
- `POST /api/v1/auth/login` accepts `{email, password, tenant_id?}` and returns `{access_token, refresh_token, token_type, expires_in, user}`
- Bcrypt password verification via `passlib`; failed attempts incremented in `login_attempts`
- Access token TTL: `ACCESS_TOKEN_EXPIRE_MIN` (default 30); refresh token TTL: `REFRESH_TOKEN_EXPIRE_DAYS` (default 7)
- Returns 401 on bad credentials, 423 on locked account, 429 on rate limit exceeded

#### Frontend
*As a user on the login page, I want to enter my email and password and be taken to the dashboard on success, so that I can start working immediately after authentication.*
- Route: `/login` renders `frontend/assets/templates/login.html`
- Form fields: `email` (`FlexInput` type=email, required), `password` (`FlexInput` type=password with show/hide toggle)
- Optional tenant selector shown when multiple tenants detected; pre-filled demo credentials per tenant shown in dev mode
- On submit: button enters loading state (`FlexSpinner`); form inputs disabled
- On success: tokens stored in `localStorage` (`tokens`, `tenantId`, `user`); redirect to `#/dashboard`
- On 401: form shakes animation + inline error "Invalid email or password"
- On 423: error "Account locked. Try again in X minutes" with countdown
- On 429: error "Too many attempts. Please wait before trying again"

---

### Story 1.1.2 — Token Refresh `[DONE]`

#### Backend
*As an API client, I want to exchange a valid refresh token for a new access token, so that sessions continue without re-authentication.*
- `POST /api/v1/auth/refresh` accepts `{refresh_token}` in body or `Authorization: Bearer` header
- Returns new `{access_token, expires_in}`; refresh token is rotated (old invalidated, new issued)
- Expired or blacklisted refresh tokens return 401 with `TOKEN_EXPIRED` code

#### Frontend
*As a user mid-session, I want my access token to renew automatically when it expires, so that I am never interrupted by an unexpected logout.*
- `api.js` `apiFetch()` intercepts any 401 response and calls `POST /auth/refresh` using the stored refresh token
- On successful refresh: new access token stored in `localStorage`; original request retried transparently
- On refresh failure (401): user redirected to `/login` with a toast "Session expired, please log in again"
- Refresh is queued — if multiple requests fail simultaneously, only one refresh call is made; others wait and retry

---

### Story 1.1.3 — Logout and Token Revocation `[DONE]`

#### Backend
*As an API, I want to revoke tokens on logout, so that stolen tokens cannot be replayed after the user signs out.*
- `POST /api/v1/auth/logout` adds the current token's `jti` to the Redis blacklist with TTL equal to remaining expiry
- Every request passes through `TokenBlacklist` check before reaching any handler
- Session record in `user_sessions` set to `is_active = false`

#### Frontend
*As a user, I want to click "Logout" in the user menu and be immediately returned to the login page, so that I know my session is ended.*
- User dropdown in top nav (triggered by avatar/name click) includes a "Logout" menu item
- Clicking Logout calls `POST /auth/logout`, clears `localStorage` (`tokens`, `tenantId`, `user`), clears in-memory `appState`
- Redirect to `/login`; browser history replaced so back button does not return to the app
- If the API call fails, localStorage is still cleared and user is redirected (fail-safe logout)

---

### Story 1.1.4 — Password Reset Flow `[DONE]`

#### Backend
*As an API, I want to support a two-step email-based password reset, so that users can recover accounts without admin intervention.*
- `POST /api/v1/auth/forgot-password` accepts `{email}` and creates a `PasswordResetToken` record; queues a notification
- `POST /api/v1/auth/reset-password` accepts `{token, new_password}`; validates token TTL and password policy; updates credential
- Always returns 200 even if email not found (prevents user enumeration)

#### Frontend
*As a user who has forgotten their password, I want to enter my email, receive a reset link, and set a new password through a guided flow, so that I can regain access without contacting support.*
- "Forgot password?" link on login page navigates to `#/forgot-password`
- Forgot-password page: single `FlexInput` for email + "Send Reset Link" button
- On submit: spinner shown; on success displays "Check your email for a reset link" confirmation card
- Reset link opens `#/reset-password?token=<token>` page with two `FlexInput` fields: "New password" + "Confirm password"
- Real-time password strength meter below the new password field using `POST /auth/strength-check`
- On mismatch: inline error "Passwords do not match" before submit
- On weak password: lists unmet policy rules below the input
- On success: toast "Password updated" + redirect to `/login`
- On expired token: error card "This reset link has expired" with a "Request a new link" button

---

### Story 1.1.5 — Password Strength Check API `[DONE]`

#### Backend
*As an API, I want to evaluate a candidate password against the current tenant's policy and return a strength score, so that UIs can provide real-time feedback.*
- `POST /api/v1/auth/strength-check` accepts `{password}` and returns `{score: 0-100, passed: bool, unmet_rules: [...]}`
- `GET /api/v1/auth/password-requirements` returns the active policy rules as a human-readable list

#### Frontend
*As a user setting a new password, I want to see a strength meter and checklist that updates as I type, so that I understand exactly what I need to do to meet the requirements.*
- Password fields on reset, change-password, and user-creation forms all use a shared `PasswordStrengthMeter` component
- Debounced call (300 ms) to `POST /auth/strength-check` on every keystroke
- Strength bar: red (0–40), amber (41–70), green (71–100) — driven by `score`
- Checklist below the bar: each policy rule shown with a ✓ (green) or ✗ (red) based on `unmet_rules`
- Submit button disabled until `passed === true`

---

## Feature 1.2 — Session Management `[DONE]`

### Story 1.2.1 — Idle and Absolute Session Timeouts `[DONE]`

#### Backend
*As an API, I want to invalidate sessions after configurable idle and absolute timeouts, so that unattended sessions are automatically closed.*
- `SessionManager` updates `last_activity_at` on each authenticated request
- Background task checks sessions against `idle_timeout_minutes` and `absolute_timeout_minutes` from `SecurityPolicy`
- Expired sessions: `is_active = false`; token `jti` added to Redis blacklist

#### Frontend
*As a user, I want to be warned before my session expires and redirected to login if I ignore the warning, so that I am never confused by a sudden "unauthorized" error mid-work.*
- Client-side timer reads `ACCESS_TOKEN_EXPIRE_MIN` from the token payload
- 2 minutes before expiry: a `FlexModal` appears — "Your session is about to expire. Stay logged in?"
- "Stay logged in" button triggers a token refresh; modal dismissed
- "Log out now" button triggers logout flow
- If user ignores modal for 2 minutes: auto-logout with toast "Session expired"

---

### Story 1.2.2 — Concurrent Session Limits `[DONE]`

#### Backend
*As an API, I want to enforce a maximum number of concurrent sessions per user, so that credential sharing is detected and limited.*
- On new login, count active sessions for the user; if `>= max_concurrent_sessions`, terminate the oldest or reject login
- `single_session_mode = true` terminates all prior sessions before creating the new one

#### Frontend
*As a user who just logged in from a new device, I want to be informed if an older session was terminated, so that I understand why I might have been logged out on another device.*
- If login response includes `sessions_terminated: true`, show an info toast: "An older session was signed out to allow this login"
- If `single_session_mode` is active, toast reads: "You have been signed in. All other sessions have been ended"

---

### Story 1.2.3 — Session Listing and Forced Termination `[DONE]`

#### Backend
*As an API, I want to expose a user's active sessions and allow individual revocation, so that users can respond to suspicious access.*
- `GET /api/v1/users/me/sessions` returns `[{id, device_hint, ip, user_agent, created_at, last_activity_at}]`
- `DELETE /api/v1/users/me/sessions/{id}` adds the session token `jti` to blacklist
- `DELETE /api/v1/users/me/sessions` terminates all sessions except the current one

#### Frontend
*As a user on my security settings page, I want to see a list of all my active sessions with device and location hints, and be able to terminate any session I don't recognize, so that I can respond immediately to unauthorized access.*
- Sessions list on `#/settings/security` page, rendered as `FlexCard` items
- Each card shows: device icon (desktop/mobile/tablet derived from user-agent), browser name, approximate location (from IP), last active time (relative: "2 hours ago")
- Current session highlighted with a "Current session" badge
- Each non-current session has a "Sign out" button; clicking opens a confirmation `FlexModal`
- "Sign out all other sessions" button at the top triggers bulk termination
- After termination: card removed from list with a fade animation; success toast shown

---

## Feature 1.3 — Password Policy Engine `[DONE]`

### Story 1.3.1 — Configurable Password Strength Rules `[DONE]`

#### Backend
*As an API, I want to validate passwords against a per-tenant configurable policy, so that weak passwords are rejected at every entry point.*
- `PasswordValidator.validate(password, policy)` checks: `min_length`, `max_length`, `require_uppercase`, `require_lowercase`, `require_digit`, `require_special_char`, `block_common_passwords`, `block_username_in_password`
- Returns `{valid: bool, violations: [{rule, message}]}`; used in login, change-password, reset-password, and user-create flows

#### Frontend
*As a tenant administrator on the security settings page, I want to configure password complexity rules using toggles and numeric inputs, so that I can meet our organization's security standards without editing config files.*
- Security policy form at `#/settings/security` → "Password Policy" section
- Toggle switches for: require uppercase, require lowercase, require digit, require special character, block common passwords
- Number inputs for: min length (default 8), max length (default 128), min unique characters
- Live preview: a sample password shown with pass/fail indicators reflecting the current policy settings
- "Save Policy" button calls `PUT /admin/security/policies/{tenant_id}`; success toast shown

---

### Story 1.3.2 — Password History and Rotation `[DONE]`

#### Backend
*As an API, I want to prevent password reuse by checking new passwords against stored history, so that rotation policies are effective.*
- On password change: new hash checked against last N bcrypt hashes in `password_history`; match → 400 with `PASSWORD_RECENTLY_USED`
- On login: checks `password_expires_at`; if expired, returns 200 with `{requires_password_change: true}`

#### Frontend
*As a user whose password has expired, I want to be redirected to a password change screen immediately after login, so that I understand I must update my password before continuing.*
- Login response with `requires_password_change: true` redirects to `#/change-password?required=true`
- Page header: "Your password has expired and must be changed before continuing"
- Form: current password + new password + confirm password fields
- If new password matches a previously used one: inline error "You cannot reuse a recent password"
- After successful change: redirect to `#/dashboard`; no back navigation to the forced-change page

---

### Story 1.3.3 — Account Lockout `[DONE]`

#### Backend
*As an API, I want to lock accounts after repeated failed logins, so that brute-force attacks are throttled.*
- `LockoutManager.record_failure(user_id)` increments `failed_attempts` in `account_lockouts`
- After `max_attempts`: sets `locked_until` (fixed duration) or calculates progressive duration
- `LockoutManager.is_locked(user_id)` returns `{locked: bool, locked_until, remaining_seconds}`

#### Frontend
*As a user who has triggered an account lockout, I want to see a clear message explaining when I can try again, so that I am not confused about why login is failing.*
- On 423 response: login form replaced with a lockout card (no inputs shown to prevent further attempts)
- Card shows: lock icon, "Account temporarily locked", "You can try again in X minutes Y seconds"
- Countdown timer updates every second using `setInterval`
- When countdown reaches zero: lockout card fades out, login form fades in
- Admin lockout notice (if configured): "Contact your administrator to unlock your account"

---

## Feature 1.4 — Two-Factor Authentication `[PLANNED]`

### Story 1.4.1 — TOTP Setup and Enrollment `[PLANNED]`

#### Backend
*As an API, I want to generate and verify TOTP secrets for user enrollment, so that users can register authenticator apps as a second factor.*
- `POST /api/v1/auth/2fa/setup/totp` generates a TOTP secret (pyotp), returns `{qr_uri, secret, backup_codes[]}`
- `POST /api/v1/auth/2fa/setup/confirm` accepts `{code}` and marks `is_2fa_enabled = true` on the user record
- Backup codes (8 × 8-char alphanumeric) stored as bcrypt hashes in `user_2fa_backup_codes`

#### Frontend
*As a user on my security settings page, I want a guided enrollment wizard that shows me a QR code to scan with my authenticator app, so that I can set up two-factor authentication without technical knowledge.*
- "Enable 2FA" button on `#/settings/security` opens a 3-step `FlexStepper` modal
- Step 1: "Install an authenticator app" — links to Google Authenticator, Authy, 1Password
- Step 2: QR code rendered using `qrcode.js`; "Can't scan?" toggle reveals the plain text secret
- Step 3: Verification — `FlexInput` for 6-digit TOTP code; auto-submits when 6 digits entered
- On success: modal transitions to "2FA Enabled" confirmation; backup codes displayed in a copyable list
- "Download backup codes" button generates a `.txt` file download
- Warning: "Store these codes safely. They won't be shown again."

---

### Story 1.4.2 — TOTP Login Verification `[PLANNED]`

#### Backend
*As an API, I want to issue a two-step login for 2FA users — first validating the password, then validating the TOTP code — so that both factors are required.*
- Password login for 2FA users returns `{mfa_required: true, mfa_challenge_token: "<jwt>"}` instead of full tokens
- `POST /api/v1/auth/2fa/verify` accepts `{mfa_challenge_token, code}` and issues full access + refresh tokens
- Challenge token expires in 5 minutes; 3 failed TOTP attempts invalidate the challenge

#### Frontend
*As a user with 2FA enabled, I want to be automatically shown a code entry screen after entering my password, so that the two-factor flow feels seamless and clear.*
- Login page detects `mfa_required: true` response and transitions to a TOTP input screen (no page navigation)
- Clean UI: "Enter the 6-digit code from your authenticator app" header
- Auto-focused 6-digit `FlexInput` with numeric keyboard hint (`inputmode="numeric"`)
- Auto-submits when 6 digits entered (no button click needed)
- "Use a backup code instead" link toggles to an 8-character text input
- On wrong code: input clears and shakes; counter shown "2 attempts remaining"
- Challenge expired toast: "Verification timed out. Please log in again" → redirect to login

---

### Story 1.4.3 — 2FA Policy Enforcement per Tenant `[PLANNED]`

#### Backend
*As an API, I want to enforce tenant-wide 2FA mandate with a grace period, so that admins can roll out 2FA requirements without immediately locking out users.*
- `SecurityPolicy.require_2fa = true` with `require_2fa_grace_days` (default 7)
- On login: if `require_2fa` is active and user has no 2FA enrolled, check `created_at + grace_days`; if grace expired return 403 with `MFA_ENROLLMENT_REQUIRED`

#### Frontend
*As a user in a tenant with mandatory 2FA, I want to see a clear notice about the requirement and a countdown to my enrollment deadline, so that I know when I must act.*
- After login (during grace period): persistent yellow banner at top of every page: "Your organization requires 2FA. Enroll by [date] — X days remaining. [Enroll Now]"
- "Enroll Now" navigates to `#/settings/security` with the 2FA enrollment modal pre-opened
- After grace expires: login succeeds to a forced-enrollment page (cannot navigate elsewhere until enrolled)

---

## Feature 1.5 — SSO / SAML / OAuth2 `[PLANNED]`

### Story 1.5.1 — SAML 2.0 Service Provider Integration `[PLANNED]`

#### Backend
*As an API, I want to act as a SAML 2.0 Service Provider, so that enterprise tenants can use their existing IdP for authentication.*
- `python3-saml` library handles SP/IdP metadata exchange and assertion parsing
- `GET /api/v1/auth/saml/metadata` returns SP metadata XML
- `POST /api/v1/auth/saml/acs` processes the IdP assertion and issues platform JWT tokens
- JIT provisioning: if the user does not exist, create from assertion attributes using the tenant's attribute mapping config

#### Frontend
*As an enterprise user on the login page, I want to click "Login with SSO" and be redirected to my company's identity provider, so that I can authenticate with my corporate credentials without a separate password.*
- Login page detects SSO config for the tenant (from `GET /auth/sso-config?tenant=<slug>`)
- If SSO is configured: "Login with [Company SSO]" button shown prominently; email/password form moved to a "Use local account" collapsible
- Clicking SSO button redirects to IdP login; after assertion, user lands on `#/dashboard`
- If JIT provisioning fails: error page "Your account could not be set up. Contact your administrator" with error code for support

---

### Story 1.5.2 — OAuth2/OIDC Provider Login `[PLANNED]`

#### Backend
*As an API, I want to support OAuth2 Authorization Code flow with PKCE, so that users can log in via Google, Microsoft, or custom OIDC providers.*
- `GET /api/v1/auth/oauth/{provider}/authorize` returns the redirect URL with `state` and `code_challenge`
- `GET /api/v1/auth/oauth/{provider}/callback` exchanges the code for tokens, fetches user info, and issues platform JWT
- Tenant admin registers providers via `POST /admin/oauth/providers` with `client_id`, `client_secret`, `discovery_url`

#### Frontend
*As a user on the login page, I want to see "Login with Google" and "Login with Microsoft" buttons, so that I can sign in with my existing work account.*
- Login page renders an OAuth button for each configured provider with the provider's official logo
- Clicking a provider button redirects to the OAuth authorize URL (opened in the same tab)
- OAuth callback page at `#/auth/callback` reads the `code` and `state` from the URL, calls the backend callback endpoint, then stores tokens and redirects to `#/dashboard`
- Error states: "Authorization was denied", "Provider is not configured", "Account already exists with a different login method" — each shown as an error card with suggested actions
