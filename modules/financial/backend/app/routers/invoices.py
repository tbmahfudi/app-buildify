"""
Invoices Router - Invoice Management
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.invoice_service import InvoiceService
from ..schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceSendRequest,
)

router = APIRouter()


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    tenant_id: str = Query(..., description="Tenant ID"),
    company_id: str = Query(..., description="Company ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    status: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[date] = Query(None, description="From date"),
    to_date: Optional[date] = Query(None, description="To date"),
    search: Optional[str] = Query(None, description="Search in invoice number"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db)
):
    """List all invoices with filtering and pagination."""
    skip = (page - 1) * page_size

    invoices, total = await InvoiceService.list_invoices(
        db=db,
        tenant_id=tenant_id,
        company_id=company_id,
        customer_id=customer_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        search=search,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return InvoiceListResponse(
        invoices=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new invoice."""
    try:
        invoice = await InvoiceService.create_invoice(db, invoice_data)
        return InvoiceResponse.model_validate(invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get invoice by ID."""
    invoice = await InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return InvoiceResponse.model_validate(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an invoice (draft only)."""
    try:
        invoice = await InvoiceService.update_invoice(db, invoice_id, invoice_data)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return InvoiceResponse.model_validate(invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an invoice (draft only)."""
    try:
        deleted = await InvoiceService.delete_invoice(db, invoice_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Invoice not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: str,
    send_request: InvoiceSendRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send invoice to customer."""
    try:
        invoice = await InvoiceService.send_invoice(db, invoice_id, send_request)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return InvoiceResponse.model_validate(invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: str,
    voided_by: str = Query(..., description="User ID who voided the invoice"),
    db: AsyncSession = Depends(get_db)
):
    """Void an invoice."""
    try:
        invoice = await InvoiceService.void_invoice(db, invoice_id, voided_by)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return InvoiceResponse.model_validate(invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
