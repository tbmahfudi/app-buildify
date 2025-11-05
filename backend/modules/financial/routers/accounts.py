"""
Account API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.dependencies import get_current_user, has_permission
from app.models.user import User
from ..models import FinancialAccount
from ..schemas.account import AccountCreate, AccountUpdate, AccountResponse
from ..permissions import FinancialPermissions

router = APIRouter(prefix="/accounts", tags=["financial-accounts"])


@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.ACCOUNTS_READ))
):
    """List all accounts for a company"""
    accounts = db.query(FinancialAccount).filter(
        FinancialAccount.tenant_id == current_user.tenant_id,
        FinancialAccount.company_id == company_id,
        FinancialAccount.is_active == True
    ).all()

    return accounts


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.ACCOUNTS_CREATE))
):
    """Create a new financial account"""

    # Check if account code already exists
    existing = db.query(FinancialAccount).filter(
        FinancialAccount.tenant_id == current_user.tenant_id,
        FinancialAccount.company_id == account.company_id,
        FinancialAccount.code == account.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account with code '{account.code}' already exists"
        )

    # Create account
    db_account = FinancialAccount(
        **account.model_dump(),
        tenant_id=current_user.tenant_id,
        created_by_user_id=current_user.id
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.ACCOUNTS_READ))
):
    """Get a specific account"""
    account = db.query(FinancialAccount).filter(
        FinancialAccount.id == account_id,
        FinancialAccount.tenant_id == current_user.tenant_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.ACCOUNTS_UPDATE))
):
    """Update an account"""
    account = db.query(FinancialAccount).filter(
        FinancialAccount.id == account_id,
        FinancialAccount.tenant_id == current_user.tenant_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Update fields
    for field, value in account_update.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.ACCOUNTS_DELETE))
):
    """Delete (deactivate) an account"""
    account = db.query(FinancialAccount).filter(
        FinancialAccount.id == account_id,
        FinancialAccount.tenant_id == current_user.tenant_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Soft delete by deactivating
    account.is_active = False
    db.commit()

    return None
