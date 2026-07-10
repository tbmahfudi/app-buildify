---
artifact_id: epic-18-patient-portal-authentication
status: active
version: 2
module: healthcare (primary), cross-module (platform auth)
launch_phase: MVP
producer: A3 Product Owner
upstream: vision-02, research-02, adr-hc-003, adr-hc-005, adr-hc-009, schema-hc-03, BACKLOG v3
created: 2026-07-05
updated: 2026-07-06
changelog:
  - "2026-07-06 (A3) v2 — REVIEW PASS. New requirement: one platform account holder may be linked to
     MANY hc_patients (self + dependents), across clinics/companies/branches. This conflicts with the
     just-accepted 1:1 model (ADR-HC-009 D5, schema-hc-03 §M, Story 18.6.1, and the from-platform
     bridge's single-patient assumption). Added an **Impact Review** section (below the invariants) and a
     new **Feature 18.10 — Household & Dependent Patients (Proxy Access)** revising the product model to
     1:N. Story 18.6.1's strict '1:1 / user_id UNIQUE' language is marked **AMENDED** (not deleted).
     Version bumped 1 → 2. Placement rationale: kept in epic-18 (not a new epic-20) because the change
     is an amendment to the exact bridge + hc_patients.user_id invariant epic-18 owns — B1 resolves it in
     one ADR-HC-009 pass rather than a cross-epic hunt."
---

# Epic 18 — Patient Portal Authentication

**Module:** Patient-facing authentication for the `healthcare` portal. Identity is **platform** (a
`User` with role `patient`); PHI is **module** (`hc_patient`, linked by `user_id`). This epic describes
the sign-in surface: how a patient obtains a platform session and how that session is bridged into the
clinical patient token.

**Launch Phase:** MVP. Email/username + password, Google OAuth, and the platform→patient bridge ship at
MVP. OTP-as-MFA and the OTP-only migration ship in the same release wave (auth is a gate for the whole
portal).

**Summary:** Patients sign in three ways — (1) email/username + password, (2) Google account (OAuth),
(3) OTP (phone) as an **optional** passwordless alternative and an **optional MFA second factor**. Every
path ends the same way: a platform JWT for the patient `User` is exchanged at the canonical
`POST /api/v1/patients/auth/from-platform` bridge for the module's patient token, which authorizes the
portal's PHI routes.

> **Supersedes ADR-HC-003 §D1** (which currently mandates OTP/phone-only patient auth). OTP is no longer
> the mandatory or only mechanism; it becomes one optional factor among three methods. B1 (Backend
> Architect) authors the superseding ADR + schema — every story below flags the specific ADR/schema
> decisions B1 must resolve in an **"Architecture note for B1"** line.

## Identity & tenancy invariants (conform to adr-hc-001 / 002 / 003)

- **Identity = platform.** One patient ↔ exactly one platform `User(role=patient)` holding
  email/username, password hash, linked Google identity, and MFA settings.
- **PHI = module.** One patient ↔ exactly one `hc_patient` row (encrypted PHI + consent), linked to the
  platform user by `hc_patient.user_id`. **~~Invariant: one patient ↔ one platform user — `user_id` is
  mandatory and unique on `hc_patient` for portal-capable patients.~~ [AMENDED v2 — see Impact Review +
  Feature 18.10]** The 1:1 invariant is superseded by a **household / proxy model**: one platform
  `User(role=patient)` (an *account holder*) may be linked to **many** `hc_patient` records — their own
  "self" patient PLUS dependents they manage — via a relationship/guardianship table. `hc_patient.user_id`
  is **no longer UNIQUE** (a single account holder owns/manages many patients); see Feature 18.10 for the
  revised relationship model and the B1 hand-off.
- **Cross-tenant patient token.** The minted patient token carries `tenant_id: null` (adr-hc-003 §D1
  claim shape is retained; only the *how-you-authenticate* changes). PHI is read only through SDK readers
  with audit (adr-hc-002); branch isolation (adr-hc-001) is unaffected because patient identity spans
  tenants.
- **i18n (adr-hc-004).** All patient-facing auth strings are id-ID (default) / en-US aware; locale is read
  from the platform `User` preference or the `Accept-Language` header on public endpoints.

---

## Impact Review (v2) — 1:1 identity → household / proxy model

**New requirement (user, 2026-07-06):** one platform account holder may be linked to **many**
`hc_patient` records — their own "self" patient PLUS dependents they register/manage (spouse,
children, elderly parents) — and those dependents may be registered at **different clinics**
(different `companies`/`branches`, and potentially different tenants). Example: a father registers
his wife and children and manages all of their care from one login.

**What this breaks in the just-accepted design (each must be revised by B1):**

| Accepted decision | Assumed | Now required |
|---|---|---|
| **ADR-HC-009 D5** / **schema-hc-03 §M** | `hc_patient.user_id` **NOT NULL + UNIQUE** (1:1) | **Drop UNIQUE.** One `user_id` maps to many `hc_patient` rows. `user_id` becomes **nullable** again (a clinic-created dependent may have no login of its own yet) — the account-holder link is expressed through a relationship, not a bare column. |
| **Story 18.6.1** | "one patient ↔ one platform user invariant" | 1:N account-holder ↔ patients; **amended below.** |
| **`from-platform` bridge** | loads the single `hc_patient WHERE user_id = sub`, mints one token | must resolve a **list** of patients the caller may act for, return them for selection, and mint a token **scoped to the chosen active patient**. |
| **Patient token** | implicitly "the one patient" | must carry the **active `patient_id`** chosen from the household set; switching patients re-mints/re-scopes. |
| **Consent (18.1.1) & audit** | patient consents for self | proxy consent + audit as "account holder X **acting on behalf of** patient Y". |

**Placement:** revised model captured as **Feature 18.10** below (kept in epic-18, not a new epic —
the change amends the exact `hc_patients.user_id` + bridge invariant this epic owns, so B1 resolves
it in one ADR-HC-009 revision). **OPEN product/legal questions are listed at the end of Feature 18.10
and must be answered by the user before B1 finalizes.**

---

## Feature 18.1 — Registration → Platform Account

### Story 18.1.1 [OPEN]
**As a** prospective Patient,
**I want to** self-register with my email/username and a password (and give consent),
**so that** I get a real platform account that owns my portal identity and a linked health profile.

**Backend AC:**
- `POST /api/v1/patients/register` — **MODULE** (healthcare), public. Supersedes the current OTP-only
  registration. New flow, in one transaction:
  1. CAPTCHA + phone-OTP verify still gate the public endpoint (reuse `sdk/captcha.py`, `sdk/otp.py`).
  2. Create a **PLATFORM** `User(role=patient)` with email (and/or username) + password hash (reuse
     platform password hashing/policy from `backend/app/core/auth.py` + `password_validator.py`).
  3. Create the **MODULE** `hc_patient` PHI row (encrypted name, DOB, phone, NIK) linked by
     `hc_patient.user_id = <new user.id>`; still capture `consent_version`, `consent_accepted_at`,
     consent IP/UA and write `hc_patient_consents`.
  4. Emit `patient.registered` audit (module) + platform `user.created` audit.
  5. Issue the platform token, then internally call the `from-platform` bridge to return a patient token
     (or return the platform token and let the SPA call the bridge — B1 to fix the seam).
- Registration must assign the patient `role` + `patients` group (reuse
  `backend/app/seeds/seed_rbac_with_groups.py`).
- Email/username uniqueness enforced at the platform `User` level; phone uniqueness still enforced on the
  module side via `phone_hash` (existing).
- **Architecture note for B1:** decide where the patient's password lives — on the platform `User`
  (`hashed_password`) is the ratified answer; confirm no separate module credential store. Decide whether
  registration mints the patient token server-side (single call) or the SPA calls `from-platform`
  after login. Make `hc_patient.user_id` **NOT NULL + UNIQUE** for new patients (migration handles
  legacy — see Story 18.9.1). Confirm which platform enrollment path creates a `role=patient` self-signup
  User without tenant scoping.

**Frontend AC:**
- Route: `/patient/register`
- Fields: email (or username), password + confirm (strength meter reusing platform policy), full name,
  DOB, phone, NIK, consent checkbox with versioned DPA text.
- Phone OTP step retained as **verification of the phone number** (not as the login mechanism); 60 s
  resend cooldown.
- On success: patient is signed in and lands on the portal home.
- All labels id-ID default / en-US.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/register`
- **Portal:** Patient Portal (public, pre-authentication)
- **Layout:** Mobile-first single-column wizard; step stepper (Akun → Data Diri → Verifikasi → Persetujuan
  — Account → Personal Data → Verification → Consent); full-screen on mobile, 480 px card on desktop.
- **Components:**
  - `FlexForm` — grouped fields per step, inline validation
  - `FlexInput` — email/username, password + confirm, full name, DOB, phone, NIK
  - `FlexPasswordStrength` — strength meter bound to platform password policy
  - `FlexInput` (OTP boxes) — 6-box phone verification with auto-advance
  - `FlexButton` — "Daftar dengan Google" (Sign up with Google) shortcut at top of step 1; "Lanjut"/"Kembali"; "Selesai"
  - `FlexModal` — DPA / consent full text with plain-language summary; "Saya Menyetujui" (I Agree) checkbox
  - `FlexAlert` — validation errors, OTP resend countdown, email-already-registered notice
- **Key interactions:**
  - Step 1 offers both "email + password" and a "Sign up with Google" shortcut (→ Story 18.3.1 first-time flow).
  - Phone OTP verifies the phone (resend after 60 s); consent checkbox mandatory before "Selesai".
  - Duplicate email → consistent "Registration failed / already registered — try signing in" (no enumeration).
- **Empty/Error state:** inline field errors; captcha challenge if abuse suspected; "Email sudah terdaftar. Masuk?" (Email already registered. Sign in?) links to login.
- **i18n:** all step titles, field labels, password-policy hints, consent/DPA body, OTP + error strings translated (id-ID default); DOB/date format in patient locale.
- **Mobile:** Primary; full-screen wizard; OTP keypad-friendly; "Daftar"/"Google" buttons 56 px full-width.

---

## Feature 18.2 — Email / Username + Password Login

### Story 18.2.1 [OPEN]
**As a** returning Patient with a platform account,
**I want to** sign in with my email (or username) and password,
**so that** I can access the portal without depending on phone OTP.

**Backend AC:**
- `POST /api/v1/auth/login` — **PLATFORM** (reuse `backend/app/routers/auth.py`). Authenticates the
  patient `User`, applies lockout + login-attempt tracking + session creation, returns platform
  access/refresh tokens (`tokens` table session).
- `POST /api/v1/patients/auth/from-platform` — **MODULE** (existing bridge). Exchanges the platform JWT
  for a patient token (mints `hc_patient_token`) after asserting the linked, active `hc_patient` row.
- If the patient has MFA enabled (Story 18.4.x), platform login returns an **MFA-challenge** state instead
  of full tokens; bridge is only called after the second factor passes.
- Emit platform `user.login` audit + module `patient.session_created` audit on bridge.
- **Architecture note for B1:** confirm the platform `login` accepts username **or** email for
  `role=patient` users (platform login is email-first today — Story 18.2 needs username lookup too).
  Define the MFA-challenge response contract on `POST /api/v1/auth/login` (see Feature 18.4). Decide
  whether the SPA calls `from-platform` explicitly or the platform login response signals "patient →
  bridge next".

**Frontend AC:**
- Route: `/patient/login`
- Email/username + password fields; "Masuk" (Sign in); links to "Lupa kata sandi?" (Forgot password) and
  "Masuk dengan Google".
- Also surfaces "Masuk dengan OTP" (Sign in with OTP) as an alternative (Story 18.4.3).
- On success (no MFA): bridge runs, patient lands on portal home. With MFA: routes to challenge screen.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/login`
- **Portal:** Patient Portal (public, pre-authentication)
- **Layout:** Mobile-first centered card; app logo; primary email/password form; social + alt-login buttons below a divider ("atau" / "or").
- **Components:**
  - `FlexForm` / `FlexInput` — email-or-username, password (show/hide toggle)
  - `FlexButton` — "Masuk" primary; "Masuk dengan Google" (Google-branded); "Masuk dengan OTP" (text link)
  - `FlexButton` (link) — "Lupa kata sandi?" (Forgot password)
  - `FlexAlert` — generic auth-failure ("Email atau kata sandi salah"), lockout notice, MFA-required redirect
- **Key interactions:**
  - Submit → platform login. No-MFA: auto-bridge → home. MFA: navigate to `#/patient/login/mfa`.
  - Generic failure message regardless of cause (no enumeration); lockout shows cooldown per platform policy.
  - Google button → Story 18.3; OTP link → Story 18.4.3.
- **Empty/Error state:** inline required-field errors; "Akun terkunci sementara" (Account temporarily locked) with retry-after.
- **i18n:** field labels, button labels, error/lockout strings, divider text translated (id-ID default).
- **Mobile:** Primary; full-width 56 px buttons; password show/hide; social buttons stacked full-width.

---

## Feature 18.3 — Google OAuth Login

### Story 18.3.1 [OPEN]
**As a** Patient,
**I want to** sign in (and, first time, sign up) with my Google account,
**so that** I can use the portal without creating or remembering a password.

**Backend AC:**
- `GET /api/v1/auth/oauth/google/start` — **PLATFORM (ADD — NEW)**. Returns the Google authorization URL
  (PKCE, state param). Google OAuth is inherently platform identity, so it is a **new platform capability**
  (the platform has no social login today).
- `GET /api/v1/auth/oauth/google/callback` — **PLATFORM (ADD — NEW)**. Exchanges the code, verifies the
  Google ID token, then resolves identity:
  - **Returning (Google identity already linked):** load the platform `User`, issue platform tokens.
  - **First-time, email matches an existing patient `User`:** **link** the Google identity to that user
    (require the account to be verified / apply the linking rule B1 defines), then issue tokens.
  - **First-time, no match:** **create** a platform `User(role=patient)` from the Google profile
    (email, name), create the linked `hc_patient` PHI shell, and require **consent capture** + phone
    collection before the portal is usable.
- After platform tokens are issued, the SPA calls `POST /api/v1/patients/auth/from-platform` — **MODULE**
  — to mint the patient token.
- Emit platform `user.oauth_login` / `user.oauth_linked` / `user.created` audits + module
  `patient.session_created`.
- **Architecture note for B1:** this is the biggest new decision. Define **where the Google identity link
  is stored** — ratified guidance: a platform-owned linkage (e.g. `user_identities` / `oauth_accounts`
  table: `provider`, `provider_subject`, `user_id`, `email`, `linked_at`), NOT a column on `hc_patient`.
  Define the **account-linking rule**: email-match auto-link only if the platform email is verified, else
  require an explicit link step (avoid account takeover via unverified email). Define first-Google-signup
  consent + phone-capture flow (consent is module PHI; can't skip it). Register the Google OAuth
  client/secret + redirect URIs as platform config. Confirm `role=patient` + `patients` group assignment
  on OAuth-created users.

**Frontend AC:**
- Entry points: "Masuk dengan Google" on `/patient/login` and "Daftar dengan Google" on `/patient/register`.
- Returning: redirect to portal home after callback + bridge.
- First-time new user: after callback, present a **consent + phone** completion screen before entering the portal.
- First-time email-match: present an **account-link confirmation** ("This email already has an account — link Google?").

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/login` + `#/patient/oauth/callback` + `#/patient/oauth/complete` (consent/phone) + `#/patient/oauth/link` (link confirm)
- **Portal:** Patient Portal (public → authenticated on completion)
- **Layout:** Google-branded button on login/register; callback shows a spinner ("Menghubungkan akun Google…"); completion/link screens are single-card centered.
- **Components:**
  - `FlexButton` — Google-branded sign-in button (per Google brand guidelines)
  - `FlexSpinner` — callback in-progress state
  - `FlexForm` — completion screen: phone + OTP verify, consent checkbox + DPA modal (first-time new user)
  - `FlexModal` — DPA / consent text (plain-language summary + legal)
  - `FlexAlert` — link-confirmation prompt ("Email ini sudah terdaftar. Tautkan Google?"), OAuth error, cancelled-flow notice
- **Key interactions:**
  - Google button → platform `oauth/google/start` redirect; callback → bridge or completion/link screen.
  - First-time new user: must complete phone verify + consent before portal access.
  - Email-match: "Tautkan" (Link) / "Batal" (Cancel) confirmation; on link, proceed to home.
  - OAuth error / user-cancelled: return to login with a translated notice.
- **Empty/Error state:** "Gagal masuk dengan Google. Coba lagi." (Failed to sign in with Google. Try again.); cancelled flow returns silently to login.
- **i18n:** button label, spinner text, completion-screen labels, consent body, link-confirmation and error strings translated (id-ID default).
- **Mobile:** Primary; Google button 56 px full-width; consent/link screens full-screen; OTP keypad-friendly.

---

## Feature 18.4 — OTP as Optional MFA & Passwordless Login

### Story 18.4.1 [OPEN]
**As a** signed-in Patient,
**I want to** enrol (or later disable) phone OTP as a second factor,
**so that** I can add MFA to my password/Google login when I choose to.

**Backend AC:**
- `POST /api/v1/patients/me/mfa/enroll` — **MODULE endpoint, PLATFORM setting**. Patient-authenticated;
  sends an OTP to the on-file phone (reuse `backend/app/routers/otp.py` transport), verifies it, then sets
  the platform `User` MFA flag `mfa_method = otp_phone`, `mfa_enabled = true`.
- `POST /api/v1/patients/me/mfa/disable` — requires a fresh OTP or password re-auth; clears the MFA flag.
- Emit platform `user.mfa_enrolled` / `user.mfa_disabled` audit.
- **Architecture note for B1:** define the **generic MFA/second-factor framework on the platform** (ADD —
  new). Ratified: MFA settings live on the platform `User` (or a platform `user_mfa` table:
  `user_id`, `method`, `enabled`, `enrolled_at`). This is a *generic* framework (OTP is the first method;
  designed so staff MFA can reuse it later). Decide the endpoint surface: mirror on platform
  (`/api/v1/auth/mfa/*`) with a module passthrough, or module-owned calling platform state — recommend
  platform-owned settings, module-owned patient-scoped endpoints.

**Frontend AC:**
- Route: `/patient/security` — "Keamanan" (Security) section with an MFA toggle.
- Enrol: confirm phone → OTP verify → MFA on. Disable: OTP or password re-auth.
- Shows current MFA state and last-changed date.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/security`
- **Portal:** Patient Portal (authenticated)
- **Layout:** Mobile-first settings list under Profil; security card with MFA toggle row.
- **Components:**
  - `FlexToggle` — "Verifikasi Dua Langkah (OTP)" (Two-step verification / OTP) enable/disable
  - `FlexInput` (OTP boxes) — enrol/disable OTP challenge
  - `FlexButton` — "Aktifkan" (Enable) / "Nonaktifkan" (Disable); "Verifikasi"
  - `FlexAlert` — success ("Verifikasi dua langkah aktif"), OTP failure, re-auth-required notice
- **Key interactions:**
  - Toggle on → phone confirm + OTP verify → MFA enabled. Toggle off → OTP/password re-auth → disabled.
  - Displays current state + last-changed date; warns that OTP requires the on-file phone.
- **Empty/Error state:** OTP failure "Kode salah. Coba lagi."; resend cooldown; re-auth prompt on disable.
- **i18n:** toggle + state labels, OTP strings, success/error, last-changed date format translated (id-ID default).
- **Mobile:** Primary; toggle row full-width; OTP keypad-friendly.

### Story 18.4.2 [OPEN]
**As a** Patient with MFA enabled,
**I want to** complete a second-factor OTP step after my password/Google login, with an option to remember this device,
**so that** my account is protected but I am not challenged on every sign-in.

**Backend AC:**
- Platform `POST /api/v1/auth/login` (and the OAuth callback) return an **MFA-challenge** state (a
  short-lived challenge token) instead of full tokens when `mfa_enabled`. — **PLATFORM (ADD)**.
- `POST /api/v1/auth/mfa/verify` — **PLATFORM (ADD)**. Accepts the challenge token + OTP; on success issues
  full platform tokens; supports a `remember_device` flag that registers a trusted-device token so future
  logins on that device skip the second factor for a bounded window.
- Only after full platform tokens does the SPA call `from-platform` (MODULE) to mint the patient token.
- Emit platform `user.mfa_challenge` / `user.mfa_passed` / `user.trusted_device_added` audit.
- **Architecture note for B1:** define the **MFA-challenge token** (short-lived, single-purpose) and the
  **trusted-device store** (ratified: platform `user_trusted_devices`: `user_id`, `device_hash`,
  `expires_at`, bound to a signed cookie / device fingerprint). Define the challenge/verify contract shared
  by password and OAuth entry paths. Define trusted-device window (e.g. 30 days) and revocation on password
  change / MFA disable.

**Frontend AC:**
- Route: `/patient/login/mfa`
- 6-box OTP input; "Ingat perangkat ini" (Remember this device) checkbox; resend with cooldown.
- On success: bridge runs, patient enters portal. Remembered device → future logins skip this step.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/login/mfa`
- **Portal:** Patient Portal (mid-authentication challenge)
- **Layout:** Mobile-first centered card; masked phone hint ("Kode dikirim ke ••••1234"); OTP boxes; remember-device checkbox.
- **Components:**
  - `FlexInput` (OTP boxes) — 6-box auto-advance
  - `FlexCheckbox` — "Ingat perangkat ini selama 30 hari" (Remember this device for 30 days)
  - `FlexButton` — "Verifikasi" primary; "Kirim ulang kode" (Resend) after cooldown
  - `FlexAlert` — invalid-code, expired-challenge (return to login), resend countdown
- **Key interactions:**
  - Enter OTP → verify → bridge → home. Remember-device sets trusted-device cookie.
  - Expired challenge token → "Sesi verifikasi kedaluwarsa. Masuk lagi." → back to login.
- **Empty/Error state:** "Kode salah"; expired-challenge redirect; resend cooldown countdown.
- **i18n:** masked-phone hint, OTP + checkbox labels, verify/resend, error strings translated (id-ID default).
- **Mobile:** Primary; OTP keypad-friendly; "Verifikasi" 56 px full-width.

### Story 18.4.3 [OPEN]
**As a** Patient,
**I want to** sign in with phone + OTP without a password (passwordless),
**so that** I retain the original OTP login as an option.

**Backend AC:**
- `POST /api/v1/patients/auth/otp/send` + `POST /api/v1/patients/auth/token` — **MODULE** (existing).
  Retained as an **optional passwordless login path**. On OTP success, resolve the `hc_patient` →
  `user_id` → platform `User`, and mint the patient token (directly or via an internal platform-token +
  bridge step).
- This path is no longer the mandatory mechanism; it is one option offered alongside password + Google.
- Emit module `patient.session_created` (method = otp_passwordless).
- **Architecture note for B1:** the existing OTP-token path returns a patient token directly without a
  platform token. Decide whether to keep that shortcut or route it through a platform token for a single
  session model. If a patient has MFA enabled, decide whether passwordless-OTP itself satisfies the factor
  (recommended: OTP-login already *is* the factor → no second challenge).

**Frontend AC:**
- Entry: "Masuk dengan OTP" link on `/patient/login`.
- Phone → OTP → portal home. Same OTP UI as MFA challenge, minus the remember-device step.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/login/otp`
- **Portal:** Patient Portal (public, pre-authentication)
- **Layout:** Mobile-first centered card; phone input step → OTP step.
- **Components:**
  - `FlexInput` — phone number (step 1), OTP boxes (step 2)
  - `FlexButton` — "Kirim Kode" (Send Code); "Masuk" (Sign in); "Kirim ulang kode" after cooldown
  - `FlexButton` (link) — "Gunakan kata sandi" (Use password instead) back to `#/patient/login`
  - `FlexAlert` — generic auth-failure (no enumeration), resend cooldown
- **Key interactions:**
  - Phone → send OTP → verify → mint patient token → home.
  - Generic failure regardless of whether phone exists.
- **Empty/Error state:** "Autentikasi gagal"; resend cooldown; CAPTCHA on abuse.
- **i18n:** phone/OTP labels, buttons, error strings translated (id-ID default).
- **Mobile:** Primary; keypad-friendly phone + OTP; 56 px buttons.

---

## Feature 18.5 — Forgot / Reset & Change Password

### Story 18.5.1 [OPEN]
**As a** Patient,
**I want to** reset a forgotten password and change my password while signed in,
**so that** I can recover and maintain access to my account.

**Backend AC:**
- `POST /api/v1/auth/reset-password-request` + `POST /api/v1/auth/reset-password-confirm` — **PLATFORM**
  (reuse `backend/app/routers/auth.py`). Emails a reset token to the patient `User`; confirm sets a new
  password hash (platform policy + password history reuse).
- `POST /api/v1/auth/change-password` — **PLATFORM** (reuse). Authenticated change with current-password
  verification and history check.
- Reset/change must not leak whether an email exists (consistent response); revoke sessions + trusted
  devices on password change (ties to Story 18.4.2).
- Emit platform `user.password_reset` / `user.password_changed` audit.
- **Architecture note for B1:** confirm the platform reset-email transport applies to `role=patient`
  users (notification transport reuse). Confirm password change revokes MFA trusted-device tokens.

**Frontend AC:**
- Routes: `/patient/forgot-password`, `/patient/reset-password?token=`, `/patient/security` (change).
- Forgot: email entry → "check your email" confirmation. Reset: new password + confirm from email link.
- Change (in Security): current + new + confirm with strength meter.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/forgot-password` | `#/patient/reset-password` | `#/patient/security`
- **Portal:** Patient Portal (forgot/reset public; change authenticated)
- **Layout:** Mobile-first centered cards; single-purpose forms.
- **Components:**
  - `FlexForm` / `FlexInput` — email (forgot); new + confirm password (reset); current + new + confirm (change)
  - `FlexPasswordStrength` — strength meter on new-password fields
  - `FlexButton` — "Kirim Tautan Reset" (Send Reset Link) / "Simpan Kata Sandi Baru" (Save New Password) / "Ubah Kata Sandi" (Change Password)
  - `FlexAlert` — generic "Jika email terdaftar, tautan reset telah dikirim"; token-expired notice; success confirmation
- **Key interactions:**
  - Forgot → generic confirmation (no enumeration). Reset link → set new password → sign-in.
  - Change → current-password verify + policy check → success + session/device revocation notice.
- **Empty/Error state:** expired/invalid reset token → "Tautan reset kedaluwarsa. Minta yang baru."; policy-violation inline hints.
- **i18n:** all labels, policy hints, generic/success/expired strings translated (id-ID default).
- **Mobile:** Primary; full-width fields + 56 px buttons.

---

## Feature 18.6 — Identity & Account Linking

### Story 18.6.1 [OPEN — AMENDED v2]
**As the** platform,
**I want to** resolve a patient's platform `User` to the `hc_patient` record(s) they are authorized to
act for and mint the clinical token from the platform session,
**so that** every auth method resolves to a consistent, authorized patient identity.

> **AMENDED v2:** the original strict *one-to-one / `user_id` UNIQUE* wording is **superseded by the
> household / proxy model in Feature 18.10.** An account holder resolves to a **set** of patients (self +
> managed dependents); the bridge selects an **active** patient. The 1:1 language is retained here only as
> struck-through history. ~~"one patient ↔ one platform user invariant; `hc_patient.user_id` mandatory +
> unique."~~

**Backend AC:**
- `POST /api/v1/patients/auth/from-platform` — **MODULE** (canonical bridge). Validates the platform JWT,
  resolves the **set** of `hc_patient` rows the caller may act for (self + active proxy grants — see
  18.10), and mints a patient token (`tenant_id: null`, roles `["patient"]`) **scoped to the active
  `patient_id`** (default = the caller's self patient, or the single member if only one). Remains the
  **single seam** every method flows through.
- If the caller resolves to **more than one** patient and none is pre-selected, the bridge returns the
  selectable set (see Story 18.10.4) rather than assuming one.
- 403 only if the caller resolves to **zero** authorized patients.
- Bridge emits module `patient.session_created` with the active `patient_id` (and `on_behalf_of` when the
  active patient ≠ self).
- **Architecture note for B1:** `hc_patient.user_id` is **NOT UNIQUE** (drop the unique index from
  schema-hc-03 §M) and **nullable** (a clinic-created dependent may not yet have a login); authorization to
  act for a patient flows through the 18.10 relationship table, not a bare column. Confirm the bridge stays
  the canonical seam for all methods; decide whether OTP-passwordless (18.4.3) routes through a platform
  token first. Define the active-patient claim in the token and how switching re-scopes it (18.10.4).

**Frontend AC:**
- No dedicated screen — this is the invisible bridge step after each successful login/register.
- On bridge failure ("no linked profile"), show a recovery screen linking to support / re-registration.

---

#### Frontend (UILDC v1.0)

- **Route:** (transparent bridge; error surfaces at `#/patient/login`)
- **Portal:** Patient Portal (post-authentication)
- **Layout:** No standalone UI; brief spinner during bridge; error card only on failure.
- **Components:**
  - `FlexSpinner` — "Menyiapkan portal Anda…" (Preparing your portal…)
  - `FlexAlert` — bridge failure: "Tidak ada profil pasien yang tertaut ke akun ini." (No patient profile linked to this account.) with support link
- **Key interactions:**
  - Successful login/register → bridge → home (spinner < 1 s typical).
  - Bridge 403 → recovery card with "Hubungi Dukungan" (Contact Support) / "Daftar" (Register) links.
- **Empty/Error state:** covered by the bridge-failure alert.
- **i18n:** spinner + error + link strings translated (id-ID default).
- **Mobile:** Primary; full-screen spinner; error card full-width.

---

## Feature 18.7 — Session & Logout (Both Tokens)

### Story 18.7.1 [OPEN]
**As a** Patient,
**I want to** sign out cleanly and manage my active sessions,
**so that** both my platform session and my patient portal session end and I can revoke other devices.

**Backend AC:**
- `POST /api/v1/patients/auth/logout` — **MODULE** (existing). Clears the `patient_refresh_token`
  HttpOnly cookie (clears the module `hc_patient_token` session).
- `POST /api/v1/auth/logout` — **PLATFORM** (reuse). Revokes the platform session (`tokens` table) and
  blacklists the platform token.
- Logout must **clear both tokens** — the SPA calls both; document the already-implemented
  logout-clears-both behavior as the contract.
- `GET /api/v1/auth/me/sessions` + `DELETE /api/v1/auth/me/sessions/{jti}` + `DELETE /api/v1/auth/me/sessions`
  — **PLATFORM** (reuse) for session listing / single-revoke / revoke-all (reuse
  `core/session_manager.py`).
- Emit platform `user.logout` + module `patient.session_ended` audit.
- **Architecture note for B1:** confirm the platform session-list surfaces patient sessions the same way
  as staff; decide whether the module patient token is independently revocable server-side (today it is a
  self-expiring JWT + cookie) or should be tracked for revoke-all. Ensure revoke-all also invalidates the
  patient token (or shortens its lifetime).

**Frontend AC:**
- "Keluar" (Log out) in the profile menu clears both tokens and returns to login.
- Security screen lists active sessions (device, last active) with "Keluar dari perangkat ini" per row and
  "Keluar dari semua perangkat".

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/security` (sessions) + global profile menu (logout)
- **Portal:** Patient Portal (authenticated)
- **Layout:** Mobile-first; sessions list card under Security; logout in profile/bottom-nav overflow.
- **Components:**
  - `FlexButton` — "Keluar" (Log out) in profile menu
  - `FlexCard` (list) — per session: device/browser, last-active, current-session badge
  - `FlexButton` (per row) — "Keluar dari perangkat ini"; footer "Keluar dari semua perangkat"
  - `FlexAlert` — logout confirmation, revoke success
- **Key interactions:**
  - "Keluar" → call platform logout + module logout → clear both → login screen.
  - Session revoke (single/all); current session flagged and not self-revocable from the list.
- **Empty/Error state:** single active session → list shows only "Perangkat ini (aktif)".
- **i18n:** logout/session labels, last-active date format, confirmations translated (id-ID default).
- **Mobile:** Primary; session cards full-width; destructive "Keluar dari semua" styled distinctly.

---

## Feature 18.8 — Security & Abuse Protection

### Story 18.8.1 [OPEN]
**As the** platform operator,
**I want** rate limiting, lockout, CAPTCHA, and audit on all patient auth endpoints,
**so that** the public auth surface resists bots, credential stuffing, and enumeration.

**Backend AC:**
- Public endpoints (`/patients/register`, `/patients/auth/otp/*`, `/patients/auth/token`,
  `/patients/auth/otp/send`, and the new `/auth/oauth/google/*`) — **rate limited** via `slowapi` + Redis
  (retain adr-hc-003 §D3 limits) and **CAPTCHA-gated** (reuse `sdk/captcha.py`).
- Platform `login` applies **account lockout** + login-attempt tracking (reuse platform LockoutManager) —
  now relevant because patients have passwords.
- All auth endpoints return **consistent, non-enumerating** error shapes.
- **Audit:** `patient.registered`, `user.login`, `user.oauth_login`, `user.oauth_linked`,
  `user.mfa_enrolled`, `user.mfa_passed`, `user.password_reset`, `patient.session_created`,
  `patient.session_ended` — module PHI-audit for patient-scoped events, platform audit for identity events.
- **Architecture note for B1:** extend rate-limit + CAPTCHA config to the new OAuth start/callback and MFA
  verify endpoints. Confirm lockout policy applies to `role=patient` logins. Define which events land in
  platform audit vs. module `hc_audit_log` and keep PHI out of platform audit.

**Frontend AC:**
- CAPTCHA widget on register / OTP-send / passwordless-OTP where required.
- Lockout and rate-limit responses render as translated, non-specific messages with retry-after.

---

#### Frontend (UILDC v1.0)

- **Route:** applies across `#/patient/register`, `#/patient/login`, `#/patient/login/otp`
- **Portal:** Patient Portal (public)
- **Layout:** CAPTCHA widget inline within forms; error banners above the submit button.
- **Components:**
  - `FlexCaptcha` — hCaptcha/Turnstile widget on public forms
  - `FlexAlert` — rate-limit ("Terlalu banyak percobaan. Coba lagi dalam N menit."), lockout, generic-failure banners
- **Key interactions:**
  - CAPTCHA required before OTP send / register submit; challenge escalates on repeated failure.
  - Rate-limit / lockout show retry-after countdown; no detail on which field failed.
- **Empty/Error state:** covered by the alert banners.
- **i18n:** CAPTCHA prompt, rate-limit/lockout/generic strings + retry-after format translated (id-ID default).
- **Mobile:** Primary; CAPTCHA sized for mobile; banners full-width.

---

## Feature 18.9 — Migration of OTP-only Patients

### Story 18.9.1 [OPEN]
**As an** existing OTP-only Patient,
**I want to** claim a password (and optionally link Google) on my next login,
**so that** my legacy phone-only account gains the new sign-in methods without losing my records.

**Backend AC:**
- Migration must **backfill a platform `User(role=patient)` for every existing `hc_patient` that lacks
  `user_id`**, seeded from phone/name, with a null/placeholder password and `must_set_password = true`.
  — **PLATFORM users created by MODULE migration**.
- On next OTP login (existing `/patients/auth/token`), if `must_set_password`, route the patient through a
  **"set a password"** (and optional "link Google") completion step before full portal access.
- Existing OTP-only registration is **superseded** by Story 18.1.1; the OTP-token login path is retained as
  passwordless (Story 18.4.3) but new signups create a platform account.
- Emit module `patient.migrated_to_platform_user` audit.
- **Architecture note for B1:** define the **backfill migration** that makes `hc_patient.user_id` NOT
  NULL: create platform users for legacy patients, set `must_set_password`, and enforce the unique index
  afterward. Decide the placeholder-credential state (login only via OTP until password set). Sequence:
  backfill users → set flags → add NOT NULL + UNIQUE constraint. This is the migration companion to
  Story 18.6.1's invariant.

**Frontend AC:**
- Route: `/patient/claim-account` (post-OTP-login interstitial for legacy patients).
- Prompt: "Amankan akun Anda — buat kata sandi" (Secure your account — create a password); optional "Tautkan Google".
- Skippable once (grace period), then enforced.

---

#### Frontend (UILDC v1.0)

- **Route:** `#/patient/claim-account`
- **Portal:** Patient Portal (post-OTP-login interstitial)
- **Layout:** Mobile-first single-card; explanatory copy + password form + optional Google link.
- **Components:**
  - `FlexForm` / `FlexInput` — email (confirm/add), new password + confirm
  - `FlexPasswordStrength` — strength meter
  - `FlexButton` — "Buat Kata Sandi" (Create Password); "Tautkan Google" (Link Google, optional); "Lewati untuk sekarang" (Skip for now, within grace period)
  - `FlexAlert` — success ("Akun Anda kini lebih aman"), grace-period-ending notice
- **Key interactions:**
  - After legacy OTP login, interstitial prompts to set a password; optional Google link.
  - "Lewati" allowed during grace period; after grace period, password creation is mandatory to proceed.
- **Empty/Error state:** policy-violation inline hints; "Lewati" hidden once grace period ends.
- **i18n:** explanatory copy, form labels, skip/create labels, success + grace-period strings translated (id-ID default).
- **Mobile:** Primary; full-width form + 56 px buttons.

---

## Feature 18.10 — Household & Dependent Patients (Proxy Access)

Revises the identity model from 1:1 to **1:N**: a platform account holder manages a *self* patient plus
zero-or-more dependents, across clinics. Proxy access to PHI is a sensitive capability — every story here
is gated by the **OPEN product/legal decisions** at the end of the feature.

### Story 18.10.1 [OPEN]
**As the** platform/module,
**I want** a relationship model where one account holder links to many patients (self + managed),
**so that** a single login can register and manage a whole household's care.

**Backend AC:**
- **MODULE** new relationship entity **`hc_patient_relationships`** (name finalized by B1 in ADR-HC-009
  v2 / schema-hc-03 §M.2; RLS-scoped): `account_user_id → users.id`, `patient_id → hc_patients.id`,
  `relationship` (self | spouse | child | parent | other), `role` (**owner | proxy** — exactly one `owner`
  + N `proxy` per patient), `status` (active | pending | revoked), `basis` (self | parental_guardian |
  delegated_adult | spousal), `granted_by`, `granted_at`, `approved_by_staff_id`, `approved_at`,
  `revoked_at`, tenant/branch context of the patient. UNIQUE(`account_user_id`, `patient_id`).
- Exactly one `relationship = self` per account holder (their own patient); zero-or-more managed. A linked
  existing patient (18.10.3) is granted `role = proxy`; `owner` is reserved for direct registration.
- `hc_patients.user_id` is **retained as a convenience denormalization of the owner** but is **no longer
  UNIQUE and is nullable** — the relationship table is the authority for "who may act for this patient."
- `GET /api/v1/patients/me/household` — returns the caller's authorized patient set (self first, then
  managed) with relationship + minimal display fields (name, clinic, dob); PHI-read-audited.
- **Architecture note for B1:** own the relationship table design + the `hc_patients.user_id` drop-UNIQUE /
  make-nullable migration; decide whether the table lives module-side (PHI-adjacent, RLS-scoped) — it
  almost certainly does. Cross-tenant membership hinges on OPEN-Q2.

**Frontend AC:**
- Portal home shows the **active patient** and a switcher affordance when the household set > 1 (see 18.10.4).

#### Frontend (UILDC v1.0)
- **Route:** `#/patient/household`
- **Portal:** Patient Portal
- **Layout:** Mobile-first list; self card pinned top, managed patients below; "Tambah Anggota" (Add member) CTA.
- **Components:** `FlexList` of `FlexCard` (name, relationship chip, clinic, avatar initial); `FlexButton` "Tambah Anggota Keluarga" (Add family member); `FlexBadge` relationship type.
- **Key interactions:** tap a member → switch active patient (18.10.4) or open manage-access (18.10.5).
- **i18n:** relationship labels + CTAs translated (id-ID default). **Mobile:** primary.

---

### Story 18.10.2 [OPEN]
**As an** account holder,
**I want to** register a new dependent patient at any clinic I choose,
**so that** I can create care records for my spouse/child/parent from my own account.

**Backend AC:**
- Reuse the registration flow (18.1.1) in **"register a dependent"** mode: creates a new `hc_patient`
  (encrypted PHI + consent captured under proxy per 18.10.6) with `user_id` = the account holder (owner)
  and a relationship row (`relationship` chosen, `role = owner`). The dependent may have **no login of its
  own** (nullable credentials) until/unless they later claim self-ownership (18.10.5).
- Clinic selection: the caller picks the target `branch` (clinic site) from clinics they may register at;
  the new `hc_patient` carries that branch/tenant. Cross-tenant allowed only per **OPEN-Q2**.
- Abuse controls from 18.8 apply (rate-limit dependent creation).
- **Architecture note for B1:** confirm a dependent `hc_patient` with null credentials is valid; define
  which `tenant_id` the dependent row takes when registered at a clinic in a different tenant than the
  account holder (OPEN-Q2), and how branch isolation (adr-hc-001) treats a cross-clinic household.

**Frontend AC:**
- Wizard mirrors self-registration but pre-tags "for a family member": relationship select, clinic select,
  dependent demographics, proxy-consent step.

#### Frontend (UILDC v1.0)
- **Route:** `#/patient/household/add`
- **Components:** `FlexStepper`; `FlexSelect` relationship + clinic; `FlexForm` demographics; proxy-consent `FlexCheckbox` + policy link.
- **Key interactions:** submit → new patient appears in household list and becomes selectable.
- **i18n / Mobile:** translated; mobile-first. **Empty/Error:** clinic-not-eligible + consent-required inline.

---

### Story 18.10.3 [OPEN]
**As an** account holder,
**I want to** link an existing patient record (already created at a clinic) to my account,
**so that** I can manage care records that were created before I had an account — without being able to claim strangers.

**Backend AC:**
- **MODULE** `POST /api/v1/patients/me/household/link` — initiates a **verified** claim on an existing
  `hc_patient`. Verification strength per **OPEN-Q3** (e.g. OTP to the patient's registered phone, or a
  clinic-issued link code). Creates a `pending` relationship that activates only on successful proof.
- Never reveals whether a given identifier matches an existing patient before verification (no enumeration).
- Emits `patient.link_requested` / `patient.link_verified` audit events.
- **Architecture note for B1:** define the verification mechanism + anti-enumeration + who can approve
  (self-service via OTP vs clinic-staff approval), and the pending→active state machine.

**Frontend AC:**
- "Tautkan Pasien" flow: enter identifier → receive/enter verification code → linked on success.

#### Frontend (UILDC v1.0)
- **Route:** `#/patient/household/link` — `FlexForm` identifier; `FlexOtpInput` verification; `FlexAlert` result.
- **i18n / Mobile / Error:** translated; mobile-first; invalid/expired-code inline; generic "if a match exists, a code was sent."

---

### Story 18.10.4 [OPEN]
**As an** account holder,
**I want to** switch which patient I'm currently viewing/acting as,
**so that** all portal data (`me/*`) reflects the selected household member.

**Backend AC:**
- The bridge (18.6.1) returns the authorized set when > 1; the client selects an active `patient_id`.
- **MODULE** `POST /api/v1/patients/auth/switch` (or a `patient_id` param on `from-platform`) — validates
  the caller is authorized for the target patient (active relationship) and **re-mints the patient token
  scoped to that `patient_id`**; the prior scoped token is invalidated.
- Every `me/*` PHI route is scoped to the token's active `patient_id`; audit records `on_behalf_of` when
  active ≠ self.
- **Architecture note for B1:** define the active-patient claim in the token, re-mint/rotation on switch,
  and whether server-side session tracks the active patient (revoke-all semantics from 18.7).

**Frontend AC:**
- Persistent active-patient indicator in the portal header; tapping opens the switcher; switching reloads scoped data.

#### Frontend (UILDC v1.0)
- **Route:** global header control (`FlexAvatarMenu` / `FlexSheet` switcher list).
- **Components:** header `FlexChip` (active patient name); bottom-sheet `FlexList` of household members with relationship chips.
- **Key interactions:** select member → spinner → scoped portal reload. **i18n / Mobile:** translated; mobile-first bottom sheet.

---

### Story 18.10.5 [OPEN]
**As an** account holder (and as the platform),
**I want to** grant/revoke another account's proxy access and detach a dependent who reaches adulthood,
**so that** access reflects real-world custody and privacy changes.

**Backend AC:**
- **MODULE** grant a second account holder proxy access to a patient (e.g. both parents manage a child):
  create an additional `relationship (role = proxy, status = active)`; `POST .../household/{patient_id}/grants`.
- Revoke: `DELETE .../grants/{grant_id}` → `status = revoked`; scoped tokens for that pairing are invalidated.
- **Detach on majority (OPEN-Q4):** when a dependent reaches the configured age of majority, flag for
  transition; the dependent claims self-ownership (relationship → `self`, `role = owner`) and prior proxy
  grants are revoked/require re-consent.
- All grant/revoke/detach emit audit events (identity + module PHI-scoped split per 18.8).
- **Architecture note for B1:** multi-owner semantics (can two accounts both be `owner`, or one owner +
  proxies?), the majority-detach workflow + config location, and grant revocation → token invalidation.

**Frontend AC:**
- Per-member "Kelola Akses" screen: list who has access, add/revoke, and (for minors nearing majority) a transition notice.

#### Frontend (UILDC v1.0)
- **Route:** `#/patient/household/{id}/access` — `FlexList` of grantees; `FlexButton` add/revoke; `FlexAlert` majority-transition.
- **i18n / Mobile / Error:** translated; mobile-first; confirm-dialog on revoke.

---

### Story 18.10.6 [OPEN]
**As the** module,
**I want** consent and audit to correctly attribute proxy actions,
**so that** we meet consent-law obligations for acting on behalf of another person.

**Backend AC:**
- Consent (extends 18.1.1 / existing `hc_patient_consents`): a proxy-captured consent records **who
  consented** (account holder), **for whom** (patient), the **basis** (self | parental/guardian | delegated
  by the adult patient), version, timestamp, IP/UA.
- Enforcement gate per **OPEN-Q1**: whether an adult may consent for another *competent adult* (spouse) at
  all, or whether the adult patient must provide their own consent / explicit delegation.
- Every PHI read/write on a non-self active patient is audited as `account_user_id` **on_behalf_of**
  `patient_id` (module `hc_audit_log`, PHI-scoped; identity events to platform audit — 18.8 split).
- **Architecture note for B1:** encode the consent-basis field + the adult-consent gate; ensure the
  `on_behalf_of` attribution threads from token → SDK PHI readers → `hc_audit_log`.

**Frontend AC:**
- Proxy-consent step in dependent registration/link; a visible "acting on behalf of {name}" banner whenever the active patient ≠ self.

#### Frontend (UILDC v1.0)
- **Components:** `FlexCheckbox` proxy-consent + basis; persistent `FlexBanner` "Bertindak atas nama {nama}" (Acting on behalf of {name}).
- **i18n / Mobile:** translated; mobile-first; banner always visible in proxy context.

---

### Product / legal decisions (Feature 18.10) — RESOLVED by user 2026-07-06

- **Q1 — Adult-for-adult consent → RESOLVED: ALLOW.** An account holder **may** manage & consent for
  another competent adult (e.g. a spouse). Consent records must still capture **who consented, for whom,
  and the basis** (18.10.6). *Legal-responsibility note: this is the customer's explicit product choice;
  the design records proxy consent faithfully but the operator owns the consent-law posture.*
- **Q2 — Cross-tenant proxy scope → RESOLVED: WITHIN ONE TENANT.** A household is confined to the account
  holder's tenant (the default single-tenant topology: one tenant, many companies/branches — adr-hc-005).
  Dependents at **dedicated-tenant** clinics are **out of scope**; dependent registration/link (18.10.2/3)
  rejects a target clinic in a different tenant. Simplifies the token (no cross-tenant patient set) and
  preserves branch/tenant isolation (adr-hc-001).
- **Q3 — Link verification → RESOLVED: CLINIC STAFF APPROVAL.** Linking an *existing* patient (18.10.3)
  requires **clinic-staff approval**: the account holder's link request creates a `pending` relationship
  that a staff member at the patient's clinic must approve before it activates. Needs a staff-side approval
  queue/endpoint. (No self-service OTP claim for existing records.)
- **Q4 — Age of majority → RESOLVED: CLINIC-MEDIATED.** Transition of a minor dependent to self-ownership
  is performed by **clinic staff** (not automatic, not self-service): staff detach the dependent / convert
  the relationship to `self`-owned and prior proxy grants are revoked pending re-consent.

---

## Story Count: 18.1 (1) + 18.2 (1) + 18.3 (1) + 18.4 (3) + 18.5 (1) + 18.6 (1) + 18.7 (1) + 18.8 (1) + 18.9 (1) + **18.10 (6)** = **17 stories**

---

## Hand-off to B1 (Backend Architect) — architecture & schema decisions

B1 authors the **superseding ADR** (supersedes ADR-HC-003 §D1) + schema deltas. Decisions to resolve:

1. **Patient password:** store on the platform `User.hashed_password` (ratified — no separate module
   credential store). Confirm platform login accepts **username OR email** for `role=patient`.
2. **Google identity storage:** new **platform** linkage table (e.g. `user_identities` /
   `oauth_accounts`: `provider`, `provider_subject`, `user_id`, `email`, `linked_at`), NOT a column on
   `hc_patient`. Define account-linking rule (email-match auto-link only if platform email verified; else
   explicit link step to prevent takeover). Register Google OAuth client/secret + redirect URIs; add
   `/api/v1/auth/oauth/google/start` + `/callback`.
3. **MFA framework (generic, platform):** MFA settings on platform `User` or `user_mfa`
   (`user_id`, `method`, `enabled`, `enrolled_at`); OTP is first method. Define MFA-challenge response on
   `POST /api/v1/auth/login` + OAuth callback, and `POST /api/v1/auth/mfa/verify`.
4. **Trusted-device store:** `user_trusted_devices` (`user_id`, `device_hash`, `expires_at`); signed
   cookie / fingerprint binding; window (e.g. 30 days); revoke on password change / MFA disable.
5. **`hc_patient.user_id`:** ~~make NOT NULL + UNIQUE~~ **[SUPERSEDED v2 by Feature 18.10]** — the
   household/proxy model makes this **1:N**: drop the UNIQUE index, keep `user_id` **nullable** (dependents
   may lack their own login), and introduce a **relationship/guardianship table** (see 18.10.1) as the
   authority for who may act for a patient. Bridge resolves a **set** and mints a token scoped to an active
   `patient_id` (18.6.1 amended, 18.10.4). See items 11–14 below.
6. **Bridge consistency:** confirm `from-platform` is the single seam for all three methods; decide whether
   OTP-passwordless routes through a platform token first (consistency) or keeps its direct mint (minimal
   change).
7. **Migration:** backfill platform `User(role=patient)` for every legacy `hc_patient` without `user_id`;
   `must_set_password` flag + grace-period interstitial; sequence backfill → flags → add NOT NULL + UNIQUE.
8. **Sessions/logout:** logout-clears-both is the contract; decide server-side revocability of the patient
   token (revoke-all should also invalidate it).
9. **Abuse/audit:** extend `slowapi` + CAPTCHA to OAuth + MFA endpoints; apply platform lockout to
   `role=patient` logins; split audit events between platform audit (identity) and module `hc_audit_log`
   (PHI-scoped), keeping PHI out of platform audit.
10. **Superseding ADR:** explicitly supersede **ADR-HC-003 §D1**; retain the `tenant_id: null` /
    `roles: ["patient"]` patient-token claim shape and adr-hc-001/002 (branch isolation + PHI-via-SDK)
    conformance.

**New tables/columns B1 must add (platform side):** `user_identities`/`oauth_accounts`, `user_mfa` (or
`User` columns), `user_trusted_devices`, `User.must_set_password`. **Module side:** ~~`hc_patient.user_id`
→ NOT NULL + UNIQUE index~~ **[SUPERSEDED v2]** — `hc_patient.user_id` **nullable, NOT UNIQUE**, plus a new
**relationship/guardianship table** (18.10.1); no new module *credential* columns.

### Hand-off addendum (v2) — household / proxy model (Feature 18.10)

11. **Relationship model:** own the `hc_patient_guardianships`/`hc_patient_links` table (18.10.1) — module
    side, RLS-scoped; the migration to **drop UNIQUE + make `hc_patient.user_id` nullable**; and the
    self/owner/proxy semantics (single `self` per account holder; multi-proxy allowed per 18.10.5).
12. **Bridge → active patient:** revise `from-platform` to resolve the authorized set and mint a token
    scoped to an **active `patient_id`**; add the switch endpoint (18.10.4); define the active-patient
    token claim + re-mint on switch + revoke-all interaction (18.7).
13. **Link verification & anti-enumeration** (18.10.3): mechanism (OTP-to-patient-phone / clinic code /
    staff approval), pending→active state machine, no existence disclosure.
14. **Proxy consent + audit** (18.10.6): consent-basis field, the adult-for-adult gate (OPEN-Q1), and the
    `on_behalf_of` attribution threaded token → SDK PHI readers → `hc_audit_log`.

**User rulings (2026-07-06) — now UNBLOCKED for B1:** Q1 = **allow adult-for-adult** consent (capture
basis); Q2 = **within one tenant** (reject cross-tenant dependents; no cross-tenant patient set in the
token); Q3 = **clinic-staff approval** to link an existing patient (staff approval queue, no self-service
OTP claim); Q4 = **clinic-mediated** majority transition (staff detach → self-owned, revoke prior grants).
B1 finalizes items 11–14 with these baked in.
