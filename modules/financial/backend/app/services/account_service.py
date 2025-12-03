"""
Account Service

Business logic for Account operations.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import uuid4

from ..models.account import Account
from ..schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountTreeNode,
    AccountBalanceUpdate,
)


class AccountService:
    """
    Service for managing accounts in the chart of accounts.
    """

    @staticmethod
    async def create_account(
        db: AsyncSession,
        account_data: AccountCreate
    ) -> Account:
        """
        Create a new account.

        Args:
            db: Database session
            account_data: Account creation data

        Returns:
            Created account

        Raises:
            ValueError: If account code already exists
            ValueError: If parent account doesn't exist
            ValueError: If parent account is not a header account
        """
        # Check if account code already exists
        existing = await AccountService.get_account_by_code(
            db,
            account_data.tenant_id,
            account_data.company_id,
            account_data.code
        )
        if existing:
            raise ValueError(f"Account with code '{account_data.code}' already exists")

        # Validate parent account if provided
        if account_data.parent_account_id:
            parent = await AccountService.get_account(db, account_data.parent_account_id)
            if not parent:
                raise ValueError("Parent account does not exist")
            if not parent.is_header:
                raise ValueError("Parent account must be a header account")
            if parent.tenant_id != account_data.tenant_id or parent.company_id != account_data.company_id:
                raise ValueError("Parent account must belong to the same tenant and company")

        # Create account
        account = Account(
            id=str(uuid4()),
            **account_data.model_dump()
        )

        db.add(account)
        await db.commit()
        await db.refresh(account)

        return account

    @staticmethod
    async def get_account(
        db: AsyncSession,
        account_id: str
    ) -> Optional[Account]:
        """
        Get account by ID.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Account or None if not found
        """
        result = await db.execute(
            select(Account)
            .where(Account.id == account_id)
            .options(selectinload(Account.parent_account))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_account_by_code(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        code: str
    ) -> Optional[Account]:
        """
        Get account by code.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            code: Account code

        Returns:
            Account or None if not found
        """
        result = await db.execute(
            select(Account).where(
                and_(
                    Account.tenant_id == tenant_id,
                    Account.company_id == company_id,
                    Account.code == code
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_accounts(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        account_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        parent_account_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Account], int]:
        """
        List accounts with filtering and pagination.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            account_type: Filter by account type
            is_active: Filter by active status
            parent_account_id: Filter by parent account
            search: Search in code and name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (accounts list, total count)
        """
        # Build query
        query = select(Account).where(
            and_(
                Account.tenant_id == tenant_id,
                Account.company_id == company_id
            )
        )

        # Apply filters
        if account_type:
            query = query.where(Account.type == account_type)

        if is_active is not None:
            query = query.where(Account.is_active == is_active)

        if parent_account_id:
            query = query.where(Account.parent_account_id == parent_account_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Account.code.ilike(search_pattern),
                    Account.name.ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(Account.id).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = len(total_result.all())

        # Apply pagination and get results
        query = query.order_by(Account.code).offset(skip).limit(limit)
        result = await db.execute(query)
        accounts = result.scalars().all()

        return list(accounts), total

    @staticmethod
    async def update_account(
        db: AsyncSession,
        account_id: str,
        account_data: AccountUpdate
    ) -> Optional[Account]:
        """
        Update account.

        Args:
            db: Database session
            account_id: Account ID
            account_data: Account update data

        Returns:
            Updated account or None if not found

        Raises:
            ValueError: If account code conflicts
            ValueError: If trying to edit non-draft account
        """
        account = await AccountService.get_account(db, account_id)
        if not account:
            return None

        # Check if code is being changed and conflicts
        if account_data.code and account_data.code != account.code:
            existing = await AccountService.get_account_by_code(
                db,
                account.tenant_id,
                account.company_id,
                account_data.code
            )
            if existing:
                raise ValueError(f"Account with code '{account_data.code}' already exists")

        # Update fields
        update_dict = account_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(account, field, value)

        await db.commit()
        await db.refresh(account)

        return account

    @staticmethod
    async def delete_account(
        db: AsyncSession,
        account_id: str
    ) -> bool:
        """
        Delete account.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If account has child accounts
            ValueError: If account has transactions
        """
        account = await AccountService.get_account(db, account_id)
        if not account:
            return False

        # Check for child accounts
        child_result = await db.execute(
            select(Account).where(Account.parent_account_id == account_id)
        )
        if child_result.scalar_one_or_none():
            raise ValueError("Cannot delete account with child accounts")

        # Check if account has been used (has non-zero balance)
        if account.current_balance != Decimal('0.00'):
            raise ValueError("Cannot delete account with non-zero balance")

        await db.delete(account)
        await db.commit()

        return True

    @staticmethod
    async def update_account_balance(
        db: AsyncSession,
        account_id: str,
        balance_update: AccountBalanceUpdate
    ) -> Optional[Account]:
        """
        Update account balance.

        Args:
            db: Database session
            account_id: Account ID
            balance_update: Balance update data

        Returns:
            Updated account or None if not found
        """
        account = await AccountService.get_account(db, account_id)
        if not account:
            return None

        account.update_balance(
            debit_amount=balance_update.debit_amount,
            credit_amount=balance_update.credit_amount
        )

        await db.commit()
        await db.refresh(account)

        return account

    @staticmethod
    async def get_chart_of_accounts_tree(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        is_active: Optional[bool] = None
    ) -> List[AccountTreeNode]:
        """
        Get chart of accounts as a tree structure.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            is_active: Filter by active status

        Returns:
            List of root account nodes with nested children
        """
        # Get all accounts
        query = select(Account).where(
            and_(
                Account.tenant_id == tenant_id,
                Account.company_id == company_id
            )
        )

        if is_active is not None:
            query = query.where(Account.is_active == is_active)

        query = query.order_by(Account.code)
        result = await db.execute(query)
        accounts = result.scalars().all()

        # Build account map
        account_map: Dict[str, AccountTreeNode] = {}
        for account in accounts:
            account_map[account.id] = AccountTreeNode(
                id=account.id,
                code=account.code,
                name=account.name,
                full_name=account.full_name,
                type=account.type,
                is_header=account.is_header,
                current_balance=account.current_balance,
                children=[]
            )

        # Build tree structure
        root_nodes = []
        for account in accounts:
            node = account_map[account.id]
            if account.parent_account_id and account.parent_account_id in account_map:
                # Add to parent's children
                parent_node = account_map[account.parent_account_id]
                parent_node.children.append(node)
            else:
                # Root node
                root_nodes.append(node)

        return root_nodes

    @staticmethod
    async def get_account_balance(
        db: AsyncSession,
        account_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get account balance details.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Balance details or None if account not found
        """
        account = await AccountService.get_account(db, account_id)
        if not account:
            return None

        return {
            "account_id": account.id,
            "account_code": account.code,
            "account_name": account.name,
            "current_balance": account.current_balance,
            "debit_balance": account.debit_balance,
            "credit_balance": account.credit_balance,
            "currency_code": account.currency_code,
            "account_type": account.type,
            "is_debit_account": account.is_debit_account,
            "is_credit_account": account.is_credit_account,
        }

    @staticmethod
    async def get_accounts_by_type(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        account_type: str,
        is_active: bool = True
    ) -> List[Account]:
        """
        Get all accounts of a specific type.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            account_type: Account type
            is_active: Filter by active status

        Returns:
            List of accounts
        """
        query = select(Account).where(
            and_(
                Account.tenant_id == tenant_id,
                Account.company_id == company_id,
                Account.type == account_type,
                Account.is_active == is_active
            )
        ).order_by(Account.code)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def deactivate_account(
        db: AsyncSession,
        account_id: str
    ) -> Optional[Account]:
        """
        Deactivate an account (soft delete).

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Deactivated account or None if not found
        """
        account = await AccountService.get_account(db, account_id)
        if not account:
            return None

        account.is_active = False
        await db.commit()
        await db.refresh(account)

        return account

    @staticmethod
    async def activate_account(
        db: AsyncSession,
        account_id: str
    ) -> Optional[Account]:
        """
        Activate an account.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Activated account or None if not found
        """
        account = await AccountService.get_account(db, account_id)
        if not account:
            return None

        account.is_active = True
        await db.commit()
        await db.refresh(account)

        return account
