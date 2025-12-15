"""
Playback History Service - Unit Tests

Comprehensive tests for the Playback History Service API endpoints.
Tests cover recording playback events, retrieving history, and statistics.
"""
import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, status, Header, Query
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, Integer, DateTime, func, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pydantic import BaseModel, Field

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

import shared.database as db_module
db_module.engine = test_engine
db_module.SessionLocal = TestSessionLocal

from shared.database import Base, UUID
from shared.auth.security import create_access_token


class PlaybackHistory(Base):
    __tablename__ = "playback_history"
    history_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(), nullable=False, index=True)
    track_id = Column(UUID(), nullable=False, index=True)
    listened_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    play_duration_ms = Column(Integer, nullable=True)
    source = Column(String(50), nullable=True)


class PlaybackEventCreate(BaseModel):
    track_id: str
    listened_at: Optional[str] = None
    play_duration_ms: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=50)


class PlaybackEventResponse(BaseModel):
    history_id: int
    user_id: str
    track_id: str
    listened_at: str
    play_duration_ms: Optional[int] = None
    source: Optional[str] = None


class PlaybackHistoryResponse(BaseModel):
    items: List[PlaybackEventResponse]
    total: int
    skip: int
    limit: int


class TrackPlayCount(BaseModel):
    track_id: str
    play_count: int


class PlaybackStatsResponse(BaseModel):
    total_plays: int
    total_duration_ms: int
    unique_tracks: int
    top_tracks: List[TrackPlayCount]
    period_days: int


class ErrorResponse(BaseModel):
    detail: str


app = FastAPI()


def get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def decode_test_token(token: str) -> Optional[dict]:
    from shared.auth.security import decode_access_token
    return decode_access_token(token)


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header required")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")
    token = authorization[7:]
    payload = decode_test_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "playback-history-service"}


@app.post("/history", response_model=PlaybackEventResponse, status_code=status.HTTP_201_CREATED)
def record_playback(event: PlaybackEventCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tid = uuid.UUID(event.track_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid track ID format")
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    listened_at = datetime.fromisoformat(event.listened_at) if event.listened_at else datetime.utcnow()
    history_entry = PlaybackHistory(user_id=uid, track_id=tid, listened_at=listened_at, play_duration_ms=event.play_duration_ms, source=event.source)
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    return PlaybackEventResponse(history_id=history_entry.history_id, user_id=str(history_entry.user_id), track_id=str(history_entry.track_id), listened_at=history_entry.listened_at.isoformat(), play_duration_ms=history_entry.play_duration_ms, source=history_entry.source)


@app.get("/history", response_model=PlaybackHistoryResponse)
def get_history(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), track_id: Optional[str] = Query(None), start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None)):
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    query = db.query(PlaybackHistory).filter(PlaybackHistory.user_id == uid)
    if track_id:
        try:
            tid = uuid.UUID(track_id)
            query = query.filter(PlaybackHistory.track_id == tid)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid track ID format")
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(PlaybackHistory.listened_at >= start)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid start_date format")
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(PlaybackHistory.listened_at <= end)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid end_date format")
    total = query.count()
    entries = query.order_by(desc(PlaybackHistory.listened_at)).offset(skip).limit(limit).all()
    items = [PlaybackEventResponse(history_id=e.history_id, user_id=str(e.user_id), track_id=str(e.track_id), listened_at=e.listened_at.isoformat(), play_duration_ms=e.play_duration_ms, source=e.source) for e in entries]
    return PlaybackHistoryResponse(items=items, total=total, skip=skip, limit=limit)


@app.get("/history/stats", response_model=PlaybackStatsResponse)
def get_stats(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), days: int = Query(30, ge=1, le=365)):
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    start_date = datetime.utcnow() - timedelta(days=days)
    base_query = db.query(PlaybackHistory).filter(PlaybackHistory.user_id == uid, PlaybackHistory.listened_at >= start_date)
    total_plays = base_query.count()
    total_duration_result = base_query.with_entities(func.sum(PlaybackHistory.play_duration_ms)).scalar()
    total_duration_ms = total_duration_result or 0
    unique_tracks = base_query.with_entities(func.count(func.distinct(PlaybackHistory.track_id))).scalar() or 0
    top_tracks_query = db.query(PlaybackHistory.track_id, func.count(PlaybackHistory.history_id).label('play_count')).filter(PlaybackHistory.user_id == uid, PlaybackHistory.listened_at >= start_date).group_by(PlaybackHistory.track_id).order_by(desc('play_count')).limit(10).all()
    top_tracks = [TrackPlayCount(track_id=str(t.track_id), play_count=t.play_count) for t in top_tracks_query]
    return PlaybackStatsResponse(total_plays=total_plays, total_duration_ms=total_duration_ms, unique_tracks=unique_tracks, top_tracks=top_tracks, period_days=days)


@app.get("/history/{history_id}", response_model=PlaybackEventResponse)
def get_history_entry(history_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    entry = db.query(PlaybackHistory).filter(PlaybackHistory.history_id == history_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History entry not found")
    if entry.user_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this entry")
    return PlaybackEventResponse(history_id=entry.history_id, user_id=str(entry.user_id), track_id=str(entry.track_id), listened_at=entry.listened_at.isoformat(), play_duration_ms=entry.play_duration_ms, source=entry.source)


@app.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_entry(history_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    entry = db.query(PlaybackHistory).filter(PlaybackHistory.history_id == history_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History entry not found")
    if entry.user_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this entry")
    db.delete(entry)
    db.commit()
    return None


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


TEST_USER_ID = str(uuid.uuid4())
TEST_USER_ID_2 = str(uuid.uuid4())


def get_auth_header(user_id: str = TEST_USER_ID) -> dict:
    token = create_access_token({"sub": user_id, "email": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


class TestHealth:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "playback-history-service"


class TestRecordPlayback:
    def test_record_playback(self):
        track_id = str(uuid.uuid4())
        response = client.post("/history", json={"track_id": track_id}, headers=get_auth_header())
        assert response.status_code == 201
        data = response.json()
        assert data["track_id"] == track_id
        assert data["user_id"] == TEST_USER_ID
        assert "history_id" in data
        assert "listened_at" in data

    def test_record_playback_with_duration(self):
        track_id = str(uuid.uuid4())
        response = client.post("/history", json={"track_id": track_id, "play_duration_ms": 180000}, headers=get_auth_header())
        assert response.status_code == 201
        assert response.json()["play_duration_ms"] == 180000

    def test_record_playback_with_source(self):
        track_id = str(uuid.uuid4())
        response = client.post("/history", json={"track_id": track_id, "source": "playlist"}, headers=get_auth_header())
        assert response.status_code == 201
        assert response.json()["source"] == "playlist"

    def test_record_playback_with_timestamp(self):
        track_id = str(uuid.uuid4())
        timestamp = "2024-01-15T10:30:00"
        response = client.post("/history", json={"track_id": track_id, "listened_at": timestamp}, headers=get_auth_header())
        assert response.status_code == 201
        assert timestamp in response.json()["listened_at"]

    def test_record_playback_full_data(self):
        track_id = str(uuid.uuid4())
        response = client.post("/history", json={"track_id": track_id, "play_duration_ms": 240000, "source": "album", "listened_at": "2024-06-01T14:00:00"}, headers=get_auth_header())
        assert response.status_code == 201
        data = response.json()
        assert data["play_duration_ms"] == 240000
        assert data["source"] == "album"

    def test_record_playback_no_auth(self):
        track_id = str(uuid.uuid4())
        response = client.post("/history", json={"track_id": track_id})
        assert response.status_code == 401

    def test_record_playback_invalid_token(self):
        track_id = str(uuid.uuid4())
        response = client.post("/history", json={"track_id": track_id}, headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401

    def test_record_playback_invalid_track_id(self):
        response = client.post("/history", json={"track_id": "invalid"}, headers=get_auth_header())
        assert response.status_code == 400

    def test_record_multiple_plays_same_track(self):
        track_id = str(uuid.uuid4())
        client.post("/history", json={"track_id": track_id}, headers=get_auth_header())
        response = client.post("/history", json={"track_id": track_id}, headers=get_auth_header())
        assert response.status_code == 201


class TestGetHistory:
    def test_get_history_empty(self):
        response = client.get("/history", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_history(self):
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        client.post("/history", json={"track_id": track1}, headers=get_auth_header())
        client.post("/history", json={"track_id": track2}, headers=get_auth_header())
        response = client.get("/history", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_get_history_pagination(self):
        for i in range(10):
            client.post("/history", json={"track_id": str(uuid.uuid4())}, headers=get_auth_header())
        response = client.get("/history?skip=3&limit=4", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 4
        assert data["total"] == 10
        assert data["skip"] == 3
        assert data["limit"] == 4

    def test_get_history_filter_by_track(self):
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        client.post("/history", json={"track_id": track1}, headers=get_auth_header())
        client.post("/history", json={"track_id": track1}, headers=get_auth_header())
        client.post("/history", json={"track_id": track2}, headers=get_auth_header())
        response = client.get(f"/history?track_id={track1}", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(item["track_id"] == track1 for item in data["items"])

    def test_get_history_filter_by_date_range(self):
        track_id = str(uuid.uuid4())
        client.post("/history", json={"track_id": track_id, "listened_at": "2024-01-15T10:00:00"}, headers=get_auth_header())
        client.post("/history", json={"track_id": track_id, "listened_at": "2024-02-15T10:00:00"}, headers=get_auth_header())
        client.post("/history", json={"track_id": track_id, "listened_at": "2024-03-15T10:00:00"}, headers=get_auth_header())
        response = client.get("/history?start_date=2024-02-01T00:00:00&end_date=2024-02-28T23:59:59", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_get_history_invalid_track_filter(self):
        response = client.get("/history?track_id=invalid", headers=get_auth_header())
        assert response.status_code == 400

    def test_get_history_invalid_date_filter(self):
        response = client.get("/history?start_date=invalid", headers=get_auth_header())
        assert response.status_code == 400

    def test_get_history_only_own(self):
        track_id = str(uuid.uuid4())
        client.post("/history", json={"track_id": track_id}, headers=get_auth_header(TEST_USER_ID))
        client.post("/history", json={"track_id": track_id}, headers=get_auth_header(TEST_USER_ID_2))
        response = client.get("/history", headers=get_auth_header(TEST_USER_ID))
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    def test_get_history_no_auth(self):
        response = client.get("/history")
        assert response.status_code == 401


class TestGetStats:
    def test_get_stats_empty(self):
        response = client.get("/history/stats", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["total_plays"] == 0
        assert data["total_duration_ms"] == 0
        assert data["unique_tracks"] == 0
        assert data["top_tracks"] == []
        assert data["period_days"] == 30

    def test_get_stats(self):
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        client.post("/history", json={"track_id": track1, "play_duration_ms": 180000}, headers=get_auth_header())
        client.post("/history", json={"track_id": track1, "play_duration_ms": 180000}, headers=get_auth_header())
        client.post("/history", json={"track_id": track2, "play_duration_ms": 240000}, headers=get_auth_header())
        response = client.get("/history/stats", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["total_plays"] == 3
        assert data["total_duration_ms"] == 600000
        assert data["unique_tracks"] == 2

    def test_get_stats_top_tracks(self):
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        for _ in range(5):
            client.post("/history", json={"track_id": track1}, headers=get_auth_header())
        for _ in range(3):
            client.post("/history", json={"track_id": track2}, headers=get_auth_header())
        response = client.get("/history/stats", headers=get_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert len(data["top_tracks"]) == 2
        assert data["top_tracks"][0]["track_id"] == track1
        assert data["top_tracks"][0]["play_count"] == 5

    def test_get_stats_custom_period(self):
        response = client.get("/history/stats?days=7", headers=get_auth_header())
        assert response.status_code == 200
        assert response.json()["period_days"] == 7

    def test_get_stats_no_auth(self):
        response = client.get("/history/stats")
        assert response.status_code == 401

    def test_get_stats_only_own(self):
        track_id = str(uuid.uuid4())
        client.post("/history", json={"track_id": track_id, "play_duration_ms": 100000}, headers=get_auth_header(TEST_USER_ID))
        client.post("/history", json={"track_id": track_id, "play_duration_ms": 200000}, headers=get_auth_header(TEST_USER_ID_2))
        response = client.get("/history/stats", headers=get_auth_header(TEST_USER_ID))
        assert response.status_code == 200
        assert response.json()["total_plays"] == 1
        assert response.json()["total_duration_ms"] == 100000


class TestGetHistoryEntry:
    def test_get_history_entry(self):
        track_id = str(uuid.uuid4())
        create_resp = client.post("/history", json={"track_id": track_id, "play_duration_ms": 180000}, headers=get_auth_header())
        history_id = create_resp.json()["history_id"]
        response = client.get(f"/history/{history_id}", headers=get_auth_header())
        assert response.status_code == 200
        assert response.json()["history_id"] == history_id
        assert response.json()["track_id"] == track_id

    def test_get_history_entry_not_found(self):
        response = client.get("/history/99999", headers=get_auth_header())
        assert response.status_code == 404

    def test_get_history_entry_other_user(self):
        track_id = str(uuid.uuid4())
        create_resp = client.post("/history", json={"track_id": track_id}, headers=get_auth_header(TEST_USER_ID))
        history_id = create_resp.json()["history_id"]
        response = client.get(f"/history/{history_id}", headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 403

    def test_get_history_entry_no_auth(self):
        response = client.get("/history/1")
        assert response.status_code == 401


class TestDeleteHistoryEntry:
    def test_delete_history_entry(self):
        track_id = str(uuid.uuid4())
        create_resp = client.post("/history", json={"track_id": track_id}, headers=get_auth_header())
        history_id = create_resp.json()["history_id"]
        response = client.delete(f"/history/{history_id}", headers=get_auth_header())
        assert response.status_code == 204
        get_resp = client.get(f"/history/{history_id}", headers=get_auth_header())
        assert get_resp.status_code == 404

    def test_delete_history_entry_not_found(self):
        response = client.delete("/history/99999", headers=get_auth_header())
        assert response.status_code == 404

    def test_delete_history_entry_other_user(self):
        track_id = str(uuid.uuid4())
        create_resp = client.post("/history", json={"track_id": track_id}, headers=get_auth_header(TEST_USER_ID))
        history_id = create_resp.json()["history_id"]
        response = client.delete(f"/history/{history_id}", headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 403

    def test_delete_history_entry_no_auth(self):
        response = client.delete("/history/1")
        assert response.status_code == 401
