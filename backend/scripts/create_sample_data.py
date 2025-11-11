"""
Script to create sample reports and dashboards for testing.
Run this script from the backend container to populate sample data.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.report import ReportDefinition, ReportType
from app.models.dashboard import Dashboard, DashboardPage, DashboardWidget, WidgetType, DashboardLayout
from datetime import datetime
import uuid


def create_sample_reports(db: Session, tenant_id: uuid.UUID, user_id: uuid.UUID):
    """Create sample report definitions."""

    reports = [
        {
            "name": "Sales Summary Report",
            "description": "Overview of sales performance with key metrics",
            "category": "Sales",
            "report_type": ReportType.TABULAR,
            "base_entity": "sales",
            "is_public": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        },
        {
            "name": "Monthly Revenue Analysis",
            "description": "Detailed breakdown of monthly revenue by product category",
            "category": "Financial",
            "report_type": ReportType.CHART,
            "base_entity": "revenue",
            "is_public": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        },
        {
            "name": "Customer Activity Report",
            "description": "Track customer engagement and activity patterns",
            "category": "Marketing",
            "report_type": ReportType.TABULAR,
            "base_entity": "customers",
            "is_public": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        },
        {
            "name": "Inventory Status",
            "description": "Current stock levels and inventory movement",
            "category": "Operations",
            "report_type": ReportType.SUMMARY,
            "base_entity": "inventory",
            "is_public": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        },
        {
            "name": "Employee Performance Dashboard",
            "description": "Key performance indicators for team members",
            "category": "HR",
            "report_type": ReportType.DASHBOARD,
            "base_entity": "employees",
            "is_public": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        }
    ]

    created_reports = []
    for report_data in reports:
        report = ReportDefinition(**report_data)
        db.add(report)
        created_reports.append(report)

    db.commit()
    print(f"✓ Created {len(created_reports)} sample reports")
    return created_reports


def create_sample_dashboards(db: Session, tenant_id: uuid.UUID, user_id: uuid.UUID):
    """Create sample dashboards."""

    dashboards_data = [
        {
            "name": "Executive Overview",
            "description": "High-level view of company performance metrics",
            "category": "Executive",
            "layout_type": DashboardLayout.GRID,
            "is_public": True,
            "show_header": True,
            "show_filters": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        },
        {
            "name": "Sales Analytics",
            "description": "Comprehensive sales performance tracking",
            "category": "Sales",
            "layout_type": DashboardLayout.GRID,
            "is_public": True,
            "show_header": True,
            "show_filters": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        },
        {
            "name": "Marketing Metrics",
            "description": "Campaign performance and customer acquisition",
            "category": "Marketing",
            "layout_type": DashboardLayout.RESPONSIVE,
            "is_public": True,
            "show_header": True,
            "show_filters": False,
            "tenant_id": tenant_id,
            "created_by": user_id
        },
        {
            "name": "Operations Dashboard",
            "description": "Real-time operational metrics and KPIs",
            "category": "Operations",
            "layout_type": DashboardLayout.GRID,
            "is_public": True,
            "show_header": True,
            "show_filters": True,
            "tenant_id": tenant_id,
            "created_by": user_id
        }
    ]

    created_dashboards = []
    for dash_data in dashboards_data:
        dashboard = Dashboard(**dash_data)
        db.add(dashboard)
        db.flush()  # Flush to get the dashboard ID

        # Create a default page for each dashboard
        page = DashboardPage(
            dashboard_id=dashboard.id,
            tenant_id=tenant_id,
            name="Overview",
            slug="overview",
            order=0,
            is_default=True
        )
        db.add(page)
        db.flush()

        # Add a sample widget to the page
        widget = DashboardWidget(
            page_id=page.id,
            tenant_id=tenant_id,
            title="Sample Metric",
            widget_type=WidgetType.KPI_CARD,
            position={"x": 0, "y": 0, "w": 4, "h": 2},
            order=0
        )
        db.add(widget)

        created_dashboards.append(dashboard)

    db.commit()
    print(f"✓ Created {len(created_dashboards)} sample dashboards")
    return created_dashboards


def main():
    """Main function to create all sample data."""
    print("\n=== Creating Sample Reports and Dashboards ===\n")

    # Get database session
    db = next(get_db())

    try:
        # You need to replace these with actual values from your database
        # Get the first tenant and user from the database
        from app.models.tenant import Tenant
        from app.models.user import User

        tenant = db.query(Tenant).first()
        if not tenant:
            print("❌ No tenant found. Please create a tenant first.")
            return

        user = db.query(User).filter(User.tenant_id == tenant.id).first()
        if not user:
            print("❌ No user found. Please create a user first.")
            return

        print(f"Using tenant: {tenant.name} ({tenant.id})")
        print(f"Using user: {user.email} ({user.id})\n")

        # Create sample data
        reports = create_sample_reports(db, tenant.id, user.id)
        dashboards = create_sample_dashboards(db, tenant.id, user.id)

        print(f"\n✓ Successfully created all sample data!")
        print(f"  - {len(reports)} reports")
        print(f"  - {len(dashboards)} dashboards")
        print("\nYou can now view them at: #/sample-reports-dashboards\n")

    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
