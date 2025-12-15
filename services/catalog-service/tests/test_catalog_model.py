"""
Unit tests for Catalog Service data models.

Test Coverage Goal: > 80% Line Coverage
Key Test Scenarios:
- Creating artists, albums, tracks, and genres
- Retrieving album with all tracks
- Testing junction tables (track_artists, track_genres)
- Model to_dict conversions
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

# Load Catalog models from hyphenated directory using importlib
spec = importlib.util.spec_from_file_location(
    "catalog",
    os.path.join(PROJECT_ROOT, "services/catalog-service/app/models/catalog.py")
)
catalog_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog_module)
Artist = catalog_module.Artist
Album = catalog_module.Album
Track = catalog_module.Track
Genre = catalog_module.Genre


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


class TestArtistModel:
    """Test cases for the Artist model."""

    def test_create_artist(self, db_session):
        """Test creating an artist with valid data."""
        artist = Artist(
            name="Test Artist",
            bio="A test artist biography",
            image_url="https://example.com/artist.jpg"
        )
        db_session.add(artist)
        db_session.commit()
        
        assert artist.artist_id is not None
        assert artist.name == "Test Artist"
        assert artist.bio == "A test artist biography"
        assert artist.created_at is not None

    def test_artist_to_dict(self, db_session):
        """Test artist model to_dict conversion."""
        artist = Artist(name="Dict Artist")
        db_session.add(artist)
        db_session.commit()
        
        artist_dict = artist.to_dict()
        assert "artist_id" in artist_dict
        assert artist_dict["name"] == "Dict Artist"
        assert "created_at" in artist_dict

    def test_artist_repr(self, db_session):
        """Test artist model string representation."""
        artist = Artist(name="Repr Artist")
        db_session.add(artist)
        db_session.commit()
        
        repr_str = repr(artist)
        assert "Repr Artist" in repr_str


class TestGenreModel:
    """Test cases for the Genre model."""

    def test_create_genre(self, db_session):
        """Test creating a genre."""
        genre = Genre(
            name="Electronic",
            description="Electronic music genre"
        )
        db_session.add(genre)
        db_session.commit()
        
        assert genre.genre_id is not None
        assert genre.name == "Electronic"

    def test_genre_unique_name(self, db_session):
        """Test that duplicate genre names are rejected."""
        genre1 = Genre(name="Rock")
        db_session.add(genre1)
        db_session.commit()
        
        genre2 = Genre(name="Rock")
        db_session.add(genre2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_genre_to_dict(self, db_session):
        """Test genre model to_dict conversion."""
        genre = Genre(name="Jazz", description="Jazz music")
        db_session.add(genre)
        db_session.commit()
        
        genre_dict = genre.to_dict()
        assert genre_dict["name"] == "Jazz"
        assert genre_dict["description"] == "Jazz music"


class TestAlbumModel:
    """Test cases for the Album model."""

    def test_create_album(self, db_session):
        """Test creating an album with an artist."""
        artist = Artist(name="Album Artist")
        db_session.add(artist)
        db_session.commit()
        
        album = Album(
            title="Test Album",
            artist_id=artist.artist_id,
            release_date=datetime(2024, 1, 1),
            cover_image_url="https://example.com/cover.jpg"
        )
        db_session.add(album)
        db_session.commit()
        
        assert album.album_id is not None
        assert album.title == "Test Album"
        assert album.artist_id == artist.artist_id

    def test_album_artist_relationship(self, db_session):
        """Test album-artist relationship."""
        artist = Artist(name="Related Artist")
        db_session.add(artist)
        db_session.commit()
        
        album = Album(title="Related Album", artist_id=artist.artist_id)
        db_session.add(album)
        db_session.commit()
        
        assert album.artist.name == "Related Artist"
        assert album in artist.albums

    def test_album_to_dict(self, db_session):
        """Test album model to_dict conversion."""
        artist = Artist(name="Dict Album Artist")
        db_session.add(artist)
        db_session.commit()
        
        album = Album(title="Dict Album", artist_id=artist.artist_id)
        db_session.add(album)
        db_session.commit()
        
        album_dict = album.to_dict()
        assert album_dict["title"] == "Dict Album"
        assert "album_id" in album_dict


class TestTrackModel:
    """Test cases for the Track model."""

    def test_create_track(self, db_session):
        """Test creating a track."""
        artist = Artist(name="Track Artist")
        db_session.add(artist)
        db_session.commit()
        
        album = Album(title="Track Album", artist_id=artist.artist_id)
        db_session.add(album)
        db_session.commit()
        
        track = Track(
            title="Test Track",
            album_id=album.album_id,
            duration_ms=180000,
            track_number=1,
            audio_url="https://cdn.example.com/track.mp3"
        )
        db_session.add(track)
        db_session.commit()
        
        assert track.track_id is not None
        assert track.title == "Test Track"
        assert track.duration_ms == 180000

    def test_track_album_relationship(self, db_session):
        """Test track-album relationship."""
        artist = Artist(name="Rel Artist")
        db_session.add(artist)
        db_session.commit()
        
        album = Album(title="Rel Album", artist_id=artist.artist_id)
        db_session.add(album)
        db_session.commit()
        
        track = Track(title="Rel Track", album_id=album.album_id, track_number=1)
        db_session.add(track)
        db_session.commit()
        
        assert track.album.title == "Rel Album"
        assert track in album.tracks

    def test_track_artist_many_to_many(self, db_session):
        """Test track-artist many-to-many relationship (featuring artists)."""
        artist1 = Artist(name="Primary Artist")
        artist2 = Artist(name="Featured Artist")
        db_session.add_all([artist1, artist2])
        db_session.commit()
        
        track = Track(title="Collab Track")
        track.artists.append(artist1)
        track.artists.append(artist2)
        db_session.add(track)
        db_session.commit()
        
        assert len(track.artists) == 2
        assert artist1 in track.artists
        assert artist2 in track.artists

    def test_track_genre_many_to_many(self, db_session):
        """Test track-genre many-to-many relationship."""
        genre1 = Genre(name="Pop")
        genre2 = Genre(name="Dance")
        db_session.add_all([genre1, genre2])
        db_session.commit()
        
        track = Track(title="Multi-Genre Track")
        track.genres.append(genre1)
        track.genres.append(genre2)
        db_session.add(track)
        db_session.commit()
        
        assert len(track.genres) == 2
        assert genre1 in track.genres

    def test_track_to_dict(self, db_session):
        """Test track model to_dict conversion."""
        track = Track(
            title="Dict Track",
            duration_ms=200000,
            track_number=5
        )
        db_session.add(track)
        db_session.commit()
        
        track_dict = track.to_dict()
        assert track_dict["title"] == "Dict Track"
        assert track_dict["duration_ms"] == 200000
        assert "track_id" in track_dict

    def test_retrieve_album_with_all_tracks(self, db_session):
        """Test retrieving an album and correctly listing all tracks."""
        artist = Artist(name="Full Album Artist")
        db_session.add(artist)
        db_session.commit()
        
        album = Album(title="Full Album", artist_id=artist.artist_id)
        db_session.add(album)
        db_session.commit()
        
        tracks = [
            Track(title=f"Track {i}", album_id=album.album_id, track_number=i)
            for i in range(1, 6)
        ]
        db_session.add_all(tracks)
        db_session.commit()
        
        retrieved_album = db_session.query(Album).filter(Album.album_id == album.album_id).first()
        assert len(retrieved_album.tracks) == 5
        assert all(t.album_id == album.album_id for t in retrieved_album.tracks)
