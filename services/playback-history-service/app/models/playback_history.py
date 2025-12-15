"""
Playback History Service Data Model

This service needs a schema optimized for high-volume insertion,
as every listening event generates a new record.
"""
import os
import sys
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index

# Add project root to path for shared imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base, UUID


class PlaybackHistory(Base):
    """
    Playback History model for storing user listening events.
    
    Optimized for high-volume writes with time-series indexing.
    
    Attributes:
        history_id: Auto-incrementing ID for high-volume logs
        user_id: The ID of the user who listened
        track_id: The ID of the track that was played (references Catalog.Track)
        listened_at: The exact time the event occurred
        play_duration_ms: How many milliseconds the user listened
        source: Context of playback (e.g., 'album', 'playlist', 'radio')
    """
    __tablename__ = "playback_history"

    history_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id = Column(
        UUID(),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    track_id = Column(
        UUID(),
        ForeignKey("tracks.track_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    listened_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    play_duration_ms = Column(
        Integer,
        nullable=True
    )
    source = Column(
        String(50),
        nullable=True
    )

    __table_args__ = (
        Index('idx_playback_history_user_listened', 'user_id', 'listened_at'),
        Index('idx_playback_history_track_listened', 'track_id', 'listened_at'),
    )

    def __repr__(self):
        return f"<PlaybackHistory(history_id={self.history_id}, user_id={self.user_id}, track_id={self.track_id})>"

    def to_dict(self):
        """Convert playback history model to dictionary representation."""
        return {
            "history_id": self.history_id,
            "user_id": str(self.user_id),
            "track_id": str(self.track_id),
            "listened_at": self.listened_at.isoformat() if self.listened_at else None,
            "play_duration_ms": self.play_duration_ms,
            "source": self.source
        }
