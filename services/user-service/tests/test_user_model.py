"""
Unit tests for User Service data models.

Test Coverage Goal: > 80% Line Coverage
Key Test Scenarios:
- Creating a user with valid data
- Retrieving user profile
- Handling missing/duplicate user IDs
- User model to_dict conversion
"""
import os
import sys
import uuid
import importlib.util
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base

# Load User model from hyphenated directory using importlib
spec = importlib.util.spec_from_file_location(
    "user",
    os.path.join(PROJECT_ROOT, "services/user-service/app/models/user.py")
)
user_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_module)
User = user_module.User


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestUserModel:
    """Test cases for the User model."""

    def test_create_user_with_valid_data(self, db_session):
        """Test creating a user with all required fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.user_id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.is_premium is False
        assert user.created_at is not None
        assert user.last_login_at is None

    def test_user_uuid_generation(self, db_session):
        """Test that user_id is automatically generated as UUID."""
        user = User(
            username="uuidtest",
            email="uuid@example.com",
            password_hash="hash123"
        )
        db_session.add(user)
        db_session.commit()
        
        assert isinstance(user.user_id, uuid.UUID)

    def test_user_unique_username(self, db_session):
        """Test that duplicate usernames are rejected."""
        user1 = User(
            username="duplicate",
            email="user1@example.com",
            password_hash="hash1"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="duplicate",
            email="user2@example.com",
            password_hash="hash2"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_user_unique_email(self, db_session):
        """Test that duplicate emails are rejected."""
        user1 = User(
            username="user1",
            email="duplicate@example.com",
            password_hash="hash1"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="user2",
            email="duplicate@example.com",
            password_hash="hash2"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_user_to_dict(self, db_session):
        """Test user model to_dict conversion."""
        user = User(
            username="dicttest",
            email="dict@example.com",
            password_hash="hash123",
            is_premium=True
        )
        db_session.add(user)
        db_session.commit()
        
        user_dict = user.to_dict()
        
        assert "user_id" in user_dict
        assert user_dict["username"] == "dicttest"
        assert user_dict["email"] == "dict@example.com"
        assert user_dict["is_premium"] is True
        assert "password_hash" not in user_dict  # Should not expose password
        assert "created_at" in user_dict

    def test_user_repr(self, db_session):
        """Test user model string representation."""
        user = User(
            username="reprtest",
            email="repr@example.com",
            password_hash="hash123"
        )
        db_session.add(user)
        db_session.commit()
        
        repr_str = repr(user)
        assert "reprtest" in repr_str
        assert "repr@example.com" in repr_str

    def test_user_premium_status(self, db_session):
        """Test setting premium status."""
        user = User(
            username="premium",
            email="premium@example.com",
            password_hash="hash123",
            is_premium=True
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.is_premium is True

    def test_user_last_login_update(self, db_session):
        """Test updating last login timestamp."""
        user = User(
            username="logintest",
            email="login@example.com",
            password_hash="hash123"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.last_login_at is None
        
        user.last_login_at = datetime.utcnow()
        db_session.commit()
        
        assert user.last_login_at is not None

    def test_retrieve_user_by_id(self, db_session):
        """Test retrieving a user by their ID."""
        user = User(
            username="findme",
            email="findme@example.com",
            password_hash="hash123"
        )
        db_session.add(user)
        db_session.commit()
        
        user_id = user.user_id
        
        found_user = db_session.query(User).filter(User.user_id == user_id).first()
        assert found_user is not None
        assert found_user.username == "findme"

    def test_retrieve_nonexistent_user(self, db_session):
        """Test retrieving a user that doesn't exist."""
        random_id = uuid.uuid4()
        found_user = db_session.query(User).filter(User.user_id == random_id).first()
        assert found_user is None
