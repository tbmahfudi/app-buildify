"""
Financial Module - Complete Setup Script

This script sets up the Financial Module for a sample tenant with:
- Default chart of accounts
- Sample customers
- Sample invoices
- Sample payments
- Sample journal entries

Usage:
    python setup_sample_data.py [tenant_code]

    Examples:
        python setup_sample_data.py TECHSTART
        python setup_sample_data.py FASHIONHUB
"""

import asyncio
import sys
from decimal import Decimal
from datetime import date, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.config import settings
from app.models import (
    Account, Customer, Invoice, InvoiceLineItem,
    Payment, PaymentAllocation, JournalEntry, JournalEntryLine, TaxRate
)
from app.services.chart_setup_service import ChartSetupService


# Default values (will be overridden by lookup)
TENANT_ID = None
COMPANY_ID = None
USER_ID = None
TENANT_CODE = None


async def setup_database():
    """Create database engine and session."""
    # Convert to async URL if needed
    database_url = settings.effective_database_url
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        database_url,
        echo=True,
        future=True
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    return async_session


async def lookup_tenant_info(session: AsyncSession, tenant_code: str):
    """
    Lookup tenant, company, and user information from database.

    Returns tuple: (tenant_id, company_id, user_id, tenant_name, company_name)
    """
    global TENANT_ID, COMPANY_ID, USER_ID, TENANT_CODE

    print("\n" + "="*60)
    print(f"LOOKING UP TENANT: {tenant_code}")
    print("="*60)

    # Query for tenant
    result = await session.execute(
        text("SELECT id, code, name FROM tenants WHERE code = :code"),
        {"code": tenant_code}
    )
    tenant_row = result.fetchone()

    if not tenant_row:
        print(f"❌ Tenant with code '{tenant_code}' not found!")
        print("\nAvailable tenants:")
        result = await session.execute(text("SELECT code, name FROM tenants"))
        for row in result.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        raise ValueError(f"Tenant '{tenant_code}' not found")

    tenant_id = str(tenant_row[0])  # Convert UUID to string
    tenant_name = tenant_row[2]
    print(f"✅ Found tenant: {tenant_name} (ID: {tenant_id})")

    # Query for company
    result = await session.execute(
        text("SELECT id, code, name FROM companies WHERE tenant_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )
    company_row = result.fetchone()

    if not company_row:
        raise ValueError(f"No company found for tenant '{tenant_code}'")

    company_id = str(company_row[0])  # Convert UUID to string
    company_name = company_row[2]
    print(f"✅ Found company: {company_name} (ID: {company_id})")

    # Query for first user in this tenant
    result = await session.execute(
        text("SELECT id, email, full_name FROM users WHERE tenant_id = :tenant_id LIMIT 1"),
        {"tenant_id": tenant_id}
    )
    user_row = result.fetchone()

    if not user_row:
        raise ValueError(f"No users found for tenant '{tenant_code}'")

    user_id = str(user_row[0])  # Convert UUID to string
    user_email = user_row[1]
    user_name = user_row[2]
    print(f"✅ Found user: {user_name} ({user_email}) (ID: {user_id})")

    # Set global variables (all as strings)
    TENANT_ID = tenant_id
    COMPANY_ID = company_id
    USER_ID = user_id
    TENANT_CODE = tenant_code

    print(f"\n{'='*60}")
    print("TENANT INFORMATION LOADED")
    print(f"{'='*60}")
    print(f"Tenant:  {tenant_name} ({tenant_code})")
    print(f"Company: {company_name}")
    print(f"User:    {user_name} ({user_email})")
    print(f"{'='*60}\n")

    return tenant_id, company_id, user_id, tenant_name, company_name


async def setup_chart_of_accounts(session: AsyncSession):
    """Setup default chart of accounts."""
    print("\n" + "="*60)
    print("SETTING UP CHART OF ACCOUNTS")
    print("="*60)

    try:
        accounts = await ChartSetupService.setup_default_chart(
            db=session,
            tenant_id=TENANT_ID,
            company_id=COMPANY_ID,
            created_by=USER_ID
        )
        print(f"✅ Created {len(accounts)} accounts")

        # Display some key accounts
        print("\nKey Accounts Created:")
        for acc in accounts[:10]:
            print(f"  - {acc.code}: {acc.name} ({acc.type})")

        return accounts
    except ValueError as e:
        print(f"⚠️  Chart of accounts already exists: {e}")
        return []


async def get_account_by_code(session: AsyncSession, code: str):
    """Helper to get account by code."""
    from sqlalchemy import select
    result = await session.execute(
        select(Account).where(
            Account.tenant_id == TENANT_ID,
            Account.company_id == COMPANY_ID,
            Account.code == code
        )
    )
    return result.scalar_one_or_none()


async def create_tax_rates(session: AsyncSession):
    """Create sample tax rates."""
    print("\n" + "="*60)
    print("CREATING TAX RATES")
    print("="*60)

    # Get tax liability account
    tax_account = await get_account_by_code(session, "2120")  # Sales Tax Payable

    tax_rates = [
        {
            "code": "VAT-STD",
            "name": "Standard VAT",
            "rate_percentage": Decimal("20.00"),
            "tax_type": "vat",
            "applies_to_sales": True,
            "tax_account_id": tax_account.id if tax_account else None,
        },
        {
            "code": "SALES-TAX",
            "name": "Sales Tax",
            "rate_percentage": Decimal("7.50"),
            "tax_type": "sales_tax",
            "applies_to_sales": True,
            "tax_account_id": tax_account.id if tax_account else None,
        },
    ]

    created_rates = []
    for rate_data in tax_rates:
        # Check if tax rate already exists
        from sqlalchemy import select
        existing = await session.execute(
            select(TaxRate).where(
                TaxRate.tenant_id == TENANT_ID,
                TaxRate.company_id == COMPANY_ID,
                TaxRate.code == rate_data["code"]
            )
        )
        existing_rate = existing.scalar_one_or_none()

        if existing_rate:
            print(f"⚠️  Tax rate already exists: {rate_data['name']} - skipping")
            created_rates.append(existing_rate)
            continue

        tax_rate = TaxRate(
            id=str(uuid4()),
            tenant_id=TENANT_ID,
            company_id=COMPANY_ID,
            created_by=USER_ID,
            effective_from=date.today(),
            is_active=True,
            is_default=(rate_data["code"] == "SALES-TAX"),
            **rate_data
        )
        session.add(tax_rate)
        created_rates.append(tax_rate)
        print(f"✅ Created tax rate: {tax_rate.name} ({tax_rate.rate_percentage}%)")

    await session.commit()
    return created_rates


async def create_customers(session: AsyncSession):
    """Create sample customers."""
    print("\n" + "="*60)
    print("CREATING CUSTOMERS")
    print("="*60)

    # Get receivables account
    receivables_account = await get_account_by_code(session, "1200")  # Accounts Receivable

    customers_data = [
        {
            "customer_number": "CUST-001",
            "name": "Acme Corporation",
            "email": "billing@acme.com",
            "phone": "+1-555-0100",
            "billing_address_line1": "123 Main Street",
            "billing_city": "New York",
            "billing_state": "NY",
            "billing_postal_code": "10001",
            "billing_country": "USA",
            "payment_terms_days": 30,
            "credit_limit": Decimal("50000.00"),
        },
        {
            "customer_number": "CUST-002",
            "name": "TechCorp Industries",
            "email": "accounts@techcorp.com",
            "phone": "+1-555-0200",
            "billing_address_line1": "456 Tech Avenue",
            "billing_city": "San Francisco",
            "billing_state": "CA",
            "billing_postal_code": "94102",
            "billing_country": "USA",
            "payment_terms_days": 15,
            "credit_limit": Decimal("75000.00"),
        },
        {
            "customer_number": "CUST-003",
            "name": "Global Solutions Ltd",
            "email": "finance@globalsolutions.com",
            "phone": "+1-555-0300",
            "billing_address_line1": "789 Business Park",
            "billing_city": "Chicago",
            "billing_state": "IL",
            "billing_postal_code": "60601",
            "billing_country": "USA",
            "payment_terms_days": 30,
            "credit_limit": Decimal("100000.00"),
        },
    ]

    customers = []
    for cust_data in customers_data:
        # Check if customer already exists
        from sqlalchemy import select
        existing = await session.execute(
            select(Customer).where(
                Customer.tenant_id == TENANT_ID,
                Customer.company_id == COMPANY_ID,
                Customer.customer_number == cust_data["customer_number"]
            )
        )
        existing_customer = existing.scalar_one_or_none()

        if existing_customer:
            print(f"⚠️  Customer already exists: {cust_data['name']} - skipping")
            customers.append(existing_customer)
            continue

        customer = Customer(
            id=str(uuid4()),
            tenant_id=TENANT_ID,
            company_id=COMPANY_ID,
            created_by=USER_ID,
            receivables_account_id=receivables_account.id if receivables_account else None,
            **cust_data
        )
        session.add(customer)
        customers.append(customer)
        print(f"✅ Created customer: {customer.name} ({customer.customer_number})")

    await session.commit()
    return customers


async def create_invoices(session: AsyncSession, customers, tax_rates):
    """Create sample invoices."""
    print("\n" + "="*60)
    print("CREATING INVOICES")
    print("="*60)

    # Get revenue account
    revenue_account = await get_account_by_code(session, "4100")  # Sales Revenue

    today = date.today()
    sales_tax = tax_rates[1] if len(tax_rates) > 1 else tax_rates[0]

    invoices_data = [
        {
            "customer": customers[0],
            "invoice_number": "INV-2025-001",
            "invoice_date": today - timedelta(days=30),
            "due_date": today,
            "status": "sent",
            "line_items": [
                {
                    "line_number": 1,
                    "description": "Professional Services - Consulting",
                    "quantity": Decimal("40.00"),
                    "unit_price": Decimal("150.00"),
                    "tax_percentage": sales_tax.rate_percentage,
                },
                {
                    "line_number": 2,
                    "description": "Software License - Annual",
                    "quantity": Decimal("1.00"),
                    "unit_price": Decimal("2500.00"),
                    "tax_percentage": sales_tax.rate_percentage,
                },
            ]
        },
        {
            "customer": customers[1],
            "invoice_number": "INV-2025-002",
            "invoice_date": today - timedelta(days=15),
            "due_date": today + timedelta(days=15),
            "status": "sent",
            "line_items": [
                {
                    "line_number": 1,
                    "description": "Web Development Services",
                    "quantity": Decimal("80.00"),
                    "unit_price": Decimal("125.00"),
                    "tax_percentage": sales_tax.rate_percentage,
                },
            ]
        },
        {
            "customer": customers[2],
            "invoice_number": "INV-2025-003",
            "invoice_date": today - timedelta(days=5),
            "due_date": today + timedelta(days=25),
            "status": "draft",
            "line_items": [
                {
                    "line_number": 1,
                    "description": "Cloud Hosting Services - Monthly",
                    "quantity": Decimal("1.00"),
                    "unit_price": Decimal("999.00"),
                    "tax_percentage": sales_tax.rate_percentage,
                },
                {
                    "line_number": 2,
                    "description": "Support Services",
                    "quantity": Decimal("10.00"),
                    "unit_price": Decimal("100.00"),
                    "tax_percentage": sales_tax.rate_percentage,
                },
            ]
        },
    ]

    invoices = []
    for inv_data in invoices_data:
        # Check if invoice already exists
        from sqlalchemy import select
        existing = await session.execute(
            select(Invoice).where(
                Invoice.tenant_id == TENANT_ID,
                Invoice.company_id == COMPANY_ID,
                Invoice.invoice_number == inv_data["invoice_number"]
            )
        )
        existing_invoice = existing.scalar_one_or_none()

        if existing_invoice:
            print(f"⚠️  Invoice already exists: {inv_data['invoice_number']} - skipping")
            invoices.append(existing_invoice)
            continue

        invoice = Invoice(
            id=str(uuid4()),
            tenant_id=TENANT_ID,
            company_id=COMPANY_ID,
            created_by=USER_ID,
            customer_id=inv_data["customer"].id,
            invoice_number=inv_data["invoice_number"],
            invoice_date=inv_data["invoice_date"],
            due_date=inv_data["due_date"],
            payment_terms_days=30,
            status=inv_data["status"],
        )

        # Create line items
        for item_data in inv_data["line_items"]:
            line_item = InvoiceLineItem(
                id=str(uuid4()),
                invoice_id=invoice.id,
                revenue_account_id=revenue_account.id if revenue_account else None,
                **item_data
            )
            line_item.calculate_line_total()
            invoice.line_items.append(line_item)

        # Calculate totals
        invoice.calculate_totals()

        session.add(invoice)
        invoices.append(invoice)
        print(f"✅ Created invoice: {invoice.invoice_number} - ${invoice.total_amount} ({invoice.status})")

    await session.commit()
    return invoices


async def create_payments(session: AsyncSession, customers, invoices):
    """Create sample payments."""
    print("\n" + "="*60)
    print("CREATING PAYMENTS")
    print("="*60)

    # Get cash account
    cash_account = await get_account_by_code(session, "1110")  # Cash and Cash Equivalents

    today = date.today()

    payments_data = [
        {
            "customer": customers[0],
            "payment_number": "PMT-2025-001",
            "payment_date": today - timedelta(days=5),
            "payment_method": "bank_transfer",
            "payment_amount": Decimal("3000.00"),
            "status": "cleared",
            "reference_number": "TXN-20250001",
        },
        {
            "customer": customers[1],
            "payment_number": "PMT-2025-002",
            "payment_date": today - timedelta(days=2),
            "payment_method": "check",
            "payment_amount": Decimal("5000.00"),
            "status": "pending",
            "check_number": "CHK-1234",
        },
    ]

    payments = []
    for pmt_data in payments_data:
        # Check if payment already exists
        from sqlalchemy import select
        existing = await session.execute(
            select(Payment).where(
                Payment.tenant_id == TENANT_ID,
                Payment.company_id == COMPANY_ID,
                Payment.payment_number == pmt_data["payment_number"]
            )
        )
        existing_payment = existing.scalar_one_or_none()

        if existing_payment:
            print(f"⚠️  Payment already exists: {pmt_data['payment_number']} - skipping")
            payments.append(existing_payment)
            continue

        payment = Payment(
            id=str(uuid4()),
            tenant_id=TENANT_ID,
            company_id=COMPANY_ID,
            created_by=USER_ID,
            customer_id=pmt_data["customer"].id,
            deposit_account_id=cash_account.id if cash_account else None,
            **{k: v for k, v in pmt_data.items() if k != "customer"}
        )

        # Set unallocated amount
        payment.unallocated_amount = payment.payment_amount

        session.add(payment)
        payments.append(payment)
        print(f"✅ Created payment: {payment.payment_number} - ${payment.payment_amount} ({payment.status})")

    await session.commit()
    return payments


async def create_journal_entries(session: AsyncSession):
    """Create sample journal entries."""
    print("\n" + "="*60)
    print("CREATING JOURNAL ENTRIES")
    print("="*60)

    # Get accounts
    cash_account = await get_account_by_code(session, "1110")
    capital_account = await get_account_by_code(session, "3100")
    expense_account = await get_account_by_code(session, "6100")

    today = date.today()

    # Check if journal entry already exists
    from sqlalchemy import select
    existing = await session.execute(
        select(JournalEntry).where(
            JournalEntry.tenant_id == TENANT_ID,
            JournalEntry.company_id == COMPANY_ID,
            JournalEntry.entry_number == "JE-2025-001"
        )
    )
    existing_entry = existing.scalar_one_or_none()

    if existing_entry:
        print(f"⚠️  Journal entry already exists: JE-2025-001 - skipping")
        return [existing_entry]

    # Opening balance entry
    entry = JournalEntry(
        id=str(uuid4()),
        tenant_id=TENANT_ID,
        company_id=COMPANY_ID,
        created_by=USER_ID,
        entry_number="JE-2025-001",
        entry_date=today - timedelta(days=60),
        description="Opening Balance - Initial Capital",
        status="posted",
        posted_at=today - timedelta(days=60),
        posted_by=USER_ID,
    )

    # Debit: Cash
    line1 = JournalEntryLine(
        id=str(uuid4()),
        journal_entry_id=entry.id,
        line_number=1,
        account_id=cash_account.id if cash_account else str(uuid4()),
        description="Initial capital contribution",
        debit_amount=Decimal("100000.00"),
        credit_amount=Decimal("0.00"),
    )

    # Credit: Owner's Capital
    line2 = JournalEntryLine(
        id=str(uuid4()),
        journal_entry_id=entry.id,
        line_number=2,
        account_id=capital_account.id if capital_account else str(uuid4()),
        description="Initial capital contribution",
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("100000.00"),
    )

    entry.lines.extend([line1, line2])
    entry.total_debit = Decimal("100000.00")
    entry.total_credit = Decimal("100000.00")

    session.add(entry)
    print(f"✅ Created journal entry: {entry.entry_number} - ${entry.total_debit}")

    await session.commit()
    return [entry]


async def main():
    """Main setup function."""
    global TENANT_ID, COMPANY_ID, USER_ID

    print("\n" + "="*60)
    print("FINANCIAL MODULE - COMPLETE SETUP")
    print("="*60)

    # Parse command line arguments
    tenant_code = None
    if len(sys.argv) > 1:
        tenant_code = sys.argv[1].upper()
    else:
        print("\n📋 Available tenant codes:")
        print("  - TECHSTART    (Tech Startup)")
        print("  - FASHIONHUB   (Retail Chain)")
        print("  - MEDCARE      (Healthcare)")
        print("  - CLOUDWORK    (Remote Tech)")
        print("  - FINTECH      (Financial Services)")
        print("\nUsage: python setup_sample_data.py [TENANT_CODE]")
        print("Example: python setup_sample_data.py TECHSTART\n")

        tenant_code = input("Enter tenant code: ").strip().upper()

    if not tenant_code:
        print("❌ No tenant code provided. Exiting.")
        return

    # Create database session
    async_session = await setup_database()

    async with async_session() as session:
        try:
            # Lookup tenant information
            await lookup_tenant_info(session, tenant_code)

            if not TENANT_ID or not COMPANY_ID or not USER_ID:
                print("❌ Failed to lookup tenant information")
                return

            # Setup chart of accounts
            accounts = await setup_chart_of_accounts(session)

            # Create tax rates
            tax_rates = await create_tax_rates(session)

            # Create customers
            customers = await create_customers(session)

            # Create invoices
            invoices = await create_invoices(session, customers, tax_rates)

            # Create payments
            payments = await create_payments(session, customers, invoices)

            # Create journal entries
            journal_entries = await create_journal_entries(session)

            print("\n" + "="*60)
            print("SETUP COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"\n✅ Chart of Accounts: {len(accounts)} accounts")
            print(f"✅ Tax Rates: {len(tax_rates)} rates")
            print(f"✅ Customers: {len(customers)} customers")
            print(f"✅ Invoices: {len(invoices)} invoices")
            print(f"✅ Payments: {len(payments)} payments")
            print(f"✅ Journal Entries: {len(journal_entries)} entries")

            print("\n" + "="*60)
            print("FRONTEND ACCESS")
            print("="*60)
            print(f"\n🌐 You can now login to the frontend with:")
            print(f"   Tenant Code: {TENANT_CODE}")
            print(f"   Users: Check seed_complete_org.py for user credentials")
            print(f"   Default password: password123")

            print("\n" + "="*60)
            print("API ACCESS")
            print("="*60)
            print("\n1. Access the API documentation:")
            print("   http://localhost:9001/docs")
            print("\n2. Test endpoints with these IDs:")
            print(f"   Tenant ID: {TENANT_ID}")
            print(f"   Company ID: {COMPANY_ID}")
            print("\n3. Example API calls:")
            print(f"   GET http://localhost:9001/api/v1/accounts?tenant_id={TENANT_ID}&company_id={COMPANY_ID}")
            print(f"   GET http://localhost:9001/api/v1/customers?tenant_id={TENANT_ID}&company_id={COMPANY_ID}")
            print(f"   GET http://localhost:9001/api/v1/invoices?tenant_id={TENANT_ID}&company_id={COMPANY_ID}")

        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(main())
