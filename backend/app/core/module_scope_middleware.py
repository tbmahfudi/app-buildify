"""
ModuleScopeMiddleware — routes module endpoints to per-tenant DBs.
Story 22.4.3
"""
from __future__ import annotations
import os
import re
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class ModuleScopeMiddleware(BaseHTTPMiddleware):
    """
    Routes ``/api/v1/modules/{module_id}/...`` requests to per-tenant module DB
    when ``DATABASE_STRATEGY=per_tenant`` is set in the environment.

    In ``shared`` mode (default) this middleware is a no-op pass-through.

    Per-tenant routing algorithm:
      1. Extract ``module_id`` from path.
      2. Look up ``tenant_module_databases`` for (tenant_id, module_id).
      3. Attach the resolved ``connection_url`` to ``request.state`` so downstream
         dependencies can acquire a scoped session from the per-tenant DB.

    For now step 3 is a *marker only* (``request.state.module_scope = module_id``).
    Full connection-pool wiring is tracked in story 22.4.3 follow-up.
    """

    MODULE_PATH_RE = re.compile(r'^/api/v1/modules/([^/]+)/')

    async def dispatch(self, request: Request, call_next):
        strategy = os.environ.get('DATABASE_STRATEGY', 'shared')
        if strategy != 'per_tenant':
            return await call_next(request)

        match = self.MODULE_PATH_RE.match(request.url.path)
        if not match:
            return await call_next(request)

        module_id = match.group(1)
        request.state.module_scope = module_id
        logger.debug(f"ModuleScopeMiddleware: per-tenant routing for module {module_id!r}")

        return await call_next(request)
