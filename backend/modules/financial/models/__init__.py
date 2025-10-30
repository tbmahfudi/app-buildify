"""
Financial Module Models

Database models for financial management including:
- Accounts (Chart of Accounts)
- Transactions
- Invoices
- Payments
"""

from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Text, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from models.base import Base, GUID, generate_uuid


class FinancialAccount(Base):
    """
    Chart of Accounts
    Represents a financial account (asset, liability, equity, revenue, expense)
    """
    __tablename__ = "financial_accounts"

    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Multi-tenancy
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id"), nullable=False, index=True)

    # Account details
    code = Column(String(50), nullable=False, index=True)  # Account code (e.g., "1000", "4100")
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Account type
    account_type = Column(String(50), nullable=False, index=True)  # asset, liability, equity, revenue, expense
    account_subtype = Column(String(50), nullable=True)  # current_asset, fixed_asset, etc.

    # Hierarchy
    parent_account_id = Column(GUID, ForeignKey("financial_accounts.id"), nullable=True)

    # Account properties
    is_active = Column(Boolean, default=True, nullable=False)
    is_header = Column(Boolean, default=False, nullable=False)  # Header accounts can't have transactions
    allow_manual_entry = Column(Boolean, default=True, nullable=False)

    # Balance tracking
    current_balance = Column(Numeric(18, 2), default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)  # ISO currency code

    # Audit
    created_by_user_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    company = relationship("Company")
    parent_account = relationship("FinancialAccount", remote_side=[id], backref="sub_accounts")
    transactions = relationship("FinancialTransaction", back_populates="account")

    def __repr__(self):
        return f"<FinancialAccount(code={self.code}, name={self.name})>"


class FinancialTransaction(Base):
    """
    Financial Transactions
    Represents journal entries and transactions
    """
    __tablename__ = "financial_transactions"

    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Multi-tenancy
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id"), nullable=False, index=True)

    # Transaction details
    transaction_number = Column(String(50), nullable=False, unique=True, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Account reference
    account_id = Column(GUID, ForeignKey("financial_accounts.id"), nullable=False, index=True)

    # Amount
    debit = Column(Numeric(18, 2), default=0, nullable=False)
    credit = Column(Numeric(18, 2), default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Reference
    reference_type = Column(String(50), nullable=True)  # invoice, payment, journal
    reference_id = Column(GUID, nullable=True)

    # Status
    is_posted = Column(Boolean, default=False, nullable=False)
    posted_at = Column(DateTime, nullable=True)
    posted_by_user_id = Column(GUID, ForeignKey("users.id"), nullable=True)

    # Audit
    created_by_user_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    company = relationship("Company")
    account = relationship("FinancialAccount", back_populates="transactions")

    def __repr__(self):
        return f"<FinancialTransaction(number={self.transaction_number}, amount={self.debit or self.credit})>"


class FinancialInvoice(Base):
    """
    Invoices
    Represents customer invoices
    """
    __tablename__ = "financial_invoices"

    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Multi-tenancy
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id"), nullable=False, index=True)

    # Invoice details
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    invoice_date = Column(DateTime, nullable=False, index=True)
    due_date = Column(DateTime, nullable=False)

    # Customer
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_address = Column(Text, nullable=True)

    # Amounts
    subtotal = Column(Numeric(18, 2), nullable=False)
    tax_amount = Column(Numeric(18, 2), default=0, nullable=False)
    total_amount = Column(Numeric(18, 2), nullable=False)
    paid_amount = Column(Numeric(18, 2), default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Status
    status = Column(String(50), default="draft", nullable=False, index=True)  # draft, sent, paid, overdue, cancelled
    sent_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)

    # Audit
    created_by_user_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    company = relationship("Company")
    line_items = relationship("FinancialInvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("FinancialPayment", back_populates="invoice")

    def __repr__(self):
        return f"<FinancialInvoice(number={self.invoice_number}, total={self.total_amount})>"


class FinancialInvoiceLineItem(Base):
    """
    Invoice Line Items
    Individual items on an invoice
    """
    __tablename__ = "financial_invoice_line_items"

    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Invoice reference
    invoice_id = Column(GUID, ForeignKey("financial_invoices.id"), nullable=False, index=True)

    # Item details
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(18, 2), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)

    # Tax
    tax_rate = Column(Numeric(5, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(18, 2), default=0, nullable=False)

    # Line number for ordering
    line_number = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    invoice = relationship("FinancialInvoice", back_populates="line_items")

    def __repr__(self):
        return f"<InvoiceLineItem(description={self.description}, amount={self.amount})>"


class FinancialPayment(Base):
    """
    Payments
    Represents payments received for invoices
    """
    __tablename__ = "financial_payments"

    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Multi-tenancy
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id"), nullable=False, index=True)

    # Payment details
    payment_number = Column(String(50), nullable=False, unique=True, index=True)
    payment_date = Column(DateTime, nullable=False, index=True)

    # Invoice reference
    invoice_id = Column(GUID, ForeignKey("financial_invoices.id"), nullable=True, index=True)

    # Amount
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Payment method
    payment_method = Column(String(50), nullable=False)  # cash, check, credit_card, bank_transfer, etc.
    reference_number = Column(String(100), nullable=True)  # Check number, transaction ID, etc.

    # Status
    status = Column(String(50), default="received", nullable=False)  # received, deposited, cleared, voided

    # Notes
    notes = Column(Text, nullable=True)

    # Audit
    created_by_user_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    company = relationship("Company")
    invoice = relationship("FinancialInvoice", back_populates="payments")

    def __repr__(self):
        return f"<FinancialPayment(number={self.payment_number}, amount={self.amount})>"
