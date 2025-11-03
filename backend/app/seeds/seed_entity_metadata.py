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
                {"field": "email", "label": "Email", "type": "text", "sortable": True, "searchable": True},
                {"field": "full_name", "label": "Full Name", "type": "text", "sortable": True, "searchable": True},
                {"field": "is_active", "label": "Status", "type": "badge", "sortable": True},
                {"field": "created_at", "label": "Created", "type": "date", "sortable": True},
            ],
            "default_sort": [["created_at", "desc"]],
            "page_size": 25,
            "enable_search": True,
            "enable_filters": True,
            "enable_export": True,
        }),
        form_config=json.dumps({
            "sections": [
                {
                    "title": "Basic Information",
                    "fields": [
                        {"name": "email", "label": "Email", "type": "email", "required": True},
                        {"name": "full_name", "label": "Full Name", "type": "text", "required": True},
                        {"name": "password", "label": "Password", "type": "password", "required": True, "create_only": True},
                    ]
                },
                {
                    "title": "Status",
                    "fields": [
                        {"name": "is_active", "label": "Active", "type": "checkbox", "default": True},
                    ]
                }
            ],
            "layout": "vertical",
            "submit_label": "Save User",
        }),
        permissions=json.dumps({
            "create": "users:create",
            "read": "users:read",
            "update": "users:update",
            "delete": "users:delete",
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
                {"field": "name", "label": "Company Name", "type": "text", "sortable": True, "searchable": True},
                {"field": "code", "label": "Code", "type": "text", "sortable": True, "searchable": True},
                {"field": "industry", "label": "Industry", "type": "text", "sortable": True},
                {"field": "is_active", "label": "Status", "type": "badge", "sortable": True},
                {"field": "created_at", "label": "Created", "type": "date", "sortable": True},
            ],
            "default_sort": [["name", "asc"]],
            "page_size": 25,
            "enable_search": True,
            "enable_filters": True,
            "enable_export": True,
        }),
        form_config=json.dumps({
            "sections": [
                {
                    "title": "Basic Information",
                    "fields": [
                        {"name": "name", "label": "Company Name", "type": "text", "required": True},
                        {"name": "code", "label": "Code", "type": "text", "required": True},
                        {"name": "industry", "label": "Industry", "type": "text"},
                        {"name": "description", "label": "Description", "type": "textarea"},
                    ]
                },
                {
                    "title": "Contact Information",
                    "fields": [
                        {"name": "email", "label": "Email", "type": "email"},
                        {"name": "phone", "label": "Phone", "type": "tel"},
                        {"name": "website", "label": "Website", "type": "url"},
                    ]
                },
                {
                    "title": "Status",
                    "fields": [
                        {"name": "is_active", "label": "Active", "type": "checkbox", "default": True},
                    ]
                }
            ],
            "layout": "vertical",
            "submit_label": "Save Company",
        }),
        permissions=json.dumps({
            "create": "companies:create",
            "read": "companies:read",
            "update": "companies:update",
            "delete": "companies:delete",
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
                {"field": "name", "label": "Branch Name", "type": "text", "sortable": True, "searchable": True},
                {"field": "code", "label": "Code", "type": "text", "sortable": True, "searchable": True},
                {"field": "city", "label": "City", "type": "text", "sortable": True},
                {"field": "is_headquarters", "label": "HQ", "type": "badge", "sortable": True},
                {"field": "is_active", "label": "Status", "type": "badge", "sortable": True},
                {"field": "created_at", "label": "Created", "type": "date", "sortable": True},
            ],
            "default_sort": [["name", "asc"]],
            "page_size": 25,
            "enable_search": True,
            "enable_filters": True,
            "enable_export": True,
        }),
        form_config=json.dumps({
            "sections": [
                {
                    "title": "Basic Information",
                    "fields": [
                        {"name": "name", "label": "Branch Name", "type": "text", "required": True},
                        {"name": "code", "label": "Code", "type": "text", "required": True},
                        {"name": "description", "label": "Description", "type": "textarea"},
                        {"name": "is_headquarters", "label": "Headquarters", "type": "checkbox", "default": False},
                    ]
                },
                {
                    "title": "Contact Information",
                    "fields": [
                        {"name": "email", "label": "Email", "type": "email"},
                        {"name": "phone", "label": "Phone", "type": "tel"},
                    ]
                },
                {
                    "title": "Address",
                    "fields": [
                        {"name": "address_line1", "label": "Address Line 1", "type": "text"},
                        {"name": "address_line2", "label": "Address Line 2", "type": "text"},
                        {"name": "city", "label": "City", "type": "text"},
                        {"name": "state", "label": "State/Province", "type": "text"},
                        {"name": "postal_code", "label": "Postal Code", "type": "text"},
                        {"name": "country", "label": "Country", "type": "text"},
                    ]
                },
                {
                    "title": "Status",
                    "fields": [
                        {"name": "is_active", "label": "Active", "type": "checkbox", "default": True},
                    ]
                }
            ],
            "layout": "vertical",
            "submit_label": "Save Branch",
        }),
        permissions=json.dumps({
            "create": "branches:create",
            "read": "branches:read",
            "update": "branches:update",
            "delete": "branches:delete",
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
                {"field": "name", "label": "Department Name", "type": "text", "sortable": True, "searchable": True},
                {"field": "code", "label": "Code", "type": "text", "sortable": True, "searchable": True},
                {"field": "description", "label": "Description", "type": "text"},
                {"field": "is_active", "label": "Status", "type": "badge", "sortable": True},
                {"field": "created_at", "label": "Created", "type": "date", "sortable": True},
            ],
            "default_sort": [["name", "asc"]],
            "page_size": 25,
            "enable_search": True,
            "enable_filters": True,
            "enable_export": True,
        }),
        form_config=json.dumps({
            "sections": [
                {
                    "title": "Basic Information",
                    "fields": [
                        {"name": "name", "label": "Department Name", "type": "text", "required": True},
                        {"name": "code", "label": "Code", "type": "text", "required": True},
                        {"name": "description", "label": "Description", "type": "textarea"},
                    ]
                },
                {
                    "title": "Status",
                    "fields": [
                        {"name": "is_active", "label": "Active", "type": "checkbox", "default": True},
                    ]
                }
            ],
            "layout": "vertical",
            "submit_label": "Save Department",
        }),
        permissions=json.dumps({
            "create": "departments:create",
            "read": "departments:read",
            "update": "departments:update",
            "delete": "departments:delete",
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
        else:
            print("  - Users metadata already exists")

        if "companies" not in existing_names:
            print("  ✓ Creating companies metadata")
            create_companies_metadata(db)
        else:
            print("  - Companies metadata already exists")

        if "branches" not in existing_names:
            print("  ✓ Creating branches metadata")
            create_branches_metadata(db)
        else:
            print("  - Branches metadata already exists")

        if "departments" not in existing_names:
            print("  ✓ Creating departments metadata")
            create_departments_metadata(db)
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
