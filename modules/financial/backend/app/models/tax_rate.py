"""
Tax Rate Model for Financial Module

Manages tax rates and tax calculations.
"""

from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Numeric, String, Text,
    CheckConstraint, UniqueConstraint, func
)

from ..core.database import Base


class TaxRate(Base):
    """
    Tax Rate model.

    Defines tax rates that can be applied to invoices and transactions.
    """
    __tablename__ = "financial_tax_rates"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Multi-tenancy
    tenant_id = Column(String(36), nullable=False, index=True)
    company_id = Column(String(36), nullable=False, index=True)

    # Tax rate identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Tax rate details
    rate_percentage = Column(Numeric(5, 2), nullable=False)
    # e.g., 7.50 for 7.5%

    # Tax type
    tax_type = Column(String(50), nullable=False)
    # sales_tax, vat, gst, excise, service_tax, other

    # Tax authority
    tax_authority = Column(String(255))
    tax_jurisdiction = Column(String(100))  # federal, state, county, city

    # Effective dates
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Tax calculation method
    is_compound = Column(Boolean, default=False, nullable=False)
    # If true, tax is calculated on subtotal + other taxes

    # Account for tax collection
    tax_account_id = Column(String(36))
    # Foreign key to financial_accounts, but not enforced to avoid circular imports

    # Applicability
    applies_to_sales = Column(Boolean, default=True, nullable=False)
    applies_to_purchases = Column(Boolean, default=False, nullable=False)

    # Geographic scope
    country_code = Column(String(2))
    state_code = Column(String(50))
    city = Column(String(100))
    postal_code = Column(String(20))

    # Metadata
    extra_data = Column(Text)  # JSON string

    # Audit fields
    created_by = Column(String(36))
    updated_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'code', name='uq_tax_rate_code'),
        CheckConstraint(
            'rate_percentage >= 0 AND rate_percentage <= 100',
            name='chk_rate_percentage_range'
        ),
        CheckConstraint(
            tax_type.in_(['sales_tax', 'vat', 'gst', 'excise', 'service_tax', 'other']),
            name='chk_tax_type'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<TaxRate(code={self.code}, name={self.name}, rate={self.rate_percentage}%)>"

    @property
    def full_name(self):
        """Return full tax rate name with percentage"""
        return f"{self.name} ({self.rate_percentage}%)"

    @property
    def is_valid(self):
        """Check if tax rate is currently valid"""
        from datetime import date
        today = date.today()

        if not self.is_active:
            return False

        if self.effective_from > today:
            return False

        if self.effective_to and self.effective_to < today:
            return False

        return True

    def calculate_tax(self, amount: Decimal) -> Decimal:
        """
        Calculate tax amount for a given base amount.

        Args:
            amount: Base amount to calculate tax on

        Returns:
            Tax amount
        """
        return amount * (self.rate_percentage / Decimal('100'))
