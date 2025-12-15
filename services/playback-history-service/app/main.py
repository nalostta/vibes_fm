"""
Playback History Service - FastAPI Application

Handles recording and retrieving user playback history.
This service:
- Records playback events (high-volume writes)
- Retrieves user's listening history
- Provides listening statistics
"""
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID as PyUUID

from fastapi import FastAPI, HTTPException, Depends, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.auth.security import decode_access_token
from shared.database import SessionLocal

import importlib.util
_models_path = os.path.join(os.path.dirname(__file__), "models", "playback_history.py")
_models_spec = importlib.util.spec_from_file_location("playback_history_models", _models_path)
_models_module = importlib.util.module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models_module)
PlaybackHistory = _models_module.PlaybackHistory

_schemas_path = os.path.join(os.path.dirname(__file__), "schemas.py")
_schemas_spec = importlib.util.spec_from_file_location("history_schemas", _schemas_path)
_schemas_module = importlib.util.module_from_spec(_schemas_spec)
_schemas_spec.loader.exec_module(_schemas_module)
PlaybackEventCreate = _schemas_module.PlaybackEventCreate
PlaybackEventResponse = _schemas_module.PlaybackEventResponse
PlaybackHistoryResponse = _schemas_module.PlaybackHistoryResponse
PlaybackStatsResponse = _schemas_module.PlaybackStatsResponse
TrackPlayCount = _schemas_module.TrackPlayCount
ErrorResponse = _schemas_module.ErrorResponse

app = FastAPI(
    title="Playback History Service",
    description="User playback history recording and retrieval service",
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
    return {"status": "healthy", "service": "playback-history-service"}


@app.post(
    "/history",
    response_model=PlaybackEventResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}}
)
def record_playback(
    event: PlaybackEventCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a playback event."""
    try:
        tid = PyUUID(event.track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    listened_at = datetime.fromisoformat(event.listened_at) if event.listened_at else datetime.utcnow()
    
    history_entry = PlaybackHistory(
        user_id=uid,
        track_id=tid,
        listened_at=listened_at,
        play_duration_ms=event.play_duration_ms,
        source=event.source
    )
    
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    
    return PlaybackEventResponse(
        history_id=history_entry.history_id,
        user_id=str(history_entry.user_id),
        track_id=str(history_entry.track_id),
        listened_at=history_entry.listened_at.isoformat(),
        play_duration_ms=history_entry.play_duration_ms,
        source=history_entry.source
    )


@app.get(
    "/history",
    response_model=PlaybackHistoryResponse,
    responses={401: {"model": ErrorResponse}}
)
def get_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    track_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get user's playback history with optional filters."""
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    query = db.query(PlaybackHistory).filter(PlaybackHistory.user_id == uid)
    
    if track_id:
        try:
            tid = PyUUID(track_id)
            query = query.filter(PlaybackHistory.track_id == tid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid track ID format"
            )
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(PlaybackHistory.listened_at >= start)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format"
            )
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(PlaybackHistory.listened_at <= end)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format"
            )
    
    total = query.count()
    
    entries = query.order_by(desc(PlaybackHistory.listened_at)).offset(skip).limit(limit).all()
    
    items = [
        PlaybackEventResponse(
            history_id=e.history_id,
            user_id=str(e.user_id),
            track_id=str(e.track_id),
            listened_at=e.listened_at.isoformat(),
            play_duration_ms=e.play_duration_ms,
            source=e.source
        )
        for e in entries
    ]
    
    return PlaybackHistoryResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@app.get(
    "/history/stats",
    response_model=PlaybackStatsResponse,
    responses={401: {"model": ErrorResponse}}
)
def get_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get user's listening statistics."""
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    base_query = db.query(PlaybackHistory).filter(
        PlaybackHistory.user_id == uid,
        PlaybackHistory.listened_at >= start_date
    )
    
    total_plays = base_query.count()
    
    total_duration_result = base_query.with_entities(
        func.sum(PlaybackHistory.play_duration_ms)
    ).scalar()
    total_duration_ms = total_duration_result or 0
    
    unique_tracks = base_query.with_entities(
        func.count(func.distinct(PlaybackHistory.track_id))
    ).scalar() or 0
    
    top_tracks_query = db.query(
        PlaybackHistory.track_id,
        func.count(PlaybackHistory.history_id).label('play_count')
    ).filter(
        PlaybackHistory.user_id == uid,
        PlaybackHistory.listened_at >= start_date
    ).group_by(
        PlaybackHistory.track_id
    ).order_by(
        desc('play_count')
    ).limit(10).all()
    
    top_tracks = [
        TrackPlayCount(
            track_id=str(t.track_id),
            play_count=t.play_count
        )
        for t in top_tracks_query
    ]
    
    return PlaybackStatsResponse(
        total_plays=total_plays,
        total_duration_ms=total_duration_ms,
        unique_tracks=unique_tracks,
        top_tracks=top_tracks,
        period_days=days
    )


@app.get(
    "/history/{history_id}",
    response_model=PlaybackEventResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def get_history_entry(
    history_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific playback history entry."""
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    entry = db.query(PlaybackHistory).filter(
        PlaybackHistory.history_id == history_id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History entry not found"
        )
    
    if entry.user_id != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this entry"
        )
    
    return PlaybackEventResponse(
        history_id=entry.history_id,
        user_id=str(entry.user_id),
        track_id=str(entry.track_id),
        listened_at=entry.listened_at.isoformat(),
        play_duration_ms=entry.play_duration_ms,
        source=entry.source
    )


@app.delete(
    "/history/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def delete_history_entry(
    history_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific playback history entry."""
    user_id = current_user.get("sub")
    uid = PyUUID(user_id)
    
    entry = db.query(PlaybackHistory).filter(
        PlaybackHistory.history_id == history_id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History entry not found"
        )
    
    if entry.user_id != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this entry"
        )
    
    db.delete(entry)
    db.commit()
    
    return None
