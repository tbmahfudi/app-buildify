"""
Journal Entries Router - Double-Entry Bookkeeping Management
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.journal_entry_service import JournalEntryService
from ..schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryListResponse,
    JournalEntryPostRequest,
    JournalEntryReverseRequest,
)

router = APIRouter()


@router.get("/", response_model=JournalEntryListResponse)
async def list_journal_entries(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    status: Optional[str] = Query(None, description="Filter by status: draft, posted, reversed, void"),
    from_date: Optional[date] = Query(None, description="Filter by entry date from"),
    to_date: Optional[date] = Query(None, description="Filter by entry date to"),
    account_id: Optional[str] = Query(None, description="Filter by account used in lines"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all journal entries for a company with filtering and pagination.

    Args:
        tenant_id: Tenant ID
        company_id: Company ID
        status: Filter by entry status
        from_date: Filter by entry date from (inclusive)
        to_date: Filter by entry date to (inclusive)
        account_id: Filter entries that use this account
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session

    Returns:
        Paginated list of journal entries with lines
    """
    skip = (page - 1) * page_size

    entries, total = await JournalEntryService.list_journal_entries(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        account_id=account_id,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return JournalEntryListResponse(
        entries=[JournalEntryResponse.model_validate(entry) for entry in entries],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=JournalEntryResponse, status_code=201)
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new journal entry with lines.

    Args:
        entry_data: Journal entry creation data
        db: Database session

    Returns:
        Created journal entry with lines

    Raises:
        400: If entry is not balanced or validation fails
        400: If entry number already exists
        400: If any account doesn't exist or is invalid
    """
    try:
        entry = await JournalEntryService.create_journal_entry(db, entry_data)
        return JournalEntryResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get journal entry by ID with lines.

    Args:
        entry_id: Journal entry ID
        db: Database session

    Returns:
        Journal entry details with lines

    Raises:
        404: If journal entry not found
    """
    entry = await JournalEntryService.get_journal_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return JournalEntryResponse.model_validate(entry)


@router.put("/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: str,
    entry_data: JournalEntryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a journal entry (draft only).

    Only draft journal entries can be updated. Posted, reversed, or void entries
    are immutable.

    Args:
        entry_id: Journal entry ID
        entry_data: Journal entry update data
        db: Database session

    Returns:
        Updated journal entry

    Raises:
        404: If journal entry not found
        400: If entry is not in draft status
        400: If update validation fails
    """
    try:
        entry = await JournalEntryService.update_journal_entry(db, entry_id, entry_data)
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return JournalEntryResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}", status_code=204)
async def delete_journal_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a journal entry (draft only).

    Only draft journal entries can be deleted. Posted, reversed, or void entries
    cannot be deleted.

    Args:
        entry_id: Journal entry ID
        db: Database session

    Returns:
        No content

    Raises:
        404: If journal entry not found
        400: If entry is not in draft status
    """
    try:
        deleted = await JournalEntryService.delete_journal_entry(db, entry_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Journal entry not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/post", response_model=JournalEntryResponse)
async def post_journal_entry(
    entry_id: str,
    post_request: JournalEntryPostRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Post a journal entry and update account balances.

    Posting a journal entry:
    1. Changes status from 'draft' to 'posted'
    2. Makes the entry immutable
    3. Updates all affected account balances
    4. Records posting date and user

    Args:
        entry_id: Journal entry ID
        post_request: Posting request with date and user
        db: Database session

    Returns:
        Posted journal entry

    Raises:
        404: If journal entry not found
        400: If entry cannot be posted (not draft, not balanced, etc.)
    """
    try:
        entry = await JournalEntryService.post_journal_entry(
            db=db,
            entry_id=entry_id,
            posting_date=post_request.posting_date,
            posted_by=post_request.posted_by
        )
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return JournalEntryResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/reverse", response_model=JournalEntryResponse)
async def reverse_journal_entry(
    entry_id: str,
    reverse_request: JournalEntryReverseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reverse a posted journal entry.

    Reversing a journal entry:
    1. Creates a new entry with opposite debit/credit amounts
    2. Marks the original entry as 'reversed'
    3. Updates account balances to reflect the reversal
    4. Links the reversal entry to the original

    Args:
        entry_id: Journal entry ID to reverse
        reverse_request: Reversal request with date, description, and user
        db: Database session

    Returns:
        Reversal journal entry (new entry)

    Raises:
        404: If journal entry not found
        400: If entry cannot be reversed (not posted, already reversed, etc.)
    """
    try:
        reversal_entry = await JournalEntryService.reverse_journal_entry(
            db=db,
            entry_id=entry_id,
            reversal_date=reverse_request.reversal_date,
            description=reverse_request.description,
            reversed_by=reverse_request.reversed_by
        )
        if not reversal_entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        return JournalEntryResponse.model_validate(reversal_entry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}/transactions", response_model=List[dict])
async def get_account_transactions(
    account_id: str,
    from_date: Optional[date] = Query(None, description="Filter by entry date from"),
    to_date: Optional[date] = Query(None, description="Filter by entry date to"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all transactions (journal entry lines) for an account.

    Returns a chronological list of all posted journal entry lines that affect
    the specified account, including running balance calculations.

    Args:
        account_id: Account ID
        from_date: Filter by entry date from (inclusive)
        to_date: Filter by entry date to (inclusive)
        db: Database session

    Returns:
        List of transactions with journal entry details and running balance

    Each transaction includes:
        - transaction_id: Line ID
        - entry_id: Journal entry ID
        - entry_number: Journal entry number
        - entry_date: Entry date
        - posting_date: Posting date
        - description: Transaction description
        - reference_number: Reference number
        - debit_amount: Debit amount
        - credit_amount: Credit amount
        - running_balance: Running balance after this transaction
        - status: Entry status
        - is_reversal: Whether this is a reversal entry
    """
    transactions = await JournalEntryService.get_account_transactions(
        db=db,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date
    )

    return transactions
