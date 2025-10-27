from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    """Login request with email and password"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    )

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }
    )

class RefreshRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="JWT refresh token")

class UserCreate(BaseModel):
    """Create new user"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")
    roles: Optional[List[str]] = Field(default_factory=list, description="User roles")
    is_superuser: bool = Field(default=False, description="Superuser flag")

class UserUpdate(BaseModel):
    """Update user information"""
    email: Optional[EmailStr] = Field(None, description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    is_active: Optional[bool] = Field(None, description="Active status")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    roles: Optional[List[str]] = Field(None, description="User roles")

class UserResponse(BaseModel):
    """User information response"""
    id: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")
    is_active: bool = Field(..., description="Active status")
    is_superuser: bool = Field(..., description="Superuser flag")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    roles: List[str] = Field(default_factory=list, description="User roles")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = ConfigDict(from_attributes=True)

class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="User email address")

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")