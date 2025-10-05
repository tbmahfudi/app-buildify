from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    tenant_id: Optional[str] = None
    roles: List[str] = []
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True