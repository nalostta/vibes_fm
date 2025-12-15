"""
Pydantic schemas for Catalog Service request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ArtistCreateRequest(BaseModel):
    """Schema for creating an artist."""
    name: str = Field(..., min_length=1, max_length=255)
    bio: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)


class ArtistUpdateRequest(BaseModel):
    """Schema for updating an artist."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    bio: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)


class ArtistResponse(BaseModel):
    """Schema for artist response."""
    artist_id: str
    name: str
    bio: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class GenreCreateRequest(BaseModel):
    """Schema for creating a genre."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GenreUpdateRequest(BaseModel):
    """Schema for updating a genre."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GenreResponse(BaseModel):
    """Schema for genre response."""
    genre_id: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class AlbumCreateRequest(BaseModel):
    """Schema for creating an album."""
    title: str = Field(..., min_length=1, max_length=255)
    artist_id: str
    release_date: Optional[datetime] = None
    cover_image_url: Optional[str] = Field(None, max_length=500)


class AlbumUpdateRequest(BaseModel):
    """Schema for updating an album."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    artist_id: Optional[str] = None
    release_date: Optional[datetime] = None
    cover_image_url: Optional[str] = Field(None, max_length=500)


class AlbumResponse(BaseModel):
    """Schema for album response."""
    album_id: str
    title: str
    artist_id: str
    release_date: Optional[str] = None
    cover_image_url: Optional[str] = None
    created_at: Optional[str] = None
    artist: Optional[ArtistResponse] = None

    class Config:
        from_attributes = True


class TrackCreateRequest(BaseModel):
    """Schema for creating a track."""
    title: str = Field(..., min_length=1, max_length=255)
    album_id: Optional[str] = None
    duration_ms: Optional[int] = Field(None, ge=0)
    track_number: Optional[int] = Field(None, ge=1)
    audio_url: Optional[str] = Field(None, max_length=500)
    artist_ids: Optional[List[str]] = None
    genre_ids: Optional[List[str]] = None


class TrackUpdateRequest(BaseModel):
    """Schema for updating a track."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    album_id: Optional[str] = None
    duration_ms: Optional[int] = Field(None, ge=0)
    track_number: Optional[int] = Field(None, ge=1)
    audio_url: Optional[str] = Field(None, max_length=500)


class TrackResponse(BaseModel):
    """Schema for track response."""
    track_id: str
    title: str
    album_id: Optional[str] = None
    duration_ms: Optional[int] = None
    track_number: Optional[int] = None
    audio_url: Optional[str] = None
    created_at: Optional[str] = None
    album: Optional[AlbumResponse] = None
    artists: Optional[List[ArtistResponse]] = None
    genres: Optional[List[GenreResponse]] = None

    class Config:
        from_attributes = True


class AlbumWithTracksResponse(BaseModel):
    """Schema for album with all tracks."""
    album_id: str
    title: str
    artist_id: str
    release_date: Optional[str] = None
    cover_image_url: Optional[str] = None
    created_at: Optional[str] = None
    artist: Optional[ArtistResponse] = None
    tracks: List[TrackResponse] = []

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Schema for search request."""
    query: str = Field(..., min_length=1, max_length=255)
    limit: int = Field(20, ge=1, le=100)


class SearchResponse(BaseModel):
    """Schema for search response."""
    tracks: List[TrackResponse] = []
    albums: List[AlbumResponse] = []
    artists: List[ArtistResponse] = []


class PaginatedResponse(BaseModel):
    """Schema for paginated list responses."""
    items: List
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
