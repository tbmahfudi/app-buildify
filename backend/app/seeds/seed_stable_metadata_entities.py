"""
Seed the "stable" entity definitions the e2e metadata suite expects to exist:
SLAPolicy, TicketCategory, SupportTicket.

Creates them per tenant as *published* EntityDefinition rows with UI config so
GET /metadata/entities lists them and the get/update/regenerate endpoints
resolve them. These back the metadata/definition layer only — no physical
tables are generated. Idempotent (skips entities that already exist).
"""
from app.core.db import SessionLocal
from app.models.data_model import EntityDefinition
from app.models.tenant import Tenant
from app.models.user import User
from app.models.base import generate_uuid


def _cfg(field_titles):
    cols = [{"field": f, "title": t} for f, t in field_titles]
    return (
        {"columns": cols, "page_size": 25},
        {"fields": [{"field": f, "title": t, "type": "text"} for f, t in field_titles], "layout": "vertical"},
    )


_STABLE_ENTITIES = [
    {"name": "SLAPolicy", "label": "SLA Policy", "plural_label": "SLA Policies",
     "table_name": "sla_policies", "category": "Support",
     "fields": [("name", "Name"), ("response_minutes", "Response Minutes")]},
    {"name": "TicketCategory", "label": "Ticket Category", "plural_label": "Ticket Categories",
     "table_name": "ticket_categories", "category": "Support",
     "fields": [("name", "Name"), ("code", "Code")]},
    {"name": "SupportTicket", "label": "Support Ticket", "plural_label": "Support Tickets",
     "table_name": "support_tickets", "category": "Support",
     "fields": [("subject", "Subject"), ("status", "Status")]},
]


def seed_stable_metadata_entities():
    db = SessionLocal()
    created = 0
    try:
        tenants = db.query(Tenant).all()
        for tenant in tenants:
            admin = db.query(User).filter(User.tenant_id == tenant.id).first()
            uid = str(admin.id) if admin else None
            for e in _STABLE_ENTITIES:
                exists = db.query(EntityDefinition).filter(
                    EntityDefinition.tenant_id == tenant.id,
                    EntityDefinition.name == e["name"],
                    EntityDefinition.is_deleted == False,
                ).first()
                if exists:
                    continue
                table_config, form_config = _cfg(e["fields"])
                db.add(EntityDefinition(
                    id=str(generate_uuid()),
                    tenant_id=tenant.id,
                    created_by=uid,
                    updated_by=uid,
                    name=e["name"],
                    label=e["label"],
                    plural_label=e.get("plural_label"),
                    description=f"{e['label']} (seeded for metadata e2e coverage)",
                    table_name=e["table_name"],
                    # 'custom' (not 'system') so the metadata update endpoint allows
                    # display_name edits — the e2e suite exercises that path.
                    entity_type="custom",
                    category=e.get("category"),
                    status="published",
                    is_active=True,
                    table_config=table_config,
                    form_config=form_config,
                ))
                created += 1
        db.commit()
        print(f"  ✓ Seeded {created} stable metadata entit(ies)")
    except Exception as exc:  # pragma: no cover - defensive
        db.rollback()
        print(f"  ⚠ stable metadata entity seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_stable_metadata_entities()
