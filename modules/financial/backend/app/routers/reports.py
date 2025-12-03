"""
Reports Router - Financial Reporting
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.report_service import ReportService

router = APIRouter()


@router.get("/trial-balance")
async def get_trial_balance(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    as_of_date: date = Query(..., description="As of date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate trial balance report.

    Shows all account balances with debits and credits.
    """
    return await ReportService.get_trial_balance(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        as_of_date=as_of_date
    )


@router.get("/balance-sheet")
async def get_balance_sheet(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    as_of_date: date = Query(..., description="As of date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate balance sheet report.

    Shows assets, liabilities, and equity.
    """
    return await ReportService.get_balance_sheet(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        as_of_date=as_of_date
    )


@router.get("/income-statement")
async def get_income_statement(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    from_date: date = Query(..., description="From date"),
    to_date: date = Query(..., description="To date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate income statement (profit & loss) report.

    Shows revenue, expenses, and net income for a period.
    """
    return await ReportService.get_income_statement(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        from_date=from_date,
        to_date=to_date
    )


@router.get("/aged-receivables")
async def get_aged_receivables(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    as_of_date: date = Query(..., description="As of date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate aged receivables report.

    Shows outstanding customer balances by age.
    """
    return await ReportService.get_aged_receivables(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        as_of_date=as_of_date
    )


@router.get("/cash-flow")
async def get_cash_flow_statement(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    from_date: date = Query(..., description="From date"),
    to_date: date = Query(..., description="To date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate cash flow statement.

    Shows cash flows from operating, investing, and financing activities.
    """
    return await ReportService.get_cash_flow_statement(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        from_date=from_date,
        to_date=to_date
    )


@router.get("/account-ledger/{account_id}")
async def get_account_ledger(
    account_id: str,
    from_date: date = Query(..., description="From date"),
    to_date: date = Query(..., description="To date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate general ledger report for a specific account.

    Shows all transactions for an account with running balance.
    """
    ledger = await ReportService.get_account_ledger(
        db=db,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date
    )

    if not ledger:
        raise HTTPException(status_code=404, detail="Account not found")

    return ledger
