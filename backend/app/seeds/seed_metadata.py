"""Seed metadata for core entities"""
import os
import uuid
import json
from sqlalchemy import create_engine, text

DB_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DB_URL, future=True)

# Company metadata
COMPANY_METADATA = {
    "entity_name": "companies",
    "display_name": "Companies",
    "description": "Manage companies in the organization",
    "icon": "building",
    "table_config": json.dumps({
        "columns": [
            {"field": "code", "title": "Code", "sortable": True, "filterable": True, "width": 120},
            {"field": "name", "title": "Name", "sortable": True, "filterable": True},
            {"field": "created_at", "title": "Created", "sortable": True, "format": "date"}
        ],
        "default_sort": [["code", "asc"]],
        "page_size": 25,
        "actions": ["view", "edit", "delete"]
    }),
    "form_config": json.dumps({
        "fields": [
            {
                "field": "code",
                "title": "Company Code",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 50}
            },
            {
                "field": "name",
                "title": "Company Name",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 255}
            }
        ],
        "layout": "vertical"
    }),
    "permissions": json.dumps({
        "admin": ["create", "read", "update", "delete"],
        "user": ["read"],
        "viewer": ["read"]
    })
}

# Branch metadata
BRANCH_METADATA = {
    "entity_name": "branches",
    "display_name": "Branches",
    "description": "Manage branches within companies",
    "icon": "building-2",
    "table_config": json.dumps({
        "columns": [
            {"field": "code", "title": "Code", "sortable": True, "filterable": True, "width": 120},
            {"field": "name", "title": "Name", "sortable": True, "filterable": True},
            {"field": "company_id", "title": "Company", "sortable": True, "filterable": True},
            {"field": "created_at", "title": "Created", "sortable": True, "format": "date"}
        ],
        "default_sort": [["code", "asc"]],
        "page_size": 25,
        "actions": ["view", "edit", "delete"]
    }),
    "form_config": json.dumps({
        "fields": [
            {
                "field": "company_id",
                "title": "Company",
                "type": "select",
                "required": True,
                "widget": "company-select"
            },
            {
                "field": "code",
                "title": "Branch Code",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 50}
            },
            {
                "field": "name",
                "title": "Branch Name",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 255}
            }
        ],
        "layout": "vertical"
    }),
    "permissions": json.dumps({
        "admin": ["create", "read", "update", "delete"],
        "user": ["read"],
        "viewer": ["read"]
    })
}

# Department metadata
DEPARTMENT_METADATA = {
    "entity_name": "departments",
    "display_name": "Departments",
    "description": "Manage departments within companies and branches",
    "icon": "users",
    "table_config": json.dumps({
        "columns": [
            {"field": "code", "title": "Code", "sortable": True, "filterable": True, "width": 120},
            {"field": "name", "title": "Name", "sortable": True, "filterable": True},
            {"field": "company_id", "title": "Company", "sortable": True, "filterable": True},
            {"field": "branch_id", "title": "Branch", "sortable": True, "filterable": True},
            {"field": "created_at", "title": "Created", "sortable": True, "format": "date"}
        ],
        "default_sort": [["code", "asc"]],
        "page_size": 25,
        "actions": ["view", "edit", "delete"]
    }),
    "form_config": json.dumps({
        "fields": [
            {
                "field": "company_id",
                "title": "Company",
                "type": "select",
                "required": True,
                "widget": "company-select"
            },
            {
                "field": "branch_id",
                "title": "Branch",
                "type": "select",
                "required": False,
                "widget": "branch-select"
            },
            {
                "field": "code",
                "title": "Department Code",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 50}
            },
            {
                "field": "name",
                "title": "Department Name",
                "type": "text",
                "required": True,
                "validators": {"maxLength": 255}
            }
        ],
        "layout": "vertical"
    }),
    "permissions": json.dumps({
        "admin": ["create", "read", "update", "delete"],
        "user": ["read"],
        "viewer": ["read"]
    })
}

def run():
    with engine.begin() as conn:
        # Insert company metadata
        conn.execute(text("""
            INSERT INTO entity_metadata (
                id, entity_name, display_name, description, icon,
                table_config, form_config, permissions,
                version, is_active, is_system
            ) VALUES (
                :id, :entity_name, :display_name, :description, :icon,
                :table_config, :form_config, :permissions,
                :version, :is_active, :is_system
            )
        """), dict(
            id=str(uuid.uuid4()),
            version=1,
            is_active=True,
            is_system=True,
            **COMPANY_METADATA
        ))
        
        # Insert branch metadata
        conn.execute(text("""
            INSERT INTO entity_metadata (
                id, entity_name, display_name, description, icon,
                table_config, form_config, permissions,
                version, is_active, is_system
            ) VALUES (
                :id, :entity_name, :display_name, :description, :icon,
                :table_config, :form_config, :permissions,
                :version, :is_active, :is_system
            )
        """), dict(
            id=str(uuid.uuid4()),
            version=1,
            is_active=True,
            is_system=True,
            **BRANCH_METADATA
        ))
        
        # Insert department metadata
        conn.execute(text("""
            INSERT INTO entity_metadata (
                id, entity_name, display_name, description, icon,
                table_config, form_config, permissions,
                version, is_active, is_system
            ) VALUES (
                :id, :entity_name, :display_name, :description, :icon,
                :table_config, :form_config, :permissions,
                :version, :is_active, :is_system
            )
        """), dict(
            id=str(uuid.uuid4()),
            version=1,
            is_active=True,
            is_system=True,
            **DEPARTMENT_METADATA
        ))
    
    print("Metadata seed completed.")
    print("\nSeeded metadata for:")
    print("  - companies")
    print("  - branches")
    print("  - departments")

if __name__ == "__main__":
    run()