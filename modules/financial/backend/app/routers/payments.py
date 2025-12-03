"""
Payments Router - Payment Management
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentListResponse,
    PaymentAllocationRequest,
    PaymentClearRequest,
    PaymentVoidRequest,
)

router = APIRouter()


@router.get("/", response_model=PaymentListResponse)
async def list_payments(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[date] = Query(None, description="Filter from payment date"),
    to_date: Optional[date] = Query(None, description="Filter to payment date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all payments for a company with filtering and pagination.

    Filters:
    - customer_id: Filter by customer
    - status: Filter by payment status (pending, cleared, allocated, partially_allocated, voided)
    - from_date: Payments on or after this date
    - to_date: Payments on or before this date
    """
    skip = (page - 1) * page_size

    payments, total = await PaymentService.list_payments(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        customer_id=customer_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return PaymentListResponse(
        payments=[PaymentResponse.model_validate(p) for p in payments],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new payment.

    Can optionally include allocations to invoices at creation time.
    """
    try:
        payment = await PaymentService.create_payment(db, payment_data)
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment details by ID.

    Returns payment with all allocations.
    """
    payment = await PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return PaymentResponse.model_validate(payment)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: str,
    payment_data: PaymentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a payment.

    Only pending payments can be updated.
    """
    try:
        payment = await PaymentService.update_payment(db, payment_id, payment_data)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a payment.

    Only pending payments without allocations can be deleted.
    """
    try:
        deleted = await PaymentService.delete_payment(db, payment_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{payment_id}/allocate", response_model=PaymentResponse)
async def allocate_payment(
    payment_id: str,
    allocation_request: PaymentAllocationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Allocate payment to invoices.

    Distributes the payment amount across one or more invoices.
    Total allocations cannot exceed the unallocated amount.

    Business Rules:
    - Payment must not be voided
    - Payment must have unallocated amount available
    - Invoices must belong to the same tenant and customer
    - Invoices must not be void or cancelled
    - Invoices must have balance due
    - Allocation amount cannot exceed invoice balance due
    """
    try:
        payment = await PaymentService.allocate_payment(
            db=db,
            payment_id=payment_id,
            allocations=allocation_request.allocations
        )
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{payment_id}/clear", response_model=PaymentResponse)
async def clear_payment(
    payment_id: str,
    clear_request: PaymentClearRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark payment as cleared.

    Indicates that the payment has cleared the bank/payment processor.
    """
    try:
        payment = await PaymentService.clear_payment(
            db=db,
            payment_id=payment_id,
            cleared_date=clear_request.cleared_date
        )
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{payment_id}/void", response_model=PaymentResponse)
async def void_payment(
    payment_id: str,
    void_request: PaymentVoidRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Void a payment.

    Only payments without allocations can be voided.
    If payment has allocations, they must be removed first.

    Business Rules:
    - Payment must not already be voided
    - Payment must have no allocations (allocated_amount must be 0)
    """
    try:
        payment = await PaymentService.void_payment(
            db=db,
            payment_id=payment_id,
            void_reason=void_request.void_reason,
            voided_by=void_request.voided_by
        )
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/unallocated/list", response_model=list[PaymentResponse])
async def get_unallocated_payments(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all unallocated payments.

    Returns payments that have unallocated amount available.
    Useful for applying payments to new invoices.
    """
    payments = await PaymentService.get_unallocated_payments(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        customer_id=customer_id
    )

    return [PaymentResponse.model_validate(p) for p in payments]
