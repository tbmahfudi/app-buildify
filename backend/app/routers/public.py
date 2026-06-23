import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/public", tags=["public"])

class TenantPublicInfo(BaseModel):
    id: str
    name: str
    code: str
    plan: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/tenants/{code}", response_model=TenantPublicInfo)
async def get_tenant_by_code(code: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.code == code, Tenant.is_active == True).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantPublicInfo(
        id=str(tenant.id),
        name=tenant.name,
        code=tenant.code,
        plan=getattr(tenant, "plan", None),
    )