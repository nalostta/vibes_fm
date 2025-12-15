"""
Pydantic schemas for User Service request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    user_id: str
    username: str
    email: str
    is_premium: bool
    created_at: str
    last_login_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """Schema for updating user profile."""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None


class UserPremiumUpdateRequest(BaseModel):
    """Schema for updating premium status."""
    is_premium: bool


class PasswordChangeRequest(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserListResponse(BaseModel):
    """Schema for list of users response."""
    users: list[UserProfileResponse]
    total: int
    page: int
    page_size: int


class SuccessResponse(BaseModel):
    """Schema for generic success response."""
    message: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
