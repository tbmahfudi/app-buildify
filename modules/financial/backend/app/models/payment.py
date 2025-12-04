"""
Payment Models for Financial Module

Implements payment processing and allocation to invoices.
"""

from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Numeric, String, Text,
    CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class Payment(Base):
    """
    Payment model.

    Represents customer payments that can be allocated to one or more invoices.
    """
    __tablename__ = "financial_payments"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Multi-tenancy
    tenant_id = Column(String(36), nullable=False, index=True)
    company_id = Column(String(36), nullable=False, index=True)

    # Payment identification
    payment_number = Column(String(50), nullable=False)
    reference_number = Column(String(100))

    # Customer
    customer_id = Column(
        String(36),
        ForeignKey("financial_customers.id"),
        nullable=False,
        index=True
    )

    # Payment details
    payment_date = Column(Date, nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)
    # cash, check, credit_card, bank_transfer, paypal, stripe, other

    # Amounts
    payment_amount = Column(Numeric(18, 2), nullable=False)
    allocated_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    unallocated_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)

    # Currency
    currency_code = Column(String(3), default="USD", nullable=False)

    # Payment method specific fields
    check_number = Column(String(50))
    card_last_four = Column(String(4))
    transaction_id = Column(String(100))  # For online payments

    # Bank details (for bank transfers)
    bank_name = Column(String(100))
    bank_account = Column(String(50))

    # Deposit account
    deposit_account_id = Column(
        String(36),
        ForeignKey("financial_accounts.id"),
        nullable=False
    )

    # Status
    status = Column(String(20), default='pending', nullable=False, index=True)
    # pending, cleared, allocated, partially_allocated, voided

    is_cleared = Column(Boolean, default=False, nullable=False)
    cleared_date = Column(Date)

    # Journal entry linkage
    journal_entry_id = Column(String(36), ForeignKey("financial_journal_entries.id"))

    # Voiding
    is_voided = Column(Boolean, default=False, nullable=False)
    voided_at = Column(DateTime)
    voided_by = Column(String(36))
    void_reason = Column(Text)

    # Description
    description = Column(Text)
    memo = Column(Text)

    # Metadata
    extra_data = Column(Text)  # JSON string

    # Audit fields
    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    deposit_account = relationship("Account", foreign_keys=[deposit_account_id])
    journal_entry = relationship("JournalEntry")
    allocations = relationship(
        "PaymentAllocation",
        back_populates="payment",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'payment_number', name='uq_payment_number'),
        CheckConstraint(
            status.in_(['pending', 'cleared', 'allocated', 'partially_allocated', 'voided']),
            name='chk_payment_status'
        ),
        CheckConstraint(
            'payment_amount > 0',
            name='chk_payment_amount_positive'
        ),
        CheckConstraint(
            'allocated_amount >= 0 AND allocated_amount <= payment_amount',
            name='chk_allocated_amount'
        ),
        CheckConstraint(
            'unallocated_amount >= 0 AND unallocated_amount <= payment_amount',
            name='chk_unallocated_amount'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<Payment(number={self.payment_number}, amount={self.payment_amount}, status={self.status})>"

    @property
    def is_fully_allocated(self):
        """Check if payment is fully allocated"""
        return self.unallocated_amount == Decimal('0')

    @property
    def can_allocate(self):
        """Check if payment can be allocated"""
        return (
            not self.is_voided and
            self.unallocated_amount > Decimal('0')
        )

    @property
    def can_void(self):
        """Check if payment can be voided"""
        return (
            not self.is_voided and
            self.allocated_amount == Decimal('0')
        )

    def calculate_allocation_totals(self):
        """Calculate allocation totals from allocations"""
        self.allocated_amount = sum(
            alloc.allocation_amount
            for alloc in self.allocations
            if not alloc.is_voided
        )
        self.unallocated_amount = self.payment_amount - self.allocated_amount

        # Update status based on allocation
        if self.allocated_amount == Decimal('0'):
            self.status = 'cleared' if self.is_cleared else 'pending'
        elif self.unallocated_amount == Decimal('0'):
            self.status = 'allocated'
        else:
            self.status = 'partially_allocated'


class PaymentAllocation(Base):
    """
    Payment Allocation model.

    Links payments to invoices, tracking how much of each payment
    is applied to each invoice.
    """
    __tablename__ = "financial_payment_allocations"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Foreign keys
    payment_id = Column(
        String(36),
        ForeignKey("financial_payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invoice_id = Column(
        String(36),
        ForeignKey("financial_invoices.id"),
        nullable=False,
        index=True
    )

    # Allocation details
    allocation_date = Column(Date, nullable=False)
    allocation_amount = Column(Numeric(18, 2), nullable=False)

    # Voiding
    is_voided = Column(Boolean, default=False, nullable=False)
    voided_at = Column(DateTime)
    voided_by = Column(String(36))

    # Description
    description = Column(Text)

    # Metadata
    extra_data = Column(Text)  # JSON string

    # Audit fields
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    payment = relationship("Payment", back_populates="allocations")
    invoice = relationship("Invoice")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'allocation_amount > 0',
            name='chk_allocation_amount_positive'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<PaymentAllocation(payment={self.payment_id[:8]}, invoice={self.invoice_id[:8]}, amount={self.allocation_amount})>"
