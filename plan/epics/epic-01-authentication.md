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
- Route: `/login` → `login.html`
- Layout: FlexSection(centered) > login-card
  - login-card: FlexStack(direction=vertical, gap=md) — logo | form fields | "Sign In" FlexButton(primary, full-width) | "Forgot password?" link

- FlexForm — login form
  - fields: Email (FlexInput, type=email, required) | Password (FlexInput, type=password, show/hide toggle)
  - optional: Tenant (FlexSelect, shown only when multiple tenants detected; pre-filled demo credentials in dev mode)

- Interactions:
  - submit form: POST /auth/login → button enters loading state; inputs disabled → on success store tokens in localStorage + redirect to `#/dashboard`
  - on 401: form shakes animation + inline error "Invalid email or password"
  - on 423: form replaced with lockout card — lock icon + "Account locked. Try again in X minutes" + countdown
  - on 429: inline error "Too many attempts. Please wait before trying again"
  - click "Forgot password?": navigates to `#/forgot-password`

- States:
  - submitting: "Sign In" button shows spinner; all inputs disabled
  - locked (423): form replaced with lockout card showing countdown timer
  - rate-limited (429): inline error above submit button

---

### Story 1.1.2 — Token Refresh `[DONE]`

#### Backend
*As an API client, I want to exchange a valid refresh token for a new access token, so that sessions continue without re-authentication.*
- `POST /api/v1/auth/refresh` accepts `{refresh_token}` in body or `Authorization: Bearer` header
- Returns new `{access_token, expires_in}`; refresh token is rotated (old invalidated, new issued)
- Expired or blacklisted refresh tokens return 401 with `TOKEN_EXPIRED` code

#### Frontend
*As a user mid-session, I want my access token to renew automatically when it expires, so that I am never interrupted by an unexpected logout.*
- No dedicated route — handled globally in `api.js` `apiFetch()`

- Interactions:
  - any API response 401: apiFetch intercepts → POST /auth/refresh using stored refresh token → on success stores new access token; retries original request transparently
  - multiple simultaneous 401s: only one refresh call made; other requests queue and retry after
  - refresh returns 401: all queued requests cancelled → redirect to `/login` + FlexAlert(type=warning) toast "Session expired, please log in again"

---

### Story 1.1.3 — Logout and Token Revocation `[DONE]`

#### Backend
*As an API, I want to revoke tokens on logout, so that stolen tokens cannot be replayed after the user signs out.*
- `POST /api/v1/auth/logout` adds the current token's `jti` to the Redis blacklist with TTL equal to remaining expiry
- Every request passes through `TokenBlacklist` check before reaching any handler
- Session record in `user_sessions` set to `is_active = false`

#### Frontend
*As a user, I want to click "Logout" in the user menu and be immediately returned to the login page, so that I know my session is ended.*
- No dedicated route — "Logout" is a menu item in the global top-nav user dropdown

- Interactions:
  - click avatar/name in top nav: opens user FlexDropdown (profile link | settings | Logout)
  - click "Logout": POST /auth/logout → clears localStorage (tokens, tenantId, user) + clears in-memory appState → redirect to `/login`; history replaced so back button cannot return to app
  - if POST /auth/logout fails: localStorage still cleared; user still redirected to `/login` (fail-safe)

---

### Story 1.1.4 — Password Reset Flow `[DONE]`

#### Backend
*As an API, I want to support a two-step email-based password reset, so that users can recover accounts without admin intervention.*
- `POST /api/v1/auth/forgot-password` accepts `{email}` and creates a `PasswordResetToken` record; queues a notification
- `POST /api/v1/auth/reset-password` accepts `{token, new_password}`; validates token TTL and password policy; updates credential
- Always returns 200 even if email not found (prevents user enumeration)

#### Frontend
*As a user who has forgotten their password, I want to enter my email, receive a reset link, and set a new password through a guided flow, so that I can regain access without contacting support.*
- Route (step 1): `#/forgot-password` → `forgot-password.html`
- Route (step 2): `#/reset-password?token=<token>` → `reset-password.html`

- Layout (step 1): FlexSection(centered) > forgot-card
  - forgot-card: FlexStack(direction=vertical) — heading | Email (FlexInput, type=email) | "Send Reset Link" FlexButton(primary)

- Layout (step 2): FlexSection(centered) > reset-card
  - reset-card: FlexStack(direction=vertical) — heading | New Password (FlexInput, type=password) | PasswordStrengthMeter | Confirm Password (FlexInput, type=password) | "Set New Password" FlexButton(primary, disabled until passed)

- Interactions:
  - submit "Send Reset Link": POST /auth/forgot-password → spinner → success card "Check your email for a reset link"
  - type in New Password: debounced 300ms → POST /auth/strength-check → PasswordStrengthMeter updates; unmet rules listed below field
  - blur Confirm Password: if mismatch → inline error "Passwords do not match"
  - submit "Set New Password": POST /auth/reset-password → success toast "Password updated" + redirect to `/login`

- States:
  - sending: "Send Reset Link" button shows spinner; input disabled
  - sent: form replaced with confirmation card "Check your email for a reset link"
  - token-expired: page shows error card "This reset link has expired" + "Request a new link" FlexButton
  - submitting: "Set New Password" button shows spinner; fields disabled

---

### Story 1.1.5 — Password Strength Check API `[IN-PROGRESS]`

#### Backend
*As an API, I want to evaluate a candidate password against the current tenant's policy and return a strength score, so that UIs can provide real-time feedback.*
- `POST /api/v1/auth/strength-check` accepts `{password}` and returns `{score: 0-100, passed: bool, unmet_rules: [...]}`
- `GET /api/v1/auth/password-requirements` returns the active policy rules as a human-readable list

#### Frontend
*As a user setting a new password, I want to see a strength meter and checklist that updates as I type, so that I understand exactly what I need to do to meet the requirements.*
- No dedicated route — `PasswordStrengthMeter` is a shared component used inside password fields across reset, change-password, and user-creation forms

- PasswordStrengthMeter — inline component rendered below any password FlexInput
  - strength bar: red (score 0–40) | amber (41–70) | green (71–100)
  - rules checklist: each policy rule shown with ✓ (green) or ✗ (red) based on `unmet_rules`

- Interactions:
  - type in password field: debounced 300ms → POST /auth/strength-check → bar color and rules checklist update in real time
  - all rules pass (`passed === true`): submit button on the containing form becomes enabled
  - any rule fails: submit button remains disabled

---

## Feature 1.2 — Session Management `[IN-PROGRESS]`

### Story 1.2.1 — Idle and Absolute Session Timeouts `[IN-PROGRESS]`

#### Backend
*As an API, I want to invalidate sessions after configurable idle and absolute timeouts, so that unattended sessions are automatically closed.*
- `SessionManager` updates `last_activity_at` on each authenticated request
- Background task checks sessions against `idle_timeout_minutes` and `absolute_timeout_minutes` from `SecurityPolicy`
- Expired sessions: `is_active = false`; token `jti` added to Redis blacklist

#### Frontend
*As a user, I want to be warned before my session expires and redirected to login if I ignore the warning, so that I am never confused by a sudden "unauthorized" error mid-work.*
- No dedicated route — session timer runs globally in `app.js`

- FlexModal(size=sm) — session expiry warning, shown automatically 2 minutes before access token expires
  - body: "Your session is about to expire. Stay logged in?"
  - footer: Log out now | Stay logged in (primary)
  - on "Stay logged in": POST /auth/refresh → modal dismissed; timer resets
  - on "Log out now": triggers standard logout flow
  - on timeout (modal ignored 2 min): auto-logout + toast "Session expired"

- Interactions:
  - 2 min before token expiry: FlexModal(size=sm) appears automatically
  - click "Stay logged in": POST /auth/refresh → modal closes; session extends
  - click "Log out now": logout flow → redirect to `/login`
  - no action for 2 min: auto-logout → redirect to `/login` + toast "Session expired"

---

### Story 1.2.2 — Concurrent Session Limits `[IN-PROGRESS]`

#### Backend
*As an API, I want to enforce a maximum number of concurrent sessions per user, so that credential sharing is detected and limited.*
- On new login, count active sessions for the user; if `>= max_concurrent_sessions`, terminate the oldest or reject login
- `single_session_mode = true` terminates all prior sessions before creating the new one

#### Frontend
*As a user who just logged in from a new device, I want to be informed if an older session was terminated, so that I understand why I might have been logged out on another device.*
- No dedicated route — handled as a toast notification immediately after successful login

- Interactions:
  - login success with `sessions_terminated: true`: FlexAlert(type=info) toast "An older session was signed out to allow this login"
  - login success with `single_session_mode` active: FlexAlert(type=info) toast "You have been signed in. All other sessions have been ended"

---

### Story 1.2.3 — Session Listing and Forced Termination `[OPEN]`

#### Backend
*As an API, I want to expose a user's active sessions and allow individual revocation, so that users can respond to suspicious access.*
- `GET /api/v1/users/me/sessions` returns `[{id, device_hint, ip, user_agent, created_at, last_activity_at}]`
- `DELETE /api/v1/users/me/sessions/{id}` adds the session token `jti` to blacklist
- `DELETE /api/v1/users/me/sessions` terminates all sessions except the current one

#### Frontend
*As a user on my security settings page, I want to see a list of all my active sessions with device and location hints, and be able to terminate any session I don't recognize, so that I can respond immediately to unauthorized access.*
- Route: `#/settings/security` → `settings.html` + `settings-page.js` (Sessions section)
- Layout: FlexStack(direction=vertical) > section-header, sessions-list
  - section-header: FlexToolbar — "Active Sessions" heading | "Sign out all other sessions" FlexButton(ghost, danger)
  - sessions-list: FlexStack(direction=vertical, gap=sm) — FlexCard per session

- FlexCard — per session (populated from GET /users/me/sessions)
  - left: device icon (desktop/mobile/tablet, derived from user-agent) | browser name | approx location (from IP)
  - right: "last active X ago" | FlexBadge(color=success) "Current session" [current only] | "Sign out" FlexButton(ghost, danger) [non-current only]

- FlexModal(size=sm) — single-session sign-out confirm
  - body: "Sign out this session?"
  - footer: Cancel | Sign out (FlexButton, variant=danger)
  - on confirm: DELETE /users/me/sessions/{id} → card fades out + success toast

- FlexModal(size=sm) — bulk sign-out confirm
  - body: "Sign out all other sessions? All devices except this one will be logged out."
  - footer: Cancel | Sign out all (FlexButton, variant=danger)
  - on confirm: DELETE /users/me/sessions → all non-current cards fade out + success toast

- Interactions:
  - click "Sign out" on a session card: opens single-session confirm FlexModal(size=sm)
  - confirm sign out: DELETE /users/me/sessions/{id} → card fades out + success toast
  - click "Sign out all other sessions": opens bulk confirm FlexModal(size=sm)
  - confirm bulk sign out: DELETE /users/me/sessions → all non-current cards fade out + success toast

- States:
  - loading: session cards show skeleton rows while GET /users/me/sessions resolves
  - single-session: "Sign out all other sessions" button hidden (only current session exists)
  - error: FlexAlert(type=error) "Could not load sessions. Retry?"

---

## Feature 1.3 — Password Policy Engine `[IN-PROGRESS]`

### Story 1.3.1 — Configurable Password Strength Rules `[IN-PROGRESS]`

#### Backend
*As an API, I want to validate passwords against a per-tenant configurable policy, so that weak passwords are rejected at every entry point.*
- `PasswordValidator.validate(password, policy)` checks: `min_length`, `max_length`, `require_uppercase`, `require_lowercase`, `require_digit`, `require_special_char`, `block_common_passwords`, `block_username_in_password`
- Returns `{valid: bool, violations: [{rule, message}]}`; used in login, change-password, reset-password, and user-create flows

#### Frontend
*As a tenant administrator on the security settings page, I want to configure password complexity rules using toggles and numeric inputs, so that I can meet our organization's security standards without editing config files.*
- Route: `#/settings/security` → `settings.html` + `settings-page.js` (Password Policy section)
- Layout: FlexSection > policy-form
  - policy-form: FlexGrid(columns=2, gap=md) — toggle column | number inputs column | live-preview panel (full-width below) | "Save Policy" FlexButton(primary)

- FlexForm — password policy
  - toggles: Require uppercase (FlexCheckbox) | Require lowercase (FlexCheckbox) | Require digit (FlexCheckbox) | Require special character (FlexCheckbox) | Block common passwords (FlexCheckbox)
  - numbers: Min length (FlexInput, type=number, default=8) | Max length (FlexInput, type=number, default=128) | Min unique characters (FlexInput, type=number)
  - live preview panel: sample password shown with pass/fail rule indicators

- Interactions:
  - change any toggle or number input: live preview updates immediately (client-side, no API call)
  - click "Save Policy": PUT /admin/security/policies/{tenant_id} → success toast | error FlexAlert(type=error)

---

### Story 1.3.2 — Password History and Rotation `[IN-PROGRESS]`

#### Backend
*As an API, I want to prevent password reuse by checking new passwords against stored history, so that rotation policies are effective.*
- On password change: new hash checked against last N bcrypt hashes in `password_history`; match → 400 with `PASSWORD_RECENTLY_USED`
- On login: checks `password_expires_at`; if expired, returns 200 with `{requires_password_change: true}`

#### Frontend
*As a user whose password has expired, I want to be redirected to a password change screen immediately after login, so that I understand I must update my password before continuing.*
- Route: `#/change-password?required=true` → `change-password.html` + `change-password-page.js`
- Layout: FlexSection(centered) > change-card
  - change-card: FlexStack(direction=vertical) — FlexAlert(type=warning) "Your password has expired and must be changed before continuing" | Current Password (FlexInput, type=password) | New Password (FlexInput, type=password) | PasswordStrengthMeter | Confirm Password (FlexInput, type=password) | "Update Password" FlexButton(primary)

- Interactions:
  - page load without `required=true`: redirect to `#/dashboard` (cannot be accessed directly)
  - type in New Password: PasswordStrengthMeter updates in real time
  - blur Confirm Password: if mismatch → inline error "Passwords do not match"
  - submit "Update Password": POST /auth/change-password → on success redirect to `#/dashboard` (history entry replaced so back skips this page)
  - if new password matches recent history: inline error "You cannot reuse a recent password"

- States:
  - submitting: "Update Password" button shows spinner; all inputs disabled

---

### Story 1.3.3 — Account Lockout `[DONE]`

#### Backend
*As an API, I want to lock accounts after repeated failed logins, so that brute-force attacks are throttled.*
- `LockoutManager.record_failure(user_id)` increments `failed_attempts` in `account_lockouts`
- After `max_attempts`: sets `locked_until` (fixed duration) or calculates progressive duration
- `LockoutManager.is_locked(user_id)` returns `{locked: bool, locked_until, remaining_seconds}`

#### Frontend
*As a user who has triggered an account lockout, I want to see a clear message explaining when I can try again, so that I am not confused about why login is failing.*
- Route: `/login` → `login.html` (lockout state replaces the login form in-place)

- Interactions:
  - login returns 423: login form fades out; lockout card fades in — lock icon + "Account temporarily locked" + "You can try again in X minutes Y seconds" countdown (setInterval, 1s tick)
  - countdown reaches zero: lockout card fades out; login form fades in and is re-enabled
  - admin lockout configured: countdown replaced with "Contact your administrator to unlock your account"

- States:
  - locked: login form hidden; lockout card shown with live countdown
  - unlocked (countdown zero): lockout card fades out; login form fades in

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
- Route: `#/settings/security` → `settings-page.js` (2FA section)

- FlexModal(size=md) — 2FA enrollment wizard, triggered by "Enable 2FA" button
  - FlexStepper(steps=3) inside modal:
    - Step 1 "Install App": links to Google Authenticator | Authy | 1Password
    - Step 2 "Scan QR Code": QR code (qrcode.js) | "Can't scan?" toggle reveals plain text secret
    - Step 3 "Verify": 6-digit FlexInput (inputmode=numeric); auto-submits on 6th digit
  - on success: stepper replaced with confirmation — "2FA Enabled" heading + backup codes in copyable list + "Download backup codes" FlexButton
  - warning banner: "Store these codes safely. They won't be shown again."

- Interactions:
  - click "Enable 2FA": opens FlexModal(size=md) enrollment wizard at Step 1
  - advance Step 1 → Step 2: POST /auth/2fa/setup/totp → QR URI rendered with qrcode.js
  - click "Can't scan?": toggles visibility of plain text secret beneath QR code
  - type TOTP code (Step 3): auto-submits when 6th digit entered → POST /auth/2fa/setup/confirm
  - on confirm success: stepper slides to confirmation view; backup codes displayed
  - click "Download backup codes": generates .txt file download of backup codes

---

### Story 1.4.2 — TOTP Login Verification `[PLANNED]`

#### Backend
*As an API, I want to issue a two-step login for 2FA users — first validating the password, then validating the TOTP code — so that both factors are required.*
- Password login for 2FA users returns `{mfa_required: true, mfa_challenge_token: "<jwt>"}` instead of full tokens
- `POST /api/v1/auth/2fa/verify` accepts `{mfa_challenge_token, code}` and issues full access + refresh tokens
- Challenge token expires in 5 minutes; 3 failed TOTP attempts invalidate the challenge

#### Frontend
*As a user with 2FA enabled, I want to be automatically shown a code entry screen after entering my password, so that the two-factor flow feels seamless and clear.*
- Route: `/login` → `login.html` (TOTP step transitions in-place; no page navigation)

- Interactions:
  - login returns `mfa_required: true`: login form slides out; TOTP screen slides in — "Enter the 6-digit code from your authenticator app" + auto-focused FlexInput(inputmode=numeric, maxlength=6)
  - type 6th digit: auto-submits → POST /auth/2fa/verify → on success store tokens + redirect to `#/dashboard`
  - wrong code: input clears + shakes animation; "X attempts remaining" counter shown
  - click "Use a backup code instead": FlexInput switches to 8-character text input
  - challenge expires (5 min): toast "Verification timed out. Please log in again" → redirect to `/login`

- States:
  - totp-input: 6-digit input shown; "Use a backup code instead" link visible
  - backup-input: 8-character text input shown; "Use authenticator code instead" link visible
  - wrong-code: input shakes; attempts-remaining counter decrements
  - challenge-expired: redirect to `/login` + expired toast

---

### Story 1.4.3 — 2FA Policy Enforcement per Tenant `[PLANNED]`

#### Backend
*As an API, I want to enforce tenant-wide 2FA mandate with a grace period, so that admins can roll out 2FA requirements without immediately locking out users.*
- `SecurityPolicy.require_2fa = true` with `require_2fa_grace_days` (default 7)
- On login: if `require_2fa` is active and user has no 2FA enrolled, check `created_at + grace_days`; if grace expired return 403 with `MFA_ENROLLMENT_REQUIRED`

#### Frontend
*As a user in a tenant with mandatory 2FA, I want to see a clear notice about the requirement and a countdown to my enrollment deadline, so that I know when I must act.*
- No dedicated route — grace-period banner renders in the global app shell; forced-enrollment replaces normal post-login navigation

- Interactions:
  - within grace period (2FA not enrolled): persistent FlexAlert(type=warning) banner at top of every page "Your organization requires 2FA. Enroll by [date] — X days remaining." + "Enroll Now" FlexButton
  - click "Enroll Now": navigates to `#/settings/security`; 2FA enrollment FlexModal pre-opened
  - grace period expired (2FA not enrolled): login succeeds but user lands on forced-enrollment page; all other navigation blocked until enrolled
  - 2FA enrolled: banner dismissed; forced-enrollment bypass lifted

- States:
  - grace-active: yellow warning banner visible on all pages
  - grace-expired: forced-enrollment page shown after login; navigation blocked
  - enrolled: banner hidden; normal navigation restored

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
- Route: `/login` → `login.html` (SSO layout variant, driven by GET /auth/sso-config?tenant=<slug>)
- Layout (SSO detected): FlexSection(centered) > login-card
  - login-card: FlexStack(direction=vertical) — logo | "Login with [Company SSO]" FlexButton(primary, full-width) | "Use local account" FlexAccordion (collapses standard email/password form)

- Interactions:
  - page load: GET /auth/sso-config?tenant=<slug> → if SSO configured, SSO button shown + local form collapsed by default
  - click "Login with [Company SSO]": redirect to IdP login URL → after assertion POST /auth/saml/acs → store tokens + redirect to `#/dashboard`
  - click "Use local account": expands FlexAccordion revealing email/password form
  - JIT provisioning fails: error page "Your account could not be set up. Contact your administrator." with error code

- States:
  - loading: login card shows skeleton while SSO config resolves
  - sso-configured: SSO button prominent; local form collapsed in FlexAccordion
  - provisioning-error: error card shown; no login form available

---

### Story 1.5.2 — OAuth2/OIDC Provider Login `[PLANNED]`

#### Backend
*As an API, I want to support OAuth2 Authorization Code flow with PKCE, so that users can log in via Google, Microsoft, or custom OIDC providers.*
- `GET /api/v1/auth/oauth/{provider}/authorize` returns the redirect URL with `state` and `code_challenge`
- `GET /api/v1/auth/oauth/{provider}/callback` exchanges the code for tokens, fetches user info, and issues platform JWT
- Tenant admin registers providers via `POST /admin/oauth/providers` with `client_id`, `client_secret`, `discovery_url`

#### Frontend
*As a user on the login page, I want to see "Login with Google" and "Login with Microsoft" buttons, so that I can sign in with my existing work account.*
- Route (login): `/login` → `login.html`
- Route (callback): `#/auth/callback` → `oauth-callback.html`
- Layout: FlexSection(centered) > login-card
  - login-card: FlexStack(direction=vertical) — logo | email/password form | "or" divider | OAuth FlexButton per configured provider (provider logo + name)

- Interactions:
  - click OAuth provider button: GET /auth/oauth/{provider}/authorize → redirect to provider login URL (same tab)
  - callback page load: reads `code` + `state` from URL → GET /auth/oauth/{provider}/callback → store tokens → redirect to `#/dashboard`
  - authorization denied: error card "Authorization was denied" + "Try again" link
  - provider not configured: error card "Provider is not configured. Contact your administrator"
  - account exists with different login method: error card with suggested action (e.g. "Log in with email/password instead")

- States:
  - callback-loading: spinner shown while GET /auth/oauth/{provider}/callback resolves
  - callback-error: error card with specific message + suggested action
