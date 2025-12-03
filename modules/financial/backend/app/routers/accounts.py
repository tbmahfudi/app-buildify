"""
Accounts Router - Chart of Accounts Management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.account_service import AccountService
from ..schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse,
    AccountTreeNode,
    AccountBalanceUpdate,
    AccountBalance,
)

router = APIRouter()


@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_account_id: Optional[str] = Query(None, description="Filter by parent account"),
    search: Optional[str] = Query(None, description="Search in code and name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all accounts for a company with filtering and pagination.

    Args:
        tenant_id: Tenant ID
        company_id: Company ID
        account_type: Filter by account type (asset, liability, equity, revenue, expense)
        is_active: Filter by active status
        parent_account_id: Filter by parent account ID
        search: Search term for code and name
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session

    Returns:
        Paginated list of accounts
    """
    skip = (page - 1) * page_size

    accounts, total = await AccountService.list_accounts(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        account_type=account_type,
        is_active=is_active,
        parent_account_id=parent_account_id,
        search=search,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return AccountListResponse(
        accounts=[AccountResponse.model_validate(acc) for acc in accounts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new account.

    Args:
        account_data: Account creation data
        db: Database session

    Returns:
        Created account

    Raises:
        400: If account code already exists
        400: If parent account doesn't exist or is invalid
    """
    try:
        account = await AccountService.create_account(db, account_data)
        return AccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tree", response_model=List[AccountTreeNode])
async def get_chart_of_accounts_tree(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chart of accounts as a hierarchical tree structure.

    Args:
        tenant_id: Tenant ID
        company_id: Company ID
        is_active: Filter by active status
        db: Database session

    Returns:
        Tree structure of accounts
    """
    tree = await AccountService.get_chart_of_accounts_tree(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        is_active=is_active
    )

    return tree


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get account by ID.

    Args:
        account_id: Account ID
        db: Database session

    Returns:
        Account details

    Raises:
        404: If account not found
    """
    account = await AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an account.

    Args:
        account_id: Account ID
        account_data: Account update data
        db: Database session

    Returns:
        Updated account

    Raises:
        404: If account not found
        400: If update validation fails
    """
    try:
        account = await AccountService.update_account(db, account_id, account_data)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        return AccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{account_id}", status_code=204)
async def delete_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an account.

    Args:
        account_id: Account ID
        db: Database session

    Returns:
        No content

    Raises:
        404: If account not found
        400: If account has child accounts or non-zero balance
    """
    try:
        deleted = await AccountService.delete_account(db, account_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Account not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{account_id}/balance", response_model=AccountBalance)
async def get_account_balance(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get account balance details.

    Args:
        account_id: Account ID
        db: Database session

    Returns:
        Account balance details

    Raises:
        404: If account not found
    """
    balance = await AccountService.get_account_balance(db, account_id)
    if not balance:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountBalance(**balance)


@router.patch("/{account_id}/balance", response_model=AccountResponse)
async def update_account_balance(
    account_id: str,
    balance_update: AccountBalanceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update account balance.

    Args:
        account_id: Account ID
        balance_update: Balance update data
        db: Database session

    Returns:
        Updated account

    Raises:
        404: If account not found
    """
    account = await AccountService.update_account_balance(db, account_id, balance_update)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountResponse.model_validate(account)


@router.post("/{account_id}/deactivate", response_model=AccountResponse)
async def deactivate_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate an account (soft delete).

    Args:
        account_id: Account ID
        db: Database session

    Returns:
        Deactivated account

    Raises:
        404: If account not found
    """
    account = await AccountService.deactivate_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountResponse.model_validate(account)


@router.post("/{account_id}/activate", response_model=AccountResponse)
async def activate_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Activate an account.

    Args:
        account_id: Account ID
        db: Database session

    Returns:
        Activated account

    Raises:
        404: If account not found
    """
    account = await AccountService.activate_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountResponse.model_validate(account)
