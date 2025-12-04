"""
Journal Entry Service

Business logic for Journal Entry operations.
Implements double-entry bookkeeping with validation.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import uuid4

from ..models.journal_entry import JournalEntry, JournalEntryLine
from ..schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryLineCreate,
)
from ..schemas.account import AccountBalanceUpdate
from .account_service import AccountService


class JournalEntryService:
    """
    Service for managing journal entries in double-entry bookkeeping.
    """

    @staticmethod
    async def create_journal_entry(
        db: AsyncSession,
        entry_data: JournalEntryCreate
    ) -> JournalEntry:
        """
        Create a new journal entry with lines.

        Args:
            db: Database session
            entry_data: Journal entry creation data with lines

        Returns:
            Created journal entry with lines

        Raises:
            ValueError: If entry is not balanced (debits != credits)
            ValueError: If entry has less than 2 lines
            ValueError: If entry number already exists
            ValueError: If any account doesn't exist
        """
        # Validate minimum lines
        if len(entry_data.lines) < 2:
            raise ValueError("Journal entry must have at least 2 lines")

        # Validate balanced (already done in schema, but double-check)
        total_debit = sum(line.debit_amount for line in entry_data.lines)
        total_credit = sum(line.credit_amount for line in entry_data.lines)

        if total_debit != total_credit:
            raise ValueError(
                f"Journal entry must be balanced. Debits: {total_debit}, Credits: {total_credit}"
            )

        # Check if entry number already exists
        existing = await JournalEntryService._get_entry_by_number(
            db,
            entry_data.tenant_id,
            entry_data.company_id,
            entry_data.entry_number
        )
        if existing:
            raise ValueError(f"Journal entry with number '{entry_data.entry_number}' already exists")

        # Validate all accounts exist
        for line in entry_data.lines:
            account = await AccountService.get_account(db, line.account_id)
            if not account:
                raise ValueError(f"Account with ID '{line.account_id}' does not exist")
            if account.is_header:
                raise ValueError(f"Cannot post to header account '{account.code} - {account.name}'")
            if not account.is_active:
                raise ValueError(f"Cannot post to inactive account '{account.code} - {account.name}'")

        # Create journal entry
        entry = JournalEntry(
            id=str(uuid4()),
            tenant_id=entry_data.tenant_id,
            company_id=entry_data.company_id,
            entry_number=entry_data.entry_number,
            reference_number=entry_data.reference_number,
            entry_date=entry_data.entry_date,
            posting_date=entry_data.posting_date,
            description=entry_data.description,
            memo=entry_data.memo,
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            currency_code=entry_data.currency_code,
            tags=entry_data.tags,
            extra_data=entry_data.extra_data,
            total_debit=total_debit,
            total_credit=total_credit,
            status='draft',
            is_posted=False,
            created_by=entry_data.created_by,
        )

        # Create journal entry lines
        for line_data in entry_data.lines:
            line = JournalEntryLine(
                id=str(uuid4()),
                journal_entry_id=entry.id,
                account_id=line_data.account_id,
                line_number=line_data.line_number,
                description=line_data.description,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount,
                department_id=line_data.department_id,
                project_id=line_data.project_id,
                extra_data=line_data.extra_data,
            )
            entry.lines.append(line)

        db.add(entry)
        await db.commit()
        await db.refresh(entry, ['lines'])

        return entry

    @staticmethod
    async def get_journal_entry(
        db: AsyncSession,
        entry_id: str
    ) -> Optional[JournalEntry]:
        """
        Get journal entry by ID with lines.

        Args:
            db: Database session
            entry_id: Journal entry ID

        Returns:
            Journal entry with lines or None if not found
        """
        result = await db.execute(
            select(JournalEntry)
            .where(JournalEntry.id == entry_id)
            .options(
                selectinload(JournalEntry.lines),
                selectinload(JournalEntry.reversed_entry)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_journal_entries(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        account_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[JournalEntry], int]:
        """
        List journal entries with filtering and pagination.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            status: Filter by status (draft, posted, reversed, void)
            from_date: Filter by entry date from
            to_date: Filter by entry date to
            account_id: Filter by account used in lines
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (journal entries list, total count)
        """
        # Build base query
        query = select(JournalEntry).where(
            and_(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.company_id == company_id
            )
        )

        # Apply filters
        if status:
            query = query.where(JournalEntry.status == status)

        if from_date:
            query = query.where(JournalEntry.entry_date >= from_date)

        if to_date:
            query = query.where(JournalEntry.entry_date <= to_date)

        if account_id:
            # Join with lines to filter by account
            query = query.join(JournalEntryLine).where(
                JournalEntryLine.account_id == account_id
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination and get results
        query = (
            query
            .options(selectinload(JournalEntry.lines))
            .order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_number.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        entries = result.scalars().unique().all()

        return list(entries), total

    @staticmethod
    async def update_journal_entry(
        db: AsyncSession,
        entry_id: str,
        entry_data: JournalEntryUpdate
    ) -> Optional[JournalEntry]:
        """
        Update a journal entry (draft only).

        Args:
            db: Database session
            entry_id: Journal entry ID
            entry_data: Journal entry update data

        Returns:
            Updated journal entry or None if not found

        Raises:
            ValueError: If entry is not in draft status
            ValueError: If entry number conflicts
        """
        entry = await JournalEntryService.get_journal_entry(db, entry_id)
        if not entry:
            return None

        # Only draft entries can be updated
        if entry.status != 'draft':
            raise ValueError("Only draft journal entries can be updated")

        # Check if entry number is being changed and conflicts
        if entry_data.entry_number and entry_data.entry_number != entry.entry_number:
            existing = await JournalEntryService._get_entry_by_number(
                db,
                entry.tenant_id,
                entry.company_id,
                entry_data.entry_number
            )
            if existing:
                raise ValueError(f"Journal entry with number '{entry_data.entry_number}' already exists")

        # Update fields
        update_dict = entry_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(entry, field, value)

        await db.commit()
        await db.refresh(entry, ['lines'])

        return entry

    @staticmethod
    async def delete_journal_entry(
        db: AsyncSession,
        entry_id: str
    ) -> bool:
        """
        Delete a journal entry (draft only).

        Args:
            db: Database session
            entry_id: Journal entry ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If entry is not in draft status
        """
        entry = await JournalEntryService.get_journal_entry(db, entry_id)
        if not entry:
            return False

        # Only draft entries can be deleted
        if entry.status != 'draft':
            raise ValueError("Only draft journal entries can be deleted")

        await db.delete(entry)
        await db.commit()

        return True

    @staticmethod
    async def post_journal_entry(
        db: AsyncSession,
        entry_id: str,
        posting_date: Optional[date] = None,
        posted_by: str = None
    ) -> Optional[JournalEntry]:
        """
        Post a journal entry and update account balances.

        Args:
            db: Database session
            entry_id: Journal entry ID
            posting_date: Posting date (defaults to today)
            posted_by: User ID who posted the entry

        Returns:
            Posted journal entry or None if not found

        Raises:
            ValueError: If entry cannot be posted
            ValueError: If entry is not balanced
            ValueError: If entry has less than 2 lines
        """
        entry = await JournalEntryService.get_journal_entry(db, entry_id)
        if not entry:
            return None

        # Validate entry can be posted
        if entry.status != 'draft':
            raise ValueError(f"Cannot post entry with status '{entry.status}'")

        if not entry.is_balanced:
            raise ValueError(
                f"Cannot post unbalanced entry. Debits: {entry.total_debit}, Credits: {entry.total_credit}"
            )

        if len(entry.lines) < 2:
            raise ValueError("Journal entry must have at least 2 lines")

        # Update entry status
        entry.status = 'posted'
        entry.is_posted = True
        entry.posting_date = posting_date or date.today()
        entry.posted_at = datetime.now()
        entry.posted_by = posted_by

        # Update account balances for each line
        for line in entry.lines:
            balance_update = AccountBalanceUpdate(
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount
            )

            account = await AccountService.update_account_balance(
                db,
                line.account_id,
                balance_update
            )

            if not account:
                raise ValueError(f"Account with ID '{line.account_id}' not found")

        await db.commit()
        await db.refresh(entry, ['lines'])

        return entry

    @staticmethod
    async def reverse_journal_entry(
        db: AsyncSession,
        entry_id: str,
        reversal_date: date,
        description: str,
        reversed_by: str
    ) -> Optional[JournalEntry]:
        """
        Reverse a posted journal entry by creating a reversal entry.

        Args:
            db: Database session
            entry_id: Journal entry ID to reverse
            reversal_date: Date of reversal
            description: Description for reversal entry
            reversed_by: User ID who reversed the entry

        Returns:
            Reversal journal entry or None if original entry not found

        Raises:
            ValueError: If entry is not posted
            ValueError: If entry is already reversed
        """
        # Get original entry
        original_entry = await JournalEntryService.get_journal_entry(db, entry_id)
        if not original_entry:
            return None

        # Validate entry can be reversed
        if original_entry.status != 'posted':
            raise ValueError("Only posted journal entries can be reversed")

        if original_entry.is_reversal:
            raise ValueError("Cannot reverse a reversal entry")

        # Check if already reversed
        if original_entry.reversed_at is not None:
            raise ValueError("Journal entry has already been reversed")

        # Generate reversal entry number
        reversal_number = f"{original_entry.entry_number}-REV"

        # Check if reversal already exists
        existing = await JournalEntryService._get_entry_by_number(
            db,
            original_entry.tenant_id,
            original_entry.company_id,
            reversal_number
        )
        if existing:
            # Append timestamp to make unique
            reversal_number = f"{reversal_number}-{int(datetime.now().timestamp())}"

        # Create reversal entry with opposite amounts
        reversal_entry = JournalEntry(
            id=str(uuid4()),
            tenant_id=original_entry.tenant_id,
            company_id=original_entry.company_id,
            entry_number=reversal_number,
            reference_number=original_entry.reference_number,
            entry_date=reversal_date,
            posting_date=reversal_date,
            description=description,
            memo=f"Reversal of {original_entry.entry_number}",
            source_type=original_entry.source_type,
            source_id=original_entry.source_id,
            currency_code=original_entry.currency_code,
            total_debit=original_entry.total_credit,  # Swap debit/credit
            total_credit=original_entry.total_debit,
            status='posted',
            is_posted=True,
            posted_at=datetime.now(),
            posted_by=reversed_by,
            is_reversal=True,
            reversed_entry_id=original_entry.id,
            created_by=reversed_by,
        )

        # Create reversal lines with opposite amounts
        for original_line in original_entry.lines:
            reversal_line = JournalEntryLine(
                id=str(uuid4()),
                journal_entry_id=reversal_entry.id,
                account_id=original_line.account_id,
                line_number=original_line.line_number,
                description=original_line.description or description,
                debit_amount=original_line.credit_amount,  # Swap debit/credit
                credit_amount=original_line.debit_amount,
                department_id=original_line.department_id,
                project_id=original_line.project_id,
                extra_data=original_line.extra_data,
            )
            reversal_entry.lines.append(reversal_line)

        # Update account balances for reversal
        for line in reversal_entry.lines:
            balance_update = AccountBalanceUpdate(
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount
            )

            await AccountService.update_account_balance(
                db,
                line.account_id,
                balance_update
            )

        # Mark original entry as reversed
        original_entry.status = 'reversed'
        original_entry.reversed_at = datetime.now()
        original_entry.reversed_by = reversed_by

        db.add(reversal_entry)
        await db.commit()
        await db.refresh(reversal_entry, ['lines'])

        return reversal_entry

    @staticmethod
    async def get_account_transactions(
        db: AsyncSession,
        account_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all transactions (journal entry lines) for an account.

        Args:
            db: Database session
            account_id: Account ID
            from_date: Filter by entry date from
            to_date: Filter by entry date to

        Returns:
            List of transaction details with journal entry info
        """
        # Build query to get lines with journal entry details
        query = (
            select(JournalEntryLine, JournalEntry)
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntryLine.account_id == account_id)
            .where(JournalEntry.is_posted == True)
        )

        # Apply date filters
        if from_date:
            query = query.where(JournalEntry.entry_date >= from_date)

        if to_date:
            query = query.where(JournalEntry.entry_date <= to_date)

        # Order by date
        query = query.order_by(
            JournalEntry.entry_date.asc(),
            JournalEntry.entry_number.asc(),
            JournalEntryLine.line_number.asc()
        )

        result = await db.execute(query)
        rows = result.all()

        # Format transactions
        transactions = []
        running_balance = Decimal('0.00')

        for line, entry in rows:
            # Calculate running balance (debit increases, credit decreases for most accounts)
            running_balance += line.debit_amount - line.credit_amount

            transactions.append({
                "transaction_id": line.id,
                "entry_id": entry.id,
                "entry_number": entry.entry_number,
                "entry_date": entry.entry_date,
                "posting_date": entry.posting_date,
                "description": line.description or entry.description,
                "reference_number": entry.reference_number,
                "debit_amount": line.debit_amount,
                "credit_amount": line.credit_amount,
                "running_balance": running_balance,
                "status": entry.status,
                "is_reversal": entry.is_reversal,
            })

        return transactions

    @staticmethod
    async def _get_entry_by_number(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        entry_number: str
    ) -> Optional[JournalEntry]:
        """
        Get journal entry by entry number (internal helper).

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            entry_number: Entry number

        Returns:
            Journal entry or None if not found
        """
        result = await db.execute(
            select(JournalEntry).where(
                and_(
                    JournalEntry.tenant_id == tenant_id,
                    JournalEntry.company_id == company_id,
                    JournalEntry.entry_number == entry_number
                )
            )
        )
        return result.scalar_one_or_none()
