from __future__ import annotations
import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

_HMAC_SECRET = os.environ.get("PHONE_HASH_SECRET")
if not _HMAC_SECRET:
    raise RuntimeError("PHONE_HASH_SECRET environment variable is required")
_HMAC_SECRET = _HMAC_SECRET.encode()

# PHI-safe templates: NO patient name, NO provider name, NO diagnosis
# Params: clinic_name, branch_name, date, time
_TEMPLATES: dict = {
    "appointment_confirmed": {
        "id-ID": "Janji temu Anda di {clinic_name} - {branch_name} telah dikonfirmasi untuk {date} pukul {time}. Terima kasih.",
        "en-US": "Your appointment at {clinic_name} - {branch_name} has been confirmed for {date} at {time}. Thank you.",
    },
    "appointment_reminder_24h": {
        "id-ID": "Pengingat: Janji temu Anda di {clinic_name} - {branch_name} adalah besok, {date} pukul {time}.",
        "en-US": "Reminder: Your appointment at {clinic_name} - {branch_name} is tomorrow, {date} at {time}.",
    },
    "appointment_reminder_2h": {
        "id-ID": "Pengingat: Janji temu Anda di {clinic_name} - {branch_name} adalah hari ini pukul {time}.",
        "en-US": "Reminder: Your appointment at {clinic_name} - {branch_name} is today at {time}.",
    },
    "appointment_cancelled": {
        "id-ID": "Janji temu Anda di {clinic_name} - {branch_name} pada {date} pukul {time} telah dibatalkan.",
        "en-US": "Your appointment at {clinic_name} - {branch_name} on {date} at {time} has been cancelled.",
    },
    "appointment_rescheduled": {
        "id-ID": "Janji temu Anda di {clinic_name} - {branch_name} telah dijadwal ulang ke {date} pukul {time}.",
        "en-US": "Your appointment at {clinic_name} - {branch_name} has been rescheduled to {date} at {time}.",
    },
    "waitlist_offer": {
        "id-ID": "Slot tersedia di {clinic_name} - {branch_name} pada {date} pukul {time}. Klaim dalam 15 menit.",
        "en-US": "A slot is available at {clinic_name} - {branch_name} on {date} at {time}. Claim within 15 minutes.",
    },
    # PHI-safe lab templates: no patient name, no result values, no provider name
    "lab_critical_alert": {
        "id-ID": "Hasil kritis tersedia untuk pasien Anda, silakan periksa sistem.",
        "en-US": "Critical results are available for your patient. Please check the system.",
    },
    "lab_results_ready": {
        "id-ID": "Hasil pemeriksaan laboratorium Anda sudah tersedia. Silakan login untuk melihat.",
        "en-US": "Your laboratory results are now available. Please log in to view them.",
    },
}


def _phone_hash(raw_phone: str) -> str:
    return hmac.new(_HMAC_SECRET, raw_phone.encode(), hashlib.sha256).hexdigest()


class NotificationService:
    def __init__(self, db: Session, tenant_id: str, branch_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.branch_id = branch_id

    def dispatch_appointment_notification(self, appointment_id: str, template_name: str) -> None:
        appt = self.db.execute(
            text("SELECT * FROM hcs_appointments WHERE id=:id LIMIT 1"),
            {"id": appointment_id},
        ).mappings().one_or_none()
        if not appt:
            logger.warning("Notification skipped: appointment %s not found", appointment_id)
            return
        self._dispatch(
            patient_id=appt["patient_id"],
            template_name=template_name,
            context=self._build_appt_context(appt),
            appointment_id=appointment_id,
            waitlist_id=None,
        )

    def dispatch_waitlist_offer_notification(self, waitlist_id: str) -> None:
        entry = self.db.execute(
            text("SELECT * FROM hcs_waitlist WHERE id=:id LIMIT 1"),
            {"id": waitlist_id},
        ).mappings().one_or_none()
        if not entry:
            logger.warning("Notification skipped: waitlist entry %s not found", waitlist_id)
            return
        slot = None
        if entry.get("offered_slot_id"):
            slot = self.db.execute(
                text("SELECT * FROM hcs_appointment_slots WHERE id=:id LIMIT 1"),
                {"id": entry["offered_slot_id"]},
            ).mappings().one_or_none()
        context = self._build_slot_context(slot) if slot else {}
        self._dispatch(
            patient_id=entry["patient_id"],
            template_name="waitlist_offer",
            context=context,
            appointment_id=None,
            waitlist_id=waitlist_id,
        )


    def dispatch_to_provider(
        self,
        provider_id: str,
        template_name: str,
        context: dict,
    ) -> None:
        """
        CR-006 fix: Dispatch a notification to the ordering PROVIDER (not the patient).

        Looks up the provider's phone number from hc_provider_contacts (or falls back
        to the user profile), then sends the given template via WhatsApp/SMS.
        """
        # Look up provider phone from hc_providers (provider_phone_enc column)
        row = self.db.execute(
            text(
                "SELECT phone_enc, locale FROM hc_providers WHERE id = :pid LIMIT 1"
            ),
            {"pid": provider_id},
        ).mappings().one_or_none()

        if not row:
            logger.warning("dispatch_to_provider: provider %s not found", provider_id)
            return

        try:
            from modules.healthcare.sdk.phi_crypto import EncryptedPHIType
            raw_phone = EncryptedPHIType().process_result_value(row["phone_enc"], None)
        except Exception:
            raw_phone = str(row.get("phone_enc", ""))

        if not raw_phone:
            logger.warning("dispatch_to_provider: no phone for provider %s", provider_id)
            return

        locale = row.get("locale") or "id-ID"
        variants = _TEMPLATES.get(template_name)
        if not variants:
            logger.error("Unknown template: %s", template_name)
            return
        body = variants.get(locale) or variants.get("id-ID", "")
        try:
            body = body.format(**context)
        except KeyError as exc:
            logger.warning("Template %s missing context key %s", template_name, exc)

        phone_hash = _phone_hash(raw_phone)
        channel, resp, send_status = self._send_whatsapp(raw_phone, body)
        if send_status == "failed":
            channel, resp, send_status = self._send_sms(raw_phone, body)

        self.log_notification(
            appointment_id=None,
            waitlist_id=None,
            channel=channel,
            template_name=template_name,
            phone_hash=phone_hash,
            send_status=send_status,
            provider_response=resp,
        )

    def _dispatch(
        self,
        patient_id: str,
        template_name: str,
        context: dict,
        appointment_id: Optional[str],
        waitlist_id: Optional[str],
    ) -> None:
        patient = self.db.execute(
            text("SELECT phone_enc, locale FROM hc_patients WHERE id=:id LIMIT 1"),
            {"id": patient_id},
        ).mappings().one_or_none()
        if not patient:
            logger.warning("Patient %s not found; skipping notification", patient_id)
            return

        try:
            from modules.healthcare.sdk.phi_crypto import EncryptedPHIType
            raw_phone = EncryptedPHIType().process_result_value(patient["phone_enc"], None)
        except Exception:
            raw_phone = str(patient.get("phone_enc", ""))

        locale = patient.get("locale") or "id-ID"
        variants = _TEMPLATES.get(template_name)
        if not variants:
            logger.error("Unknown template: %s", template_name)
            return
        body = variants.get(locale) or variants.get("id-ID", "")
        try:
            body = body.format(**context)
        except KeyError as exc:
            logger.warning("Template %s missing context key %s", template_name, exc)

        phone_hash = _phone_hash(raw_phone)
        channel, resp, send_status = self._send_whatsapp(raw_phone, body)
        if send_status == "failed":
            channel, resp, send_status = self._send_sms(raw_phone, body)

        self.log_notification(
            appointment_id=appointment_id,
            waitlist_id=waitlist_id,
            channel=channel,
            template_name=template_name,
            phone_hash=phone_hash,
            send_status=send_status,
            provider_response=resp,
        )

    def _send_whatsapp(self, phone: str, body: str) -> tuple:
        import requests as _req
        wa_url = os.environ.get("WHATSAPP_API_URL")
        wa_token = os.environ.get("WHATSAPP_API_TOKEN")
        if not wa_url or not wa_token:
            return "whatsapp", {"error": "WHATSAPP_API_URL/TOKEN not configured"}, "failed"
        try:
            resp = _req.post(
                wa_url,
                json={"to": phone, "body": body},
                headers={"Authorization": f"Bearer {wa_token}"},
                timeout=60,
            )
            if resp.ok:
                return "whatsapp", resp.json(), "sent"
            return "whatsapp", {"status_code": resp.status_code, "body": resp.text[:200]}, "failed"
        except Exception as exc:
            return "whatsapp", {"error": str(exc)}, "failed"

    def _send_sms(self, phone: str, body: str) -> tuple:
        import requests as _req
        sms_url = os.environ.get("SMS_GATEWAY_URL")
        if not sms_url:
            logger.warning("SMS_GATEWAY_URL not set; skipping SMS")
            return "sms", {"error": "SMS_GATEWAY_URL not configured"}, "failed"
        try:
            resp = _req.post(sms_url, json={"to": phone, "message": body}, timeout=30)
            if resp.ok:
                return "sms", resp.json(), "sent"
            return "sms", {"status_code": resp.status_code, "body": resp.text[:200]}, "failed"
        except Exception as exc:
            return "sms", {"error": str(exc)}, "failed"

    def log_notification(
        self,
        appointment_id: Optional[str],
        waitlist_id: Optional[str],
        channel: str,
        template_name: str,
        phone_hash: str,
        send_status: str,
        provider_response: dict,
    ) -> None:
        try:
            from modules.sdk.db import generate_uuid
            self.db.execute(
                text(
                    "INSERT INTO hcs_notification_log "
                    "(id,tenant_id,appointment_id,waitlist_id,channel,template_name,"
                    "recipient_phone_hash,status,provider_response,created_at) "
                    "VALUES (:id,:tid,:aid,:wid,:ch,:tpl,:ph,:st,:resp::jsonb,NOW())"
                ),
                dict(
                    id=str(generate_uuid()), tid=self.tenant_id,
                    aid=appointment_id, wid=waitlist_id,
                    ch=channel, tpl=template_name, ph=phone_hash,
                    st=send_status, resp=json.dumps(provider_response),
                ),
            )
            self.db.commit()
        except Exception as exc:
            logger.error("Failed to log notification: %s", exc, exc_info=True)

    def _build_appt_context(self, appt: dict) -> dict:
        branch = self.db.execute(
            text("SELECT branch_name FROM hc_branches WHERE id=:id LIMIT 1"),
            {"id": appt["branch_id"]},
        ).mappings().one_or_none()
        clinic_name = branch["branch_name"] if branch else "Klinik"
        branch_name = branch["branch_name"] if branch else ""
        scheduled_at = appt.get("scheduled_at")
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at)
        date_str = scheduled_at.strftime("%d %B %Y") if scheduled_at else ""
        time_str = scheduled_at.strftime("%H:%M") if scheduled_at else ""
        return {"clinic_name": clinic_name, "branch_name": branch_name, "date": date_str, "time": time_str}

    def _build_slot_context(self, slot: dict) -> dict:
        branch = self.db.execute(
            text("SELECT branch_name FROM hc_branches WHERE id=:id LIMIT 1"),
            {"id": slot["branch_id"]},
        ).mappings().one_or_none()
        clinic_name = branch["branch_name"] if branch else "Klinik"
        branch_name = branch["branch_name"] if branch else ""
        date_str = str(slot.get("slot_date", ""))
        time_str = str(slot.get("start_time", ""))[:5]
        return {"clinic_name": clinic_name, "branch_name": branch_name, "date": date_str, "time": time_str}


__all__ = ["NotificationService"]
