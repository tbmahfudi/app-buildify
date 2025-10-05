from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Company Schemas
class CompanyBase(BaseModel):
    code: str
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Branch Schemas
class BranchBase(BaseModel):
    company_id: str
    code: str
    name: str

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class BranchResponse(BranchBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Department Schemas
class DepartmentBase(BaseModel):
    company_id: str
    branch_id: Optional[str] = None
    code: str
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    branch_id: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# List responses
class CompanyListResponse(BaseModel):
    items: List[CompanyResponse]
    total: int

class BranchListResponse(BaseModel):
    items: List[BranchResponse]
    total: int

class DepartmentListResponse(BaseModel):
    items: List[DepartmentResponse]
    total: int