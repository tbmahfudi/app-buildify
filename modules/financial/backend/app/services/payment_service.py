"""
Payment Service

Business logic for Payment operations.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import uuid4

from ..models.payment import Payment, PaymentAllocation
from ..models.invoice import Invoice
from ..schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentAllocationCreate,
)


class PaymentService:
    """
    Service for managing payments and payment allocations.
    """

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        payment_data: PaymentCreate
    ) -> Payment:
        """
        Create a new payment with optional allocations.

        Args:
            db: Database session
            payment_data: Payment creation data

        Returns:
            Created payment

        Raises:
            ValueError: If business rules are violated
        """
        # Check if payment number already exists
        existing = await PaymentService.get_payment_by_number(
            db,
            payment_data.tenant_id,
            payment_data.company_id,
            payment_data.payment_number
        )
        if existing:
            raise ValueError(f"Payment with number '{payment_data.payment_number}' already exists")

        # Validate payment amount
        if payment_data.payment_amount <= Decimal('0'):
            raise ValueError("Payment amount must be greater than zero")

        # Create payment
        payment_dict = payment_data.model_dump(exclude={'allocations'})
        payment = Payment(
            id=str(uuid4()),
            allocated_amount=Decimal('0.00'),
            unallocated_amount=payment_data.payment_amount,
            **payment_dict
        )

        db.add(payment)

        # Process allocations if provided
        if payment_data.allocations:
            total_allocation = Decimal('0.00')

            for alloc_data in payment_data.allocations:
                # Validate allocation amount
                if alloc_data.allocation_amount <= Decimal('0'):
                    raise ValueError("Allocation amount must be greater than zero")

                total_allocation += alloc_data.allocation_amount

                # Check if total allocation exceeds payment amount
                if total_allocation > payment_data.payment_amount:
                    raise ValueError("Total allocations cannot exceed payment amount")

                # Get invoice and validate
                invoice = await db.get(Invoice, alloc_data.invoice_id)
                if not invoice:
                    raise ValueError(f"Invoice {alloc_data.invoice_id} not found")

                if invoice.tenant_id != payment_data.tenant_id:
                    raise ValueError("Invoice and payment must belong to the same tenant")

                if invoice.customer_id != payment_data.customer_id:
                    raise ValueError("Invoice and payment must belong to the same customer")

                if invoice.status in ['void', 'cancelled']:
                    raise ValueError(f"Cannot allocate to {invoice.status} invoice")

                if invoice.balance_due <= Decimal('0'):
                    raise ValueError(f"Invoice {invoice.invoice_number} is fully paid")

                if alloc_data.allocation_amount > invoice.balance_due:
                    raise ValueError(
                        f"Allocation amount {alloc_data.allocation_amount} exceeds "
                        f"invoice balance due {invoice.balance_due}"
                    )

                # Create allocation
                allocation = PaymentAllocation(
                    id=str(uuid4()),
                    payment_id=payment.id,
                    invoice_id=alloc_data.invoice_id,
                    allocation_date=alloc_data.allocation_date,
                    allocation_amount=alloc_data.allocation_amount,
                    description=alloc_data.description,
                    extra_data=alloc_data.extra_data,
                    created_by=alloc_data.created_by
                )
                db.add(allocation)

                # Update invoice
                invoice.apply_payment(alloc_data.allocation_amount)
                invoice.last_payment_date = alloc_data.allocation_date

            # Update payment allocation totals
            payment.allocated_amount = total_allocation
            payment.unallocated_amount = payment.payment_amount - total_allocation

            # Update payment status
            if payment.unallocated_amount == Decimal('0'):
                payment.status = 'allocated'
            elif payment.allocated_amount > Decimal('0'):
                payment.status = 'partially_allocated'

        await db.commit()
        await db.refresh(payment)

        # Load relationships
        result = await db.execute(
            select(Payment)
            .options(selectinload(Payment.allocations))
            .where(Payment.id == payment.id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_payment(
        db: AsyncSession,
        payment_id: str
    ) -> Optional[Payment]:
        """
        Get payment by ID with allocations.

        Args:
            db: Database session
            payment_id: Payment ID

        Returns:
            Payment or None if not found
        """
        result = await db.execute(
            select(Payment)
            .options(selectinload(Payment.allocations))
            .where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_payment_by_number(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        payment_number: str
    ) -> Optional[Payment]:
        """
        Get payment by payment number.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            payment_number: Payment number

        Returns:
            Payment or None if not found
        """
        result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.tenant_id == tenant_id,
                    Payment.company_id == company_id,
                    Payment.payment_number == payment_number
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_payments(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Payment], int]:
        """
        List payments with filtering and pagination.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            customer_id: Filter by customer ID
            status: Filter by status
            from_date: Filter by payment date from
            to_date: Filter by payment date to
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (payments list, total count)
        """
        # Build query
        query = select(Payment).where(
            and_(
                Payment.tenant_id == tenant_id,
                Payment.company_id == company_id
            )
        )

        # Apply filters
        if customer_id:
            query = query.where(Payment.customer_id == customer_id)

        if status:
            query = query.where(Payment.status == status)

        if from_date:
            query = query.where(Payment.payment_date >= from_date)

        if to_date:
            query = query.where(Payment.payment_date <= to_date)

        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and get results
        query = (
            query
            .options(selectinload(Payment.allocations))
            .order_by(Payment.payment_date.desc(), Payment.payment_number.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        payments = result.scalars().all()

        return list(payments), total

    @staticmethod
    async def update_payment(
        db: AsyncSession,
        payment_id: str,
        payment_data: PaymentUpdate
    ) -> Optional[Payment]:
        """
        Update payment. Only pending payments can be updated.

        Args:
            db: Database session
            payment_id: Payment ID
            payment_data: Payment update data

        Returns:
            Updated payment or None if not found

        Raises:
            ValueError: If business rules are violated
        """
        payment = await PaymentService.get_payment(db, payment_id)
        if not payment:
            return None

        # Only pending payments can be updated
        if payment.status != 'pending':
            raise ValueError("Only pending payments can be updated")

        if payment.is_voided:
            raise ValueError("Cannot update voided payment")

        # Check if payment number is being changed and conflicts
        if payment_data.payment_number and payment_data.payment_number != payment.payment_number:
            existing = await PaymentService.get_payment_by_number(
                db,
                payment.tenant_id,
                payment.company_id,
                payment_data.payment_number
            )
            if existing:
                raise ValueError(f"Payment with number '{payment_data.payment_number}' already exists")

        # Validate payment amount if being changed
        if payment_data.payment_amount is not None:
            if payment_data.payment_amount <= Decimal('0'):
                raise ValueError("Payment amount must be greater than zero")

            # Update unallocated amount
            payment.unallocated_amount = payment_data.payment_amount - payment.allocated_amount

            if payment.unallocated_amount < Decimal('0'):
                raise ValueError("Payment amount cannot be less than allocated amount")

        # Update fields
        update_dict = payment_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == 'payment_amount':
                # Already handled above
                payment.payment_amount = value
            else:
                setattr(payment, field, value)

        await db.commit()
        await db.refresh(payment)

        # Reload with relationships
        return await PaymentService.get_payment(db, payment_id)

    @staticmethod
    async def delete_payment(
        db: AsyncSession,
        payment_id: str
    ) -> bool:
        """
        Delete payment. Only pending payments can be deleted.

        Args:
            db: Database session
            payment_id: Payment ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If payment cannot be deleted
        """
        payment = await PaymentService.get_payment(db, payment_id)
        if not payment:
            return False

        # Only pending payments can be deleted
        if payment.status != 'pending':
            raise ValueError("Only pending payments can be deleted")

        if payment.is_voided:
            raise ValueError("Cannot delete voided payment")

        if payment.allocated_amount > Decimal('0'):
            raise ValueError("Cannot delete payment with allocations")

        await db.delete(payment)
        await db.commit()

        return True

    @staticmethod
    async def allocate_payment(
        db: AsyncSession,
        payment_id: str,
        allocations: List[PaymentAllocationCreate]
    ) -> Payment:
        """
        Allocate payment to invoices.

        Args:
            db: Database session
            payment_id: Payment ID
            allocations: List of allocations to create

        Returns:
            Updated payment

        Raises:
            ValueError: If business rules are violated
        """
        payment = await PaymentService.get_payment(db, payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.is_voided:
            raise ValueError("Cannot allocate voided payment")

        if payment.unallocated_amount <= Decimal('0'):
            raise ValueError("Payment is fully allocated")

        # Validate allocations
        total_new_allocation = Decimal('0.00')
        invoice_ids = set()

        for alloc_data in allocations:
            # Check for duplicate invoice IDs
            if alloc_data.invoice_id in invoice_ids:
                raise ValueError(f"Cannot allocate to the same invoice multiple times")
            invoice_ids.add(alloc_data.invoice_id)

            # Validate allocation amount
            if alloc_data.allocation_amount <= Decimal('0'):
                raise ValueError("Allocation amount must be greater than zero")

            total_new_allocation += alloc_data.allocation_amount

        # Check if total allocation exceeds unallocated amount
        if total_new_allocation > payment.unallocated_amount:
            raise ValueError(
                f"Total allocations {total_new_allocation} exceed "
                f"unallocated amount {payment.unallocated_amount}"
            )

        # Process allocations
        for alloc_data in allocations:
            # Get invoice and validate
            invoice = await db.get(Invoice, alloc_data.invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {alloc_data.invoice_id} not found")

            if invoice.tenant_id != payment.tenant_id:
                raise ValueError("Invoice and payment must belong to the same tenant")

            if invoice.customer_id != payment.customer_id:
                raise ValueError("Invoice and payment must belong to the same customer")

            if invoice.status in ['void', 'cancelled']:
                raise ValueError(f"Cannot allocate to {invoice.status} invoice")

            if invoice.balance_due <= Decimal('0'):
                raise ValueError(f"Invoice {invoice.invoice_number} is fully paid")

            if alloc_data.allocation_amount > invoice.balance_due:
                raise ValueError(
                    f"Allocation amount {alloc_data.allocation_amount} exceeds "
                    f"invoice balance due {invoice.balance_due}"
                )

            # Check if allocation already exists for this invoice
            existing_alloc = None
            for existing in payment.allocations:
                if existing.invoice_id == alloc_data.invoice_id and not existing.is_voided:
                    existing_alloc = existing
                    break

            if existing_alloc:
                raise ValueError(f"Payment already allocated to invoice {invoice.invoice_number}")

            # Create allocation
            allocation = PaymentAllocation(
                id=str(uuid4()),
                payment_id=payment.id,
                invoice_id=alloc_data.invoice_id,
                allocation_date=alloc_data.allocation_date,
                allocation_amount=alloc_data.allocation_amount,
                description=alloc_data.description,
                extra_data=alloc_data.extra_data,
                created_by=alloc_data.created_by
            )
            db.add(allocation)

            # Update invoice
            invoice.apply_payment(alloc_data.allocation_amount)
            invoice.last_payment_date = alloc_data.allocation_date

        # Update payment allocation totals
        payment.calculate_allocation_totals()

        await db.commit()
        await db.refresh(payment)

        # Reload with relationships
        return await PaymentService.get_payment(db, payment_id)

    @staticmethod
    async def clear_payment(
        db: AsyncSession,
        payment_id: str,
        cleared_date: date
    ) -> Payment:
        """
        Mark payment as cleared.

        Args:
            db: Database session
            payment_id: Payment ID
            cleared_date: Date payment cleared

        Returns:
            Updated payment

        Raises:
            ValueError: If payment cannot be cleared
        """
        payment = await PaymentService.get_payment(db, payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.is_voided:
            raise ValueError("Cannot clear voided payment")

        if payment.is_cleared:
            raise ValueError("Payment is already cleared")

        payment.is_cleared = True
        payment.cleared_date = cleared_date

        # Update status if not allocated
        if payment.allocated_amount == Decimal('0'):
            payment.status = 'cleared'

        await db.commit()
        await db.refresh(payment)

        return await PaymentService.get_payment(db, payment_id)

    @staticmethod
    async def void_payment(
        db: AsyncSession,
        payment_id: str,
        void_reason: str,
        voided_by: str
    ) -> Payment:
        """
        Void a payment. Only unallocated payments can be voided.

        Args:
            db: Database session
            payment_id: Payment ID
            void_reason: Reason for voiding
            voided_by: User ID who voided the payment

        Returns:
            Voided payment

        Raises:
            ValueError: If payment cannot be voided
        """
        payment = await PaymentService.get_payment(db, payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.is_voided:
            raise ValueError("Payment is already voided")

        if payment.allocated_amount > Decimal('0'):
            raise ValueError(
                "Cannot void payment with allocations. "
                "Remove all allocations before voiding."
            )

        payment.is_voided = True
        payment.voided_at = datetime.utcnow()
        payment.voided_by = voided_by
        payment.void_reason = void_reason
        payment.status = 'voided'

        await db.commit()
        await db.refresh(payment)

        return await PaymentService.get_payment(db, payment_id)

    @staticmethod
    async def get_unallocated_payments(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        customer_id: Optional[str] = None
    ) -> List[Payment]:
        """
        Get unallocated payments (payments with unallocated amount > 0).

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            customer_id: Optional customer ID filter

        Returns:
            List of unallocated payments
        """
        query = select(Payment).where(
            and_(
                Payment.tenant_id == tenant_id,
                Payment.company_id == company_id,
                Payment.is_voided == False,
                Payment.unallocated_amount > Decimal('0')
            )
        )

        if customer_id:
            query = query.where(Payment.customer_id == customer_id)

        query = query.order_by(Payment.payment_date.asc())

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def void_allocation(
        db: AsyncSession,
        allocation_id: str,
        voided_by: str
    ) -> PaymentAllocation:
        """
        Void a payment allocation and reverse the invoice payment.

        Args:
            db: Database session
            allocation_id: Allocation ID
            voided_by: User ID who voided the allocation

        Returns:
            Voided allocation

        Raises:
            ValueError: If allocation cannot be voided
        """
        allocation = await db.get(PaymentAllocation, allocation_id)
        if not allocation:
            raise ValueError("Allocation not found")

        if allocation.is_voided:
            raise ValueError("Allocation is already voided")

        # Get payment and invoice
        payment = await PaymentService.get_payment(db, allocation.payment_id)
        invoice = await db.get(Invoice, allocation.invoice_id)

        if not payment or not invoice:
            raise ValueError("Payment or invoice not found")

        # Void allocation
        allocation.is_voided = True
        allocation.voided_at = datetime.utcnow()
        allocation.voided_by = voided_by

        # Reverse invoice payment
        invoice.paid_amount -= allocation.allocation_amount
        invoice.balance_due = invoice.total_amount - invoice.paid_amount

        # Update invoice status
        if invoice.balance_due == invoice.total_amount:
            # Fully reversed
            if invoice.status in ['paid', 'partially_paid']:
                invoice.status = 'sent'
        elif invoice.paid_amount > Decimal('0'):
            invoice.status = 'partially_paid'

        # Recalculate payment allocation totals
        payment.calculate_allocation_totals()

        await db.commit()
        await db.refresh(allocation)

        return allocation
