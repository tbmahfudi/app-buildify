"""
Customer Model for Financial Module

Represents customers for invoicing and accounts receivable.
"""

from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class Customer(Base):
    """
    Customer master data model.

    Stores customer information for invoicing and accounts receivable.
    """
    __tablename__ = "financial_customers"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Multi-tenancy
    tenant_id = Column(String(36), nullable=False, index=True)
    company_id = Column(String(36), nullable=False, index=True)

    # Customer identification
    customer_number = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))

    # Contact information
    email = Column(String(255), index=True)
    phone = Column(String(50))
    website = Column(String(255))

    # Billing address
    billing_address_line1 = Column(String(255))
    billing_address_line2 = Column(String(255))
    billing_city = Column(String(100))
    billing_state = Column(String(100))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(100))

    # Shipping address
    shipping_address_line1 = Column(String(255))
    shipping_address_line2 = Column(String(255))
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_postal_code = Column(String(20))
    shipping_country = Column(String(100))

    # Financial details
    currency_code = Column(String(3), default="USD", nullable=False)
    payment_terms_days = Column(Integer, default=30, nullable=False)
    credit_limit = Column(Numeric(18, 2))

    # Tax information
    tax_id = Column(String(50))
    tax_exempt = Column(Boolean, default=False, nullable=False)

    # Accounts
    receivables_account_id = Column(String(36), ForeignKey("financial_accounts.id"))

    # Balance tracking
    current_balance = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    overdue_balance = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata
    notes = Column(Text)
    extra_data = Column(Text)  # JSON string

    # Audit fields
    created_by = Column(String(36))
    updated_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    receivables_account = relationship("Account", foreign_keys=[receivables_account_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'customer_number', name='uq_customer_number'),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<Customer(number={self.customer_number}, name={self.name})>"

    @property
    def full_address(self):
        """Return formatted billing address"""
        parts = [
            self.billing_address_line1,
            self.billing_address_line2,
            f"{self.billing_city}, {self.billing_state} {self.billing_postal_code}",
            self.billing_country
        ]
        return "\n".join(filter(None, parts))

    @property
    def has_overdue_balance(self):
        """Check if customer has overdue invoices"""
        return self.overdue_balance > Decimal('0')

    def update_balance(self, amount: Decimal):
        """
        Update customer balance.

        Args:
            amount: Amount to add (positive) or subtract (negative)
        """
        self.current_balance += amount
