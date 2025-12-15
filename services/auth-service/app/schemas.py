"""
Pydantic schemas for Auth Service request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenValidationRequest(BaseModel):
    """Schema for token validation request."""
    token: str


class TokenValidationResponse(BaseModel):
    """Schema for token validation response."""
    valid: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    message: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    user_id: str
    username: str
    email: str
    is_premium: bool
    created_at: str

    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    """Schema for registration response."""
    message: str
    user: UserResponse


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
