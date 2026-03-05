"""
Seed UI Config for Core System Entities

This script seeds table_config, form_config, and permissions directly onto
EntityDefinition rows for core system entities (users, companies, branches,
departments).  The entity_metadata table no longer exists; UI config now lives
on entity_definitions.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.data_model import EntityDefinition


# ---------------------------------------------------------------------------
# Per-entity config payloads
# ---------------------------------------------------------------------------

_ENTITY_CONFIGS = {
    "users": {
        "table_config": {
            "columns": [
                {"field": "email", "title": "Email", "sortable": True, "filterable": True},
                {"field": "full_name", "title": "Full Name", "sortable": True, "filterable": True},
                {"field": "is_active", "title": "Status", "sortable": True, "filterable": True},
                {"field": "created_at", "title": "Created", "sortable": True, "filterable": True, "format": "date"},
            ],
            "default_sort": [["created_at", "desc"]],
            "page_size": 25,
            "actions": ["view", "edit", "delete"],
            "selectable": True,
            "exportable": True,
        },
        "form_config": {
            "fields": [
                {"field": "email", "title": "Email", "type": "email", "required": True},
                {"field": "full_name", "title": "Full Name", "type": "text", "required": True},
                {"field": "password", "title": "Password", "type": "password", "required": True},
                {"field": "is_active", "title": "Active", "type": "boolean", "default": True},
            ],
            "layout": "vertical",
            "submit_button_text": "Save User",
            "cancel_button_text": "Cancel",
        },
        "permissions": {
            "create": ["users:create"],
            "read": ["users:read"],
            "update": ["users:update"],
            "delete": ["users:delete"],
        },
    },
    "companies": {
        "table_config": {
            "columns": [
                {"field": "name", "title": "Company Name", "sortable": True, "filterable": True},
                {"field": "code", "title": "Code", "sortable": True, "filterable": True},
                {"field": "industry", "title": "Industry", "sortable": True, "filterable": True},
                {"field": "is_active", "title": "Status", "sortable": True, "filterable": True},
                {"field": "created_at", "title": "Created", "sortable": True, "filterable": True, "format": "date"},
            ],
            "default_sort": [["name", "asc"]],
            "page_size": 25,
            "actions": ["view", "edit", "delete"],
            "selectable": True,
            "exportable": True,
        },
        "form_config": {
            "fields": [
                {"field": "name", "title": "Company Name", "type": "text", "required": True},
                {"field": "code", "title": "Code", "type": "text", "required": True},
                {"field": "industry", "title": "Industry", "type": "text"},
                {"field": "description", "title": "Description", "type": "text"},
                {"field": "email", "title": "Email", "type": "email"},
                {"field": "phone", "title": "Phone", "type": "text"},
                {"field": "website", "title": "Website", "type": "text"},
                {"field": "is_active", "title": "Active", "type": "boolean", "default": True},
            ],
            "layout": "vertical",
            "submit_button_text": "Save Company",
            "cancel_button_text": "Cancel",
        },
        "permissions": {
            "create": ["companies:create"],
            "read": ["companies:read"],
            "update": ["companies:update"],
            "delete": ["companies:delete"],
        },
    },
    "branches": {
        "table_config": {
            "columns": [
                {"field": "name", "title": "Branch Name", "sortable": True, "filterable": True},
                {"field": "code", "title": "Code", "sortable": True, "filterable": True},
                {"field": "city", "title": "City", "sortable": True, "filterable": True},
                {"field": "is_headquarters", "title": "HQ", "sortable": True, "filterable": True},
                {"field": "is_active", "title": "Status", "sortable": True, "filterable": True},
                {"field": "created_at", "title": "Created", "sortable": True, "filterable": True, "format": "date"},
            ],
            "default_sort": [["name", "asc"]],
            "page_size": 25,
            "actions": ["view", "edit", "delete"],
            "selectable": True,
            "exportable": True,
        },
        "form_config": {
            "fields": [
                {"field": "name", "title": "Branch Name", "type": "text", "required": True},
                {"field": "code", "title": "Code", "type": "text", "required": True},
                {"field": "description", "title": "Description", "type": "text"},
                {"field": "is_headquarters", "title": "Headquarters", "type": "boolean", "default": False},
                {"field": "email", "title": "Email", "type": "email"},
                {"field": "phone", "title": "Phone", "type": "text"},
                {"field": "address_line1", "title": "Address Line 1", "type": "text"},
                {"field": "address_line2", "title": "Address Line 2", "type": "text"},
                {"field": "city", "title": "City", "type": "text"},
                {"field": "state", "title": "State/Province", "type": "text"},
                {"field": "postal_code", "title": "Postal Code", "type": "text"},
                {"field": "country", "title": "Country", "type": "text"},
                {"field": "is_active", "title": "Active", "type": "boolean", "default": True},
            ],
            "layout": "vertical",
            "submit_button_text": "Save Branch",
            "cancel_button_text": "Cancel",
        },
        "permissions": {
            "create": ["branches:create"],
            "read": ["branches:read"],
            "update": ["branches:update"],
            "delete": ["branches:delete"],
        },
    },
    "departments": {
        "table_config": {
            "columns": [
                {"field": "name", "title": "Department Name", "sortable": True, "filterable": True},
                {"field": "code", "title": "Code", "sortable": True, "filterable": True},
                {"field": "description", "title": "Description", "sortable": False, "filterable": True},
                {"field": "is_active", "title": "Status", "sortable": True, "filterable": True},
                {"field": "created_at", "title": "Created", "sortable": True, "filterable": True, "format": "date"},
            ],
            "default_sort": [["name", "asc"]],
            "page_size": 25,
            "actions": ["view", "edit", "delete"],
            "selectable": True,
            "exportable": True,
        },
        "form_config": {
            "fields": [
                {"field": "name", "title": "Department Name", "type": "text", "required": True},
                {"field": "code", "title": "Code", "type": "text", "required": True},
                {"field": "description", "title": "Description", "type": "text"},
                {"field": "is_active", "title": "Active", "type": "boolean", "default": True},
            ],
            "layout": "vertical",
            "submit_button_text": "Save Department",
            "cancel_button_text": "Cancel",
        },
        "permissions": {
            "create": ["departments:create"],
            "read": ["departments:read"],
            "update": ["departments:update"],
            "delete": ["departments:delete"],
        },
    },
}


def seed_entity_metadata():
    """Seed UI config onto EntityDefinition rows for core system entities."""
    db = SessionLocal()

    try:
        print("Seeding entity UI config...")

        entity_names = list(_ENTITY_CONFIGS.keys())
        entities = db.query(EntityDefinition).filter(
            EntityDefinition.name.in_(entity_names)
        ).all()
        entity_map = {e.name: e for e in entities}

        for name, config in _ENTITY_CONFIGS.items():
            entity = entity_map.get(name)
            if entity is None:
                print(f"  - Entity '{name}' not found in entity_definitions, skipping")
                continue

            if entity.table_config is not None:
                print(f"  - UI config for '{name}' already exists, skipping")
                continue

            entity.table_config = config["table_config"]
            entity.form_config = config["form_config"]
            entity.permissions = config["permissions"]
            print(f"  + Seeded UI config for '{name}'")

        db.commit()
        print("Entity UI config seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding entity UI config: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_entity_metadata()
