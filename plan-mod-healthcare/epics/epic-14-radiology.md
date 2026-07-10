---
artifact_id: epic-14-radiology
status: active
version: 1
module: healthcare_radiology
launch_phase: R3
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 14 — Radiology / Imaging

**Module:** `healthcare_radiology` (requires `healthcare` base; parallels the lab pattern in epic-05)
**Launch Phase:** R3
**Depth:** Outline (epic header + one-line story list; detailed AC/UILDC deferred to build time).
**Summary:** Imaging order management (X-Ray / CT / MRI / Ultrasound), image upload/attachment, radiologist
reporting, and report verification. **PACS/DICOM viewer bundling is scope-out (Scope-Out #12)** — this module
provides the order/report workflow and an image-attachment adapter, not an image store or DICOM viewer.

---

## Feature 14.1 — Imaging Order Management
- Story 14.1.1 — Doctor orders an imaging study (modality ∈ X-Ray/CT/MRI/Ultrasound) with clinical indication, linked to the encounter.
- Story 14.1.2 — Radiographer views and accepts incoming imaging orders in the branch worklist.
- Story 14.1.3 — Radiographer records study performed / patient no-show / rescheduled, advancing order status.

## Feature 14.2 — Image Upload & Attachment
- Story 14.2.1 — Radiographer uploads/attaches acquired images or an external-PACS reference to the study (adapter; no DICOM viewer bundled — Scope-Out #12).
- Story 14.2.2 — Doctor/radiologist views attached images/thumbnails or opens the external viewer link from the study.

## Feature 14.3 — Radiologist Reporting
- Story 14.3.1 — Radiologist drafts a structured imaging report (findings, impression) for a study.
- Story 14.3.2 — Radiologist finalizes the report; ordering doctor is notified (reuse epic-13 transport, PHI-safe).

## Feature 14.4 — Report Verification & Release
- Story 14.4.1 — Senior radiologist / Branch Manager verifies and releases the report; released report becomes visible to the ordering doctor and (per policy) the patient portal.

## Story Count: Feature 14.1 (3) + 14.2 (2) + 14.3 (2) + 14.4 (1) = **8 stories**
