"""
Shared pytest fixtures for all microservice tests.
Uses in-memory SQLite database for testing isolation.
"""
import os
import sys

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base

# Create a test-specific Base for SQLite compatibility
TestBase = declarative_base()


@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session with all tables."""
    from shared.database import Base
    
    # Import all models to register them with Base.metadata
    # Note: Using hyphenated directory names requires importlib
    import importlib.util
    
    # Load catalog models
    spec = importlib.util.spec_from_file_location(
        "catalog", 
        os.path.join(PROJECT_ROOT, "services/catalog-service/app/models/catalog.py")
    )
    catalog_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(catalog_module)
    
    # Load user models
    spec = importlib.util.spec_from_file_location(
        "user",
        os.path.join(PROJECT_ROOT, "services/user-service/app/models/user.py")
    )
    user_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_module)
    
    # Load playback history models
    spec = importlib.util.spec_from_file_location(
        "playback_history",
        os.path.join(PROJECT_ROOT, "services/playback-history-service/app/models/playback_history.py")
    )
    playback_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(playback_module)
    
    # Load library/playlist models
    spec = importlib.util.spec_from_file_location(
        "playlist",
        os.path.join(PROJECT_ROOT, "services/library-playlist-service/app/models/playlist.py")
    )
    playlist_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(playlist_module)
    
    Base.metadata.create_all(bind=test_engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=test_engine)
