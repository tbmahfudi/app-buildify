"""
Invoice API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.dependencies import get_db, get_current_user, has_permission
from app.models.user import User
from ..models import FinancialInvoice, FinancialInvoiceLineItem
from ..schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from ..permissions import FinancialPermissions

router = APIRouter(prefix="/invoices", tags=["financial-invoices"])


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.INVOICES_READ))
):
    """List all invoices for a company"""
    invoices = db.query(FinancialInvoice).filter(
        FinancialInvoice.tenant_id == current_user.tenant_id,
        FinancialInvoice.company_id == company_id
    ).all()

    return invoices


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.INVOICES_CREATE))
):
    """Create a new invoice"""

    # Check if invoice number already exists
    existing = db.query(FinancialInvoice).filter(
        FinancialInvoice.tenant_id == current_user.tenant_id,
        FinancialInvoice.invoice_number == invoice.invoice_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice with number '{invoice.invoice_number}' already exists"
        )

    # Calculate totals
    subtotal = 0
    tax_amount = 0

    for item in invoice.line_items:
        item_amount = item.quantity * item.unit_price
        item_tax = item_amount * (item.tax_rate / 100)
        subtotal += item_amount
        tax_amount += item_tax

    total_amount = subtotal + tax_amount

    # Create invoice
    invoice_data = invoice.model_dump(exclude={"line_items"})
    db_invoice = FinancialInvoice(
        **invoice_data,
        tenant_id=current_user.tenant_id,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        created_by_user_id=current_user.id
    )
    db.add(db_invoice)
    db.flush()

    # Create line items
    for idx, item in enumerate(invoice.line_items, start=1):
        item_amount = item.quantity * item.unit_price
        item_tax = item_amount * (item.tax_rate / 100)

        db_line_item = FinancialInvoiceLineItem(
            invoice_id=db_invoice.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item_amount,
            tax_rate=item.tax_rate,
            tax_amount=item_tax,
            line_number=idx
        )
        db.add(db_line_item)

    db.commit()
    db.refresh(db_invoice)

    return db_invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.INVOICES_READ))
):
    """Get a specific invoice"""
    invoice = db.query(FinancialInvoice).filter(
        FinancialInvoice.id == invoice_id,
        FinancialInvoice.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(FinancialPermissions.INVOICES_SEND))
):
    """Send an invoice to customer"""
    invoice = db.query(FinancialInvoice).filter(
        FinancialInvoice.id == invoice_id,
        FinancialInvoice.tenant_id == current_user.tenant_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if invoice.status == "draft":
        invoice.status = "sent"
        invoice.sent_at = datetime.utcnow()
        db.commit()

    return {"message": "Invoice sent successfully", "invoice_id": invoice_id}
