"""TEMPLATE module API routes."""
from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

# SDK-only imports
from modules.sdk.dependencies import tenant_scoped_session, get_current_user, has_permission
from .models import TEMPLATEItem
from .schemas import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse

router = APIRouter(
    prefix="/api/v1/modules/TEMPLATE",
    tags=["TEMPLATE"],
)


@router.get("/items", response_model=ItemListResponse, summary="List TEMPLATE items")
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_permission("TEMPLATE:read")),
):
    offset = (page - 1) * page_size
    query = db.query(TEMPLATEItem).filter(TEMPLATEItem.is_active == True)
    total = query.count()
    items = query.offset(offset).limit(page_size).all()
    return ItemListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/items", response_model=ItemResponse, status_code=201, summary="Create a TEMPLATE item")
async def create_item(
    payload: ItemCreate,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_permission("TEMPLATE:write")),
):
    item = TEMPLATEItem(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/items/{item_id}", response_model=ItemResponse, summary="Get a TEMPLATE item")
async def get_item(
    item_id: uuid.UUID,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_permission("TEMPLATE:read")),
):
    item = db.query(TEMPLATEItem).filter(TEMPLATEItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/items/{item_id}", response_model=ItemResponse, summary="Update a TEMPLATE item")
async def update_item(
    item_id: uuid.UUID,
    payload: ItemUpdate,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_permission("TEMPLATE:write")),
):
    item = db.query(TEMPLATEItem).filter(TEMPLATEItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=204, summary="Delete a TEMPLATE item")
async def delete_item(
    item_id: uuid.UUID,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_permission("TEMPLATE:write")),
):
    item = db.query(TEMPLATEItem).filter(TEMPLATEItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
