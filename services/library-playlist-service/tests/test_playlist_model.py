"""
Unit tests for Library & Playlist Service data models.

Test Coverage Goal: > 80% Line Coverage
Key Test Scenarios:
- Creating playlists
- Adding/removing tracks from playlists
- User library management
- Edge cases: adding duplicate tracks, deleting non-existent playlists
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

# Load Playlist models
spec = importlib.util.spec_from_file_location(
    "playlist",
    os.path.join(PROJECT_ROOT, "services/library-playlist-service/app/models/playlist.py")
)
playlist_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(playlist_module)
Playlist = playlist_module.Playlist
PlaylistTrack = playlist_module.PlaylistTrack
UserLibrary = playlist_module.UserLibrary


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
    """Create a test user for playlist tests."""
    user = User(
        username="playlistuser",
        email="playlist@example.com",
        password_hash="hash123"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_tracks(db_session):
    """Create test tracks for playlist tests."""
    tracks = [
        Track(title=f"Test Track {i}", duration_ms=180000 + i * 1000)
        for i in range(5)
    ]
    db_session.add_all(tracks)
    db_session.commit()
    return tracks


class TestPlaylistModel:
    """Test cases for the Playlist model."""

    def test_create_playlist(self, db_session, test_user):
        """Test creating a playlist."""
        playlist = Playlist(
            owner_user_id=test_user.user_id,
            name="My Playlist",
            is_private=True
        )
        db_session.add(playlist)
        db_session.commit()
        
        assert playlist.playlist_id is not None
        assert playlist.name == "My Playlist"
        assert playlist.is_private is True
        assert playlist.created_at is not None

    def test_playlist_default_private(self, db_session, test_user):
        """Test that playlists are private by default."""
        playlist = Playlist(
            owner_user_id=test_user.user_id,
            name="Default Private"
        )
        db_session.add(playlist)
        db_session.commit()
        
        assert playlist.is_private is True

    def test_playlist_to_dict(self, db_session, test_user):
        """Test playlist model to_dict conversion."""
        playlist = Playlist(
            owner_user_id=test_user.user_id,
            name="Dict Playlist"
        )
        db_session.add(playlist)
        db_session.commit()
        
        playlist_dict = playlist.to_dict()
        assert playlist_dict["name"] == "Dict Playlist"
        assert "playlist_id" in playlist_dict
        assert "owner_user_id" in playlist_dict

    def test_playlist_repr(self, db_session, test_user):
        """Test playlist model string representation."""
        playlist = Playlist(
            owner_user_id=test_user.user_id,
            name="Repr Playlist"
        )
        db_session.add(playlist)
        db_session.commit()
        
        repr_str = repr(playlist)
        assert "Repr Playlist" in repr_str


class TestPlaylistTrackModel:
    """Test cases for the PlaylistTrack junction model."""

    def test_add_track_to_playlist(self, db_session, test_user, test_tracks):
        """Test adding a track to a playlist."""
        playlist = Playlist(owner_user_id=test_user.user_id, name="Track Test")
        db_session.add(playlist)
        db_session.commit()
        
        playlist_track = PlaylistTrack(
            playlist_id=playlist.playlist_id,
            track_id=test_tracks[0].track_id,
            position=1
        )
        db_session.add(playlist_track)
        db_session.commit()
        
        assert playlist_track.playlist_track_id is not None
        assert playlist_track.position == 1

    def test_add_multiple_tracks_with_ordering(self, db_session, test_user, test_tracks):
        """Test adding multiple tracks with proper ordering."""
        playlist = Playlist(owner_user_id=test_user.user_id, name="Ordered Playlist")
        db_session.add(playlist)
        db_session.commit()
        
        for i, track in enumerate(test_tracks):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.playlist_id,
                track_id=track.track_id,
                position=i + 1
            )
            db_session.add(playlist_track)
        db_session.commit()
        
        # Verify ordering
        tracks_in_playlist = db_session.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist.playlist_id
        ).order_by(PlaylistTrack.position).all()
        
        assert len(tracks_in_playlist) == 5
        for i, pt in enumerate(tracks_in_playlist):
            assert pt.position == i + 1

    def test_playlist_track_relationship(self, db_session, test_user, test_tracks):
        """Test playlist-track relationship via junction table."""
        playlist = Playlist(owner_user_id=test_user.user_id, name="Rel Playlist")
        db_session.add(playlist)
        db_session.commit()
        
        playlist_track = PlaylistTrack(
            playlist_id=playlist.playlist_id,
            track_id=test_tracks[0].track_id,
            position=1
        )
        db_session.add(playlist_track)
        db_session.commit()
        
        assert playlist_track.playlist.name == "Rel Playlist"
        assert playlist_track in playlist.tracks

    def test_playlist_track_to_dict(self, db_session, test_user, test_tracks):
        """Test playlist track model to_dict conversion."""
        playlist = Playlist(owner_user_id=test_user.user_id, name="Dict PT")
        db_session.add(playlist)
        db_session.commit()
        
        playlist_track = PlaylistTrack(
            playlist_id=playlist.playlist_id,
            track_id=test_tracks[0].track_id,
            position=1
        )
        db_session.add(playlist_track)
        db_session.commit()
        
        pt_dict = playlist_track.to_dict()
        assert pt_dict["position"] == 1
        assert "playlist_id" in pt_dict
        assert "track_id" in pt_dict

    def test_remove_track_from_playlist(self, db_session, test_user, test_tracks):
        """Test removing a track from a playlist."""
        playlist = Playlist(owner_user_id=test_user.user_id, name="Remove Test")
        db_session.add(playlist)
        db_session.commit()
        
        playlist_track = PlaylistTrack(
            playlist_id=playlist.playlist_id,
            track_id=test_tracks[0].track_id,
            position=1
        )
        db_session.add(playlist_track)
        db_session.commit()
        
        # Remove the track
        db_session.delete(playlist_track)
        db_session.commit()
        
        remaining = db_session.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist.playlist_id
        ).all()
        assert len(remaining) == 0


class TestUserLibraryModel:
    """Test cases for the UserLibrary model."""

    def test_save_track_to_library(self, db_session, test_user, test_tracks):
        """Test saving a track to user's library."""
        library_entry = UserLibrary(
            user_id=test_user.user_id,
            track_id=test_tracks[0].track_id
        )
        db_session.add(library_entry)
        db_session.commit()
        
        assert library_entry.saved_at is not None

    def test_library_composite_primary_key(self, db_session, test_user, test_tracks):
        """Test that duplicate user-track combinations are rejected."""
        entry1 = UserLibrary(
            user_id=test_user.user_id,
            track_id=test_tracks[0].track_id
        )
        db_session.add(entry1)
        db_session.commit()
        
        entry2 = UserLibrary(
            user_id=test_user.user_id,
            track_id=test_tracks[0].track_id
        )
        db_session.add(entry2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_library_to_dict(self, db_session, test_user, test_tracks):
        """Test user library model to_dict conversion."""
        entry = UserLibrary(
            user_id=test_user.user_id,
            track_id=test_tracks[0].track_id
        )
        db_session.add(entry)
        db_session.commit()
        
        entry_dict = entry.to_dict()
        assert "user_id" in entry_dict
        assert "track_id" in entry_dict
        assert "saved_at" in entry_dict

    def test_library_repr(self, db_session, test_user, test_tracks):
        """Test user library model string representation."""
        entry = UserLibrary(
            user_id=test_user.user_id,
            track_id=test_tracks[0].track_id
        )
        db_session.add(entry)
        db_session.commit()
        
        repr_str = repr(entry)
        assert "UserLibrary" in repr_str

    def test_remove_track_from_library(self, db_session, test_user, test_tracks):
        """Test removing a track from user's library."""
        entry = UserLibrary(
            user_id=test_user.user_id,
            track_id=test_tracks[0].track_id
        )
        db_session.add(entry)
        db_session.commit()
        
        db_session.delete(entry)
        db_session.commit()
        
        remaining = db_session.query(UserLibrary).filter(
            UserLibrary.user_id == test_user.user_id
        ).all()
        assert len(remaining) == 0


class TestEdgeCases:
    """Test edge cases for Library & Playlist Service."""

    def test_delete_nonexistent_playlist(self, db_session, test_user):
        """Test handling deletion of a playlist that doesn't exist."""
        random_id = uuid.uuid4()
        playlist = db_session.query(Playlist).filter(Playlist.playlist_id == random_id).first()
        assert playlist is None

    def test_add_track_already_in_playlist(self, db_session, test_user, test_tracks):
        """Test adding a track that's already in the playlist (different position)."""
        playlist = Playlist(owner_user_id=test_user.user_id, name="Duplicate Test")
        db_session.add(playlist)
        db_session.commit()
        
        # Add same track twice at different positions (allowed)
        pt1 = PlaylistTrack(
            playlist_id=playlist.playlist_id,
            track_id=test_tracks[0].track_id,
            position=1
        )
        pt2 = PlaylistTrack(
            playlist_id=playlist.playlist_id,
            track_id=test_tracks[0].track_id,
            position=2
        )
        db_session.add_all([pt1, pt2])
        db_session.commit()
        
        # Should have 2 entries (same track can appear multiple times)
        count = db_session.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist.playlist_id
        ).count()
        assert count == 2
