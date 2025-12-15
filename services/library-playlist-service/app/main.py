"""
Library & Playlist Service - FastAPI Application

Handles user library management and playlist CRUD operations.
This service:
- Manages user's saved/liked tracks (library)
- Creates and manages playlists
- Adds/removes tracks from playlists
"""
import os
import sys
import uuid
from datetime import datetime
from typing import Optional, List
from uuid import UUID as PyUUID

from fastapi import FastAPI, HTTPException, Depends, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.auth.security import decode_access_token
from shared.database import SessionLocal

import importlib.util
_models_path = os.path.join(os.path.dirname(__file__), "models", "playlist.py")
_models_spec = importlib.util.spec_from_file_location("playlist_models", _models_path)
_models_module = importlib.util.module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models_module)
Playlist = _models_module.Playlist
PlaylistTrack = _models_module.PlaylistTrack
UserLibrary = _models_module.UserLibrary

_schemas_path = os.path.join(os.path.dirname(__file__), "schemas.py")
_schemas_spec = importlib.util.spec_from_file_location("library_schemas", _schemas_path)
_schemas_module = importlib.util.module_from_spec(_schemas_spec)
_schemas_spec.loader.exec_module(_schemas_module)
PlaylistCreate = _schemas_module.PlaylistCreate
PlaylistUpdate = _schemas_module.PlaylistUpdate
PlaylistResponse = _schemas_module.PlaylistResponse
PlaylistWithTracksResponse = _schemas_module.PlaylistWithTracksResponse
PlaylistTrackAdd = _schemas_module.PlaylistTrackAdd
PlaylistTrackResponse = _schemas_module.PlaylistTrackResponse
LibraryTrackAdd = _schemas_module.LibraryTrackAdd
LibraryTrackResponse = _schemas_module.LibraryTrackResponse
ErrorResponse = _schemas_module.ErrorResponse

app = FastAPI(
    title="Library & Playlist Service",
    description="User library and playlist management service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Validate JWT token and return current user."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = authorization[7:]
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "library-playlist-service"}


@app.post(
    "/playlists",
    response_model=PlaylistResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}}
)
def create_playlist(
    playlist: PlaylistCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new playlist."""
    user_id = current_user.get("sub")
    
    db_playlist = Playlist(
        playlist_id=uuid.uuid4(),
        owner_user_id=PyUUID(user_id),
        name=playlist.name,
        is_private=playlist.is_private
    )
    
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    
    return PlaylistResponse(
        playlist_id=str(db_playlist.playlist_id),
        owner_user_id=str(db_playlist.owner_user_id),
        name=db_playlist.name,
        is_private=db_playlist.is_private,
        created_at=db_playlist.created_at.isoformat(),
        track_count=0
    )


@app.get(
    "/playlists",
    response_model=List[PlaylistResponse],
    responses={401: {"model": ErrorResponse}}
)
def list_playlists(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List user's playlists."""
    user_id = current_user.get("sub")
    
    playlists = db.query(Playlist).filter(
        Playlist.owner_user_id == PyUUID(user_id)
    ).offset(skip).limit(limit).all()
    
    result = []
    for p in playlists:
        track_count = db.query(func.count(PlaylistTrack.playlist_track_id)).filter(
            PlaylistTrack.playlist_id == p.playlist_id
        ).scalar()
        
        result.append(PlaylistResponse(
            playlist_id=str(p.playlist_id),
            owner_user_id=str(p.owner_user_id),
            name=p.name,
            is_private=p.is_private,
            created_at=p.created_at.isoformat(),
            track_count=track_count
        ))
    
    return result


@app.get(
    "/playlists/{playlist_id}",
    response_model=PlaylistWithTracksResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def get_playlist(
    playlist_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get playlist with tracks."""
    try:
        pid = PyUUID(playlist_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid playlist ID format"
        )
    
    user_id = current_user.get("sub")
    
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if playlist.is_private and str(playlist.owner_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this playlist"
        )
    
    tracks = db.query(PlaylistTrack).filter(
        PlaylistTrack.playlist_id == pid
    ).order_by(PlaylistTrack.position).all()
    
    track_responses = [
        PlaylistTrackResponse(
            playlist_track_id=t.playlist_track_id,
            playlist_id=str(t.playlist_id),
            track_id=str(t.track_id),
            added_at=t.added_at.isoformat(),
            position=t.position
        )
        for t in tracks
    ]
    
    return PlaylistWithTracksResponse(
        playlist_id=str(playlist.playlist_id),
        owner_user_id=str(playlist.owner_user_id),
        name=playlist.name,
        is_private=playlist.is_private,
        created_at=playlist.created_at.isoformat(),
        tracks=track_responses
    )


@app.put(
    "/playlists/{playlist_id}",
    response_model=PlaylistResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def update_playlist(
    playlist_id: str,
    playlist_update: PlaylistUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a playlist."""
    try:
        pid = PyUUID(playlist_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid playlist ID format"
        )
    
    user_id = current_user.get("sub")
    
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this playlist"
        )
    
    if playlist_update.name is not None:
        playlist.name = playlist_update.name
    if playlist_update.is_private is not None:
        playlist.is_private = playlist_update.is_private
    
    db.commit()
    db.refresh(playlist)
    
    track_count = db.query(func.count(PlaylistTrack.playlist_track_id)).filter(
        PlaylistTrack.playlist_id == pid
    ).scalar()
    
    return PlaylistResponse(
        playlist_id=str(playlist.playlist_id),
        owner_user_id=str(playlist.owner_user_id),
        name=playlist.name,
        is_private=playlist.is_private,
        created_at=playlist.created_at.isoformat(),
        track_count=track_count
    )


@app.delete(
    "/playlists/{playlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def delete_playlist(
    playlist_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a playlist."""
    try:
        pid = PyUUID(playlist_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid playlist ID format"
        )
    
    user_id = current_user.get("sub")
    
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this playlist"
        )
    
    db.delete(playlist)
    db.commit()
    
    return None


@app.post(
    "/playlists/{playlist_id}/tracks",
    response_model=PlaylistTrackResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}}
)
def add_track_to_playlist(
    playlist_id: str,
    track_data: PlaylistTrackAdd,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a track to a playlist."""
    try:
        pid = PyUUID(playlist_id)
        tid = PyUUID(track_data.track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    user_id = current_user.get("sub")
    
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this playlist"
        )
    
    existing = db.query(PlaylistTrack).filter(
        PlaylistTrack.playlist_id == pid,
        PlaylistTrack.track_id == tid
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Track already in playlist"
        )
    
    max_position = db.query(func.max(PlaylistTrack.position)).filter(
        PlaylistTrack.playlist_id == pid
    ).scalar() or 0
    
    position = track_data.position if track_data.position is not None else max_position + 1
    
    playlist_track = PlaylistTrack(
        playlist_id=pid,
        track_id=tid,
        position=position
    )
    
    db.add(playlist_track)
    db.commit()
    db.refresh(playlist_track)
    
    return PlaylistTrackResponse(
        playlist_track_id=playlist_track.playlist_track_id,
        playlist_id=str(playlist_track.playlist_id),
        track_id=str(playlist_track.track_id),
        added_at=playlist_track.added_at.isoformat(),
        position=playlist_track.position
    )


@app.delete(
    "/playlists/{playlist_id}/tracks/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def remove_track_from_playlist(
    playlist_id: str,
    track_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a track from a playlist."""
    try:
        pid = PyUUID(playlist_id)
        tid = PyUUID(track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    user_id = current_user.get("sub")
    
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this playlist"
        )
    
    playlist_track = db.query(PlaylistTrack).filter(
        PlaylistTrack.playlist_id == pid,
        PlaylistTrack.track_id == tid
    ).first()
    
    if not playlist_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not in playlist"
        )
    
    db.delete(playlist_track)
    db.commit()
    
    return None


@app.post(
    "/library/tracks",
    response_model=LibraryTrackResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 409: {"model": ErrorResponse}}
)
def add_track_to_library(
    track_data: LibraryTrackAdd,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a track to user's library."""
    try:
        tid = PyUUID(track_data.track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    existing = db.query(UserLibrary).filter(
        UserLibrary.user_id == uid,
        UserLibrary.track_id == tid
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Track already in library"
        )
    
    library_entry = UserLibrary(
        user_id=uid,
        track_id=tid
    )
    
    db.add(library_entry)
    db.commit()
    db.refresh(library_entry)
    
    return LibraryTrackResponse(
        user_id=str(library_entry.user_id),
        track_id=str(library_entry.track_id),
        saved_at=library_entry.saved_at.isoformat()
    )


@app.get(
    "/library/tracks",
    response_model=List[LibraryTrackResponse],
    responses={401: {"model": ErrorResponse}}
)
def get_library_tracks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's library tracks."""
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    tracks = db.query(UserLibrary).filter(
        UserLibrary.user_id == uid
    ).order_by(UserLibrary.saved_at.desc()).offset(skip).limit(limit).all()
    
    return [
        LibraryTrackResponse(
            user_id=str(t.user_id),
            track_id=str(t.track_id),
            saved_at=t.saved_at.isoformat()
        )
        for t in tracks
    ]


@app.delete(
    "/library/tracks/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def remove_track_from_library(
    track_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a track from user's library."""
    try:
        tid = PyUUID(track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    library_entry = db.query(UserLibrary).filter(
        UserLibrary.user_id == uid,
        UserLibrary.track_id == tid
    ).first()
    
    if not library_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not in library"
        )
    
    db.delete(library_entry)
    db.commit()
    
    return None
