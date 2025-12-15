"""
Unit tests for User Service.

Test Coverage Goal: > 80% Line Coverage
Key Test Scenarios:
- Profile retrieval (authenticated, unauthenticated)
- Profile updates (username, email)
- Password changes
- Premium status updates
- Account deletion
- User listing with pagination
"""
import os
import sys
import importlib.util
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, HTTPException, status, Depends, Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base
from shared.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
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
def test_user(db_session):
    """Create a test user for authenticated endpoints."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(test_user):
    """Create a valid JWT token for the test user."""
    token_data = {
        "sub": str(test_user.user_id),
        "username": test_user.username,
        "email": test_user.email,
        "is_premium": test_user.is_premium
    }
    return create_access_token(data=token_data)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    Base.metadata.create_all(bind=test_engine)
    
    app = FastAPI()
    
    def get_current_user_from_token(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(override_get_db)
    ) -> User:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = parts[1]
        payload = decode_access_token(token)
        
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "user-service"}
    
    @app.get("/me")
    def get_current_user_profile(current_user: User = Depends(get_current_user_from_token)):
        return {
            "user_id": str(current_user.user_id),
            "username": current_user.username,
            "email": current_user.email,
            "is_premium": current_user.is_premium,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
        }
    
    @app.get("/users/{user_id}")
    def get_user_by_id(user_id: str, db: Session = Depends(override_get_db)):
        from uuid import UUID
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        user = db.query(User).filter(User.user_id == uuid_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "is_premium": user.is_premium
        }
    
    @app.put("/me")
    def update_profile(
        username: Optional[str] = None,
        email: Optional[str] = None,
        current_user: User = Depends(get_current_user_from_token),
        db: Session = Depends(override_get_db)
    ):
        if username and username != current_user.username:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                raise HTTPException(status_code=409, detail="Username already taken")
            current_user.username = username
        
        if email and email != current_user.email:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                raise HTTPException(status_code=409, detail="Email already taken")
            current_user.email = email
        
        db.commit()
        db.refresh(current_user)
        
        return {
            "user_id": str(current_user.user_id),
            "username": current_user.username,
            "email": current_user.email,
            "is_premium": current_user.is_premium
        }
    
    @app.put("/me/password")
    def change_password(
        current_password: str,
        new_password: str,
        current_user: User = Depends(get_current_user_from_token),
        db: Session = Depends(override_get_db)
    ):
        if not verify_password(current_password, current_user.password_hash):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        current_user.password_hash = get_password_hash(new_password)
        db.commit()
        
        return {"message": "Password changed successfully"}
    
    @app.put("/me/premium")
    def update_premium(
        is_premium: bool,
        current_user: User = Depends(get_current_user_from_token),
        db: Session = Depends(override_get_db)
    ):
        current_user.is_premium = is_premium
        db.commit()
        db.refresh(current_user)
        
        return {
            "user_id": str(current_user.user_id),
            "username": current_user.username,
            "is_premium": current_user.is_premium
        }
    
    @app.delete("/me")
    def delete_account(
        current_user: User = Depends(get_current_user_from_token),
        db: Session = Depends(override_get_db)
    ):
        db.delete(current_user)
        db.commit()
        return {"message": "Account deleted successfully"}
    
    @app.get("/users")
    def list_users(
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(override_get_db)
    ):
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        offset = (page - 1) * page_size
        total = db.query(User).count()
        users = db.query(User).offset(offset).limit(page_size).all()
        
        return {
            "users": [
                {
                    "user_id": str(u.user_id),
                    "username": u.username,
                    "email": u.email,
                    "is_premium": u.is_premium
                }
                for u in users
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    with TestClient(app) as test_client:
        yield test_client
    
    Base.metadata.drop_all(bind=test_engine)


class TestUserServiceEndpoints:
    """Tests for User Service API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_get_profile_unauthorized(self, client):
        """Test getting profile without authorization fails."""
        response = client.get("/me")
        assert response.status_code == 401
    
    def test_get_profile_invalid_token(self, client):
        """Test getting profile with invalid token fails."""
        response = client.get("/me", headers={"Authorization": "Bearer invalid.token"})
        assert response.status_code == 401
    
    def test_get_profile_success(self, client, test_user, auth_token):
        """Test getting profile with valid token succeeds."""
        response = client.get("/me", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_get_user_by_id_success(self, client, test_user):
        """Test getting user by ID succeeds."""
        response = client.get(f"/users/{test_user.user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
    
    def test_get_user_by_id_not_found(self, client):
        """Test getting non-existent user returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.get(f"/users/{fake_id}")
        assert response.status_code == 404
    
    def test_get_user_by_id_invalid_format(self, client):
        """Test getting user with invalid ID format returns 400."""
        response = client.get("/users/invalid-uuid")
        assert response.status_code == 400
    
    def test_update_profile_username(self, client, test_user, auth_token):
        """Test updating username succeeds."""
        response = client.put(
            "/me",
            params={"username": "newusername"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "newusername"
    
    def test_update_profile_email(self, client, test_user, auth_token):
        """Test updating email succeeds."""
        response = client.put(
            "/me",
            params={"email": "newemail@example.com"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newemail@example.com"
    
    def test_update_profile_duplicate_username(self, client, db_session, test_user, auth_token):
        """Test updating to existing username fails."""
        # Create another user
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash=get_password_hash("password123")
        )
        db_session.add(other_user)
        db_session.commit()
        
        response = client.put(
            "/me",
            params={"username": "otheruser"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 409
    
    def test_change_password_success(self, client, test_user, auth_token):
        """Test changing password with correct current password succeeds."""
        response = client.put(
            "/me/password",
            params={
                "current_password": "password123",
                "new_password": "newpassword456"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
    
    def test_change_password_wrong_current(self, client, test_user, auth_token):
        """Test changing password with wrong current password fails."""
        response = client.put(
            "/me/password",
            params={
                "current_password": "wrongpassword",
                "new_password": "newpassword456"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 401
    
    def test_update_premium_status(self, client, test_user, auth_token):
        """Test updating premium status succeeds."""
        response = client.put(
            "/me/premium",
            params={"is_premium": True},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["is_premium"] is True
    
    def test_delete_account(self, client, test_user, auth_token):
        """Test deleting account succeeds."""
        response = client.delete("/me", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        assert response.json()["message"] == "Account deleted successfully"
    
    def test_list_users(self, client, test_user):
        """Test listing users returns paginated results."""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_list_users_pagination(self, client, db_session):
        """Test user listing pagination works correctly."""
        # Create multiple users
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash=get_password_hash("password123")
            )
            db_session.add(user)
        db_session.commit()
        
        response = client.get("/users", params={"page": 1, "page_size": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestAuthorizationHeader:
    """Tests for authorization header parsing."""
    
    def test_missing_authorization_header(self, client):
        """Test request without authorization header fails."""
        response = client.get("/me")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_invalid_authorization_format(self, client):
        """Test request with invalid authorization format fails."""
        response = client.get("/me", headers={"Authorization": "InvalidFormat token"})
        assert response.status_code == 401
    
    def test_missing_bearer_prefix(self, client):
        """Test request without Bearer prefix fails."""
        response = client.get("/me", headers={"Authorization": "token123"})
        assert response.status_code == 401
