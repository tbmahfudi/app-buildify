"""
TEMPLATE module API routes.

All routes MUST be prefixed with /api/v1/modules/TEMPLATE/
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/v1/modules/TEMPLATE",
    tags=["TEMPLATE"],
)


# ── Example endpoint ─────────────────────────────────────────────────────────

@router.get("/items", summary="List TEMPLATE items")
async def list_items():
    """
    TODO: Replace with real implementation.
    Returns a list of TEMPLATE items for the current tenant.
    """
    return {"items": [], "total": 0}


@router.get("/items/{item_id}", summary="Get a single TEMPLATE item")
async def get_item(item_id: str):
    """TODO: Replace with real implementation."""
    raise HTTPException(status_code=404, detail="Item not found")
