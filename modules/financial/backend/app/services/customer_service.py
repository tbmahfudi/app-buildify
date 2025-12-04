"""
Customer Service

Business logic for Customer operations.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from ..models.customer import Customer
from ..schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerBalanceSummary,
)


class CustomerService:
    """
    Service for managing customers.
    """

    @staticmethod
    async def create_customer(
        db: AsyncSession,
        customer_data: CustomerCreate
    ) -> Customer:
        """
        Create a new customer.

        Args:
            db: Database session
            customer_data: Customer creation data

        Returns:
            Created customer

        Raises:
            ValueError: If customer number already exists
        """
        # Check if customer number already exists
        existing = await CustomerService.get_customer_by_number(
            db,
            customer_data.tenant_id,
            customer_data.company_id,
            customer_data.customer_number
        )
        if existing:
            raise ValueError(f"Customer with number '{customer_data.customer_number}' already exists")

        # Create customer
        customer = Customer(
            id=str(uuid4()),
            **customer_data.model_dump()
        )

        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def get_customer(
        db: AsyncSession,
        customer_id: str
    ) -> Optional[Customer]:
        """
        Get customer by ID.

        Args:
            db: Database session
            customer_id: Customer ID

        Returns:
            Customer or None if not found
        """
        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_customer_by_number(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        customer_number: str
    ) -> Optional[Customer]:
        """
        Get customer by customer number.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            customer_number: Customer number

        Returns:
            Customer or None if not found
        """
        result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.company_id == company_id,
                    Customer.customer_number == customer_number
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_customers(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Customer], int]:
        """
        List customers with filtering and pagination.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            is_active: Filter by active status
            search: Search in customer number, name, email
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (customers list, total count)
        """
        # Build query
        query = select(Customer).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.company_id == company_id
            )
        )

        # Apply filters
        if is_active is not None:
            query = query.where(Customer.is_active == is_active)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Customer.customer_number.ilike(search_pattern),
                    Customer.name.ilike(search_pattern),
                    Customer.email.ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and get results
        query = query.order_by(Customer.customer_number).offset(skip).limit(limit)
        result = await db.execute(query)
        customers = result.scalars().all()

        return list(customers), total

    @staticmethod
    async def update_customer(
        db: AsyncSession,
        customer_id: str,
        customer_data: CustomerUpdate
    ) -> Optional[Customer]:
        """
        Update customer.

        Args:
            db: Database session
            customer_id: Customer ID
            customer_data: Customer update data

        Returns:
            Updated customer or None if not found

        Raises:
            ValueError: If customer number conflicts
        """
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        # Check if customer number is being changed and conflicts
        if customer_data.customer_number and customer_data.customer_number != customer.customer_number:
            existing = await CustomerService.get_customer_by_number(
                db,
                customer.tenant_id,
                customer.company_id,
                customer_data.customer_number
            )
            if existing:
                raise ValueError(f"Customer with number '{customer_data.customer_number}' already exists")

        # Update fields
        update_dict = customer_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(customer, field, value)

        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def delete_customer(
        db: AsyncSession,
        customer_id: str
    ) -> bool:
        """
        Delete customer.

        Args:
            db: Database session
            customer_id: Customer ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If customer has transactions
        """
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return False

        # Check if customer has been used (has non-zero balance)
        if customer.current_balance != Decimal('0.00'):
            raise ValueError("Cannot delete customer with non-zero balance")

        await db.delete(customer)
        await db.commit()

        return True

    @staticmethod
    async def update_customer_balance(
        db: AsyncSession,
        customer_id: str,
        amount: Decimal,
        is_increase: bool = True
    ) -> Optional[Customer]:
        """
        Update customer balance.

        Args:
            db: Database session
            customer_id: Customer ID
            amount: Amount to add or subtract
            is_increase: True to increase balance, False to decrease

        Returns:
            Updated customer or None if not found
        """
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        if is_increase:
            customer.current_balance += amount
        else:
            customer.current_balance -= amount

        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def get_customer_balance(
        db: AsyncSession,
        customer_id: str
    ) -> Optional[CustomerBalanceSummary]:
        """
        Get customer balance summary.

        Args:
            db: Database session
            customer_id: Customer ID

        Returns:
            Balance summary or None if customer not found
        """
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        available_credit = None
        if customer.credit_limit:
            available_credit = customer.credit_limit - customer.current_balance

        return CustomerBalanceSummary(
            customer_id=customer.id,
            customer_number=customer.customer_number,
            customer_name=customer.name,
            current_balance=customer.current_balance,
            overdue_balance=customer.overdue_balance,
            credit_limit=customer.credit_limit,
            available_credit=available_credit
        )

    @staticmethod
    async def deactivate_customer(
        db: AsyncSession,
        customer_id: str
    ) -> Optional[Customer]:
        """
        Deactivate a customer (soft delete).

        Args:
            db: Database session
            customer_id: Customer ID

        Returns:
            Deactivated customer or None if not found
        """
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        customer.is_active = False
        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def activate_customer(
        db: AsyncSession,
        customer_id: str
    ) -> Optional[Customer]:
        """
        Activate a customer.

        Args:
            db: Database session
            customer_id: Customer ID

        Returns:
            Activated customer or None if not found
        """
        customer = await CustomerService.get_customer(db, customer_id)
        if not customer:
            return None

        customer.is_active = True
        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def get_customers_with_overdue_balance(
        db: AsyncSession,
        tenant_id: str,
        company_id: str
    ) -> List[Customer]:
        """
        Get all customers with overdue balance.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID

        Returns:
            List of customers with overdue balance
        """
        query = select(Customer).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.company_id == company_id,
                Customer.overdue_balance > Decimal('0.00'),
                Customer.is_active == True
            )
        ).order_by(Customer.overdue_balance.desc())

        result = await db.execute(query)
        return list(result.scalars().all())
