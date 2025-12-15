"""
Unit tests for Playback History Service data models.

Test Coverage Goal: > 80% Line Coverage
Key Test Scenarios:
- Recording playback events
- High-volume insertion handling
- Time-series indexing verification
- Model to_dict conversion
"""
import os
import sys
import uuid
import importlib.util
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base

# Load User model
spec = importlib.util.spec_from_file_location(
    "user",
    os.path.join(PROJECT_ROOT, "services/user-service/app/models/user.py")
)
user_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_module)
User = user_module.User

# Load Track model from Catalog service
spec = importlib.util.spec_from_file_location(
    "catalog",
    os.path.join(PROJECT_ROOT, "services/catalog-service/app/models/catalog.py")
)
catalog_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog_module)
Track = catalog_module.Track

# Load PlaybackHistory model
spec = importlib.util.spec_from_file_location(
    "playback_history",
    os.path.join(PROJECT_ROOT, "services/playback-history-service/app/models/playback_history.py")
)
playback_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(playback_module)
PlaybackHistory = playback_module.PlaybackHistory


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


@pytest.fixture
def test_user(db_session):
    """Create a test user for playback history tests."""
    user = User(
        username="historyuser",
        email="history@example.com",
        password_hash="hash123"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_track(db_session):
    """Create a test track for playback history tests."""
    track = Track(
        title="Test Track",
        duration_ms=180000
    )
    db_session.add(track)
    db_session.commit()
    return track


class TestPlaybackHistoryModel:
    """Test cases for the PlaybackHistory model."""

    def test_create_playback_event(self, db_session, test_user, test_track):
        """Test creating a playback history event."""
        event = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id,
            play_duration_ms=120000,
            source="album"
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.history_id is not None
        assert event.listened_at is not None
        assert event.play_duration_ms == 120000
        assert event.source == "album"

    def test_auto_increment_history_id(self, db_session, test_user, test_track):
        """Test that history_id auto-increments for high-volume logs."""
        events = []
        for i in range(5):
            event = PlaybackHistory(
                user_id=test_user.user_id,
                track_id=test_track.track_id,
                play_duration_ms=60000 + i * 1000,
                source="playlist"
            )
            db_session.add(event)
            events.append(event)
        db_session.commit()
        
        # Verify auto-incrementing IDs
        ids = [e.history_id for e in events]
        assert len(set(ids)) == 5  # All unique
        assert ids == sorted(ids)  # Sequential

    def test_playback_event_to_dict(self, db_session, test_user, test_track):
        """Test playback history model to_dict conversion."""
        event = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id,
            play_duration_ms=90000,
            source="radio"
        )
        db_session.add(event)
        db_session.commit()
        
        event_dict = event.to_dict()
        assert "history_id" in event_dict
        assert "user_id" in event_dict
        assert "track_id" in event_dict
        assert "listened_at" in event_dict
        assert event_dict["play_duration_ms"] == 90000
        assert event_dict["source"] == "radio"

    def test_playback_event_repr(self, db_session, test_user, test_track):
        """Test playback history model string representation."""
        event = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id
        )
        db_session.add(event)
        db_session.commit()
        
        repr_str = repr(event)
        assert "PlaybackHistory" in repr_str

    def test_playback_source_types(self, db_session, test_user, test_track):
        """Test different playback source types."""
        sources = ["album", "playlist", "radio", "search", "library"]
        
        for source in sources:
            event = PlaybackHistory(
                user_id=test_user.user_id,
                track_id=test_track.track_id,
                source=source
            )
            db_session.add(event)
        db_session.commit()
        
        events = db_session.query(PlaybackHistory).filter(
            PlaybackHistory.user_id == test_user.user_id
        ).all()
        
        assert len(events) == 5
        recorded_sources = [e.source for e in events]
        assert set(recorded_sources) == set(sources)

    def test_playback_without_duration(self, db_session, test_user, test_track):
        """Test creating playback event without duration (nullable field)."""
        event = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id,
            source="album"
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.play_duration_ms is None

    def test_playback_without_source(self, db_session, test_user, test_track):
        """Test creating playback event without source (nullable field)."""
        event = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id,
            play_duration_ms=180000
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.source is None


class TestPlaybackHistoryQueries:
    """Test cases for querying playback history."""

    def test_query_user_history(self, db_session, test_user, test_track):
        """Test querying playback history for a specific user."""
        # Create multiple events
        for i in range(10):
            event = PlaybackHistory(
                user_id=test_user.user_id,
                track_id=test_track.track_id,
                play_duration_ms=60000 + i * 1000
            )
            db_session.add(event)
        db_session.commit()
        
        user_history = db_session.query(PlaybackHistory).filter(
            PlaybackHistory.user_id == test_user.user_id
        ).all()
        
        assert len(user_history) == 10

    def test_query_track_plays(self, db_session, test_user, test_track):
        """Test querying all plays of a specific track."""
        # Create another user
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash="hash456"
        )
        db_session.add(user2)
        db_session.commit()
        
        # Both users play the same track
        event1 = PlaybackHistory(user_id=test_user.user_id, track_id=test_track.track_id)
        event2 = PlaybackHistory(user_id=user2.user_id, track_id=test_track.track_id)
        db_session.add_all([event1, event2])
        db_session.commit()
        
        track_plays = db_session.query(PlaybackHistory).filter(
            PlaybackHistory.track_id == test_track.track_id
        ).all()
        
        assert len(track_plays) == 2

    def test_query_by_time_range(self, db_session, test_user, test_track):
        """Test querying playback history by time range."""
        now = datetime.utcnow()
        
        # Create events at different times
        event1 = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id
        )
        event1.listened_at = now - timedelta(hours=2)
        
        event2 = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id
        )
        event2.listened_at = now - timedelta(hours=1)
        
        event3 = PlaybackHistory(
            user_id=test_user.user_id,
            track_id=test_track.track_id
        )
        event3.listened_at = now
        
        db_session.add_all([event1, event2, event3])
        db_session.commit()
        
        # Query events from last 90 minutes
        cutoff = now - timedelta(minutes=90)
        recent_events = db_session.query(PlaybackHistory).filter(
            PlaybackHistory.listened_at >= cutoff
        ).all()
        
        assert len(recent_events) == 2

    def test_order_by_listened_at(self, db_session, test_user, test_track):
        """Test ordering playback history by listened_at timestamp."""
        now = datetime.utcnow()
        
        events = []
        for i in range(5):
            event = PlaybackHistory(
                user_id=test_user.user_id,
                track_id=test_track.track_id
            )
            event.listened_at = now - timedelta(hours=i)
            events.append(event)
        
        db_session.add_all(events)
        db_session.commit()
        
        # Query in descending order (most recent first)
        ordered_events = db_session.query(PlaybackHistory).filter(
            PlaybackHistory.user_id == test_user.user_id
        ).order_by(PlaybackHistory.listened_at.desc()).all()
        
        assert len(ordered_events) == 5
        # Verify ordering
        for i in range(len(ordered_events) - 1):
            assert ordered_events[i].listened_at >= ordered_events[i + 1].listened_at


class TestHighVolumeScenarios:
    """Test high-volume insertion scenarios."""

    def test_bulk_insert_performance(self, db_session, test_user, test_track):
        """Test bulk insertion of playback events."""
        events = [
            PlaybackHistory(
                user_id=test_user.user_id,
                track_id=test_track.track_id,
                play_duration_ms=60000 + i,
                source="playlist"
            )
            for i in range(100)
        ]
        
        db_session.add_all(events)
        db_session.commit()
        
        count = db_session.query(PlaybackHistory).filter(
            PlaybackHistory.user_id == test_user.user_id
        ).count()
        
        assert count == 100

    def test_multiple_users_same_track(self, db_session, test_track):
        """Test multiple users playing the same track."""
        users = []
        for i in range(10):
            user = User(
                username=f"bulkuser{i}",
                email=f"bulk{i}@example.com",
                password_hash="hash"
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()
        
        # Each user plays the track
        for user in users:
            event = PlaybackHistory(
                user_id=user.user_id,
                track_id=test_track.track_id
            )
            db_session.add(event)
        db_session.commit()
        
        total_plays = db_session.query(PlaybackHistory).filter(
            PlaybackHistory.track_id == test_track.track_id
        ).count()
        
        assert total_plays == 10
