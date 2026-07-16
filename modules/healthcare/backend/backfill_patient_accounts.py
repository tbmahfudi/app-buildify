"""
Backfill script: give legacy phone/OTP-only patients a platform account (ADR-HC-009 §D7).

Before ADR-011, a patient existed only as an ``hc_patients`` row authenticated by phone+OTP;
there was no platform ``users`` row and therefore no password, no MFA, and no RBAC. D7
migrates those patients onto platform accounts so the one auth stack covers everyone —
which is also what unblocks removing the module's OTP-login path (ADR-011 S6b, GH#692).

Run inside the HEALTHCARE container (it has the PHI key and the hc models; the backend
container does not decrypt PHI):

    docker exec app_buildify_healthcare python3 \
        /app/modules/healthcare/backfill_patient_accounts.py --dry-run
    docker exec app_buildify_healthcare python3 \
        /app/modules/healthcare/backfill_patient_accounts.py --apply

Idempotent: a patient that already has an account is skipped, so re-running is a no-op and
a half-finished run is safe to resume.

WHO IS MIGRATED — self-owned legacy patients only::

    user_id IS NULL
    AND NOT EXISTS (owner relationship for this patient)
    AND status='active' AND deleted_at IS NULL

The ``NOT EXISTS(owner)`` clause is load-bearing, not defensive. A **dependent** (a child in
a household) legitimately has ``user_id IS NULL`` — ADR-HC-009 **V-D5** made that column
nullable precisely so dependents exist without a login, and V-D6/V-D7 put their authority in
``hc_patient_relationships`` instead. Minting an account for a dependent would hand a child a
login their guardian is supposed to hold, and would break the household model. So an existing
``role='owner'`` row means "somebody already acts for this patient" → skip.

WHAT EACH MIGRATED PATIENT GETS

* a platform ``User``: ``must_set_password=True``, an **unusable** random password, the
  shared SaaS tenant, their Company, and the manifest-declared ``patients`` group
  (ADR-012 D5 — the group is resolved-or-fail, never skipped);
* ``hc_patients.user_id`` linked to it;
* a ``relationship='self' / role='owner'`` row, so the household model sees them as their
  own account holder from day one;
* a ``patient.migrated_to_platform_user`` audit event.

SYNTHETIC EMAIL — deliberate, not a shortcut. ``users.email`` is NOT NULL + UNIQUE, and a
patient's stored email is *unverified PHI*. Seeding it as the account's login email would
(a) collide whenever that address is already a user, and (b) create a password-reset path
into somebody's medical records for whoever controls that mailbox — bypassing the phone-OTP
proof the claim flow exists to require. So every backfilled account starts on a
non-deliverable ``@patients.invalid`` address (RFC 2606 reserved), and the patient's real
email is captured at claim time, where epic-18 Story 18.9.1 already asks for it
("email (confirm/add)").

The patient then logs in with phone+OTP as they always have; that response now carries
``must_set_password`` (18.9.1), and the portal routes them to ``/patients/auth/claim-account``.
"""

from __future__ import annotations

import argparse
import logging
import os
import secrets
import sys
from datetime import datetime

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("backfill_patient_accounts")

MODULE = "healthcare"
SYNTHETIC_EMAIL_DOMAIN = os.environ.get("PATIENT_SYNTHETIC_EMAIL_DOMAIN", "patients.invalid")

# Patients with no account of their own and no one acting for them. See the module
# docstring for why NOT EXISTS(owner) is required rather than merely user_id IS NULL.
TARGET_SQL = text(
    """
    SELECT p.id, p.company_id, p.tenant_id
    FROM hc_patients p
    WHERE p.user_id IS NULL
      AND p.status = 'active'
      AND p.deleted_at IS NULL
      AND NOT EXISTS (
          SELECT 1 FROM hc_patient_relationships r
          WHERE r.patient_id = p.id AND r.role = 'owner'
      )
    ORDER BY p.created_at
    """
)


def _synthetic_email(patient_id: str) -> str:
    """A unique, non-deliverable placeholder login (replaced by the real one at claim)."""
    return f"patient-{patient_id}@{SYNTHETIC_EMAIL_DOMAIN}"


def _unusable_password() -> str:
    """A random secret nobody holds — and one that always satisfies the strength policy.

    ``users.hashed_password`` is NOT NULL, so a backfilled account cannot simply have "no
    password" — it gets one that cannot be guessed and is never shown to anyone. Combined
    with ``must_set_password=True`` this makes password login fail as a plain wrong-password
    (GH#693 moved that check after verify_password, so it does not leak the account's
    existence either).

    The ``Aa1!`` suffix is not decoration. ``create_patient_account`` runs every password
    through the tenant's strength policy, and ``token_urlsafe`` output is only [A-Za-z0-9_-]
    — so it contains a special character purely by luck, and a run would fail on a random
    subset of patients with "must contain at least one special character". (Observed: 1 of 3
    on the first live run.) Pinning one character of each class makes the generator
    policy-proof rather than probabilistically compliant. Entropy is unaffected — the
    48-byte random prefix carries it.
    """
    return secrets.token_urlsafe(48) + "Aa1!"


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill legacy patients onto platform accounts (D7)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Report what would change; write nothing")
    group.add_argument("--apply", action="store_true", help="Perform the backfill")
    parser.add_argument("--limit", type=int, default=0, help="Cap the number migrated (0 = all)")
    args = parser.parse_args()

    from app.core.db import SessionLocal
    from app.core.module_system.tenancy import resolve_shared_tenant_id
    from app.services.account_service import AccountExistsError, create_patient_account
    from app.services.module_rbac_service import EndUserRBACNotProvisioned
    from modules.healthcare.models import HCPatient, HCPatientRelationship
    from modules.healthcare.sdk.phi_audit import write_event_audit

    db = SessionLocal()
    migrated = skipped = failed = 0
    try:
        # Fail fast and clearly if ADR-012 provisioning has not run: every account we are
        # about to mint needs that group, and finding out on patient #1 of 5000 is worse
        # than finding out now.
        shared_tenant_id = resolve_shared_tenant_id(db, module=MODULE)

        rows = db.execute(TARGET_SQL).fetchall()
        if args.limit:
            rows = rows[: args.limit]
        logger.info("%d legacy patient(s) to migrate (self-owned, no account)", len(rows))

        if args.dry_run:
            for r in rows:
                logger.info(
                    "WOULD migrate patient=%s company=%s -> user(%s, must_set_password=True) "
                    "+ self/owner relationship",
                    r[0],
                    r[1],
                    _synthetic_email(str(r[0])),
                )
            logger.info("dry run: nothing written")
            return 0

        for r in rows:
            patient_id, company_id, patient_tenant_id = str(r[0]), str(r[1]), str(r[2])

            patient = db.query(HCPatient).filter(HCPatient.id == patient_id).first()
            if patient is None or patient.user_id:
                skipped += 1
                continue

            try:
                # One SAVEPOINT per patient: a single bad row (e.g. a colliding synthetic
                # address) must not abort the whole run or leave a half-migrated patient.
                with db.begin_nested():
                    user = create_patient_account(
                        db,
                        tenant_id=shared_tenant_id,
                        email=_synthetic_email(patient_id),
                        password=_unusable_password(),
                        # PHI columns are EncryptedPHIType — the ORM decrypts on read.
                        full_name=patient.full_name,
                        phone=patient.phone,
                        default_company_id=company_id,
                        end_user_module=MODULE,
                        must_set_password=True,
                    )

                    patient.user_id = str(user.id)

                    db.add(
                        HCPatientRelationship(
                            tenant_id=patient_tenant_id,
                            account_user_id=str(user.id),
                            patient_id=patient_id,
                            relationship="self",
                            role="owner",
                            status="active",
                            basis="self",
                            granted_by=str(user.id),
                            granted_at=datetime.utcnow(),
                        )
                    )

                    write_event_audit(
                        db=db,
                        actor_id="system",
                        actor_type="system",
                        event_type="patient.migrated_to_platform_user",
                        entity_type="hc_patient",
                        entity_id=patient_id,
                        tenant_id=patient_tenant_id,
                        metadata={"user_id": str(user.id), "company_id": company_id},
                    )

                db.commit()
                migrated += 1
                logger.info("migrated patient=%s -> user=%s", patient_id, user.id)

            except (AccountExistsError, EndUserRBACNotProvisioned) as exc:
                db.rollback()
                failed += 1
                logger.error("patient=%s FAILED: %s", patient_id, exc)
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                failed += 1
                logger.error("patient=%s FAILED: %s", patient_id, exc, exc_info=True)

        logger.info("done: migrated=%d skipped=%d failed=%d", migrated, skipped, failed)
        return 1 if failed else 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
