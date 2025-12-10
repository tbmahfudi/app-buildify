"""
Invoice Models for Financial Module

Implements invoicing with line items, taxes, and payment tracking.
"""

from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class Invoice(Base):
    """
    Invoice header model.

    Represents customer invoices with line items, taxes, and payment tracking.
    """
    __tablename__ = "financial_invoices"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Multi-tenancy
    tenant_id = Column(String(36), nullable=False, index=True)
    company_id = Column(String(36), nullable=False, index=True)

    # Invoice identification
    invoice_number = Column(String(50), nullable=False)
    reference_number = Column(String(100))

    # Customer
    customer_id = Column(
        String(36),
        ForeignKey("financial_customers.id"),
        nullable=False,
        index=True
    )

    # Dates
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    payment_terms_days = Column(Integer, default=30, nullable=False)

    # Description
    description = Column(Text)
    memo = Column(Text)

    # Status
    status = Column(String(20), default='draft', nullable=False, index=True)
    # draft, sent, partially_paid, paid, overdue, void, cancelled

    # Financial totals
    subtotal = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    tax_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    discount_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    total_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)

    # Payment tracking
    paid_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    balance_due = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    last_payment_date = Column(Date)

    # Currency
    currency_code = Column(String(3), default="USD", nullable=False)

    # Discount (percentage or fixed amount)
    discount_type = Column(String(20))  # percentage, fixed
    discount_value = Column(Numeric(18, 2), default=Decimal('0.00'))

    # Shipping
    shipping_amount = Column(Numeric(18, 2), default=Decimal('0.00'))

    # Journal entry linkage
    journal_entry_id = Column(String(36), ForeignKey("financial_journal_entries.id"))

    # Delivery tracking
    sent_at = Column(DateTime)
    sent_by = Column(String(36))
    delivered_at = Column(DateTime)

    # Metadata
    tags = Column(Text)  # JSON string
    extra_data = Column(Text)  # JSON string

    # Audit fields
    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    journal_entry = relationship("JournalEntry")
    line_items = relationship(
        "InvoiceLineItem",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'invoice_number', name='uq_invoice_number'),
        CheckConstraint(
            status.in_(['draft', 'sent', 'partially_paid', 'paid', 'overdue', 'void', 'cancelled']),
            name='chk_invoice_status'
        ),
        CheckConstraint(
            'total_amount >= 0',
            name='chk_total_positive'
        ),
        CheckConstraint(
            'paid_amount >= 0 AND paid_amount <= total_amount',
            name='chk_paid_amount'
        ),
        CheckConstraint(
            'balance_due >= 0 AND balance_due <= total_amount',
            name='chk_balance_due'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<Invoice(number={self.invoice_number}, status={self.status}, total={self.total_amount})>"

    @property
    def is_draft(self):
        """Check if invoice is in draft status"""
        return self.status == 'draft'

    @property
    def is_paid(self):
        """Check if invoice is fully paid"""
        return self.balance_due == Decimal('0') and self.paid_amount == self.total_amount

    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        from datetime import date
        return (
            self.status not in ['paid', 'void', 'cancelled'] and
            self.due_date < date.today() and
            self.balance_due > Decimal('0')
        )

    @property
    def can_edit(self):
        """Check if invoice can be edited"""
        return self.status == 'draft'

    @property
    def can_void(self):
        """Check if invoice can be voided"""
        return self.status in ['draft', 'sent'] and self.paid_amount == Decimal('0')

    def calculate_totals(self):
        """Calculate invoice totals from line items"""
        self.subtotal = sum(item.line_total for item in self.line_items)
        self.tax_amount = sum(item.tax_amount for item in self.line_items)

        # Initialize defaults if None
        if self.discount_value is None:
            self.discount_value = Decimal('0.00')
        if self.discount_amount is None:
            self.discount_amount = Decimal('0.00')
        if self.paid_amount is None:
            self.paid_amount = Decimal('0.00')

        # Apply discount
        if self.discount_type == 'percentage':
            self.discount_amount = self.subtotal * (self.discount_value / Decimal('100'))
        elif self.discount_type == 'fixed':
            self.discount_amount = self.discount_value
        else:
            self.discount_amount = Decimal('0.00')

        # Calculate total
        self.total_amount = (
            self.subtotal +
            self.tax_amount +
            (self.shipping_amount or Decimal('0.00')) -
            self.discount_amount
        )

        # Update balance
        self.balance_due = self.total_amount - self.paid_amount

    def apply_payment(self, amount: Decimal):
        """
        Apply a payment to the invoice.

        Args:
            amount: Payment amount to apply
        """
        self.paid_amount += amount
        self.balance_due = self.total_amount - self.paid_amount

        # Update status based on payment
        if self.balance_due == Decimal('0'):
            self.status = 'paid'
        elif self.paid_amount > Decimal('0'):
            self.status = 'partially_paid'


class InvoiceLineItem(Base):
    """
    Invoice line item model.

    Represents individual items/services on an invoice.
    """
    __tablename__ = "financial_invoice_line_items"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Foreign key
    invoice_id = Column(
        String(36),
        ForeignKey("financial_invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Line details
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)

    # Item reference (optional - for inventory integration)
    item_id = Column(String(36))
    item_code = Column(String(50))

    # Quantity and pricing
    quantity = Column(Numeric(18, 4), default=Decimal('1.0000'), nullable=False)
    unit_price = Column(Numeric(18, 2), nullable=False)
    line_total = Column(Numeric(18, 2), nullable=False)

    # Discount
    discount_percentage = Column(Numeric(5, 2), default=Decimal('0.00'))
    discount_amount = Column(Numeric(18, 2), default=Decimal('0.00'))

    # Tax
    tax_rate_id = Column(String(36))  # Reference to tax rate
    tax_percentage = Column(Numeric(5, 2), default=Decimal('0.00'))
    tax_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    is_taxable = Column(Boolean, default=True, nullable=False)

    # Account for revenue recognition
    revenue_account_id = Column(
        String(36),
        ForeignKey("financial_accounts.id")
    )

    # Dimensions (optional)
    department_id = Column(String(36))
    project_id = Column(String(36))

    # Metadata
    extra_data = Column(Text)  # JSON string

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    revenue_account = relationship("Account")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'quantity > 0',
            name='chk_line_quantity_positive'
        ),
        CheckConstraint(
            'unit_price >= 0',
            name='chk_line_price_positive'
        ),
        CheckConstraint(
            'line_total >= 0',
            name='chk_line_total_positive'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<InvoiceLineItem(desc={self.description[:30]}, qty={self.quantity}, total={self.line_total})>"

    def calculate_line_total(self):
        """Calculate line total including discounts and taxes"""
        # Base amount
        base_amount = self.quantity * self.unit_price

        # Initialize defaults if None
        if self.discount_percentage is None:
            self.discount_percentage = Decimal('0.00')
        if self.discount_amount is None:
            self.discount_amount = Decimal('0.00')
        if self.tax_percentage is None:
            self.tax_percentage = Decimal('0.00')
        if self.tax_amount is None:
            self.tax_amount = Decimal('0.00')

        # Apply discount
        if self.discount_percentage > Decimal('0'):
            self.discount_amount = base_amount * (self.discount_percentage / Decimal('100'))

        # Subtotal after discount
        subtotal = base_amount - self.discount_amount

        # Calculate tax
        if self.is_taxable and self.tax_percentage > Decimal('0'):
            self.tax_amount = subtotal * (self.tax_percentage / Decimal('100'))
        else:
            self.tax_amount = Decimal('0.00')

        # Final line total
        self.line_total = subtotal + self.tax_amount
