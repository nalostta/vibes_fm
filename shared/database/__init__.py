"""
Shared database module for all microservices.
"""
from .base import Base, engine, SessionLocal, get_db, DATABASE_URL
from .types import UUID

__all__ = ["Base", "engine", "SessionLocal", "get_db", "DATABASE_URL", "UUID"]
