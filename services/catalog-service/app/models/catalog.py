"""
Catalog Service Data Models

This service manages metadata for Artists, Albums, Tracks, and Genres.
The track_id from this service is referenced by other services (Playback History, Library, Playlist).
"""
import os
import sys
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship

# Add project root to path for shared imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base, UUID


# Junction table for many-to-many relationship between tracks and artists (for featuring artists)
track_artists = Table(
    'track_artists',
    Base.metadata,
    Column('track_id', UUID(), ForeignKey('tracks.track_id', ondelete='CASCADE'), primary_key=True),
    Column('artist_id', UUID(), ForeignKey('artists.artist_id', ondelete='CASCADE'), primary_key=True),
    Column('is_primary', Integer, default=0)  # 1 for primary artist, 0 for featuring
)

# Junction table for many-to-many relationship between tracks and genres
track_genres = Table(
    'track_genres',
    Base.metadata,
    Column('track_id', UUID(), ForeignKey('tracks.track_id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', UUID(), ForeignKey('genres.genre_id', ondelete='CASCADE'), primary_key=True)
)


class Artist(Base):
    """
    Artist model for storing artist information.
    
    Attributes:
        artist_id: Unique identifier for the artist
        name: Artist's display name
        bio: Artist biography/description
        image_url: URL to artist's profile image
        created_at: When the artist was added to the catalog
    """
    __tablename__ = "artists"

    artist_id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    name = Column(
        String(255),
        nullable=False,
        index=True
    )
    bio = Column(
        String(2000),
        nullable=True
    )
    image_url = Column(
        String(500),
        nullable=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", secondary=track_artists, back_populates="artists")

    def __repr__(self):
        return f"<Artist(artist_id={self.artist_id}, name={self.name})>"

    def to_dict(self):
        """Convert artist model to dictionary representation."""
        return {
            "artist_id": str(self.artist_id),
            "name": self.name,
            "bio": self.bio,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Genre(Base):
    """
    Genre model for categorizing tracks.
    
    Attributes:
        genre_id: Unique identifier for the genre
        name: Genre name
        description: Genre description
    """
    __tablename__ = "genres"

    genre_id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    description = Column(
        String(500),
        nullable=True
    )

    tracks = relationship("Track", secondary=track_genres, back_populates="genres")

    def __repr__(self):
        return f"<Genre(genre_id={self.genre_id}, name={self.name})>"

    def to_dict(self):
        """Convert genre model to dictionary representation."""
        return {
            "genre_id": str(self.genre_id),
            "name": self.name,
            "description": self.description
        }


class Album(Base):
    """
    Album model for storing album information.
    
    Attributes:
        album_id: Unique identifier for the album
        title: Album title
        artist_id: Primary artist who created the album
        release_date: When the album was released
        cover_image_url: URL to album cover art
        created_at: When the album was added to the catalog
    """
    __tablename__ = "albums"

    album_id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    title = Column(
        String(255),
        nullable=False,
        index=True
    )
    artist_id = Column(
        UUID(),
        ForeignKey("artists.artist_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    release_date = Column(
        DateTime,
        nullable=True
    )
    cover_image_url = Column(
        String(500),
        nullable=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")

    def __repr__(self):
        return f"<Album(album_id={self.album_id}, title={self.title})>"

    def to_dict(self):
        """Convert album model to dictionary representation."""
        return {
            "album_id": str(self.album_id),
            "title": self.title,
            "artist_id": str(self.artist_id),
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "cover_image_url": self.cover_image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Track(Base):
    """
    Track model for storing track/song information.
    
    This is the central entity referenced by other services via track_id.
    
    Attributes:
        track_id: Unique identifier for the track (referenced by other services)
        title: Track title
        album_id: Album this track belongs to
        duration_ms: Track duration in milliseconds
        track_number: Position in the album
        audio_url: CDN URL for the audio file
        created_at: When the track was added to the catalog
    """
    __tablename__ = "tracks"

    track_id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    title = Column(
        String(255),
        nullable=False,
        index=True
    )
    album_id = Column(
        UUID(),
        ForeignKey("albums.album_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    duration_ms = Column(
        Integer,
        nullable=True
    )
    track_number = Column(
        Integer,
        nullable=True
    )
    audio_url = Column(
        String(500),
        nullable=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    album = relationship("Album", back_populates="tracks")
    artists = relationship("Artist", secondary=track_artists, back_populates="tracks")
    genres = relationship("Genre", secondary=track_genres, back_populates="tracks")

    __table_args__ = (
        Index('idx_track_album_number', 'album_id', 'track_number'),
    )

    def __repr__(self):
        return f"<Track(track_id={self.track_id}, title={self.title})>"

    def to_dict(self):
        """Convert track model to dictionary representation."""
        return {
            "track_id": str(self.track_id),
            "title": self.title,
            "album_id": str(self.album_id) if self.album_id else None,
            "duration_ms": self.duration_ms,
            "track_number": self.track_number,
            "audio_url": self.audio_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
