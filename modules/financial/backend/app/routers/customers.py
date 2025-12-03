"""
Customers Router - Customer Management
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.customer_service import CustomerService
from ..schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerBalanceSummary,
)

router = APIRouter()


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in number, name, email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all customers for a company with filtering and pagination.
    """
    skip = (page - 1) * page_size

    customers, total = await CustomerService.list_customers(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return CustomerListResponse(
        customers=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new customer."""
    try:
        customer = await CustomerService.create_customer(db, customer_data)
        return CustomerResponse.model_validate(customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get customer by ID."""
    customer = await CustomerService.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a customer."""
    try:
        customer = await CustomerService.update_customer(db, customer_id, customer_data)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return CustomerResponse.model_validate(customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a customer."""
    try:
        deleted = await CustomerService.delete_customer(db, customer_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Customer not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{customer_id}/balance", response_model=CustomerBalanceSummary)
async def get_customer_balance(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get customer balance summary."""
    balance = await CustomerService.get_customer_balance(db, customer_id)
    if not balance:
        raise HTTPException(status_code=404, detail="Customer not found")

    return balance


@router.post("/{customer_id}/deactivate", response_model=CustomerResponse)
async def deactivate_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a customer."""
    customer = await CustomerService.deactivate_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerResponse.model_validate(customer)


@router.post("/{customer_id}/activate", response_model=CustomerResponse)
async def activate_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Activate a customer."""
    customer = await CustomerService.activate_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerResponse.model_validate(customer)
