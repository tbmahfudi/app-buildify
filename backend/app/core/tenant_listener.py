"""
backend/app/core/tenant_listener.py
SQLAlchemy ORM event listener for tenant-scope enforcement.
Story 22.3.1 / T-22.004 + T-22.005

Design
------
Scope is stored in a ContextVar (_current_tenant_id) defined in
app.core.tenant.scope and set per-request by the tenant_scoped_session
FastAPI dependency.  The listener reads that ContextVar -- it does NOT rely
on session-level attributes, so it is safe across async and threaded contexts.

Fail-loud guarantee (arch-22 section 3.2)
------------------------------------------
Any ORM SELECT / UPDATE / DELETE against a __tenant_scoped__ = True model
that executes without scope raises TenantScopeMissingError immediately.
There is no silent pass.

Superuser bypass
----------------
When the ContextVar holds the sentinel string '__superuser__' (set by
with_admin_cross_tenant_scope() or the superuser path of
tenant_scoped_session), the listener skips filtering and lets the query
proceed unmodified.

Install
-------
Call TenantScopeListener.install(engine) once at FastAPI lifespan startup,
AFTER tenant_scoped_session is deployed to all tenant routes (T-22.009)
to avoid HTTP 500 storms on existing requests that do not yet set scope.
"""
from __future__ import annotations

import logging

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.tenant.scope import (
    TenantScopeNotSetError as TenantScopeMissingError,
    _current_tenant_id,
)

logger = logging.getLogger(__name__)

_SCOPE_ATTR = '_tenant_scope'

# ---------------------------------------------------------------------------
# Session-attribute helpers (T-22.005 API)
# ---------------------------------------------------------------------------
# Provided for background tasks that create a plain SessionLocal and must set
# scope manually.  They write both the ContextVar AND the session attribute so
# that either lookup path works.


def set_tenant_scope(session: Session, tenant_id) -> None:
    """Bind tenant_id to session and to the current ContextVar context."""
    _current_tenant_id.set(str(tenant_id))  # type: ignore[arg-type]
    setattr(session, _SCOPE_ATTR, str(tenant_id))
    logger.debug('tenant_scope.set (session) tenant_id=%s', tenant_id)


def clear_tenant_scope(session: Session) -> None:
    """Remove the tenant binding from session and reset the ContextVar."""
    _current_tenant_id.set(None)
    if hasattr(session, _SCOPE_ATTR):
        delattr(session, _SCOPE_ATTR)
    logger.debug('tenant_scope.clear (session)')


# ---------------------------------------------------------------------------
# TenantScopeListener
# ---------------------------------------------------------------------------


class TenantScopeListener:
    """Intercepts all ORM SELECT / UPDATE / DELETE on __tenant_scoped__ models.

    Raises TenantScopeMissingError (-> HTTP 500) when ContextVar scope is not set.
    Skips filtering when the superuser sentinel '__superuser__' is present.

    Usage::

        from app.core.db import engine
        from app.core.tenant_listener import TenantScopeListener

        TenantScopeListener.install(engine)
    """

    @classmethod
    def install(cls, engine) -> None:
        """Register the do_orm_execute hook on the Session class.

        The event is registered on the Session class (not the engine) so it
        fires for every session bound to this engine.

        Must be called AFTER all routes use tenant_scoped_session (T-22.009
        merged) to prevent HTTP 500 storms on unscoped requests.
        """
        event.listen(Session, 'do_orm_execute', cls._on_orm_execute)
        # do_orm_execute does NOT fire for unit-of-work flushes (session.add /
        # session.delete + flush), so INSERT/UPDATE/DELETE on a scoped model
        # would otherwise bypass enforcement. before_flush closes that gap.
        event.listen(Session, 'before_flush', cls._on_before_flush)
        logger.info('TenantScopeListener installed on Session')

    @staticmethod
    def _on_before_flush(session, flush_context, instances) -> None:
        """Enforce tenant scope on unit-of-work INSERT / UPDATE / DELETE.

        Fires for every pending write before it is flushed to the database.
        For any ``__tenant_scoped__`` instance in ``session.new`` / ``dirty`` /
        ``deleted``:
          * '__superuser__' sentinel -> allow (cross-tenant admin path).
          * scope unset -> raise TenantScopeMissingError (fail-loud).
          * scope set, but the instance carries a DIFFERENT tenant_id -> raise
            (a write must not target a foreign tenant's row).
        """
        scope = _current_tenant_id.get()
        if scope == '__superuser__':
            return

        for state_set in (session.new, session.dirty, session.deleted):
            for obj in state_set:
                if not getattr(type(obj), '__tenant_scoped__', False):
                    continue
                if scope is None:
                    logger.error(
                        'tenant_scope.flush.missing model=%s', type(obj).__name__
                    )
                    raise TenantScopeMissingError(
                        f'Write on tenant-scoped model {type(obj).__name__!r} '
                        'flushed without tenant scope set. Use '
                        'tenant_scoped_session() or set_tenant_scope(session, '
                        'tenant_id) for background tasks.'
                    )
                row_tenant = getattr(obj, 'tenant_id', None)
                if row_tenant is not None and str(row_tenant) != str(scope):
                    logger.error(
                        'tenant_scope.flush.cross_tenant model=%s row_tenant=%s scope=%s',
                        type(obj).__name__, row_tenant, scope,
                    )
                    raise TenantScopeMissingError(
                        f'Write on tenant-scoped model {type(obj).__name__!r} '
                        f'targets tenant {row_tenant} but the active scope is '
                        f'{scope}. Cross-tenant writes are not permitted.'
                    )

    @staticmethod
    def _on_orm_execute(orm_execute_state) -> None:
        """Called by SQLAlchemy before every ORM statement execution.

        For each mapped entity that declares __tenant_scoped__ = True:
          1. Read scope from the ContextVar; fall back to session attribute for
             background tasks that use set_tenant_scope(session, tenant_id).
          2. '__superuser__' sentinel -> skip filtering, return immediately.
          3. None (scope not set) -> raise TenantScopeMissingError (fail-loud).
          4. Valid tenant UUID -> inject WHERE tenant_id = :scope.
        """
        # Resolve the set of mappers in this statement.
        # all_mappers covers joins; bind_mapper covers simple single-entity queries.
        try:
            mappers = list(orm_execute_state.all_mappers)
        except AttributeError:
            bm = getattr(orm_execute_state, 'bind_mapper', None)
            mappers = [bm] if bm is not None else []

        if not mappers:
            return

        # Read scope: ContextVar is authoritative; fall back to session attr.
        scope = _current_tenant_id.get()
        if scope is None:
            scope = getattr(orm_execute_state.session, _SCOPE_ATTR, None)

        for mapper in mappers:
            if mapper is None:
                continue
            model = mapper.class_
            if not getattr(model, '__tenant_scoped__', False):
                continue

            # A scoped model is involved -- enforce scope.

            if scope == '__superuser__':
                logger.debug(
                    'tenant_scope.listener superuser bypass model=%s', model.__name__
                )
                return  # Bypass applies to all entities in this query

            if scope is None:
                logger.error(
                    'tenant_scope.missing model=%s statement=%s',
                    model.__name__,
                    type(orm_execute_state.statement).__name__,
                )
                raise TenantScopeMissingError(
                    f'Query on tenant-scoped model {model.__name__!r} executed without '
                    'tenant scope set. Use tenant_scoped_session() dependency or '
                    'set_tenant_scope(session, tenant_id) for background tasks.'
                )

            # Inject WHERE tenant_id = :scope.
            tenant_col = getattr(model, 'tenant_id', None)
            if tenant_col is None:
                logger.warning(
                    'tenant_scope.listener model %s has __tenant_scoped__=True '
                    'but no tenant_id column; skipping filter injection',
                    model.__name__,
                )
                return

            orm_execute_state.statement = orm_execute_state.statement.where(
                tenant_col == scope
            )
            logger.debug(
                'tenant_scope.listener injected tenant_id filter model=%s scope=%s',
                model.__name__,
                scope,
            )
            # Inject once per query even when multiple scoped models appear in a join.
            return
