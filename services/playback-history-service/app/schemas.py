"""
Playback History Service - Pydantic Schemas

Request and response models for the Playback History Service API.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class PlaybackEventCreate(BaseModel):
    """Schema for creating a playback event."""
    track_id: str
    listened_at: Optional[str] = None
    play_duration_ms: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=50)


class PlaybackEventResponse(BaseModel):
    """Schema for playback event response."""
    history_id: int
    user_id: str
    track_id: str
    listened_at: str
    play_duration_ms: Optional[int] = None
    source: Optional[str] = None


class PlaybackHistoryResponse(BaseModel):
    """Schema for paginated playback history response."""
    items: List[PlaybackEventResponse]
    total: int
    skip: int
    limit: int


class TrackPlayCount(BaseModel):
    """Schema for track play count in stats."""
    track_id: str
    play_count: int


class PlaybackStatsResponse(BaseModel):
    """Schema for playback statistics response."""
    total_plays: int
    total_duration_ms: int
    unique_tracks: int
    top_tracks: List[TrackPlayCount]
    period_days: int


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
