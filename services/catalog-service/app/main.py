"""
Catalog Service - FastAPI Application

Handles metadata management for:
- Artists
- Albums
- Tracks
- Genres
- Search functionality
"""
import os
import sys
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Add project root to path for shared imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.database import Base, engine, get_db

# Import models - use dynamic import to handle both package and direct execution
import importlib.util
_models_path = os.path.join(os.path.dirname(__file__), "models", "catalog.py")
_models_spec = importlib.util.spec_from_file_location("catalog_models", _models_path)
_models_module = importlib.util.module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models_module)
Artist = _models_module.Artist
Album = _models_module.Album
Track = _models_module.Track
Genre = _models_module.Genre
track_artists = _models_module.track_artists
track_genres = _models_module.track_genres

# Import schemas
_schemas_path = os.path.join(os.path.dirname(__file__), "schemas.py")
_schemas_spec = importlib.util.spec_from_file_location("catalog_schemas", _schemas_path)
_schemas_module = importlib.util.module_from_spec(_schemas_spec)
_schemas_spec.loader.exec_module(_schemas_module)
ArtistCreateRequest = _schemas_module.ArtistCreateRequest
ArtistUpdateRequest = _schemas_module.ArtistUpdateRequest
ArtistResponse = _schemas_module.ArtistResponse
GenreCreateRequest = _schemas_module.GenreCreateRequest
GenreUpdateRequest = _schemas_module.GenreUpdateRequest
GenreResponse = _schemas_module.GenreResponse
AlbumCreateRequest = _schemas_module.AlbumCreateRequest
AlbumUpdateRequest = _schemas_module.AlbumUpdateRequest
AlbumResponse = _schemas_module.AlbumResponse
AlbumWithTracksResponse = _schemas_module.AlbumWithTracksResponse
TrackCreateRequest = _schemas_module.TrackCreateRequest
TrackUpdateRequest = _schemas_module.TrackUpdateRequest
TrackResponse = _schemas_module.TrackResponse
SearchResponse = _schemas_module.SearchResponse
ErrorResponse = _schemas_module.ErrorResponse

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Catalog Service",
    description="Metadata management service for artists, albums, tracks, and genres",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def artist_to_response(artist: Artist) -> ArtistResponse:
    """Convert Artist model to ArtistResponse."""
    return ArtistResponse(
        artist_id=str(artist.artist_id),
        name=artist.name,
        bio=artist.bio,
        image_url=artist.image_url,
        created_at=artist.created_at.isoformat() if artist.created_at else None
    )


def genre_to_response(genre: Genre) -> GenreResponse:
    """Convert Genre model to GenreResponse."""
    return GenreResponse(
        genre_id=str(genre.genre_id),
        name=genre.name,
        description=genre.description
    )


def album_to_response(album: Album, include_artist: bool = False) -> AlbumResponse:
    """Convert Album model to AlbumResponse."""
    return AlbumResponse(
        album_id=str(album.album_id),
        title=album.title,
        artist_id=str(album.artist_id),
        release_date=album.release_date.isoformat() if album.release_date else None,
        cover_image_url=album.cover_image_url,
        created_at=album.created_at.isoformat() if album.created_at else None,
        artist=artist_to_response(album.artist) if include_artist and album.artist else None
    )


def track_to_response(track: Track, include_relations: bool = False) -> TrackResponse:
    """Convert Track model to TrackResponse."""
    return TrackResponse(
        track_id=str(track.track_id),
        title=track.title,
        album_id=str(track.album_id) if track.album_id else None,
        duration_ms=track.duration_ms,
        track_number=track.track_number,
        audio_url=track.audio_url,
        created_at=track.created_at.isoformat() if track.created_at else None,
        album=album_to_response(track.album, include_artist=True) if include_relations and track.album else None,
        artists=[artist_to_response(a) for a in track.artists] if include_relations else None,
        genres=[genre_to_response(g) for g in track.genres] if include_relations else None
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "catalog-service"}


# ==================== Artist Endpoints ====================

@app.post(
    "/artists",
    response_model=ArtistResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}}
)
def create_artist(request: ArtistCreateRequest, db: Session = Depends(get_db)):
    """Create a new artist."""
    artist = Artist(
        name=request.name,
        bio=request.bio,
        image_url=request.image_url
    )
    db.add(artist)
    db.commit()
    db.refresh(artist)
    return artist_to_response(artist)


@app.get("/artists", response_model=List[ArtistResponse])
def list_artists(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all artists with pagination."""
    offset = (page - 1) * page_size
    artists = db.query(Artist).offset(offset).limit(page_size).all()
    return [artist_to_response(a) for a in artists]


@app.get(
    "/artists/{artist_id}",
    response_model=ArtistResponse,
    responses={404: {"model": ErrorResponse}}
)
def get_artist(artist_id: str, db: Session = Depends(get_db)):
    """Get an artist by ID."""
    try:
        uuid_id = UUID(artist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artist ID format")
    
    artist = db.query(Artist).filter(Artist.artist_id == uuid_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist_to_response(artist)


@app.put(
    "/artists/{artist_id}",
    response_model=ArtistResponse,
    responses={404: {"model": ErrorResponse}}
)
def update_artist(artist_id: str, request: ArtistUpdateRequest, db: Session = Depends(get_db)):
    """Update an artist."""
    try:
        uuid_id = UUID(artist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artist ID format")
    
    artist = db.query(Artist).filter(Artist.artist_id == uuid_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    if request.name is not None:
        artist.name = request.name
    if request.bio is not None:
        artist.bio = request.bio
    if request.image_url is not None:
        artist.image_url = request.image_url
    
    db.commit()
    db.refresh(artist)
    return artist_to_response(artist)


@app.delete(
    "/artists/{artist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}}
)
def delete_artist(artist_id: str, db: Session = Depends(get_db)):
    """Delete an artist."""
    try:
        uuid_id = UUID(artist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artist ID format")
    
    artist = db.query(Artist).filter(Artist.artist_id == uuid_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    db.delete(artist)
    db.commit()
    return None


# ==================== Genre Endpoints ====================

@app.post(
    "/genres",
    response_model=GenreResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}}
)
def create_genre(request: GenreCreateRequest, db: Session = Depends(get_db)):
    """Create a new genre."""
    existing = db.query(Genre).filter(Genre.name == request.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Genre with this name already exists")
    
    genre = Genre(
        name=request.name,
        description=request.description
    )
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre_to_response(genre)


@app.get("/genres", response_model=List[GenreResponse])
def list_genres(db: Session = Depends(get_db)):
    """List all genres."""
    genres = db.query(Genre).all()
    return [genre_to_response(g) for g in genres]


@app.get(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    responses={404: {"model": ErrorResponse}}
)
def get_genre(genre_id: str, db: Session = Depends(get_db)):
    """Get a genre by ID."""
    try:
        uuid_id = UUID(genre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid genre ID format")
    
    genre = db.query(Genre).filter(Genre.genre_id == uuid_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre_to_response(genre)


@app.put(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}}
)
def update_genre(genre_id: str, request: GenreUpdateRequest, db: Session = Depends(get_db)):
    """Update a genre."""
    try:
        uuid_id = UUID(genre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid genre ID format")
    
    genre = db.query(Genre).filter(Genre.genre_id == uuid_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    if request.name is not None:
        existing = db.query(Genre).filter(Genre.name == request.name, Genre.genre_id != uuid_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Genre with this name already exists")
        genre.name = request.name
    if request.description is not None:
        genre.description = request.description
    
    db.commit()
    db.refresh(genre)
    return genre_to_response(genre)


@app.delete(
    "/genres/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}}
)
def delete_genre(genre_id: str, db: Session = Depends(get_db)):
    """Delete a genre."""
    try:
        uuid_id = UUID(genre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid genre ID format")
    
    genre = db.query(Genre).filter(Genre.genre_id == uuid_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    db.delete(genre)
    db.commit()
    return None


# ==================== Album Endpoints ====================

@app.post(
    "/albums",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def create_album(request: AlbumCreateRequest, db: Session = Depends(get_db)):
    """Create a new album."""
    try:
        artist_uuid = UUID(request.artist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artist ID format")
    
    artist = db.query(Artist).filter(Artist.artist_id == artist_uuid).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    album = Album(
        title=request.title,
        artist_id=artist_uuid,
        release_date=request.release_date,
        cover_image_url=request.cover_image_url
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return album_to_response(album, include_artist=True)


@app.get("/albums", response_model=List[AlbumResponse])
def list_albums(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    artist_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all albums with pagination, optionally filtered by artist."""
    query = db.query(Album)
    
    if artist_id:
        try:
            artist_uuid = UUID(artist_id)
            query = query.filter(Album.artist_id == artist_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid artist ID format")
    
    offset = (page - 1) * page_size
    albums = query.offset(offset).limit(page_size).all()
    return [album_to_response(a, include_artist=True) for a in albums]


@app.get(
    "/albums/{album_id}",
    response_model=AlbumWithTracksResponse,
    responses={404: {"model": ErrorResponse}}
)
def get_album(album_id: str, db: Session = Depends(get_db)):
    """Get an album by ID with all its tracks."""
    try:
        uuid_id = UUID(album_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid album ID format")
    
    album = db.query(Album).filter(Album.album_id == uuid_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    return AlbumWithTracksResponse(
        album_id=str(album.album_id),
        title=album.title,
        artist_id=str(album.artist_id),
        release_date=album.release_date.isoformat() if album.release_date else None,
        cover_image_url=album.cover_image_url,
        created_at=album.created_at.isoformat() if album.created_at else None,
        artist=artist_to_response(album.artist) if album.artist else None,
        tracks=[track_to_response(t) for t in sorted(album.tracks, key=lambda x: x.track_number or 0)]
    )


@app.put(
    "/albums/{album_id}",
    response_model=AlbumResponse,
    responses={404: {"model": ErrorResponse}}
)
def update_album(album_id: str, request: AlbumUpdateRequest, db: Session = Depends(get_db)):
    """Update an album."""
    try:
        uuid_id = UUID(album_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid album ID format")
    
    album = db.query(Album).filter(Album.album_id == uuid_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if request.title is not None:
        album.title = request.title
    if request.artist_id is not None:
        try:
            artist_uuid = UUID(request.artist_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid artist ID format")
        artist = db.query(Artist).filter(Artist.artist_id == artist_uuid).first()
        if not artist:
            raise HTTPException(status_code=404, detail="Artist not found")
        album.artist_id = artist_uuid
    if request.release_date is not None:
        album.release_date = request.release_date
    if request.cover_image_url is not None:
        album.cover_image_url = request.cover_image_url
    
    db.commit()
    db.refresh(album)
    return album_to_response(album, include_artist=True)


@app.delete(
    "/albums/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}}
)
def delete_album(album_id: str, db: Session = Depends(get_db)):
    """Delete an album."""
    try:
        uuid_id = UUID(album_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid album ID format")
    
    album = db.query(Album).filter(Album.album_id == uuid_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    db.delete(album)
    db.commit()
    return None


# ==================== Track Endpoints ====================

@app.post(
    "/tracks",
    response_model=TrackResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def create_track(request: TrackCreateRequest, db: Session = Depends(get_db)):
    """Create a new track."""
    album_uuid = None
    if request.album_id:
        try:
            album_uuid = UUID(request.album_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid album ID format")
        album = db.query(Album).filter(Album.album_id == album_uuid).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")
    
    track = Track(
        title=request.title,
        album_id=album_uuid,
        duration_ms=request.duration_ms,
        track_number=request.track_number,
        audio_url=request.audio_url
    )
    
    # Add artists if provided
    if request.artist_ids:
        for artist_id in request.artist_ids:
            try:
                artist_uuid = UUID(artist_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid artist ID format: {artist_id}")
            artist = db.query(Artist).filter(Artist.artist_id == artist_uuid).first()
            if not artist:
                raise HTTPException(status_code=404, detail=f"Artist not found: {artist_id}")
            track.artists.append(artist)
    
    # Add genres if provided
    if request.genre_ids:
        for genre_id in request.genre_ids:
            try:
                genre_uuid = UUID(genre_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid genre ID format: {genre_id}")
            genre = db.query(Genre).filter(Genre.genre_id == genre_uuid).first()
            if not genre:
                raise HTTPException(status_code=404, detail=f"Genre not found: {genre_id}")
            track.genres.append(genre)
    
    db.add(track)
    db.commit()
    db.refresh(track)
    return track_to_response(track, include_relations=True)


@app.get("/tracks", response_model=List[TrackResponse])
def list_tracks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    album_id: Optional[str] = None,
    artist_id: Optional[str] = None,
    genre_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all tracks with pagination and optional filters."""
    query = db.query(Track)
    
    if album_id:
        try:
            album_uuid = UUID(album_id)
            query = query.filter(Track.album_id == album_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid album ID format")
    
    if artist_id:
        try:
            artist_uuid = UUID(artist_id)
            query = query.join(Track.artists).filter(Artist.artist_id == artist_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid artist ID format")
    
    if genre_id:
        try:
            genre_uuid = UUID(genre_id)
            query = query.join(Track.genres).filter(Genre.genre_id == genre_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid genre ID format")
    
    offset = (page - 1) * page_size
    tracks = query.offset(offset).limit(page_size).all()
    return [track_to_response(t, include_relations=True) for t in tracks]


@app.get(
    "/tracks/{track_id}",
    response_model=TrackResponse,
    responses={404: {"model": ErrorResponse}}
)
def get_track(track_id: str, db: Session = Depends(get_db)):
    """Get a track by ID with all relations."""
    try:
        uuid_id = UUID(track_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid track ID format")
    
    track = db.query(Track).filter(Track.track_id == uuid_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track_to_response(track, include_relations=True)


@app.put(
    "/tracks/{track_id}",
    response_model=TrackResponse,
    responses={404: {"model": ErrorResponse}}
)
def update_track(track_id: str, request: TrackUpdateRequest, db: Session = Depends(get_db)):
    """Update a track."""
    try:
        uuid_id = UUID(track_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid track ID format")
    
    track = db.query(Track).filter(Track.track_id == uuid_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if request.title is not None:
        track.title = request.title
    if request.album_id is not None:
        try:
            album_uuid = UUID(request.album_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid album ID format")
        album = db.query(Album).filter(Album.album_id == album_uuid).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")
        track.album_id = album_uuid
    if request.duration_ms is not None:
        track.duration_ms = request.duration_ms
    if request.track_number is not None:
        track.track_number = request.track_number
    if request.audio_url is not None:
        track.audio_url = request.audio_url
    
    db.commit()
    db.refresh(track)
    return track_to_response(track, include_relations=True)


@app.delete(
    "/tracks/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}}
)
def delete_track(track_id: str, db: Session = Depends(get_db)):
    """Delete a track."""
    try:
        uuid_id = UUID(track_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid track ID format")
    
    track = db.query(Track).filter(Track.track_id == uuid_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    db.delete(track)
    db.commit()
    return None


@app.post(
    "/tracks/{track_id}/artists/{artist_id}",
    response_model=TrackResponse,
    responses={404: {"model": ErrorResponse}}
)
def add_artist_to_track(track_id: str, artist_id: str, db: Session = Depends(get_db)):
    """Add an artist to a track."""
    try:
        track_uuid = UUID(track_id)
        artist_uuid = UUID(artist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    track = db.query(Track).filter(Track.track_id == track_uuid).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    artist = db.query(Artist).filter(Artist.artist_id == artist_uuid).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    if artist not in track.artists:
        track.artists.append(artist)
        db.commit()
        db.refresh(track)
    
    return track_to_response(track, include_relations=True)


@app.delete(
    "/tracks/{track_id}/artists/{artist_id}",
    response_model=TrackResponse,
    responses={404: {"model": ErrorResponse}}
)
def remove_artist_from_track(track_id: str, artist_id: str, db: Session = Depends(get_db)):
    """Remove an artist from a track."""
    try:
        track_uuid = UUID(track_id)
        artist_uuid = UUID(artist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    track = db.query(Track).filter(Track.track_id == track_uuid).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    artist = db.query(Artist).filter(Artist.artist_id == artist_uuid).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    if artist in track.artists:
        track.artists.remove(artist)
        db.commit()
        db.refresh(track)
    
    return track_to_response(track, include_relations=True)


@app.post(
    "/tracks/{track_id}/genres/{genre_id}",
    response_model=TrackResponse,
    responses={404: {"model": ErrorResponse}}
)
def add_genre_to_track(track_id: str, genre_id: str, db: Session = Depends(get_db)):
    """Add a genre to a track."""
    try:
        track_uuid = UUID(track_id)
        genre_uuid = UUID(genre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    track = db.query(Track).filter(Track.track_id == track_uuid).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    genre = db.query(Genre).filter(Genre.genre_id == genre_uuid).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    if genre not in track.genres:
        track.genres.append(genre)
        db.commit()
        db.refresh(track)
    
    return track_to_response(track, include_relations=True)


@app.delete(
    "/tracks/{track_id}/genres/{genre_id}",
    response_model=TrackResponse,
    responses={404: {"model": ErrorResponse}}
)
def remove_genre_from_track(track_id: str, genre_id: str, db: Session = Depends(get_db)):
    """Remove a genre from a track."""
    try:
        track_uuid = UUID(track_id)
        genre_uuid = UUID(genre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    track = db.query(Track).filter(Track.track_id == track_uuid).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    genre = db.query(Genre).filter(Genre.genre_id == genre_uuid).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    
    if genre in track.genres:
        track.genres.remove(genre)
        db.commit()
        db.refresh(track)
    
    return track_to_response(track, include_relations=True)


# ==================== Search Endpoint ====================

@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search for tracks, albums, and artists.
    
    Uses database LIKE queries for MVP. Can be replaced with
    Elasticsearch for production-grade search.
    """
    search_term = f"%{q}%"
    
    # Search tracks
    tracks = db.query(Track).filter(
        Track.title.ilike(search_term)
    ).limit(limit).all()
    
    # Search albums
    albums = db.query(Album).filter(
        Album.title.ilike(search_term)
    ).limit(limit).all()
    
    # Search artists
    artists = db.query(Artist).filter(
        or_(
            Artist.name.ilike(search_term),
            Artist.bio.ilike(search_term)
        )
    ).limit(limit).all()
    
    return SearchResponse(
        tracks=[track_to_response(t, include_relations=True) for t in tracks],
        albums=[album_to_response(a, include_artist=True) for a in albums],
        artists=[artist_to_response(a) for a in artists]
    )
