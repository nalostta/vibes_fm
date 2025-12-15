"""
Library & Playlist Service Data Models

This service manages the user's saved content (UserLibrary) and custom lists (Playlist).
"""
import os
import sys
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Add project root to path for shared imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base


class Playlist(Base):
    """
    Playlist model for storing user-created playlists.
    
    Attributes:
        playlist_id: Unique identifier for the playlist
        owner_user_id: The user who created the playlist
        name: Name of the playlist
        is_private: Visibility flag (default: True for MVP)
        created_at: When the playlist was created
    """
    __tablename__ = "playlists"

    playlist_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    owner_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(
        String(255),
        nullable=False
    )
    is_private = Column(
        Boolean,
        default=True,
        nullable=False
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Playlist(playlist_id={self.playlist_id}, name={self.name}, owner={self.owner_user_id})>"

    def to_dict(self):
        """Convert playlist model to dictionary representation."""
        return {
            "playlist_id": str(self.playlist_id),
            "owner_user_id": str(self.owner_user_id),
            "name": self.name,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PlaylistTrack(Base):
    """
    Junction table for playlist-track relationships with ordering support.
    
    Attributes:
        playlist_track_id: Auto-incrementing ID for track ordering
        playlist_id: The specific playlist
        track_id: The track added to the playlist (references Catalog.Track)
        added_at: When the track was added
        position: The track's order within the playlist
    """
    __tablename__ = "playlist_tracks"

    playlist_track_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    playlist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("playlists.playlist_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracks.track_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    added_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    position = Column(
        Integer,
        nullable=False,
        index=True
    )

    playlist = relationship("Playlist", back_populates="tracks")

    __table_args__ = (
        Index('idx_playlist_track_position', 'playlist_id', 'position'),
    )

    def __repr__(self):
        return f"<PlaylistTrack(playlist_id={self.playlist_id}, track_id={self.track_id}, position={self.position})>"

    def to_dict(self):
        """Convert playlist track model to dictionary representation."""
        return {
            "playlist_track_id": self.playlist_track_id,
            "playlist_id": str(self.playlist_id),
            "track_id": str(self.track_id),
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "position": self.position
        }


class UserLibrary(Base):
    """
    User Library model for storing user's saved/liked tracks.
    
    Uses composite primary key of (user_id, track_id) to prevent duplicates.
    
    Attributes:
        user_id: The user's ID
        track_id: The track the user saved (references Catalog.Track)
        saved_at: When the user saved the track
    """
    __tablename__ = "user_library"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracks.track_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    saved_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<UserLibrary(user_id={self.user_id}, track_id={self.track_id})>"

    def to_dict(self):
        """Convert user library model to dictionary representation."""
        return {
            "user_id": str(self.user_id),
            "track_id": str(self.track_id),
            "saved_at": self.saved_at.isoformat() if self.saved_at else None
        }
