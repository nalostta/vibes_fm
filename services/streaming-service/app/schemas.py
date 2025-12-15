"""
Pydantic schemas for Streaming Service request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StreamRequest(BaseModel):
    """Schema for requesting a stream URL."""
    track_id: str
    quality: Optional[str] = Field("high", pattern="^(low|medium|high)$")


class StreamResponse(BaseModel):
    """Schema for stream URL response."""
    track_id: str
    stream_url: str
    expires_at: str
    quality: str


class PlaybackStartRequest(BaseModel):
    """Schema for notifying playback start."""
    track_id: str
    source: Optional[str] = Field("direct", max_length=50)


class PlaybackStartResponse(BaseModel):
    """Schema for playback start confirmation."""
    track_id: str
    session_id: str
    started_at: str


class PlaybackEndRequest(BaseModel):
    """Schema for notifying playback end."""
    session_id: str
    play_duration_ms: int = Field(..., ge=0)


class PlaybackEndResponse(BaseModel):
    """Schema for playback end confirmation."""
    session_id: str
    recorded: bool


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
