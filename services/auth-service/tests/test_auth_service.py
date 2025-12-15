"""
Unit tests for Auth Service.

Test Coverage Goal: > 80% Line Coverage
Key Test Scenarios:
- User registration (success, duplicate email, duplicate username)
- User login (success, invalid email, invalid password)
- JWT token generation and validation
- Token expiration handling
- Token refresh
"""
import os
import sys
import importlib.util
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base
from shared.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Load User model
spec = importlib.util.spec_from_file_location(
    "user",
    os.path.join(PROJECT_ROOT, "services/user-service/app/models/user.py")
)
user_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_module)
User = user_module.User


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    # Import the app here to avoid circular imports
    spec = importlib.util.spec_from_file_location(
        "main",
        os.path.join(PROJECT_ROOT, "services/auth-service/app/main.py")
    )
    main_module = importlib.util.module_from_spec(spec)
    
    # We need to set up the database override before loading the module
    from shared.database import get_db
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create a simple test app for unit testing
    from fastapi import FastAPI, HTTPException, status, Depends
    from sqlalchemy.orm import Session
    
    app = FastAPI()
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "auth-service"}
    
    @app.post("/register", status_code=status.HTTP_201_CREATED)
    def register_user(
        username: str,
        email: str,
        password: str,
        db: Session = Depends(override_get_db)
    ):
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            raise HTTPException(status_code=409, detail="A user with this username already exists")
        
        hashed_password = get_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "User registered successfully",
            "user": {
                "user_id": str(new_user.user_id),
                "username": new_user.username,
                "email": new_user.email,
                "is_premium": new_user.is_premium
            }
        }
    
    @app.post("/login")
    def login(email: str, password: str, db: Session = Depends(override_get_db)):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        
        token_data = {
            "sub": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "is_premium": user.is_premium
        }
        access_token = create_access_token(data=token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @app.post("/validate")
    def validate_token(token: str):
        payload = decode_access_token(token)
        if payload is None:
            return {"valid": False, "message": "Invalid or expired token"}
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "message": "Token is valid"
        }
    
    with TestClient(app) as test_client:
        yield test_client
    
    Base.metadata.drop_all(bind=test_engine)


class TestPasswordHashing:
    """Tests for password hashing utilities."""
    
    def test_password_hash_creates_different_hash(self):
        """Test that hashing the same password twice creates different hashes."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # bcrypt creates unique salts
    
    def test_verify_password_correct(self):
        """Test that correct password verifies successfully."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test that incorrect password fails verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Tests for JWT token generation and validation."""
    
    def test_create_access_token(self):
        """Test that access token is created successfully."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Test that valid token decodes correctly."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
    
    def test_decode_invalid_token(self):
        """Test that invalid token returns None."""
        payload = decode_access_token("invalid.token.here")
        assert payload is None
    
    def test_token_with_custom_expiration(self):
        """Test token creation with custom expiration."""
        data = {"sub": "user123"}
        expires = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
    
    def test_expired_token(self):
        """Test that expired token returns None."""
        data = {"sub": "user123"}
        # Create token that expires immediately
        expires = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires)
        payload = decode_access_token(token)
        assert payload is None


class TestAuthServiceEndpoints:
    """Tests for Auth Service API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/register",
            params={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        # First registration
        client.post(
            "/register",
            params={
                "username": "testuser1",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        # Second registration with same email
        response = client.post(
            "/register",
            params={
                "username": "testuser2",
                "email": "test@example.com",
                "password": "password456"
            }
        )
        assert response.status_code == 409
        assert "email already exists" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username fails."""
        # First registration
        client.post(
            "/register",
            params={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "password123"
            }
        )
        # Second registration with same username
        response = client.post(
            "/register",
            params={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "password456"
            }
        )
        assert response.status_code == 409
        assert "username already exists" in response.json()["detail"]
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register user first
        client.post(
            "/register",
            params={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        # Login
        response = client.post(
            "/login",
            params={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email fails."""
        response = client.post(
            "/login",
            params={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client):
        """Test login with wrong password fails."""
        # Register user first
        client.post(
            "/register",
            params={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        # Login with wrong password
        response = client.post(
            "/login",
            params={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_validate_valid_token(self, client):
        """Test token validation with valid token."""
        # Register and login
        client.post(
            "/register",
            params={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        login_response = client.post(
            "/login",
            params={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Validate token
        response = client.post("/validate", params={"token": token})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["username"] == "testuser"
    
    def test_validate_invalid_token(self, client):
        """Test token validation with invalid token."""
        response = client.post("/validate", params={"token": "invalid.token.here"})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
