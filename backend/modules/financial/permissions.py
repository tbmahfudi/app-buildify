"""
Financial Module Permissions

Permission definitions for the financial module.
"""

from enum import Enum


class FinancialPermissions(str, Enum):
    """Financial module permission codes"""

    # Accounts
    ACCOUNTS_READ = "financial:accounts:read:company"
    ACCOUNTS_CREATE = "financial:accounts:create:company"
    ACCOUNTS_UPDATE = "financial:accounts:update:company"
    ACCOUNTS_DELETE = "financial:accounts:delete:company"

    # Transactions
    TRANSACTIONS_READ = "financial:transactions:read:company"
    TRANSACTIONS_CREATE = "financial:transactions:create:company"
    TRANSACTIONS_UPDATE = "financial:transactions:update:company"
    TRANSACTIONS_DELETE = "financial:transactions:delete:company"
    TRANSACTIONS_POST = "financial:transactions:post:company"

    # Invoices
    INVOICES_READ = "financial:invoices:read:company"
    INVOICES_CREATE = "financial:invoices:create:company"
    INVOICES_UPDATE = "financial:invoices:update:company"
    INVOICES_DELETE = "financial:invoices:delete:company"
    INVOICES_SEND = "financial:invoices:send:company"

    # Payments
    PAYMENTS_READ = "financial:payments:read:company"
    PAYMENTS_CREATE = "financial:payments:create:company"
    PAYMENTS_UPDATE = "financial:payments:update:company"
    PAYMENTS_DELETE = "financial:payments:delete:company"

    # Reports
    REPORTS_VIEW = "financial:reports:read:company"
    REPORTS_EXPORT = "financial:reports:export:company"
