"""
Journal Entry Models for Financial Module

Implements double-entry bookkeeping with journal entries and lines.
"""

from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class JournalEntry(Base):
    """
    Journal Entry header model.

    Represents a journal entry in double-entry bookkeeping.
    Each entry must have balanced debits and credits.
    """
    __tablename__ = "financial_journal_entries"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Multi-tenancy
    tenant_id = Column(String(36), nullable=False, index=True)
    company_id = Column(String(36), nullable=False, index=True)

    # Entry identification
    entry_number = Column(String(50), nullable=False)
    reference_number = Column(String(100))

    # Entry details
    entry_date = Column(Date, nullable=False, index=True)
    posting_date = Column(Date)

    # Description
    description = Column(Text, nullable=False)
    memo = Column(Text)

    # Status
    status = Column(String(20), default='draft', nullable=False, index=True)
    is_posted = Column(Boolean, default=False, nullable=False)
    posted_at = Column(DateTime)
    posted_by = Column(String(36))

    # Reversal tracking
    is_reversal = Column(Boolean, default=False, nullable=False)
    reversed_entry_id = Column(String(36), ForeignKey("financial_journal_entries.id"))
    reversed_at = Column(DateTime)
    reversed_by = Column(String(36))

    # Source tracking
    source_type = Column(String(50))  # manual, invoice, payment, adjustment
    source_id = Column(String(36))

    # Totals (must be equal)
    total_debit = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    total_credit = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)

    # Currency
    currency_code = Column(String(3), default="USD", nullable=False)

    # Metadata
    tags = Column(Text)  # JSON string
    extra_data = Column(Text)  # JSON string

    # Audit fields
    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    lines = relationship(
        "JournalEntryLine",
        back_populates="journal_entry",
        cascade="all, delete-orphan"
    )
    reversed_entry = relationship(
        "JournalEntry",
        remote_side=[id],
        backref="reversal_entries"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'entry_number', name='uq_entry_number'),
        CheckConstraint(
            status.in_(['draft', 'posted', 'reversed', 'void']),
            name='chk_entry_status'
        ),
        CheckConstraint(
            'total_debit = total_credit',
            name='chk_balanced'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<JournalEntry(number={self.entry_number}, status={self.status})>"

    @property
    def is_balanced(self):
        """Check if debits equal credits"""
        return self.total_debit == self.total_credit

    @property
    def can_post(self):
        """Check if entry can be posted"""
        return (
            self.status == 'draft' and
            self.is_balanced and
            len(self.lines) >= 2
        )

    @property
    def can_edit(self):
        """Check if entry can be edited"""
        return self.status == 'draft'

    def calculate_totals(self):
        """Calculate total debits and credits from lines"""
        self.total_debit = sum(line.debit_amount for line in self.lines)
        self.total_credit = sum(line.credit_amount for line in self.lines)


class JournalEntryLine(Base):
    """
    Journal Entry line model.

    Represents individual debit/credit lines in a journal entry.
    """
    __tablename__ = "financial_journal_entry_lines"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Foreign keys
    journal_entry_id = Column(
        String(36),
        ForeignKey("financial_journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    account_id = Column(
        String(36),
        ForeignKey("financial_accounts.id"),
        nullable=False,
        index=True
    )

    # Line details
    line_number = Column(Integer, nullable=False)
    description = Column(Text)

    # Amounts (either debit OR credit, not both)
    debit_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    credit_amount = Column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)

    # Dimensions (optional)
    department_id = Column(String(36))
    project_id = Column(String(36))

    # Metadata
    extra_data = Column(Text)  # JSON string

    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            '(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0)',
            name='chk_line_amount'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<JournalEntryLine(account={self.account.code if self.account else 'N/A'}, debit={self.debit_amount}, credit={self.credit_amount})>"

    @property
    def is_debit(self):
        """Check if this is a debit line"""
        return self.debit_amount > Decimal('0')

    @property
    def is_credit(self):
        """Check if this is a credit line"""
        return self.credit_amount > Decimal('0')

    @property
    def amount(self):
        """Get the line amount (either debit or credit)"""
        return self.debit_amount if self.is_debit else self.credit_amount
