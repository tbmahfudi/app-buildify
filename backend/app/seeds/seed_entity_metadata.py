"""
Seed Entity Metadata for Core Entities

This script creates metadata definitions for core system entities:
- Users
- Companies
- Branches
- Departments

The metadata defines table/grid configuration and form configuration for each entity.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.metadata import EntityMetadata


def create_users_metadata(db: Session):
    """Create metadata for users entity"""
    metadata = EntityMetadata(
        entity_name="users",
        display_name="Users",
        description="System users with roles and permissions",
        icon="bi-people-fill",
        table_config=json.dumps({
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
        }),
        form_config=json.dumps({
            "fields": [
                {"field": "email", "title": "Email", "type": "email", "required": True},
                {"field": "full_name", "title": "Full Name", "type": "text", "required": True},
                {"field": "password", "title": "Password", "type": "password", "required": True},
                {"field": "is_active", "title": "Active", "type": "boolean", "default": True},
            ],
            "layout": "vertical",
            "submit_button_text": "Save User",
            "cancel_button_text": "Cancel",
        }),
        permissions=json.dumps({
            "create": ["users:create"],
            "read": ["users:read"],
            "update": ["users:update"],
            "delete": ["users:delete"],
        }),
        version=1,
        is_active=True,
        is_system=True,
    )

    db.add(metadata)


def create_companies_metadata(db: Session):
    """Create metadata for companies entity"""
    metadata = EntityMetadata(
        entity_name="companies",
        display_name="Companies",
        description="Organizations and companies in the system",
        icon="bi-building",
        table_config=json.dumps({
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
        }),
        form_config=json.dumps({
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
        }),
        permissions=json.dumps({
            "create": ["companies:create"],
            "read": ["companies:read"],
            "update": ["companies:update"],
            "delete": ["companies:delete"],
        }),
        version=1,
        is_active=True,
        is_system=True,
    )

    db.add(metadata)


def create_branches_metadata(db: Session):
    """Create metadata for branches entity"""
    metadata = EntityMetadata(
        entity_name="branches",
        display_name="Branches",
        description="Company branches and locations",
        icon="bi-diagram-3",
        table_config=json.dumps({
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
        }),
        form_config=json.dumps({
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
        }),
        permissions=json.dumps({
            "create": ["branches:create"],
            "read": ["branches:read"],
            "update": ["branches:update"],
            "delete": ["branches:delete"],
        }),
        version=1,
        is_active=True,
        is_system=True,
    )

    db.add(metadata)


def create_departments_metadata(db: Session):
    """Create metadata for departments entity"""
    metadata = EntityMetadata(
        entity_name="departments",
        display_name="Departments",
        description="Organizational departments",
        icon="bi-people",
        table_config=json.dumps({
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
        }),
        form_config=json.dumps({
            "fields": [
                {"field": "name", "title": "Department Name", "type": "text", "required": True},
                {"field": "code", "title": "Code", "type": "text", "required": True},
                {"field": "description", "title": "Description", "type": "text"},
                {"field": "is_active", "title": "Active", "type": "boolean", "default": True},
            ],
            "layout": "vertical",
            "submit_button_text": "Save Department",
            "cancel_button_text": "Cancel",
        }),
        permissions=json.dumps({
            "create": ["departments:create"],
            "read": ["departments:read"],
            "update": ["departments:update"],
            "delete": ["departments:delete"],
        }),
        version=1,
        is_active=True,
        is_system=True,
    )

    db.add(metadata)


def seed_entity_metadata():
    """Seed all entity metadata"""
    db = SessionLocal()

    try:
        print("🌱 Seeding entity metadata...")

        # Check if metadata already exists
        existing = db.query(EntityMetadata).filter(
            EntityMetadata.entity_name.in_(["users", "companies", "branches", "departments"])
        ).all()

        existing_names = {m.entity_name for m in existing}

        # Create metadata for entities that don't exist
        if "users" not in existing_names:
            print("  ✓ Creating users metadata")
            create_users_metadata(db)
            db.flush()  # Force ID generation immediately
        else:
            print("  - Users metadata already exists")

        if "companies" not in existing_names:
            print("  ✓ Creating companies metadata")
            create_companies_metadata(db)
            db.flush()  # Force ID generation immediately
        else:
            print("  - Companies metadata already exists")

        if "branches" not in existing_names:
            print("  ✓ Creating branches metadata")
            create_branches_metadata(db)
            db.flush()  # Force ID generation immediately
        else:
            print("  - Branches metadata already exists")

        if "departments" not in existing_names:
            print("  ✓ Creating departments metadata")
            create_departments_metadata(db)
            db.flush()  # Force ID generation immediately
        else:
            print("  - Departments metadata already exists")

        db.commit()
        print("✅ Entity metadata seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding entity metadata: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_entity_metadata()
