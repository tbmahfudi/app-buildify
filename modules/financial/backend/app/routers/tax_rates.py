"""
Tax Rates Router - Tax Rate Management
"""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.tax_rate_service import TaxRateService
from ..schemas.tax_rate import (
    TaxRateCreate,
    TaxRateUpdate,
    TaxRateResponse,
    TaxRateListResponse,
    TaxCalculationRequest,
    TaxCalculationResponse,
)

router = APIRouter()


@router.get("/", response_model=TaxRateListResponse)
async def list_tax_rates(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    tax_type: Optional[str] = Query(None, description="Filter by tax type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all tax rates for a company with filtering and pagination.

    Args:
        tenant_id: Tenant ID
        company_id: Company ID
        is_active: Filter by active status
        tax_type: Filter by tax type (sales_tax, vat, gst, excise, service_tax, other)
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session

    Returns:
        Paginated list of tax rates
    """
    skip = (page - 1) * page_size

    tax_rates, total = await TaxRateService.list_tax_rates(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        is_active=is_active,
        tax_type=tax_type,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return TaxRateListResponse(
        tax_rates=[TaxRateResponse.model_validate(tr) for tr in tax_rates],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=TaxRateResponse, status_code=201)
async def create_tax_rate(
    tax_rate_data: TaxRateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tax rate.

    Args:
        tax_rate_data: Tax rate creation data
        db: Database session

    Returns:
        Created tax rate

    Raises:
        400: If tax rate code already exists
    """
    try:
        tax_rate = await TaxRateService.create_tax_rate(db, tax_rate_data)
        return TaxRateResponse.model_validate(tax_rate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active", response_model=List[TaxRateResponse])
async def get_active_tax_rates(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    applies_to_sales: Optional[bool] = Query(None, description="Filter by applies_to_sales"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active tax rates for a company.

    Args:
        tenant_id: Tenant ID
        company_id: Company ID
        applies_to_sales: Filter by applies_to_sales flag
        db: Database session

    Returns:
        List of active tax rates
    """
    tax_rates = await TaxRateService.get_active_tax_rates(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        applies_to_sales=applies_to_sales
    )

    return [TaxRateResponse.model_validate(tr) for tr in tax_rates]


@router.get("/default", response_model=TaxRateResponse)
async def get_default_tax_rate(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get default tax rate for a company.

    Args:
        tenant_id: Tenant ID
        company_id: Company ID
        db: Database session

    Returns:
        Default tax rate

    Raises:
        404: If no default tax rate found
    """
    tax_rate = await TaxRateService.get_default_tax_rate(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id
    )

    if not tax_rate:
        raise HTTPException(status_code=404, detail="No default tax rate found")

    return TaxRateResponse.model_validate(tax_rate)


@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_tax(
    calculation_request: TaxCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate tax for a given amount.

    Args:
        calculation_request: Tax calculation request
        db: Database session

    Returns:
        Tax calculation details

    Raises:
        404: If tax rate not found
        400: If tax rate is not currently valid
    """
    try:
        result = await TaxRateService.calculate_tax(
            db=db,
            tax_rate_id=calculation_request.tax_rate_id,
            amount=calculation_request.amount
        )

        if not result:
            raise HTTPException(status_code=404, detail="Tax rate not found")

        return TaxCalculationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tax_rate_id}", response_model=TaxRateResponse)
async def get_tax_rate(
    tax_rate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get tax rate by ID.

    Args:
        tax_rate_id: Tax rate ID
        db: Database session

    Returns:
        Tax rate details

    Raises:
        404: If tax rate not found
    """
    tax_rate = await TaxRateService.get_tax_rate(db, tax_rate_id)
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    return TaxRateResponse.model_validate(tax_rate)


@router.put("/{tax_rate_id}", response_model=TaxRateResponse)
async def update_tax_rate(
    tax_rate_id: str,
    tax_rate_data: TaxRateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a tax rate.

    Args:
        tax_rate_id: Tax rate ID
        tax_rate_data: Tax rate update data
        db: Database session

    Returns:
        Updated tax rate

    Raises:
        404: If tax rate not found
        400: If update validation fails
    """
    try:
        tax_rate = await TaxRateService.update_tax_rate(db, tax_rate_id, tax_rate_data)
        if not tax_rate:
            raise HTTPException(status_code=404, detail="Tax rate not found")

        return TaxRateResponse.model_validate(tax_rate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tax_rate_id}", status_code=204)
async def delete_tax_rate(
    tax_rate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a tax rate.

    Args:
        tax_rate_id: Tax rate ID
        db: Database session

    Returns:
        No content

    Raises:
        404: If tax rate not found
        400: If tax rate is in use
    """
    try:
        deleted = await TaxRateService.delete_tax_rate(db, tax_rate_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Tax rate not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
