"""
Auth Service - FastAPI Application

Handles user authentication including:
- User registration
- User login with JWT token generation
- Token validation
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Add project root to path for shared imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base, engine, get_db
from shared.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Import User model using importlib due to hyphenated directory names
import importlib.util
spec = importlib.util.spec_from_file_location(
    "user",
    os.path.join(PROJECT_ROOT, "services/user-service/app/models/user.py")
)
user_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_module)
User = user_module.User

from .schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    TokenValidationRequest,
    TokenValidationResponse,
    UserResponse,
    RegisterResponse,
    ErrorResponse
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication service for user registration, login, and JWT token management",
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


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth-service"}


@app.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        409: {"model": ErrorResponse, "description": "User already exists"}
    }
)
def register_user(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Creates a new user account with the provided username, email, and password.
    The password is securely hashed before storage.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == request.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists"
        )
    
    # Create new user with hashed password
    hashed_password = get_password_hash(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RegisterResponse(
        message="User registered successfully",
        user=UserResponse(
            user_id=str(new_user.user_id),
            username=new_user.username,
            email=new_user.email,
            is_premium=new_user.is_premium,
            created_at=new_user.created_at.isoformat()
        )
    )


@app.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"}
    }
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Validates the user's email and password, then returns a JWT access token
    that can be used for subsequent authenticated requests.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    
    # Create access token
    token_data = {
        "sub": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "is_premium": user.is_premium
    }
    access_token = create_access_token(data=token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )


@app.post(
    "/validate",
    response_model=TokenValidationResponse
)
def validate_token(request: TokenValidationRequest):
    """
    Validate a JWT token.
    
    Decodes and validates the provided JWT token, returning information
    about whether it's valid and the associated user if so.
    """
    payload = decode_access_token(request.token)
    
    if payload is None:
        return TokenValidationResponse(
            valid=False,
            message="Invalid or expired token"
        )
    
    return TokenValidationResponse(
        valid=True,
        user_id=payload.get("sub"),
        username=payload.get("username"),
        message="Token is valid"
    )


@app.post("/refresh", response_model=TokenResponse)
def refresh_token(request: TokenValidationRequest, db: Session = Depends(get_db)):
    """
    Refresh an existing JWT token.
    
    Validates the current token and issues a new one with extended expiration.
    """
    payload = decode_access_token(request.token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    token_data = {
        "sub": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "is_premium": user.is_premium
    }
    access_token = create_access_token(data=token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
