"""
Report Service

Business logic for Financial Reports.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.account import Account
from ..models.journal_entry import JournalEntry, JournalEntryLine
from ..models.invoice import Invoice
from ..models.payment import Payment
from ..models.customer import Customer


class ReportService:
    """
    Service for generating financial reports.
    """

    @staticmethod
    async def get_trial_balance(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate trial balance report.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            as_of_date: Date for the trial balance

        Returns:
            Trial balance report with accounts and balances
        """
        # Get all active accounts
        query = select(Account).where(
            and_(
                Account.tenant_id == tenant_id,
                Account.company_id == company_id,
                Account.is_active == True,
                Account.is_header == False  # Only detail accounts
            )
        ).order_by(Account.code)

        result = await db.execute(query)
        accounts = result.scalars().all()

        # Build trial balance
        trial_balance_lines = []
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')

        for account in accounts:
            debit_amount = Decimal('0.00')
            credit_amount = Decimal('0.00')

            if account.is_debit_account:
                debit_amount = abs(account.current_balance)
            else:
                credit_amount = abs(account.current_balance)

            if debit_amount > 0 or credit_amount > 0:
                trial_balance_lines.append({
                    "account_code": account.code,
                    "account_name": account.name,
                    "account_type": account.type,
                    "debit_amount": debit_amount,
                    "credit_amount": credit_amount
                })

                total_debit += debit_amount
                total_credit += credit_amount

        return {
            "report_name": "Trial Balance",
            "tenant_id": tenant_id,
            "company_id": company_id,
            "as_of_date": as_of_date,
            "lines": trial_balance_lines,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": total_debit == total_credit
        }

    @staticmethod
    async def get_balance_sheet(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate balance sheet report.

        Returns:
            Balance sheet with assets, liabilities, and equity
        """
        # Get all active accounts
        query = select(Account).where(
            and_(
                Account.tenant_id == tenant_id,
                Account.company_id == company_id,
                Account.is_active == True
            )
        ).order_by(Account.code)

        result = await db.execute(query)
        accounts = result.scalars().all()

        # Organize by account type
        assets = []
        liabilities = []
        equity = []

        total_assets = Decimal('0.00')
        total_liabilities = Decimal('0.00')
        total_equity = Decimal('0.00')

        for account in accounts:
            if not account.is_header and account.current_balance != Decimal('0.00'):
                item = {
                    "account_code": account.code,
                    "account_name": account.name,
                    "balance": abs(account.current_balance)
                }

                if account.type == 'asset':
                    assets.append(item)
                    total_assets += abs(account.current_balance)
                elif account.type == 'liability':
                    liabilities.append(item)
                    total_liabilities += abs(account.current_balance)
                elif account.type == 'equity':
                    equity.append(item)
                    total_equity += abs(account.current_balance)

        return {
            "report_name": "Balance Sheet",
            "tenant_id": tenant_id,
            "company_id": company_id,
            "as_of_date": as_of_date,
            "assets": {
                "items": assets,
                "total": total_assets
            },
            "liabilities": {
                "items": liabilities,
                "total": total_liabilities
            },
            "equity": {
                "items": equity,
                "total": total_equity
            },
            "total_liabilities_and_equity": total_liabilities + total_equity,
            "is_balanced": total_assets == (total_liabilities + total_equity)
        }

    @staticmethod
    async def get_income_statement(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Generate income statement (profit & loss) report.

        Returns:
            Income statement with revenue, expenses, and net income
        """
        # Get all active revenue and expense accounts
        query = select(Account).where(
            and_(
                Account.tenant_id == tenant_id,
                Account.company_id == company_id,
                Account.is_active == True,
                or_(
                    Account.type == 'revenue',
                    Account.type == 'expense'
                )
            )
        ).order_by(Account.type, Account.code)

        result = await db.execute(query)
        accounts = result.scalars().all()

        # Organize by type
        revenue_items = []
        expense_items = []

        total_revenue = Decimal('0.00')
        total_expenses = Decimal('0.00')

        for account in accounts:
            if not account.is_header and account.current_balance != Decimal('0.00'):
                item = {
                    "account_code": account.code,
                    "account_name": account.name,
                    "amount": abs(account.current_balance)
                }

                if account.type == 'revenue':
                    revenue_items.append(item)
                    total_revenue += abs(account.current_balance)
                elif account.type == 'expense':
                    expense_items.append(item)
                    total_expenses += abs(account.current_balance)

        net_income = total_revenue - total_expenses

        return {
            "report_name": "Income Statement",
            "tenant_id": tenant_id,
            "company_id": company_id,
            "from_date": from_date,
            "to_date": to_date,
            "revenue": {
                "items": revenue_items,
                "total": total_revenue
            },
            "expenses": {
                "items": expense_items,
                "total": total_expenses
            },
            "net_income": net_income,
            "net_income_percentage": (net_income / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')
        }

    @staticmethod
    async def get_aged_receivables(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate aged receivables report.

        Returns:
            Aged receivables by customer with aging buckets
        """
        # Get all unpaid invoices
        query = select(Invoice).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.company_id == company_id,
                Invoice.balance_due > Decimal('0.00'),
                Invoice.status.notin_(['void', 'cancelled'])
            )
        ).order_by(Invoice.customer_id, Invoice.due_date)

        result = await db.execute(query)
        invoices = result.scalars().all()

        # Group by customer and age
        customers_data = {}

        for invoice in invoices:
            if invoice.customer_id not in customers_data:
                customers_data[invoice.customer_id] = {
                    "customer_id": invoice.customer_id,
                    "customer_name": "",  # Will be filled later
                    "current": Decimal('0.00'),
                    "days_1_30": Decimal('0.00'),
                    "days_31_60": Decimal('0.00'),
                    "days_61_90": Decimal('0.00'),
                    "over_90": Decimal('0.00'),
                    "total": Decimal('0.00')
                }

            # Calculate days overdue
            days_overdue = (as_of_date - invoice.due_date).days
            balance = invoice.balance_due

            if days_overdue <= 0:
                customers_data[invoice.customer_id]["current"] += balance
            elif days_overdue <= 30:
                customers_data[invoice.customer_id]["days_1_30"] += balance
            elif days_overdue <= 60:
                customers_data[invoice.customer_id]["days_31_60"] += balance
            elif days_overdue <= 90:
                customers_data[invoice.customer_id]["days_61_90"] += balance
            else:
                customers_data[invoice.customer_id]["over_90"] += balance

            customers_data[invoice.customer_id]["total"] += balance

        # Get customer names
        if customers_data:
            customer_ids = list(customers_data.keys())
            customer_query = select(Customer).where(Customer.id.in_(customer_ids))
            customer_result = await db.execute(customer_query)
            customers = customer_result.scalars().all()

            for customer in customers:
                if customer.id in customers_data:
                    customers_data[customer.id]["customer_name"] = customer.name

        # Calculate totals
        report_data = list(customers_data.values())
        totals = {
            "current": sum(c["current"] for c in report_data),
            "days_1_30": sum(c["days_1_30"] for c in report_data),
            "days_31_60": sum(c["days_31_60"] for c in report_data),
            "days_61_90": sum(c["days_61_90"] for c in report_data),
            "over_90": sum(c["over_90"] for c in report_data),
            "total": sum(c["total"] for c in report_data)
        }

        return {
            "report_name": "Aged Receivables",
            "tenant_id": tenant_id,
            "company_id": company_id,
            "as_of_date": as_of_date,
            "customers": report_data,
            "totals": totals
        }

    @staticmethod
    async def get_cash_flow_statement(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Generate cash flow statement (simplified).

        Returns:
            Cash flow from operations, investing, and financing
        """
        # Get cash/bank accounts
        cash_accounts_query = select(Account).where(
            and_(
                Account.tenant_id == tenant_id,
                Account.company_id == company_id,
                Account.is_active == True,
                Account.category == 'cash'
            )
        )

        cash_result = await db.execute(cash_accounts_query)
        cash_accounts = cash_result.scalars().all()

        beginning_cash = sum(acc.current_balance for acc in cash_accounts)

        # Get payments received (operating)
        payments_query = select(func.sum(Payment.payment_amount)).where(
            and_(
                Payment.tenant_id == tenant_id,
                Payment.company_id == company_id,
                Payment.payment_date >= from_date,
                Payment.payment_date <= to_date,
                Payment.is_voided == False
            )
        )

        payments_result = await db.execute(payments_query)
        cash_from_customers = payments_result.scalar() or Decimal('0.00')

        # Get invoices created (operating - simplified)
        invoices_query = select(func.sum(Invoice.total_amount)).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.company_id == company_id,
                Invoice.invoice_date >= from_date,
                Invoice.invoice_date <= to_date,
                Invoice.status != 'void'
            )
        )

        invoices_result = await db.execute(invoices_query)
        total_sales = invoices_result.scalar() or Decimal('0.00')

        # Simplified cash flow
        cash_from_operations = cash_from_customers
        cash_from_investing = Decimal('0.00')  # Placeholder
        cash_from_financing = Decimal('0.00')  # Placeholder

        net_change = cash_from_operations + cash_from_investing + cash_from_financing
        ending_cash = beginning_cash  # In reality, would need to calculate actual change

        return {
            "report_name": "Cash Flow Statement",
            "tenant_id": tenant_id,
            "company_id": company_id,
            "from_date": from_date,
            "to_date": to_date,
            "operating_activities": {
                "cash_from_customers": cash_from_customers,
                "total_sales": total_sales,
                "net_cash_from_operations": cash_from_operations
            },
            "investing_activities": {
                "net_cash_from_investing": cash_from_investing
            },
            "financing_activities": {
                "net_cash_from_financing": cash_from_financing
            },
            "net_change_in_cash": net_change,
            "beginning_cash": beginning_cash,
            "ending_cash": ending_cash
        }

    @staticmethod
    async def get_account_ledger(
        db: AsyncSession,
        account_id: str,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Generate general ledger report for a specific account.

        Returns:
            Account ledger with all transactions
        """
        # Get account
        account_query = select(Account).where(Account.id == account_id)
        account_result = await db.execute(account_query)
        account = account_result.scalar_one_or_none()

        if not account:
            return None

        # Get journal entry lines for this account
        lines_query = select(JournalEntryLine).join(JournalEntry).where(
            and_(
                JournalEntryLine.account_id == account_id,
                JournalEntry.entry_date >= from_date,
                JournalEntry.entry_date <= to_date,
                JournalEntry.status == 'posted'
            )
        ).order_by(JournalEntry.entry_date, JournalEntry.entry_number)

        lines_result = await db.execute(lines_query)
        lines = lines_result.scalars().all()

        # Build ledger
        transactions = []
        running_balance = Decimal('0.00')

        for line in lines:
            debit = line.debit_amount
            credit = line.credit_amount

            if account.is_debit_account:
                running_balance += debit - credit
            else:
                running_balance += credit - debit

            transactions.append({
                "date": line.journal_entry.entry_date,
                "entry_number": line.journal_entry.entry_number,
                "description": line.description or line.journal_entry.description,
                "debit": debit,
                "credit": credit,
                "balance": running_balance
            })

        return {
            "report_name": "Account Ledger",
            "account_code": account.code,
            "account_name": account.name,
            "account_type": account.type,
            "from_date": from_date,
            "to_date": to_date,
            "transactions": transactions,
            "ending_balance": running_balance
        }
