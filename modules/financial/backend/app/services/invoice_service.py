"""
Invoice Service

Business logic for Invoice operations.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import uuid4

from ..models.invoice import Invoice, InvoiceLineItem
from ..models.customer import Customer
from ..schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceLineItemCreate,
    InvoiceSendRequest,
)


class InvoiceService:
    """
    Service for managing invoices.
    """

    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        invoice_data: InvoiceCreate
    ) -> Invoice:
        """
        Create a new invoice with line items.

        Args:
            db: Database session
            invoice_data: Invoice creation data

        Returns:
            Created invoice

        Raises:
            ValueError: If invoice number already exists
            ValueError: If customer doesn't exist
        """
        # Check if invoice number already exists
        existing = await InvoiceService.get_invoice_by_number(
            db,
            invoice_data.tenant_id,
            invoice_data.company_id,
            invoice_data.invoice_number
        )
        if existing:
            raise ValueError(f"Invoice with number '{invoice_data.invoice_number}' already exists")

        # Verify customer exists
        customer_result = await db.execute(
            select(Customer).where(Customer.id == invoice_data.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if not customer:
            raise ValueError("Customer not found")

        # Extract line items
        line_items_data = invoice_data.line_items
        invoice_dict = invoice_data.model_dump(exclude={'line_items'})

        # Create invoice
        invoice = Invoice(
            id=str(uuid4()),
            **invoice_dict
        )

        # Create line items
        for item_data in line_items_data:
            line_item = InvoiceLineItem(
                id=str(uuid4()),
                invoice_id=invoice.id,
                **item_data.model_dump()
            )
            # Calculate line totals
            line_item.calculate_line_total()
            invoice.line_items.append(line_item)

        # Calculate invoice totals
        invoice.calculate_totals()

        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)

        return invoice

    @staticmethod
    async def get_invoice(
        db: AsyncSession,
        invoice_id: str
    ) -> Optional[Invoice]:
        """Get invoice by ID with line items."""
        result = await db.execute(
            select(Invoice)
            .where(Invoice.id == invoice_id)
            .options(
                selectinload(Invoice.line_items),
                selectinload(Invoice.customer)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_invoice_by_number(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        invoice_number: str
    ) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        result = await db.execute(
            select(Invoice).where(
                and_(
                    Invoice.tenant_id == tenant_id,
                    Invoice.company_id == company_id,
                    Invoice.invoice_number == invoice_number
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_invoices(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Invoice], int]:
        """
        List invoices with filtering and pagination.
        """
        query = select(Invoice).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.company_id == company_id
            )
        )

        # Apply filters
        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)

        if status:
            query = query.where(Invoice.status == status)

        if from_date:
            query = query.where(Invoice.invoice_date >= from_date)

        if to_date:
            query = query.where(Invoice.invoice_date <= to_date)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Invoice.invoice_number.ilike(search_pattern),
                    Invoice.reference_number.ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit)
        query = query.options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.customer)
        )

        result = await db.execute(query)
        invoices = result.scalars().all()

        return list(invoices), total

    @staticmethod
    async def update_invoice(
        db: AsyncSession,
        invoice_id: str,
        invoice_data: InvoiceUpdate
    ) -> Optional[Invoice]:
        """
        Update invoice (only if in draft status).
        """
        invoice = await InvoiceService.get_invoice(db, invoice_id)
        if not invoice:
            return None

        if not invoice.can_edit:
            raise ValueError("Cannot edit invoice that is not in draft status")

        # Update fields
        update_dict = invoice_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(invoice, field, value)

        # Recalculate totals
        invoice.calculate_totals()

        await db.commit()
        await db.refresh(invoice)

        return invoice

    @staticmethod
    async def delete_invoice(
        db: AsyncSession,
        invoice_id: str
    ) -> bool:
        """
        Delete invoice (only if in draft status).
        """
        invoice = await InvoiceService.get_invoice(db, invoice_id)
        if not invoice:
            return False

        if not invoice.can_edit:
            raise ValueError("Cannot delete invoice that is not in draft status")

        await db.delete(invoice)
        await db.commit()

        return True

    @staticmethod
    async def send_invoice(
        db: AsyncSession,
        invoice_id: str,
        send_request: InvoiceSendRequest
    ) -> Optional[Invoice]:
        """
        Mark invoice as sent.
        """
        invoice = await InvoiceService.get_invoice(db, invoice_id)
        if not invoice:
            return None

        if invoice.status not in ['draft', 'sent']:
            raise ValueError("Invoice has already been processed")

        invoice.status = 'sent'
        invoice.sent_at = datetime.utcnow()
        invoice.sent_by = send_request.sent_by

        await db.commit()
        await db.refresh(invoice)

        return invoice

    @staticmethod
    async def void_invoice(
        db: AsyncSession,
        invoice_id: str,
        voided_by: str
    ) -> Optional[Invoice]:
        """
        Void an invoice.
        """
        invoice = await InvoiceService.get_invoice(db, invoice_id)
        if not invoice:
            return None

        if not invoice.can_void:
            raise ValueError("Cannot void invoice with payments")

        invoice.status = 'void'

        await db.commit()
        await db.refresh(invoice)

        return invoice

    @staticmethod
    async def apply_payment_to_invoice(
        db: AsyncSession,
        invoice_id: str,
        payment_amount: Decimal
    ) -> Optional[Invoice]:
        """
        Apply payment to invoice and update balance.
        """
        invoice = await InvoiceService.get_invoice(db, invoice_id)
        if not invoice:
            return None

        if invoice.status == 'void':
            raise ValueError("Cannot apply payment to void invoice")

        invoice.apply_payment(payment_amount)

        await db.commit()
        await db.refresh(invoice)

        return invoice

    @staticmethod
    async def get_overdue_invoices(
        db: AsyncSession,
        tenant_id: str,
        company_id: str
    ) -> List[Invoice]:
        """
        Get all overdue invoices.
        """
        query = select(Invoice).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.company_id == company_id,
                Invoice.due_date < date.today(),
                Invoice.balance_due > Decimal('0.00'),
                Invoice.status.notin_(['paid', 'void', 'cancelled'])
            )
        ).order_by(Invoice.due_date)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_customer_invoices(
        db: AsyncSession,
        customer_id: str,
        status: Optional[str] = None
    ) -> List[Invoice]:
        """
        Get all invoices for a customer.
        """
        query = select(Invoice).where(Invoice.customer_id == customer_id)

        if status:
            query = query.where(Invoice.status == status)

        query = query.order_by(Invoice.invoice_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())
