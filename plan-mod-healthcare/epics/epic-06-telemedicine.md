---
artifact_id: epic-06-telemedicine
status: active
version: 2
module: healthcare_telemedicine
launch_phase: Month 6+ (separate legal gate)
producer: A3 Product Owner
upstream: vision-02, research-02
created: 2026-06-21
---

# Epic 06 — Telemedicine Module

**Module:** `healthcare_telemedicine` (requires `healthcare` base + `healthcare_scheduling`)
**Launch Phase:** Month 6+ — GA gated by a separate legal review (Permenkes No. 20/2019)
**Summary:** Video consultation sessions, SOAP documentation during session, and PHI-compliant session recording policy.

> **Regulatory gate:** This module MUST NOT be activated for any tenant until a legal review of
> Permenkes No. 20/2019 is complete and the review outcome is accepted by App-Buildify product leadership.
> The gate is enforced server-side on module activation.

---

## Feature 6.1 — Video Consultation

### Story 6.1.1 [OPEN]
**As a** Doctor,
**I want to** create a telemedicine session for a scheduled appointment and share a join link with the patient,
**so that** the consultation can proceed securely without an in-person visit — with Permenkes 20/2019 consent captured.

**Backend AC:**
- `POST /api/v1/tenants/:tenant_id/branches/:branch_id/telemedicine/sessions` — auth: Doctor; payload: `appointment_id` (scheduling module required); validates appointment is for current doctor + branch; generates session with `session_id`, `join_link_doctor`, `join_link_patient`, `status: scheduled`.
- Pre-session consent flow: patient must accept telemedicine consent (Permenkes 20/2019-aligned, in Bahasa Indonesia) before join link is activated; consent record stored with `session_id`, `version`, `accepted_at`.
- Session creation emits `telemedicine.session_created` audit event.
- Video provider is adapter-based (platform selects provider; clinic cannot override to reduce PHI leakage risk).

**Frontend AC:**
- Route: `/clinic/telemedicine/sessions/:session_id` (staff)
- Session card: patient name, appointment time, join button (active only when patient consent received).
- "Copy Patient Link" button; link sent via WhatsApp (PHI-safe: session reference only, no diagnosis).
- Patient portal: consent modal in Bahasa Indonesia (plain language) before patient join link activates; "I Consent" / "I Do Not Consent" buttons.
- All labels in active locale.

---

### Story 6.1.2 [OPEN]
**As a** Patient,
**I want to** join my telemedicine appointment via a browser link,
**so that** I can consult with my doctor without installing a native app.

**Backend AC:**
- `GET /api/v1/telemedicine/sessions/:session_id/join?token=` — auth: Patient (token in join link); validates consent is recorded; returns video session credentials.
- Session credentials are short-lived (1-hour TTL); re-generated on re-join.
- Patient join event emits `telemedicine.patient_joined` audit event.

**Frontend AC:**
- Route: `/telemedicine/join/:session_id` (patient portal, browser-based)
- Pre-join check: camera and microphone permission request; device test (camera preview, mic level).
- Waiting room state while doctor has not joined.
- In-session: video grid, mute/camera toggle, end call button; no recording controls visible to patient unless recording is opted in.
- All labels in active locale; works on Android Chrome mid-range device.

---

## Feature 6.2 — Session Documentation

### Story 6.2.1 [OPEN]
**As a** Doctor,
**I want to** record SOAP notes during or immediately after a telemedicine session,
**so that** the encounter is fully documented and linked to the patient's record.

**Backend AC:**
- Telemedicine session automatically creates an `encounter` record (linked to the appointment and session); SOAP notes API is the same as Feature 1.3.2 endpoint, with `encounter_source: telemedicine`.
- `PUT /api/v1/.../encounters/:encounter_id` — SOAP fields; encounter must be in `in_progress` status (session active) or `pending_documentation` (within 30 minutes of session end).
- After 30 minutes post-session-end without documentation, status moves to `documentation_overdue` and Branch Manager is alerted.

**Frontend AC:**
- Route: SOAP editor panel rendered in-session (side panel) and post-session (`/clinic/telemedicine/sessions/:session_id/notes`).
- Auto-save every 30 seconds.
- Post-session: "Complete Encounter" button; reminder banner if documentation overdue.
- All labels in active locale; timestamp in branch timezone.

---

## Feature 6.3 — Session Recording Policy

### Story 6.3.1 [OPEN]
**As a** Patient,
**I want to** have explicit control over whether my telemedicine session is recorded,
**so that** I can exercise my data rights under UU PDP No. 27/2022 and Permenkes 20/2019.

**Backend AC:**
- Recording is OPT-IN only; default is `recording: disabled`; cannot be changed to opt-out by tenant config.
- Recording consent: separate from telemedicine consent; patient must explicitly check "I consent to recording" before a recording starts; consent record stored with `session_id`, `recording_consent_version`, `accepted_at`.
- `POST /api/v1/telemedicine/sessions/:session_id/recording/start` — auth: Doctor; requires patient recording consent = `accepted`; otherwise 403.
- Recordings stored in tenant-isolated, encrypted storage; retention period configurable per tenant (default: 90 days); automated deletion job; deletion event logged.
- Patient can request recording deletion: `DELETE /api/v1/patients/me/telemedicine-recordings/:recording_id` — triggers deletion workflow with 7-day review window.

**Frontend AC:**
- Patient portal: before session, two separate consent steps — (1) telemedicine consent, (2) optional recording consent with clear "this is optional" framing.
- In-session: recording indicator (red dot) visible when recording is active; patient can withdraw recording consent mid-session (triggers stop-recording workflow).
- Route: `/patient/records/telemedicine` — list of past sessions; recording availability badge; "Request Recording Deletion" button per recorded session.
- All consent text in active locale (Bahasa Indonesia default); plain language required.

---

## Story Count: Feature 6.1 (2) + 6.2 (1) + 6.3 (1) = **4 stories**
