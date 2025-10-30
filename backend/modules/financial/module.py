"""
Financial Module

Main module definition for the Financial Management module.
"""

from fastapi import APIRouter
from pathlib import Path
from typing import List, Dict, Any
import logging

from core.module_system.base_module import BaseModule
from .routers import accounts_router, invoices_router
from .permissions import FinancialPermissions
from .models import (
    FinancialAccount,
    FinancialTransaction,
    FinancialInvoice,
    FinancialInvoiceLineItem,
    FinancialPayment
)

logger = logging.getLogger(__name__)


class FinancialModule(BaseModule):
    """
    Financial Management Module

    Provides complete financial management capabilities including:
    - Chart of Accounts
    - Transactions and Journal Entries
    - Invoicing
    - Payment Tracking
    - Financial Reporting
    """

    def get_router(self) -> APIRouter:
        """
        Return the main router for the financial module.

        This router aggregates all sub-routers (accounts, invoices, etc.)
        """
        router = APIRouter(
            prefix="/api/v1/financial",
            tags=["financial"]
        )

        # Include sub-routers
        router.include_router(accounts_router)
        router.include_router(invoices_router)

        # Add health check endpoint
        @router.get("/health")
        async def health_check():
            return {
                "module": self.name,
                "version": self.version,
                "status": "healthy"
            }

        return router

    def get_permissions(self) -> List[Dict[str, Any]]:
        """
        Return permissions defined in manifest.

        Permissions are extracted from the manifest.json file.
        """
        return self.manifest.get("permissions", [])

    def get_models(self) -> List[Any]:
        """
        Return SQLAlchemy models for migration discovery.

        These models will be used by Alembic to generate migrations.
        """
        return [
            FinancialAccount,
            FinancialTransaction,
            FinancialInvoice,
            FinancialInvoiceLineItem,
            FinancialPayment
        ]

    def pre_install(self, db_session: Any) -> tuple[bool, str | None]:
        """
        Pre-installation checks.

        Validate that required dependencies are met.
        """
        logger.info("Running pre-install checks for Financial module")

        # Check if database connection is available
        try:
            db_session.execute("SELECT 1")
            return True, None
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    def post_install(self, db_session: Any) -> None:
        """
        Post-installation tasks.

        Create default chart of accounts.
        """
        logger.info("Running post-install tasks for Financial module")

        # Default accounts will be created via seeds
        # This is handled by the seed file
        pass

    def post_enable(self, db_session: Any, tenant_id: str) -> None:
        """
        Post-enable tasks for a tenant.

        Create tenant-specific default accounts.
        """
        logger.info(f"Setting up Financial module for tenant {tenant_id}")

        # Here we could create default chart of accounts for the tenant
        # For now, this is left to be done manually or via seed data
        pass

    def pre_disable(self, db_session: Any, tenant_id: str) -> tuple[bool, str | None]:
        """
        Pre-disable checks.

        Ensure no active invoices or transactions prevent disabling.
        """
        logger.info(f"Checking if Financial module can be disabled for tenant {tenant_id}")

        # Check for unpaid invoices
        from sqlalchemy import func
        unpaid_count = db_session.query(func.count(FinancialInvoice.id)).filter(
            FinancialInvoice.tenant_id == tenant_id,
            FinancialInvoice.status.in_(["draft", "sent", "overdue"])
        ).scalar()

        if unpaid_count > 0:
            return False, f"Cannot disable: {unpaid_count} unpaid/draft invoices exist"

        return True, None

    def post_disable(self, db_session: Any, tenant_id: str) -> None:
        """
        Post-disable cleanup.

        Archive or cleanup tenant-specific data if needed.
        """
        logger.info(f"Financial module disabled for tenant {tenant_id}")
        # No cleanup needed - data is preserved
        pass
