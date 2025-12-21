"""
Shared User Model

This schema holds all authentication and profile information for users.
Used by both auth-service and user-service.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime

from shared.database import Base, UUID


class User(Base):
    """
    User model for storing user authentication and profile information.
    
    Attributes:
        user_id: Unique identifier for the user (UUID)
        username: Unique display name for the user
        email: Unique email address for authentication
        password_hash: Securely hashed password
        created_at: Timestamp of account creation
        last_login_at: Timestamp of last successful login
        is_premium: Flag indicating premium subscription status
    """
    __tablename__ = "users"

    user_id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash = Column(
        String(255),
        nullable=False
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    last_login_at = Column(
        DateTime,
        nullable=True
    )
    is_premium = Column(
        Boolean,
        default=False,
        nullable=False
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, email={self.email})>"

    def to_dict(self):
        """Convert user model to dictionary representation."""
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "is_premium": self.is_premium
        }
