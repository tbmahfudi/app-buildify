"""
Account Model for Financial Module

Represents accounts in the chart of accounts.
Supports hierarchical structure and multi-currency.
"""

from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Numeric, String, Text,
    CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class Account(Base):
    """
    Chart of Accounts model.

    Supports:
    - Hierarchical structure (parent/child accounts)
    - Multi-currency
    - Balance tracking
    - Account types: asset, liability, equity, revenue, expense
    """
    __tablename__ = "financial_accounts"

    # Primary key - using UUID from base
    id = Column(String(36), primary_key=True)

    # Multi-tenancy (REQUIRED)
    tenant_id = Column(String(36), nullable=False, index=True)
    company_id = Column(String(36), nullable=False, index=True)

    # Account identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Account classification
    type = Column(String(50), nullable=False)  # asset, liability, equity, revenue, expense
    category = Column(String(100))  # cash, receivables, fixed_assets, etc.
    sub_category = Column(String(100))  # bank_accounts, petty_cash, etc.

    # Account properties
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_header = Column(Boolean, default=False, nullable=False)  # Header account (no transactions)
    parent_account_id = Column(String(36), ForeignKey("financial_accounts.id"))

    # Balance tracking
    current_balance = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    debit_balance = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    credit_balance = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)

    # Currency
    currency_code = Column(String(3), default="USD", nullable=False)

    # Additional properties
    tax_category = Column(String(50))  # taxable, non_taxable, tax_exempt
    requires_department = Column(Boolean, default=False, nullable=False)
    requires_project = Column(Boolean, default=False, nullable=False)

    # Metadata (JSON stored as string for compatibility)
    extra_data = Column(Text)  # Will be JSON string

    # Audit fields
    created_by = Column(String(36))
    updated_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    parent_account = relationship(
        "Account",
        remote_side=[id],
        backref="child_accounts"
    )

    # Constraints
    __table_args__ = (
        # Unique account code per company
        UniqueConstraint('tenant_id', 'company_id', 'code', name='uq_account_code'),

        # Validate account type
        CheckConstraint(
            type.in_(['asset', 'liability', 'equity', 'revenue', 'expense']),
            name='chk_account_type'
        ),

        # Index for performance
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<Account(code={self.code}, name={self.name}, type={self.type})>"

    @property
    def full_name(self):
        """Return full account name with code"""
        return f"{self.code} - {self.name}"

    @property
    def is_debit_account(self):
        """Check if this is a debit-normal account"""
        return self.type in ['asset', 'expense']

    @property
    def is_credit_account(self):
        """Check if this is a credit-normal account"""
        return self.type in ['liability', 'equity', 'revenue']

    def calculate_balance(self):
        """
        Calculate correct balance based on account type.

        For asset/expense: Balance = Debit - Credit
        For liability/equity/revenue: Balance = Credit - Debit
        """
        if self.is_debit_account:
            return self.debit_balance - self.credit_balance
        else:
            return self.credit_balance - self.debit_balance

    def update_balance(self, debit_amount: Decimal = Decimal('0'),
                      credit_amount: Decimal = Decimal('0')):
        """
        Update account balance with debit/credit amounts.

        Args:
            debit_amount: Amount to add to debit balance
            credit_amount: Amount to add to credit balance
        """
        self.debit_balance += debit_amount
        self.credit_balance += credit_amount
        self.current_balance = self.calculate_balance()
