---
id: E4
title: Scheduling Sub-Module
module: healthcare_scheduling
status: OPEN
depends_on: [healthcare]
---

# Epic 4 — Scheduling Sub-Module (`healthcare_scheduling`)

## Purpose
Enable appointment booking, provider calendar management, HIPAA-compliant patient reminders,
and waitlist management within the healthcare suite.

**Dependency:** requires the `healthcare` base module to be active.

---

## Feature 4.1 — Appointment Booking

### E4.1.1 — Patient Self-Scheduling Request [OPEN]
> **As a** patient (or their proxy),
> **I want** to submit an appointment request for an available provider slot,
> **so that** I can initiate booking without calling the clinic.

**Backend AC:**
- `POST /api/scheduling/appointments/request` accepts `{ patient_id, provider_id, requested_slot_start, appointment_type }`.
- Slot availability is validated; conflicting slots return 409.
- Appointment status on creation: `requested`.
- PHI collected during self-scheduling (name, contact) routes through the base module's PHI access layer; raw PHI is not stored in the scheduling table.
- Self-scheduling endpoint is rate-limited (max 5 requests per patient per 24 hours).

**Frontend AC:**
- Self-scheduling interface shows a provider's available slots in a calendar grid (week view default).
- Only future slots are selectable; past slots are grayed out.
- Patient contact pre-fill is available if the patient record exists; new patients are prompted to register first.
- Submission confirmation screen shows the request ID and estimated confirmation window (no appointment-specific PHI in the confirmation).

---

### E4.1.2 — Appointment Confirmation and Rescheduling by Staff [OPEN]
> **As a** clinical operations manager,
> **I want** to confirm or reschedule pending appointment requests,
> **so that** the schedule accurately reflects provider availability and patient needs.

**Backend AC:**
- `PATCH /api/scheduling/appointments/{id}/confirm` transitions status `requested` → `confirmed`; triggers reminder dispatch (see E4.2.1).
- `PATCH /api/scheduling/appointments/{id}/reschedule` requires `new_slot_start`; validates slot availability; updates status to `confirmed`.
- Both actions are audit-logged.
- `GET /api/scheduling/appointments?status=requested` returns pending requests for staff action.

**Frontend AC:**
- Pending requests appear in a "To Confirm" queue with patient reference, requested slot, and appointment type.
- "Confirm" action is one-click; "Reschedule" opens a slot picker calendar.
- After confirmation, the appointment moves to the schedule view and the patient receives a reminder (per E4.2.1).
- Bulk confirmation of multiple requests is supported via checkboxes + "Confirm Selected".

---

## Feature 4.2 — Provider Calendar

### E4.2.1 — Provider Availability Configuration [OPEN]
> **As a** provider or admin,
> **I want** to define my weekly availability blocks and block-off exceptions,
> **so that** self-scheduling only offers slots when I am actually available.

**Backend AC:**
- `POST /api/scheduling/availability` accepts `{ provider_id, day_of_week, start_time, end_time, slot_duration_minutes }` for recurring availability.
- `POST /api/scheduling/availability/exceptions` accepts `{ provider_id, date, all_day_block: true | { start_time, end_time } }` for one-off blocks.
- Slot generation is computed at query time from availability rules minus exceptions; slots are not pre-materialized.
- Only the provider themselves or an `admin` can modify availability for a provider ID.

**Frontend AC:**
- Provider availability page shows a weekly grid; clicking a time block opens a "Set Available" form.
- Exception blocking is accessible from the calendar via "Block Off Time" which opens a date + time range picker.
- Blocked times are visually distinct (striped pattern) from available slots.
- Changes take effect immediately; a toast confirms the save.

---

## Feature 4.3 — HIPAA-Compliant Reminders

### E4.3.1 — Appointment Reminder Dispatch (HIPAA-Safe) [OPEN]
> **As a** clinical operations manager,
> **I want** appointment reminders sent to patients that contain only time/location (no PHI),
> **so that** patients are reminded of their appointment without risking PHI exposure via SMS/email.

**Backend AC:**
- Reminder dispatch is triggered on appointment confirmation (E4.1.2) and at a configurable advance window (default: 24 hours before slot).
- Reminder content template is system-enforced: `"Reminder: You have an appointment on {date} at {time} at {clinic_name}. Reply STOP to opt out."` — no patient name, provider name, or appointment type in SMS.
- Email reminders may include the patient's first name (fetched from base module PHI layer) and clinic location only.
- Opt-out (`STOP`) is recorded in the patient's contact preferences; future reminders are suppressed.
- Reminder dispatch uses the platform's notification primitive; no direct SMS vendor dependency is introduced by this sub-module.

**Frontend AC:**
- Reminder settings page (admin) shows the system-enforced SMS template as read-only with an explanatory note about HIPAA compliance.
- Email reminder template is configurable but a validator warns if it detects a PHI field placeholder (provider name, diagnosis, etc.).
- Patient contact preference shows "SMS Reminders: Opted Out" if the patient has sent STOP; staff can see this but cannot override it.
- Admin can configure the reminder advance window (1 hour to 7 days) via a dropdown.

---

## Feature 4.4 — Waitlist

### E4.4.1 — Waitlist Enrollment and Notification [OPEN]
> **As a** patient or clinical staff member,
> **I want** to add a patient to a provider's waitlist when no slots are available,
> **so that** they are offered the next cancellation slot automatically.

**Backend AC:**
- `POST /api/scheduling/waitlist` accepts `{ patient_id, provider_id, preferred_date_range_start, preferred_date_range_end, appointment_type }`.
- When a confirmed appointment is cancelled, the system scans the waitlist for the earliest-enrolled eligible patient and dispatches an offer notification.
- Offer notification contains only: date/time options (no PHI); patient has 4 hours to respond before the offer expires and moves to the next waitlist entry.
- Waitlist position is FIFO within the same provider and appointment type.

**Frontend AC:**
- "Add to Waitlist" button appears on the self-scheduling interface when no slots are available.
- Patient waitlist entry shows estimated position and preferred date range.
- When an offer is made, the patient receives an in-app notification (and email if opted in) with a link to confirm the slot.
- Staff can view the waitlist per provider, see enrollment order, and manually remove entries.
