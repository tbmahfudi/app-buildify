"""
Chart of Accounts Setup Service

Utility service for setting up default chart of accounts for new companies.
"""

import json
import os
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from ..models.account import Account
from ..services.account_service import AccountService


class ChartSetupService:
    """
    Service for setting up chart of accounts from templates.
    """

    @staticmethod
    def load_template(template_name: str = "default") -> Dict:
        """
        Load chart of accounts template from JSON file.

        Args:
            template_name: Name of the template (default: "default")

        Returns:
            Template data as dictionary

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(
            current_dir,
            "..",
            "data",
            f"{template_name}_chart_of_accounts.json"
        )

        with open(template_path, 'r') as f:
            return json.load(f)

    @staticmethod
    async def setup_default_chart(
        db: AsyncSession,
        tenant_id: str,
        company_id: str,
        created_by: str,
        template_name: str = "default"
    ) -> List[Account]:
        """
        Set up default chart of accounts for a company.

        Args:
            db: Database session
            tenant_id: Tenant ID
            company_id: Company ID
            created_by: User ID who is setting up the chart
            template_name: Template name to use

        Returns:
            List of created accounts

        Raises:
            ValueError: If chart already exists for the company
        """
        # Check if company already has accounts
        existing_accounts, total = await AccountService.list_accounts(
            db=db,
            tenant_id=tenant_id,
            company_id=company_id,
            skip=0,
            limit=1
        )

        if total > 0:
            raise ValueError("Company already has a chart of accounts")

        # Load template
        template = ChartSetupService.load_template(template_name)

        # First pass: Create all accounts without parent references
        accounts_by_code = {}
        created_accounts = []

        for account_data in template["accounts"]:
            parent_code = account_data.pop("parent_code", None)

            account = Account(
                id=str(uuid4()),
                tenant_id=tenant_id,
                company_id=company_id,
                created_by=created_by,
                **account_data
            )

            accounts_by_code[account.code] = {
                "account": account,
                "parent_code": parent_code
            }

        # Second pass: Set parent account IDs
        for code, data in accounts_by_code.items():
            account = data["account"]
            parent_code = data["parent_code"]

            if parent_code and parent_code in accounts_by_code:
                account.parent_account_id = accounts_by_code[parent_code]["account"].id

            db.add(account)
            created_accounts.append(account)

        await db.commit()

        # Refresh all accounts
        for account in created_accounts:
            await db.refresh(account)

        return created_accounts

    @staticmethod
    async def get_template_info(template_name: str = "default") -> Dict:
        """
        Get information about a chart of accounts template.

        Args:
            template_name: Template name

        Returns:
            Template metadata
        """
        template = ChartSetupService.load_template(template_name)

        # Count accounts by type
        type_counts = {}
        for account in template["accounts"]:
            acc_type = account["type"]
            type_counts[acc_type] = type_counts.get(acc_type, 0) + 1

        return {
            "name": template["name"],
            "description": template["description"],
            "total_accounts": len(template["accounts"]),
            "accounts_by_type": type_counts,
            "header_accounts": sum(1 for a in template["accounts"] if a.get("is_header", False)),
            "detail_accounts": sum(1 for a in template["accounts"] if not a.get("is_header", False))
        }

    @staticmethod
    def validate_template(template_data: Dict) -> tuple[bool, List[str]]:
        """
        Validate a chart of accounts template.

        Args:
            template_data: Template data to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        if "name" not in template_data:
            errors.append("Template missing 'name' field")

        if "accounts" not in template_data:
            errors.append("Template missing 'accounts' field")
            return False, errors

        # Check accounts
        codes_seen = set()
        for i, account in enumerate(template_data["accounts"]):
            # Check required fields
            required_fields = ["code", "name", "type"]
            for field in required_fields:
                if field not in account:
                    errors.append(f"Account {i}: Missing required field '{field}'")

            # Check for duplicate codes
            if "code" in account:
                if account["code"] in codes_seen:
                    errors.append(f"Account {i}: Duplicate code '{account['code']}'")
                codes_seen.add(account["code"])

            # Validate type
            if "type" in account:
                valid_types = ["asset", "liability", "equity", "revenue", "expense"]
                if account["type"] not in valid_types:
                    errors.append(f"Account {i}: Invalid type '{account['type']}'")

            # Check parent code exists
            if "parent_code" in account:
                parent_code = account["parent_code"]
                if parent_code not in codes_seen:
                    # Parent might be defined later, so just warn
                    pass

        return len(errors) == 0, errors
