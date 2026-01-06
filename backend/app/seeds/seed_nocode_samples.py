"""
Phase 1 No-Code Platform Sample Data Seed
==========================================
Creates sample data for all no-code features:
- Data Model Designer: Sample entities with fields
- Workflow Designer: Sample workflows
- Automation System: Sample automation rules
- Lookup Configuration: Sample lookups

Run: python -m app.seeds.seed_nocode_samples
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.data_model import EntityDefinition, FieldDefinition, RelationshipDefinition
from app.models.workflow import WorkflowDefinition, WorkflowState, WorkflowTransition
from app.models.automation import AutomationRule
from app.models.lookup import LookupConfiguration
from app.models.tenant import Tenant
from app.models.user import User
from app.models.base import generate_uuid


def get_or_create_tenant(db: Session):
    """Get the first tenant or create a default one."""
    tenant = db.query(Tenant).filter(
        Tenant.is_active == True,
        Tenant.deleted_at == None
    ).first()

    if not tenant:
        print("⚠️  No tenant found. Creating default tenant...")
        tenant = Tenant(
            id=str(generate_uuid()),
            name="Default Tenant",
            code="default",
            subscription_status="active",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(tenant)
        db.commit()
        print(f"  ✅ Created tenant: {tenant.name}")

    return tenant


def get_or_create_user(db: Session, tenant_id: str):
    """Get the first admin user for the tenant."""
    user = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.is_active == True
    ).first()

    if not user:
        print("  ⚠️  Warning: No user found. Some relationships may be incomplete.")
        return None

    return user


def seed_data_model_samples(db: Session, tenant_id: str, user_id: str = None):
    """Seed sample entities and fields for Data Model Designer."""
    print("\n" + "="*80)
    print("DATA MODEL DESIGNER - SAMPLE DATA")
    print("="*80 + "\n")

    entities_data = [
        {
            "name": "customer",
            "label": "Customer",
            "plural_label": "Customers",
            "description": "Customer records with contact information and preferences",
            "table_name": "customers",
            "category": "CRM",
            "icon": "user-circle",
            "is_audited": True,
            "supports_soft_delete": True,
            "supports_attachments": True,
            "status": "published",
            "fields": [
                {"name": "first_name", "label": "First Name", "field_type": "string", "data_type": "VARCHAR", "max_length": 100, "is_required": True},
                {"name": "last_name", "label": "Last Name", "field_type": "string", "data_type": "VARCHAR", "max_length": 100, "is_required": True},
                {"name": "email", "label": "Email", "field_type": "email", "data_type": "VARCHAR", "max_length": 255, "is_required": True, "is_unique": True},
                {"name": "phone", "label": "Phone", "field_type": "phone", "data_type": "VARCHAR", "max_length": 20},
                {"name": "company", "label": "Company", "field_type": "string", "data_type": "VARCHAR", "max_length": 200},
                {"name": "status", "label": "Status", "field_type": "choice", "data_type": "VARCHAR", "default_value": "active", "allowed_values": ["active", "inactive", "prospect"]},
                {"name": "customer_since", "label": "Customer Since", "field_type": "date", "data_type": "DATE"},
                {"name": "lifetime_value", "label": "Lifetime Value", "field_type": "decimal", "data_type": "NUMERIC", "decimal_places": 2},
            ]
        },
        {
            "name": "order",
            "label": "Order",
            "plural_label": "Orders",
            "description": "Sales orders and transactions",
            "table_name": "orders",
            "category": "Sales",
            "icon": "shopping-cart",
            "is_audited": True,
            "supports_soft_delete": True,
            "status": "published",
            "fields": [
                {"name": "order_number", "label": "Order Number", "field_type": "string", "data_type": "VARCHAR", "max_length": 50, "is_required": True, "is_unique": True},
                {"name": "order_date", "label": "Order Date", "field_type": "datetime", "data_type": "TIMESTAMP", "is_required": True, "default_value": "now()"},
                {"name": "total_amount", "label": "Total Amount", "field_type": "decimal", "data_type": "NUMERIC", "is_required": True, "decimal_places": 2},
                {"name": "status", "label": "Status", "field_type": "choice", "data_type": "VARCHAR", "default_value": "pending", "allowed_values": ["pending", "confirmed", "shipped", "delivered", "cancelled"]},
                {"name": "shipping_address", "label": "Shipping Address", "field_type": "text", "data_type": "TEXT"},
                {"name": "notes", "label": "Notes", "field_type": "text", "data_type": "TEXT"},
            ]
        },
        {
            "name": "product",
            "label": "Product",
            "plural_label": "Products",
            "description": "Product catalog with inventory tracking",
            "table_name": "products",
            "category": "Inventory",
            "icon": "package",
            "is_audited": True,
            "supports_soft_delete": True,
            "status": "draft",
            "fields": [
                {"name": "sku", "label": "SKU", "field_type": "string", "data_type": "VARCHAR", "max_length": 50, "is_required": True, "is_unique": True},
                {"name": "name", "label": "Product Name", "field_type": "string", "data_type": "VARCHAR", "max_length": 200, "is_required": True},
                {"name": "description", "label": "Description", "field_type": "text", "data_type": "TEXT"},
                {"name": "price", "label": "Price", "field_type": "decimal", "data_type": "NUMERIC", "is_required": True, "decimal_places": 2},
                {"name": "cost", "label": "Cost", "field_type": "decimal", "data_type": "NUMERIC", "decimal_places": 2},
                {"name": "stock_quantity", "label": "Stock Quantity", "field_type": "integer", "data_type": "INTEGER", "default_value": "0"},
                {"name": "is_active", "label": "Active", "field_type": "boolean", "data_type": "BOOLEAN", "default_value": "true"},
                {"name": "category", "label": "Category", "field_type": "string", "data_type": "VARCHAR", "max_length": 100},
            ]
        },
    ]

    created_entities = {}

    for entity_data in entities_data:
        # Check if entity already exists
        existing = db.query(EntityDefinition).filter(
            EntityDefinition.tenant_id == tenant_id,
            EntityDefinition.name == entity_data["name"],
            EntityDefinition.is_deleted == False
        ).first()

        if existing:
            print(f"  ⏭️  Entity exists: {entity_data['label']}")
            created_entities[entity_data["name"]] = existing
            continue

        # Create entity
        fields_data = entity_data.pop("fields", [])

        entity = EntityDefinition(
            id=str(generate_uuid()),
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **entity_data
        )
        db.add(entity)
        db.flush()

        # Create fields
        for idx, field_data in enumerate(fields_data):
            field = FieldDefinition(
                id=str(generate_uuid()),
                entity_id=entity.id,
                tenant_id=tenant_id,
                display_order=idx + 1,
                is_system=False,
                is_indexed=field_data.get("is_unique", False),
                validation_rules=[],
                **field_data
            )
            db.add(field)

        created_entities[entity_data["name"]] = entity
        print(f"  ✅ Created entity: {entity.label} with {len(fields_data)} fields")

    db.commit()

    return created_entities


def seed_workflow_samples(db: Session, tenant_id: str, user_id: str = None, entities: dict = None):
    """Seed sample workflows."""
    print("\n" + "="*80)
    print("WORKFLOW DESIGNER - SAMPLE DATA")
    print("="*80 + "\n")

    workflows_data = [
        {
            "name": "order_approval",
            "label": "Order Approval Process",
            "description": "Multi-step approval workflow for high-value orders",
            "category": "Sales",
            "trigger_type": "manual",
            "canvas_data": {
                "nodes": [
                    {"id": "start", "type": "start", "position": {"x": 100, "y": 100}},
                    {"id": "review", "type": "task", "position": {"x": 300, "y": 100}, "data": {"label": "Manager Review"}},
                    {"id": "approve", "type": "task", "position": {"x": 500, "y": 100}, "data": {"label": "Finance Approval"}},
                    {"id": "end", "type": "end", "position": {"x": 700, "y": 100}}
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "review"},
                    {"id": "e2", "source": "review", "target": "approve", "label": "Approved"},
                    {"id": "e3", "source": "approve", "target": "end", "label": "Complete"}
                ]
            },
            "states": [
                {"name": "draft", "label": "Draft", "state_type": "start", "color": "gray"},
                {"name": "pending_review", "label": "Pending Manager Review", "state_type": "intermediate", "color": "yellow"},
                {"name": "pending_approval", "label": "Pending Finance Approval", "state_type": "intermediate", "color": "blue"},
                {"name": "approved", "label": "Approved", "state_type": "end", "is_final": True, "color": "green"},
                {"name": "rejected", "label": "Rejected", "state_type": "end", "is_final": True, "color": "red"},
            ],
            "transitions": [
                {"name": "submit", "from_state": "draft", "to_state": "pending_review", "label": "Submit for Review"},
                {"name": "approve_manager", "from_state": "pending_review", "to_state": "pending_approval", "label": "Manager Approved"},
                {"name": "reject_manager", "from_state": "pending_review", "to_state": "rejected", "label": "Manager Rejected"},
                {"name": "approve_finance", "from_state": "pending_approval", "to_state": "approved", "label": "Finance Approved"},
                {"name": "reject_finance", "from_state": "pending_approval", "to_state": "rejected", "label": "Finance Rejected"},
            ]
        },
        {
            "name": "customer_onboarding",
            "label": "Customer Onboarding",
            "description": "Step-by-step customer onboarding process",
            "category": "CRM",
            "trigger_type": "automatic",
            "canvas_data": {
                "nodes": [
                    {"id": "start", "type": "start", "position": {"x": 100, "y": 100}},
                    {"id": "verify", "type": "task", "position": {"x": 300, "y": 100}, "data": {"label": "Verify Information"}},
                    {"id": "setup", "type": "task", "position": {"x": 500, "y": 100}, "data": {"label": "Account Setup"}},
                    {"id": "end", "type": "end", "position": {"x": 700, "y": 100}}
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "verify"},
                    {"id": "e2", "source": "verify", "target": "setup"},
                    {"id": "e3", "source": "setup", "target": "end"}
                ]
            },
            "states": [
                {"name": "new", "label": "New Customer", "state_type": "start", "color": "blue"},
                {"name": "verifying", "label": "Verification in Progress", "state_type": "intermediate", "color": "yellow"},
                {"name": "setting_up", "label": "Setting Up Account", "state_type": "intermediate", "color": "purple"},
                {"name": "active", "label": "Active Customer", "state_type": "end", "is_final": True, "color": "green"},
            ],
            "transitions": [
                {"name": "start_verification", "from_state": "new", "to_state": "verifying", "label": "Start Verification"},
                {"name": "verified", "from_state": "verifying", "to_state": "setting_up", "label": "Verified"},
                {"name": "setup_complete", "from_state": "setting_up", "to_state": "active", "label": "Setup Complete"},
            ]
        }
    ]

    for workflow_data in workflows_data:
        # Check if workflow already exists
        existing = db.query(WorkflowDefinition).filter(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.name == workflow_data["name"],
            WorkflowDefinition.is_deleted == False
        ).first()

        if existing:
            print(f"  ⏭️  Workflow exists: {workflow_data['label']}")
            continue

        states_data = workflow_data.pop("states", [])
        transitions_data = workflow_data.pop("transitions", [])

        # Create workflow
        workflow = WorkflowDefinition(
            id=str(generate_uuid()),
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            is_published=True,
            published_at=datetime.utcnow(),
            **workflow_data
        )
        db.add(workflow)
        db.flush()

        # Create states
        state_map = {}
        for state_data in states_data:
            state = WorkflowState(
                id=str(generate_uuid()),
                workflow_id=workflow.id,
                tenant_id=tenant_id,
                **state_data
            )
            db.add(state)
            state_map[state_data["name"]] = state

        db.flush()

        # Create transitions
        for transition_data in transitions_data:
            from_state_name = transition_data.pop("from_state")
            to_state_name = transition_data.pop("to_state")

            transition = WorkflowTransition(
                id=str(generate_uuid()),
                workflow_id=workflow.id,
                tenant_id=tenant_id,
                from_state_id=state_map[from_state_name].id,
                to_state_id=state_map[to_state_name].id,
                **transition_data
            )
            db.add(transition)

        print(f"  ✅ Created workflow: {workflow.label} with {len(states_data)} states, {len(transitions_data)} transitions")

    db.commit()


def seed_automation_samples(db: Session, tenant_id: str, user_id: str = None, entities: dict = None):
    """Seed sample automation rules."""
    print("\n" + "="*80)
    print("AUTOMATION SYSTEM - SAMPLE DATA")
    print("="*80 + "\n")

    automations_data = [
        {
            "name": "welcome_email",
            "label": "Send Welcome Email to New Customers",
            "description": "Automatically send welcome email when a new customer is created",
            "category": "Customer Engagement",
            "trigger_type": "database_event",
            "event_type": "create",
            "trigger_timing": "after",
            "trigger_config": {
                "entity": "customer",
                "events": ["create"]
            },
            "has_conditions": False,
            "conditions": {},
            "actions": [
                {
                    "type": "send_email",
                    "config": {
                        "to": "{{record.email}}",
                        "subject": "Welcome to Our Platform!",
                        "template": "welcome_customer",
                        "variables": {
                            "customer_name": "{{record.first_name}}"
                        }
                    }
                }
            ],
            "is_active": True,
            "execution_order": 1
        },
        {
            "name": "high_value_order_alert",
            "label": "Alert on High Value Orders",
            "description": "Send notification to sales manager when order exceeds $10,000",
            "category": "Sales",
            "trigger_type": "database_event",
            "event_type": "create",
            "trigger_timing": "after",
            "trigger_config": {
                "entity": "order",
                "events": ["create"]
            },
            "has_conditions": True,
            "conditions": {
                "operator": "and",
                "rules": [
                    {
                        "field": "total_amount",
                        "operator": "greater_than",
                        "value": 10000
                    }
                ]
            },
            "actions": [
                {
                    "type": "send_notification",
                    "config": {
                        "recipient_role": "sales_manager",
                        "title": "High Value Order Alert",
                        "message": "New order #{{record.order_number}} for ${{record.total_amount}}"
                    }
                },
                {
                    "type": "log_event",
                    "config": {
                        "level": "info",
                        "message": "High value order created: {{record.id}}"
                    }
                }
            ],
            "is_active": True,
            "execution_order": 1
        },
        {
            "name": "low_stock_alert",
            "label": "Low Stock Alert",
            "description": "Send alert when product stock falls below threshold",
            "category": "Inventory",
            "trigger_type": "database_event",
            "event_type": "update",
            "trigger_timing": "after",
            "trigger_config": {
                "entity": "product",
                "events": ["update"],
                "watch_fields": ["stock_quantity"]
            },
            "has_conditions": True,
            "conditions": {
                "operator": "and",
                "rules": [
                    {
                        "field": "stock_quantity",
                        "operator": "less_than",
                        "value": 10
                    },
                    {
                        "field": "is_active",
                        "operator": "equals",
                        "value": True
                    }
                ]
            },
            "actions": [
                {
                    "type": "send_notification",
                    "config": {
                        "recipient_role": "inventory_manager",
                        "title": "Low Stock Alert",
                        "message": "Product {{record.name}} (SKU: {{record.sku}}) is low on stock: {{record.stock_quantity}} units remaining"
                    }
                }
            ],
            "is_active": True,
            "execution_order": 1
        },
        {
            "name": "daily_sales_report",
            "label": "Daily Sales Report",
            "description": "Generate and send daily sales summary report",
            "category": "Reporting",
            "trigger_type": "scheduled",
            "schedule_type": "cron",
            "cron_expression": "0 18 * * *",  # 6 PM every day
            "schedule_timezone": "UTC",
            "trigger_config": {
                "type": "scheduled",
                "frequency": "daily"
            },
            "has_conditions": False,
            "conditions": {},
            "actions": [
                {
                    "type": "run_report",
                    "config": {
                        "report_name": "daily_sales_summary",
                        "parameters": {
                            "date": "{{today}}"
                        }
                    }
                },
                {
                    "type": "send_email",
                    "config": {
                        "to": "sales@company.com",
                        "subject": "Daily Sales Report - {{today}}",
                        "template": "daily_sales_report",
                        "attach_report": True
                    }
                }
            ],
            "is_active": True,
            "execution_order": 1
        }
    ]

    for automation_data in automations_data:
        # Check if automation already exists
        existing = db.query(AutomationRule).filter(
            AutomationRule.tenant_id == tenant_id,
            AutomationRule.name == automation_data["name"],
            AutomationRule.is_deleted == False
        ).first()

        if existing:
            print(f"  ⏭️  Automation exists: {automation_data['label']}")
            continue

        # Set next run time for scheduled automations
        if automation_data.get("trigger_type") == "scheduled":
            automation_data["next_run_at"] = datetime.utcnow() + timedelta(hours=1)

        # Create automation
        automation = AutomationRule(
            id=str(generate_uuid()),
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **automation_data
        )
        db.add(automation)

        print(f"  ✅ Created automation: {automation.label}")

    db.commit()


def seed_lookup_samples(db: Session, tenant_id: str, user_id: str = None, entities: dict = None):
    """Seed sample lookup configurations."""
    print("\n" + "="*80)
    print("LOOKUP CONFIGURATION - SAMPLE DATA")
    print("="*80 + "\n")

    lookups_data = [
        {
            "name": "order_status",
            "label": "Order Status Options",
            "description": "Standard order status values",
            "source_type": "static_list",
            "static_options": [
                {"value": "pending", "label": "Pending", "color": "yellow", "icon": "clock"},
                {"value": "confirmed", "label": "Confirmed", "color": "blue", "icon": "check-circle"},
                {"value": "shipped", "label": "Shipped", "color": "purple", "icon": "truck"},
                {"value": "delivered", "label": "Delivered", "color": "green", "icon": "package-check"},
                {"value": "cancelled", "label": "Cancelled", "color": "red", "icon": "x-circle"},
            ],
            "enable_caching": True,
            "cache_ttl_seconds": 86400,  # 24 hours
            "is_active": True
        },
        {
            "name": "customer_status",
            "label": "Customer Status",
            "description": "Customer lifecycle status",
            "source_type": "static_list",
            "static_options": [
                {"value": "prospect", "label": "Prospect", "color": "gray"},
                {"value": "active", "label": "Active", "color": "green"},
                {"value": "inactive", "label": "Inactive", "color": "yellow"},
                {"value": "churned", "label": "Churned", "color": "red"},
            ],
            "enable_caching": True,
            "cache_ttl_seconds": 86400,
            "is_active": True
        },
        {
            "name": "countries",
            "label": "Countries",
            "description": "List of countries",
            "source_type": "static_list",
            "static_options": [
                {"value": "US", "label": "United States", "region": "North America"},
                {"value": "CA", "label": "Canada", "region": "North America"},
                {"value": "GB", "label": "United Kingdom", "region": "Europe"},
                {"value": "DE", "label": "Germany", "region": "Europe"},
                {"value": "FR", "label": "France", "region": "Europe"},
                {"value": "AU", "label": "Australia", "region": "Oceania"},
                {"value": "JP", "label": "Japan", "region": "Asia"},
                {"value": "CN", "label": "China", "region": "Asia"},
            ],
            "enable_caching": True,
            "cache_ttl_seconds": 604800,  # 7 days
            "is_active": True,
            "enable_search": True
        },
        {
            "name": "product_categories",
            "label": "Product Categories",
            "description": "Product categorization",
            "source_type": "static_list",
            "static_options": [
                {"value": "electronics", "label": "Electronics", "icon": "laptop"},
                {"value": "clothing", "label": "Clothing", "icon": "tshirt"},
                {"value": "books", "label": "Books", "icon": "book"},
                {"value": "home", "label": "Home & Garden", "icon": "house"},
                {"value": "sports", "label": "Sports & Outdoors", "icon": "basketball"},
                {"value": "toys", "label": "Toys & Games", "icon": "gift"},
            ],
            "enable_caching": True,
            "cache_ttl_seconds": 86400,
            "is_active": True
        }
    ]

    for lookup_data in lookups_data:
        # Check if lookup already exists
        existing = db.query(LookupConfiguration).filter(
            LookupConfiguration.tenant_id == tenant_id,
            LookupConfiguration.name == lookup_data["name"],
            LookupConfiguration.is_deleted == False
        ).first()

        if existing:
            print(f"  ⏭️  Lookup exists: {lookup_data['label']}")
            continue

        # Create lookup
        lookup = LookupConfiguration(
            id=str(generate_uuid()),
            tenant_id=tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **lookup_data
        )
        db.add(lookup)

        print(f"  ✅ Created lookup: {lookup.label} with {len(lookup_data.get('static_options', []))} options")

    db.commit()


def seed_all_samples(db: Session):
    """Main function to seed all sample data."""
    print("\n" + "="*80)
    print("PHASE 1 NO-CODE PLATFORM - SAMPLE DATA SEED")
    print("="*80 + "\n")

    # Get or create tenant
    tenant = get_or_create_tenant(db)
    print(f"📋 Using tenant: {tenant.name} (ID: {tenant.id})\n")

    # Get user
    user = get_or_create_user(db, tenant.id)
    user_id = user.id if user else None

    # Seed data for each feature
    entities = seed_data_model_samples(db, tenant.id, user_id)
    seed_workflow_samples(db, tenant.id, user_id, entities)
    seed_automation_samples(db, tenant.id, user_id, entities)
    seed_lookup_samples(db, tenant.id, user_id, entities)

    print("\n" + "="*80)
    print("SAMPLE DATA SEED COMPLETE")
    print("="*80 + "\n")

    print("Summary:")
    print("  • Data Model Designer: Sample entities (Customer, Order, Product) with fields")
    print("  • Workflow Designer: Sample workflows (Order Approval, Customer Onboarding)")
    print("  • Automation System: Sample automation rules (Welcome email, Alerts, Reports)")
    print("  • Lookup Configuration: Sample lookups (Statuses, Countries, Categories)")
    print()


def main():
    """Main entry point for the seed script."""
    db = SessionLocal()
    try:
        seed_all_samples(db)
        print("✅ All sample data seeded successfully!\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
