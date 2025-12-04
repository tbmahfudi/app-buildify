"""
Tax Rate Service

Business logic for Tax Rate operations.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from ..models.tax_rate import TaxRate
from ..schemas.tax_rate import (
    TaxRateCreate,
    TaxRateUpdate,
)


class TaxRateService:
    """
    Service for managing tax rates.
    """

    @staticmethod
    async def create_tax_rate(
        db: AsyncSession,
        tax_rate_data: TaxRateCreate
    ) -> TaxRate:
        """
        Create a new tax rate.

        Args:
            db: Database session
            tax_rate_data: Tax rate creation data

        Returns:
            Created tax rate

        Raises:
            ValueError: If tax rate code already exists
        """
        # Check if tax rate code already exists
        existing = await TaxRateService.get_tax_rate_by_code(
            db,
            tax_rate_data.tenant_id,
            tax_rate_data.company_id,
            tax_rate_data.code
        )
        if existing:
            raise ValueError(f"Tax rate with code '{tax_rate_data.code}' already exists")

        # Create tax rate
        tax_rate = TaxRate(
            id=str(uuid4()),
            **tax_rate_data.model_dump()
        )

        db.add(tax_rate)
        await db.commit()
        await db.refresh(tax_rate)

        return tax_rate

    @staticmethod
    async def get_tax_rate(
        db: AsyncSession,
        tax_rate_id: str
    ) -> Optional[TaxRate]:
        """
        Get tax rate by ID.

        Args:
            db: Database session
            tax_rate_id: Tax rate ID

        Returns:
            Tax rate or None if not found
        """
        result = await db.execute(
            select(TaxRate).where(TaxRate.id == tax_rate_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_tax_rate_by_code(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        code: str
    ) -> Optional[TaxRate]:
        """
        Get tax rate by code.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            code: Tax rate code

        Returns:
            Tax rate or None if not found
        """
        result = await db.execute(
            select(TaxRate).where(
                and_(
                    TaxRate.tenant_id == tenant_id,
                    TaxRate.company_id == company_id,
                    TaxRate.code == code
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_tax_rates(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        is_active: Optional[bool] = None,
        tax_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[TaxRate], int]:
        """
        List tax rates with filtering and pagination.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            is_active: Filter by active status
            tax_type: Filter by tax type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (tax rates list, total count)
        """
        # Build query
        query = select(TaxRate).where(
            and_(
                TaxRate.tenant_id == tenant_id,
                TaxRate.company_id == company_id
            )
        )

        # Apply filters
        if is_active is not None:
            query = query.where(TaxRate.is_active == is_active)

        if tax_type:
            query = query.where(TaxRate.tax_type == tax_type)

        # Get total count
        count_query = select(TaxRate.id).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = len(total_result.all())

        # Apply pagination and get results
        query = query.order_by(TaxRate.code).offset(skip).limit(limit)
        result = await db.execute(query)
        tax_rates = result.scalars().all()

        return list(tax_rates), total

    @staticmethod
    async def update_tax_rate(
        db: AsyncSession,
        tax_rate_id: str,
        tax_rate_data: TaxRateUpdate
    ) -> Optional[TaxRate]:
        """
        Update tax rate.

        Args:
            db: Database session
            tax_rate_id: Tax rate ID
            tax_rate_data: Tax rate update data

        Returns:
            Updated tax rate or None if not found

        Raises:
            ValueError: If tax rate code conflicts
        """
        tax_rate = await TaxRateService.get_tax_rate(db, tax_rate_id)
        if not tax_rate:
            return None

        # Check if code is being changed and conflicts
        if tax_rate_data.code and tax_rate_data.code != tax_rate.code:
            existing = await TaxRateService.get_tax_rate_by_code(
                db,
                tax_rate.tenant_id,
                tax_rate.company_id,
                tax_rate_data.code
            )
            if existing:
                raise ValueError(f"Tax rate with code '{tax_rate_data.code}' already exists")

        # Update fields
        update_dict = tax_rate_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(tax_rate, field, value)

        await db.commit()
        await db.refresh(tax_rate)

        return tax_rate

    @staticmethod
    async def delete_tax_rate(
        db: AsyncSession,
        tax_rate_id: str
    ) -> bool:
        """
        Delete tax rate.

        Args:
            db: Database session
            tax_rate_id: Tax rate ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If tax rate is in use
        """
        tax_rate = await TaxRateService.get_tax_rate(db, tax_rate_id)
        if not tax_rate:
            return False

        # TODO: Check if tax rate is used in invoices or transactions
        # For now, we'll allow deletion

        await db.delete(tax_rate)
        await db.commit()

        return True

    @staticmethod
    async def get_active_tax_rates(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        applies_to_sales: Optional[bool] = None
    ) -> List[TaxRate]:
        """
        Get all active tax rates for a company.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            applies_to_sales: Filter by applies_to_sales flag

        Returns:
            List of active tax rates
        """
        today = date.today()

        query = select(TaxRate).where(
            and_(
                TaxRate.tenant_id == tenant_id,
                TaxRate.company_id == company_id,
                TaxRate.is_active == True,
                TaxRate.effective_from <= today,
                or_(
                    TaxRate.effective_to.is_(None),
                    TaxRate.effective_to >= today
                )
            )
        )

        if applies_to_sales is not None:
            query = query.where(TaxRate.applies_to_sales == applies_to_sales)

        query = query.order_by(TaxRate.code)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def calculate_tax(
        db: AsyncSession,
        tax_rate_id: str,
        amount: Decimal
    ) -> Optional[dict]:
        """
        Calculate tax amount for a given base amount.

        Args:
            db: Database session
            tax_rate_id: Tax rate ID
            amount: Base amount to calculate tax on

        Returns:
            Dictionary with tax calculation details or None if tax rate not found

        Raises:
            ValueError: If tax rate is not currently valid
        """
        tax_rate = await TaxRateService.get_tax_rate(db, tax_rate_id)
        if not tax_rate:
            return None

        # Check if tax rate is valid
        if not tax_rate.is_valid:
            raise ValueError("Tax rate is not currently valid")

        # Calculate tax
        tax_amount = tax_rate.calculate_tax(amount)
        total_amount = amount + tax_amount

        return {
            "amount": amount,
            "tax_rate_id": tax_rate.id,
            "tax_rate_code": tax_rate.code,
            "tax_rate_name": tax_rate.name,
            "tax_percentage": tax_rate.rate_percentage,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
        }

    @staticmethod
    async def get_default_tax_rate(
        db: AsyncSession,
        tenant_id: str,
        company_id: str
    ) -> Optional[TaxRate]:
        """
        Get default tax rate for a company.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID

        Returns:
            Default tax rate or None if not found
        """
        today = date.today()

        result = await db.execute(
            select(TaxRate).where(
                and_(
                    TaxRate.tenant_id == tenant_id,
                    TaxRate.company_id == company_id,
                    TaxRate.is_active == True,
                    TaxRate.is_default == True,
                    TaxRate.effective_from <= today,
                    or_(
                        TaxRate.effective_to.is_(None),
                        TaxRate.effective_to >= today
                    )
                )
            ).order_by(TaxRate.code).limit(1)
        )
        return result.scalar_one_or_none()
