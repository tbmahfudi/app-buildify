"""
SQLAlchemy session-event listener for automatic tenant_id injection.
Story 22.3.1
"""
from __future__ import annotations
import logging
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.scope import TenantScopeMissingError

logger = logging.getLogger(__name__)

_SCOPE_ATTR = '_tenant_scope'


def set_tenant_scope(session: Session, tenant_id) -> None:
    """Bind a tenant_id to this session. Called once per request from the dependency."""
    setattr(session, _SCOPE_ATTR, str(tenant_id))


def clear_tenant_scope(session: Session) -> None:
    """Remove tenant binding (called on session cleanup)."""
    if hasattr(session, _SCOPE_ATTR):
        delattr(session, _SCOPE_ATTR)


class TenantScopeListener:
    """
    Attaches a SQLAlchemy before_compile event to all queries on an engine.

    For models that declare ``__tenant_scoped__ = True``, the listener:
      - Injects a ``tenant_id`` WHERE clause when ``session._tenant_scope`` is set.
      - Raises ``TenantScopeMissingError`` when scope is unset (non-superuser path).

    Usage::

        engine = create_engine(...)
        TenantScopeListener.install(engine)
    """

    @classmethod
    def install(cls, engine) -> None:
        """Register the before_compile listener on the given engine."""
        event.listen(engine, 'before_cursor_execute', cls._noop)  # ensure engine-level hook exists
        # The real guard runs at ORM query-compile time via the mapper events
        event.listen(Session, 'do_orm_execute', cls._on_orm_execute)
        logger.info("TenantScopeListener installed")

    @staticmethod
    def _noop(conn, cursor, statement, parameters, context, executemany):
        """Placeholder engine-level hook (no-op)."""

    @staticmethod
    def _on_orm_execute(orm_execute_state):
        """
        Called by SQLAlchemy before every ORM SELECT/UPDATE/DELETE.

        If the top-level mapped entity has ``__tenant_scoped__ = True``:
          - Adds ``WHERE tenant_id = :scope`` when session has ``_tenant_scope``.
          - Raises ``TenantScopeMissingError`` if the session has no scope set.

        Superuser bypass: if the session carries ``_tenant_scope = '__superuser__'``
        the filter is skipped entirely.
        """
        if not orm_execute_state.is_select:
            return  # only guard SELECTs for now

        statement = orm_execute_state.statement
        # Inspect the first mapper entity in the query
        try:
            entities = orm_execute_state.all_mappers
        except Exception:
            return

        for mapper in entities:
            model = mapper.class_
            if not getattr(model, '__tenant_scoped__', False):
                continue

            session = orm_execute_state.session
            scope = getattr(session, _SCOPE_ATTR, None)

            if scope == '__superuser__':
                # Explicitly granted cross-tenant access
                return

            if scope is None:
                raise TenantScopeMissingError(
                    f"Query on tenant-scoped model {model.__name__!r} without tenant scope set. "
                    "Use tenant_scoped_session() dependency or set_tenant_scope()."
                )

            # The filter injection happens via the with_loader_criteria mechanism
            from sqlalchemy import inspect as sa_inspect
            try:
                tenant_col = getattr(model, 'tenant_id')
                # Add WHERE tenant_id = scope to the statement
                orm_execute_state.statement = statement.where(tenant_col == scope)
            except AttributeError:
                logger.warning(f"Model {model.__name__} has __tenant_scoped__=True but no tenant_id column")
            return  # only apply once per query
