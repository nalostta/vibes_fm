"""
Library & Playlist Service - Pydantic Schemas

Request and response models for the Library & Playlist Service API.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class PlaylistCreate(BaseModel):
    """Schema for creating a new playlist."""
    name: str = Field(..., min_length=1, max_length=255)
    is_private: bool = Field(default=True)


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_private: Optional[bool] = None


class PlaylistResponse(BaseModel):
    """Schema for playlist response."""
    playlist_id: str
    owner_user_id: str
    name: str
    is_private: bool
    created_at: str
    track_count: int = 0


class PlaylistTrackAdd(BaseModel):
    """Schema for adding a track to a playlist."""
    track_id: str
    position: Optional[int] = None


class PlaylistTrackResponse(BaseModel):
    """Schema for playlist track response."""
    playlist_track_id: int
    playlist_id: str
    track_id: str
    added_at: str
    position: int


class PlaylistWithTracksResponse(BaseModel):
    """Schema for playlist with tracks response."""
    playlist_id: str
    owner_user_id: str
    name: str
    is_private: bool
    created_at: str
    tracks: List[PlaylistTrackResponse] = []


class LibraryTrackAdd(BaseModel):
    """Schema for adding a track to user library."""
    track_id: str


class LibraryTrackResponse(BaseModel):
    """Schema for library track response."""
    user_id: str
    track_id: str
    saved_at: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
