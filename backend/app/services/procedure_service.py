"""
Procedure Service — Call named PostgreSQL functions from the service layer.

This module provides a thin, tenant-aware wrapper for invoking DB-level
functions (stored procedures) via SQLAlchemy's text() API.

Design decisions
----------------
* All results are returned as plain dicts — no ORM mapping needed.
* tenant_id is always injected so procedures can enforce row isolation
  without trusting the caller.
* Decimal / datetime values are coerced to JSON-serialisable types.
* Use this service for queries that are too expensive or complex to
  express through DynamicEntityService.aggregate_records():
    - Recursive CTEs (hierarchy / BOM traversal)
    - Multi-step financial calculations (AR aging, amortisation)
    - Materialized view refreshes
    - Cross-module aggregations

Usage example
-------------
    service = ProcedureService(db, current_user)

    # Call a DB function that returns a table
    rows = await service.call("fn_ar_aging", {
        "as_of_date": "2026-04-15",
        "currency":   "USD",
    })

    # Call a DB function that returns a scalar
    balance = await service.call_scalar("fn_account_balance", {
        "account_id": "...",
    })
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported functions registry
#
# Maps a logical name to a fully-qualified PostgreSQL function name.
# Register new functions here rather than hard-coding them in callers.
# ---------------------------------------------------------------------------
PROCEDURE_REGISTRY: Dict[str, str] = {
    # Financial module
    "fn_ar_aging":          "fn_ar_aging",
    "fn_ap_aging":          "fn_ap_aging",
    "fn_account_balance":   "fn_account_balance",
    "fn_cash_flow":         "fn_cash_flow",
    # Add more as DB functions are created
}


class ProcedureService:
    """
    Tenant-aware caller for named PostgreSQL functions.

    All public methods automatically inject :tenant_id into the parameter
    dict so that DB functions can enforce row-level isolation without
    depending on the caller to remember.
    """

    def __init__(self, db: Session, current_user: Any):
        self.db = db
        self.current_user = current_user
        self._tenant_id: Optional[str] = (
            str(current_user.tenant_id) if getattr(current_user, "tenant_id", None) else None
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def call(
        self,
        procedure_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Call a set-returning PostgreSQL function and return all rows as dicts.

        Args:
            procedure_name: Logical name registered in PROCEDURE_REGISTRY,
                            or a raw ``schema.fn_name`` string.
            params:         Named parameters for the function (do NOT include
                            tenant_id — it is injected automatically).

        Returns:
            List of row dicts.

        Raises:
            ValueError: If procedure_name is not in the registry and does not
                        look like a qualified identifier.
        """
        fn_name = self._resolve(procedure_name)
        bound_params = self._inject_tenant(params or {})
        param_sql = self._build_param_sql(bound_params)

        sql = text(f"SELECT * FROM {fn_name}({param_sql})")
        logger.debug("ProcedureService.call: %s %s", fn_name, bound_params)

        try:
            result = self.db.execute(sql, bound_params)
            return [self._serialize_row(dict(row._mapping)) for row in result]
        except Exception as exc:
            logger.error("ProcedureService.call failed [%s]: %s", fn_name, exc)
            raise

    async def call_scalar(
        self,
        procedure_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Call a scalar PostgreSQL function (returns a single value).

        Returns:
            The scalar value, coerced to a JSON-serialisable Python type.
        """
        fn_name = self._resolve(procedure_name)
        bound_params = self._inject_tenant(params or {})
        param_sql = self._build_param_sql(bound_params)

        sql = text(f"SELECT {fn_name}({param_sql})")
        logger.debug("ProcedureService.call_scalar: %s %s", fn_name, bound_params)

        try:
            result = self.db.execute(sql, bound_params)
            value = result.scalar()
            return self._coerce(value)
        except Exception as exc:
            logger.error("ProcedureService.call_scalar failed [%s]: %s", fn_name, exc)
            raise

    async def refresh_materialized_view(self, view_name: str, concurrently: bool = False) -> None:
        """
        Refresh a PostgreSQL materialized view.

        Args:
            view_name:    Unqualified or schema-qualified view name.
            concurrently: Use REFRESH CONCURRENTLY (requires a unique index on
                          the view; does not lock reads).
        """
        concur_clause = "CONCURRENTLY " if concurrently else ""
        sql = text(f"REFRESH MATERIALIZED VIEW {concur_clause}{view_name}")
        logger.info("Refreshing materialized view: %s (concurrently=%s)", view_name, concurrently)
        try:
            self.db.execute(sql)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("Failed to refresh materialized view %s: %s", view_name, exc)
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve(self, name: str) -> str:
        """Resolve a logical procedure name to its DB-level function name."""
        if name in PROCEDURE_REGISTRY:
            return PROCEDURE_REGISTRY[name]
        # Allow callers to pass a raw qualified name (e.g. "public.fn_foo")
        if "." in name or name.startswith("fn_"):
            return name
        raise ValueError(
            f"Unknown procedure '{name}'. Register it in PROCEDURE_REGISTRY "
            "or pass a qualified function name (e.g. 'public.fn_foo')."
        )

    def _inject_tenant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of params with tenant_id injected (if available)."""
        merged = dict(params)
        if self._tenant_id and "tenant_id" not in merged:
            merged["tenant_id"] = self._tenant_id
        return merged

    @staticmethod
    def _build_param_sql(params: Dict[str, Any]) -> str:
        """Build the positional/named parameter SQL fragment, e.g. ':tenant_id, :as_of_date'."""
        return ", ".join(f":{k}" for k in params)

    @staticmethod
    def _coerce(value: Any) -> Any:
        """Coerce a single value to a JSON-serialisable Python type."""
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    def _serialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce all values in a row dict to JSON-serialisable types."""
        return {k: self._coerce(v) for k, v in row.items()}
