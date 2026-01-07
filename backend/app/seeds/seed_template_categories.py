"""
Seed Template Categories
========================
Creates hierarchical categories for organizing no-code templates.

Run: python -m app.seeds.seed_template_categories
"""

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.template_category import TemplateCategory
from app.models.base import generate_uuid
from datetime import datetime


def seed_template_categories(db: Session):
    """Seed template categories."""
    print("\n" + "="*80)
    print("TEMPLATE CATEGORIES")
    print("="*80 + "\n")

    categories = [
        # ==================== Industry Categories ====================
        {
            "code": "industry",
            "name": "Industry Templates",
            "description": "Templates organized by industry vertical",
            "icon": "buildings",
            "color": "blue",
            "category_type": "industry",
            "level": 0,
            "path": "/industry/",
            "display_order": 1,
            "is_featured": True,
            "children": [
                {
                    "code": "healthcare",
                    "name": "Healthcare",
                    "description": "Medical, hospital, and healthcare templates",
                    "icon": "heartbeat",
                    "color": "red",
                    "category_type": "industry",
                    "level": 1,
                    "display_order": 1
                },
                {
                    "code": "finance",
                    "name": "Finance & Banking",
                    "description": "Financial services, banking, and investment templates",
                    "icon": "bank",
                    "color": "green",
                    "category_type": "industry",
                    "level": 1,
                    "display_order": 2
                },
                {
                    "code": "retail",
                    "name": "Retail & E-commerce",
                    "description": "Retail, online stores, and inventory management",
                    "icon": "storefront",
                    "color": "purple",
                    "category_type": "industry",
                    "level": 1,
                    "display_order": 3
                },
                {
                    "code": "manufacturing",
                    "name": "Manufacturing",
                    "description": "Production, supply chain, and quality management",
                    "icon": "factory",
                    "color": "orange",
                    "category_type": "industry",
                    "level": 1,
                    "display_order": 4
                },
                {
                    "code": "education",
                    "name": "Education",
                    "description": "Schools, universities, and training organizations",
                    "icon": "student",
                    "color": "indigo",
                    "category_type": "industry",
                    "level": 1,
                    "display_order": 5
                },
                {
                    "code": "real_estate",
                    "name": "Real Estate",
                    "description": "Property management and real estate agencies",
                    "icon": "house",
                    "color": "teal",
                    "category_type": "industry",
                    "level": 1,
                    "display_order": 6
                }
            ]
        },

        # ==================== Use Case Categories ====================
        {
            "code": "use_case",
            "name": "Use Case Templates",
            "description": "Templates organized by business function",
            "icon": "briefcase",
            "color": "green",
            "category_type": "use_case",
            "level": 0,
            "path": "/use_case/",
            "display_order": 2,
            "is_featured": True,
            "children": [
                {
                    "code": "crm",
                    "name": "CRM & Sales",
                    "description": "Customer relationship management and sales tracking",
                    "icon": "users-three",
                    "color": "blue",
                    "category_type": "use_case",
                    "level": 1,
                    "display_order": 1,
                    "is_featured": True
                },
                {
                    "code": "project_management",
                    "name": "Project Management",
                    "description": "Task tracking, project planning, and team collaboration",
                    "icon": "kanban",
                    "color": "purple",
                    "category_type": "use_case",
                    "level": 1,
                    "display_order": 2,
                    "is_featured": True
                },
                {
                    "code": "hr",
                    "name": "Human Resources",
                    "description": "Employee management, recruitment, and payroll",
                    "icon": "identification-badge",
                    "color": "pink",
                    "category_type": "use_case",
                    "level": 1,
                    "display_order": 3
                },
                {
                    "code": "inventory",
                    "name": "Inventory Management",
                    "description": "Stock tracking, warehouse management, and logistics",
                    "icon": "package",
                    "color": "orange",
                    "category_type": "use_case",
                    "level": 1,
                    "display_order": 4
                },
                {
                    "code": "document_management",
                    "name": "Document Management",
                    "description": "File storage, document tracking, and version control",
                    "icon": "files",
                    "color": "gray",
                    "category_type": "use_case",
                    "level": 1,
                    "display_order": 5
                },
                {
                    "code": "support",
                    "name": "Customer Support",
                    "description": "Ticketing, help desk, and customer service",
                    "icon": "headset",
                    "color": "cyan",
                    "category_type": "use_case",
                    "level": 1,
                    "display_order": 6
                }
            ]
        },

        # ==================== Function Categories ====================
        {
            "code": "function",
            "name": "Functional Templates",
            "description": "Templates organized by core function",
            "icon": "function",
            "color": "purple",
            "category_type": "function",
            "level": 0,
            "path": "/function/",
            "display_order": 3,
            "children": [
                {
                    "code": "data_collection",
                    "name": "Data Collection",
                    "description": "Forms, surveys, and data entry templates",
                    "icon": "clipboard-text",
                    "color": "blue",
                    "category_type": "function",
                    "level": 1,
                    "display_order": 1
                },
                {
                    "code": "reporting",
                    "name": "Reporting & Analytics",
                    "description": "Reports, dashboards, and data visualization",
                    "icon": "chart-line",
                    "color": "green",
                    "category_type": "function",
                    "level": 1,
                    "display_order": 2
                },
                {
                    "code": "workflow_automation",
                    "name": "Workflow Automation",
                    "description": "Approval processes and automated workflows",
                    "icon": "git-branch",
                    "color": "purple",
                    "category_type": "function",
                    "level": 1,
                    "display_order": 3
                },
                {
                    "code": "communication",
                    "name": "Communication",
                    "description": "Messaging, notifications, and collaboration",
                    "icon": "chats-circle",
                    "color": "cyan",
                    "category_type": "function",
                    "level": 1,
                    "display_order": 4
                }
            ]
        },

        # ==================== General/Starter Templates ====================
        {
            "code": "general",
            "name": "General Templates",
            "description": "Generic templates suitable for any industry",
            "icon": "star",
            "color": "yellow",
            "category_type": "general",
            "level": 0,
            "path": "/general/",
            "display_order": 4,
            "is_featured": True
        }
    ]

    created_count = 0
    skipped_count = 0

    def create_category(cat_data, parent_id=None):
        nonlocal created_count, skipped_count

        # Check if category already exists
        existing = db.query(TemplateCategory).filter(
            TemplateCategory.code == cat_data["code"]
        ).first()

        if existing:
            print(f"  ⏭️  Category exists: {cat_data['name']}")
            skipped_count += 1
            return existing

        # Build path
        if parent_id:
            parent = db.query(TemplateCategory).filter(TemplateCategory.id == parent_id).first()
            path = f"{parent.path}{cat_data['code']}/"
        else:
            path = cat_data.get("path", f"/{cat_data['code']}/")

        # Extract children and remove keys that will be set explicitly
        children = cat_data.pop("children", [])
        cat_data.pop("path", None)  # Remove path as we're setting it explicitly

        # Create category
        category = TemplateCategory(
            id=str(generate_uuid()),
            parent_id=parent_id,
            path=path,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **cat_data
        )
        db.add(category)
        db.flush()
        created_count += 1
        print(f"  ✅ Created category: {category.name} ({category.code})")

        # Create children
        for child_data in children:
            create_category(child_data, category.id)

        return category

    # Create all categories
    for cat_data in categories:
        create_category(cat_data.copy())

    db.commit()

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"  ✅ Created: {created_count} categories")
    print(f"  ⏭️  Skipped: {skipped_count} categories (already exist)")
    print()


def main():
    """Main entry point for the category seed script."""
    db = SessionLocal()
    try:
        seed_template_categories(db)
        print("✅ Template categories seeded successfully!\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
