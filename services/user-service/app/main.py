"""
User Service - FastAPI Application

Handles user profile management including:
- Profile retrieval
- Profile updates
- Password changes
- Premium status management
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from shared.database import Base, engine, get_db
from shared.auth import verify_password, get_password_hash, decode_access_token
from shared.models import User
from .schemas import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserPremiumUpdateRequest,
    PasswordChangeRequest,
    UserListResponse,
    SuccessResponse,
    ErrorResponse
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="User Service",
    description="User profile management service for CRUD operations on user data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Extracts the Bearer token from the Authorization header,
    validates it, and returns the associated user.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = parts[1]
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


def user_to_response(user: User) -> UserProfileResponse:
    """Convert User model to UserProfileResponse."""
    return UserProfileResponse(
        user_id=str(user.user_id),
        username=user.username,
        email=user.email,
        is_premium=user.is_premium,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "user-service"}


@app.get(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    
    Requires a valid JWT token in the Authorization header.
    """
    return user_to_response(current_user)


@app.get(
    "/users/{user_id}",
    response_model=UserProfileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    """
    Get a user's public profile by their ID.
    
    Returns basic profile information for any user.
    """
    try:
        uuid_id = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.user_id == uuid_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_to_response(user)


@app.put(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Conflict - username/email already taken"}
    }
)
def update_current_user_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current authenticated user's profile.
    
    Allows updating username and/or email. Both fields are optional.
    """
    # Check if new username is already taken
    if request.username and request.username != current_user.username:
        existing = db.query(User).filter(User.username == request.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
        current_user.username = request.username
    
    # Check if new email is already taken
    if request.email and request.email != current_user.email:
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already taken"
            )
        current_user.email = request.email
    
    db.commit()
    db.refresh(current_user)
    
    return user_to_response(current_user)


@app.put(
    "/me/password",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized or incorrect password"}
    }
)
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.
    
    Requires the current password for verification before setting the new password.
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update to new password
    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return SuccessResponse(message="Password changed successfully")


@app.put(
    "/me/premium",
    response_model=UserProfileResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
def update_premium_status(
    request: UserPremiumUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's premium subscription status.
    
    In a real application, this would be triggered by a payment system.
    For MVP, this allows direct status updates.
    """
    current_user.is_premium = request.is_premium
    db.commit()
    db.refresh(current_user)
    
    return user_to_response(current_user)


@app.delete(
    "/me",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current authenticated user's account.
    
    This action is irreversible and will remove all user data.
    """
    db.delete(current_user)
    db.commit()
    
    return SuccessResponse(message="Account deleted successfully")


@app.get(
    "/users",
    response_model=UserListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
def list_users(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all users with pagination.
    
    Returns a paginated list of user profiles.
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    
    offset = (page - 1) * page_size
    
    total = db.query(User).count()
    users = db.query(User).offset(offset).limit(page_size).all()
    
    return UserListResponse(
        users=[user_to_response(u) for u in users],
        total=total,
        page=page,
        page_size=page_size
    )
