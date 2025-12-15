"""
Custom SQLAlchemy types for cross-database compatibility.
"""
import uuid as uuid_module
from sqlalchemy import String, TypeDecorator


class UUID(TypeDecorator):
    """
    Platform-independent UUID type that works with both PostgreSQL and SQLite.
    
    Uses String(36) as the underlying implementation, which stores UUIDs as
    their string representation. This allows the same model code to work
    with both PostgreSQL (production) and SQLite (testing).
    """
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert UUID to string when storing in database."""
        if value is not None:
            if isinstance(value, uuid_module.UUID):
                return str(value)
            return value
        return value

    def process_result_value(self, value, dialect):
        """Convert string back to UUID when reading from database."""
        if value is not None:
            if not isinstance(value, uuid_module.UUID):
                return uuid_module.UUID(value)
        return value
