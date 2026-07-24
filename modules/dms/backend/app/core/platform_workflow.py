"""Client for the platform workflow engine (E4).

DMS is standalone, so it drives approvals over HTTP against the core platform's
`/api/v1/workflows` API, forwarding the caller's JWT (the engine is the source of
truth for approval state, SLA, escalation and history). Instances attach to a DMS
document via `source_module='dms'` + `record_id=<document_id>` (see the
pg_workflow_module_records generalization).
"""

from typing import Any, Dict, List, Optional

import httpx

from ..config import settings

SOURCE_MODULE = "dms"
_BASE = f"{settings.CORE_PLATFORM_URL}/api/v1/workflows"


class WorkflowError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def _request(method: str, path: str, token: str, **kw) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(method, f"{_BASE}{path}", headers=_headers(token), **kw)
    except httpx.HTTPError as e:
        raise WorkflowError(f"Workflow service unreachable: {e}", 502)
    if resp.status_code >= 400:
        detail = resp.text[:300]
        try:
            body = resp.json()
            detail = body.get("detail", detail)
        except Exception:  # noqa: BLE001
            pass
        raise WorkflowError(
            detail if isinstance(detail, str) else str(detail), resp.status_code
        )
    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


class PlatformWorkflow:
    @staticmethod
    async def list_published(token: str) -> List[Dict[str, Any]]:
        rows = await _request("GET", "/", token) or []
        return [w for w in rows if w.get("is_published")]

    @staticmethod
    async def start(
        token: str, *, workflow_id: str, record_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return await _request("POST", "/instances", token, json={
            "workflow_id": workflow_id,
            "source_module": SOURCE_MODULE,
            "record_id": record_id,
            "context_data": context or {},
        })

    @staticmethod
    async def list_for_record(token: str, record_id: str) -> List[Dict[str, Any]]:
        return await _request(
            "GET", f"/instances?source_module={SOURCE_MODULE}&record_id={record_id}", token
        ) or []

    @staticmethod
    async def get_instance(token: str, instance_id: str) -> Dict[str, Any]:
        return await _request("GET", f"/instances/{instance_id}", token)

    @staticmethod
    async def available_transitions(token: str, instance_id: str) -> List[Dict[str, Any]]:
        return await _request("GET", f"/instances/{instance_id}/available-transitions", token) or []

    @staticmethod
    async def execute(
        token: str, instance_id: str, *, transition_id: str, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        return await _request("POST", f"/instances/{instance_id}/execute", token, json={
            "transition_id": transition_id,
            "comment": comment,
            "data": {},
        })

    @staticmethod
    async def history(token: str, instance_id: str) -> List[Dict[str, Any]]:
        return await _request("GET", f"/instances/{instance_id}/history", token) or []
