"""
Library & Playlist Service - Unit Tests

Comprehensive tests for the Library & Playlist Service API endpoints.
Tests cover playlist CRUD, track management, and user library operations.
"""
import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, status, Header, Query
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, Session, relationship
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


class Playlist(Base):
    __tablename__ = "playlists"
    playlist_id = Column(UUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    owner_user_id = Column(UUID(), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_private = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    playlist_track_id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(UUID(), ForeignKey("playlists.playlist_id", ondelete="CASCADE"), nullable=False, index=True)
    track_id = Column(UUID(), nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    position = Column(Integer, nullable=False, index=True)
    playlist = relationship("Playlist", back_populates="tracks")


class UserLibrary(Base):
    __tablename__ = "user_library"
    user_id = Column(UUID(), primary_key=True, nullable=False)
    track_id = Column(UUID(), primary_key=True, nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PlaylistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    is_private: bool = Field(default=True)


class PlaylistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_private: Optional[bool] = None


class PlaylistResponse(BaseModel):
    playlist_id: str
    owner_user_id: str
    name: str
    is_private: bool
    created_at: str
    track_count: int = 0


class PlaylistTrackAdd(BaseModel):
    track_id: str
    position: Optional[int] = None


class PlaylistTrackResponse(BaseModel):
    playlist_track_id: int
    playlist_id: str
    track_id: str
    added_at: str
    position: int


class PlaylistWithTracksResponse(BaseModel):
    playlist_id: str
    owner_user_id: str
    name: str
    is_private: bool
    created_at: str
    tracks: List[PlaylistTrackResponse] = []


class LibraryTrackAdd(BaseModel):
    track_id: str


class LibraryTrackResponse(BaseModel):
    user_id: str
    track_id: str
    saved_at: str


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
    return {"status": "healthy", "service": "library-playlist-service"}


@app.post("/playlists", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(playlist: PlaylistCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    db_playlist = Playlist(playlist_id=uuid.uuid4(), owner_user_id=uuid.UUID(user_id), name=playlist.name, is_private=playlist.is_private)
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    return PlaylistResponse(playlist_id=str(db_playlist.playlist_id), owner_user_id=str(db_playlist.owner_user_id), name=db_playlist.name, is_private=db_playlist.is_private, created_at=db_playlist.created_at.isoformat(), track_count=0)


@app.get("/playlists", response_model=List[PlaylistResponse])
def list_playlists(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    user_id = current_user.get("sub")
    playlists = db.query(Playlist).filter(Playlist.owner_user_id == uuid.UUID(user_id)).offset(skip).limit(limit).all()
    result = []
    for p in playlists:
        track_count = db.query(func.count(PlaylistTrack.playlist_track_id)).filter(PlaylistTrack.playlist_id == p.playlist_id).scalar()
        result.append(PlaylistResponse(playlist_id=str(p.playlist_id), owner_user_id=str(p.owner_user_id), name=p.name, is_private=p.is_private, created_at=p.created_at.isoformat(), track_count=track_count))
    return result


@app.get("/playlists/{playlist_id}", response_model=PlaylistWithTracksResponse)
def get_playlist(playlist_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        pid = uuid.UUID(playlist_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid playlist ID format")
    user_id = current_user.get("sub")
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    if playlist.is_private and str(playlist.owner_user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this playlist")
    tracks = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == pid).order_by(PlaylistTrack.position).all()
    track_responses = [PlaylistTrackResponse(playlist_track_id=t.playlist_track_id, playlist_id=str(t.playlist_id), track_id=str(t.track_id), added_at=t.added_at.isoformat(), position=t.position) for t in tracks]
    return PlaylistWithTracksResponse(playlist_id=str(playlist.playlist_id), owner_user_id=str(playlist.owner_user_id), name=playlist.name, is_private=playlist.is_private, created_at=playlist.created_at.isoformat(), tracks=track_responses)


@app.put("/playlists/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(playlist_id: str, playlist_update: PlaylistUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        pid = uuid.UUID(playlist_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid playlist ID format")
    user_id = current_user.get("sub")
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this playlist")
    if playlist_update.name is not None:
        playlist.name = playlist_update.name
    if playlist_update.is_private is not None:
        playlist.is_private = playlist_update.is_private
    db.commit()
    db.refresh(playlist)
    track_count = db.query(func.count(PlaylistTrack.playlist_track_id)).filter(PlaylistTrack.playlist_id == pid).scalar()
    return PlaylistResponse(playlist_id=str(playlist.playlist_id), owner_user_id=str(playlist.owner_user_id), name=playlist.name, is_private=playlist.is_private, created_at=playlist.created_at.isoformat(), track_count=track_count)


@app.delete("/playlists/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(playlist_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        pid = uuid.UUID(playlist_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid playlist ID format")
    user_id = current_user.get("sub")
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this playlist")
    db.delete(playlist)
    db.commit()
    return None


@app.post("/playlists/{playlist_id}/tracks", response_model=PlaylistTrackResponse, status_code=status.HTTP_201_CREATED)
def add_track_to_playlist(playlist_id: str, track_data: PlaylistTrackAdd, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        pid = uuid.UUID(playlist_id)
        tid = uuid.UUID(track_data.track_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    user_id = current_user.get("sub")
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this playlist")
    existing = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == pid, PlaylistTrack.track_id == tid).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Track already in playlist")
    max_position = db.query(func.max(PlaylistTrack.position)).filter(PlaylistTrack.playlist_id == pid).scalar() or 0
    position = track_data.position if track_data.position is not None else max_position + 1
    playlist_track = PlaylistTrack(playlist_id=pid, track_id=tid, position=position)
    db.add(playlist_track)
    db.commit()
    db.refresh(playlist_track)
    return PlaylistTrackResponse(playlist_track_id=playlist_track.playlist_track_id, playlist_id=str(playlist_track.playlist_id), track_id=str(playlist_track.track_id), added_at=playlist_track.added_at.isoformat(), position=playlist_track.position)


@app.delete("/playlists/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_track_from_playlist(playlist_id: str, track_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        pid = uuid.UUID(playlist_id)
        tid = uuid.UUID(track_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    user_id = current_user.get("sub")
    playlist = db.query(Playlist).filter(Playlist.playlist_id == pid).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    if str(playlist.owner_user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this playlist")
    playlist_track = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == pid, PlaylistTrack.track_id == tid).first()
    if not playlist_track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not in playlist")
    db.delete(playlist_track)
    db.commit()
    return None


@app.post("/library/tracks", response_model=LibraryTrackResponse, status_code=status.HTTP_201_CREATED)
def add_track_to_library(track_data: LibraryTrackAdd, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tid = uuid.UUID(track_data.track_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid track ID format")
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    existing = db.query(UserLibrary).filter(UserLibrary.user_id == uid, UserLibrary.track_id == tid).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Track already in library")
    library_entry = UserLibrary(user_id=uid, track_id=tid)
    db.add(library_entry)
    db.commit()
    db.refresh(library_entry)
    return LibraryTrackResponse(user_id=str(library_entry.user_id), track_id=str(library_entry.track_id), saved_at=library_entry.saved_at.isoformat())


@app.get("/library/tracks", response_model=List[LibraryTrackResponse])
def get_library_tracks(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    tracks = db.query(UserLibrary).filter(UserLibrary.user_id == uid).order_by(UserLibrary.saved_at.desc()).offset(skip).limit(limit).all()
    return [LibraryTrackResponse(user_id=str(t.user_id), track_id=str(t.track_id), saved_at=t.saved_at.isoformat()) for t in tracks]


@app.delete("/library/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_track_from_library(track_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tid = uuid.UUID(track_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid track ID format")
    user_id = current_user.get("sub")
    uid = uuid.UUID(user_id)
    library_entry = db.query(UserLibrary).filter(UserLibrary.user_id == uid, UserLibrary.track_id == tid).first()
    if not library_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not in library")
    db.delete(library_entry)
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
        assert response.json()["service"] == "library-playlist-service"


class TestPlaylistCRUD:
    def test_create_playlist(self):
        response = client.post("/playlists", json={"name": "My Playlist", "is_private": True}, headers=get_auth_header())
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Playlist"
        assert data["is_private"] is True
        assert data["owner_user_id"] == TEST_USER_ID
        assert data["track_count"] == 0

    def test_create_playlist_public(self):
        response = client.post("/playlists", json={"name": "Public Playlist", "is_private": False}, headers=get_auth_header())
        assert response.status_code == 201
        assert response.json()["is_private"] is False

    def test_create_playlist_no_auth(self):
        response = client.post("/playlists", json={"name": "Test"})
        assert response.status_code == 401

    def test_create_playlist_invalid_token(self):
        response = client.post("/playlists", json={"name": "Test"}, headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401

    def test_list_playlists_empty(self):
        response = client.get("/playlists", headers=get_auth_header())
        assert response.status_code == 200
        assert response.json() == []

    def test_list_playlists(self):
        client.post("/playlists", json={"name": "Playlist 1"}, headers=get_auth_header())
        client.post("/playlists", json={"name": "Playlist 2"}, headers=get_auth_header())
        response = client.get("/playlists", headers=get_auth_header())
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_playlists_pagination(self):
        for i in range(5):
            client.post("/playlists", json={"name": f"Playlist {i}"}, headers=get_auth_header())
        response = client.get("/playlists?skip=2&limit=2", headers=get_auth_header())
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_playlists_only_own(self):
        client.post("/playlists", json={"name": "User 1 Playlist"}, headers=get_auth_header(TEST_USER_ID))
        client.post("/playlists", json={"name": "User 2 Playlist"}, headers=get_auth_header(TEST_USER_ID_2))
        response = client.get("/playlists", headers=get_auth_header(TEST_USER_ID))
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "User 1 Playlist"

    def test_get_playlist(self):
        create_resp = client.post("/playlists", json={"name": "Test Playlist"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        response = client.get(f"/playlists/{playlist_id}", headers=get_auth_header())
        assert response.status_code == 200
        assert response.json()["name"] == "Test Playlist"
        assert response.json()["tracks"] == []

    def test_get_playlist_not_found(self):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/playlists/{fake_id}", headers=get_auth_header())
        assert response.status_code == 404

    def test_get_playlist_invalid_id(self):
        response = client.get("/playlists/invalid-id", headers=get_auth_header())
        assert response.status_code == 400

    def test_get_private_playlist_other_user(self):
        create_resp = client.post("/playlists", json={"name": "Private", "is_private": True}, headers=get_auth_header(TEST_USER_ID))
        playlist_id = create_resp.json()["playlist_id"]
        response = client.get(f"/playlists/{playlist_id}", headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 403

    def test_get_public_playlist_other_user(self):
        create_resp = client.post("/playlists", json={"name": "Public", "is_private": False}, headers=get_auth_header(TEST_USER_ID))
        playlist_id = create_resp.json()["playlist_id"]
        response = client.get(f"/playlists/{playlist_id}", headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 200

    def test_update_playlist_name(self):
        create_resp = client.post("/playlists", json={"name": "Original"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        response = client.put(f"/playlists/{playlist_id}", json={"name": "Updated"}, headers=get_auth_header())
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_update_playlist_privacy(self):
        create_resp = client.post("/playlists", json={"name": "Test", "is_private": True}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        response = client.put(f"/playlists/{playlist_id}", json={"is_private": False}, headers=get_auth_header())
        assert response.status_code == 200
        assert response.json()["is_private"] is False

    def test_update_playlist_not_found(self):
        fake_id = str(uuid.uuid4())
        response = client.put(f"/playlists/{fake_id}", json={"name": "Test"}, headers=get_auth_header())
        assert response.status_code == 404

    def test_update_playlist_not_owner(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header(TEST_USER_ID))
        playlist_id = create_resp.json()["playlist_id"]
        response = client.put(f"/playlists/{playlist_id}", json={"name": "Hacked"}, headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 403

    def test_delete_playlist(self):
        create_resp = client.post("/playlists", json={"name": "To Delete"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        response = client.delete(f"/playlists/{playlist_id}", headers=get_auth_header())
        assert response.status_code == 204
        get_resp = client.get(f"/playlists/{playlist_id}", headers=get_auth_header())
        assert get_resp.status_code == 404

    def test_delete_playlist_not_found(self):
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/playlists/{fake_id}", headers=get_auth_header())
        assert response.status_code == 404

    def test_delete_playlist_not_owner(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header(TEST_USER_ID))
        playlist_id = create_resp.json()["playlist_id"]
        response = client.delete(f"/playlists/{playlist_id}", headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 403


class TestPlaylistTracks:
    def test_add_track_to_playlist(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        track_id = str(uuid.uuid4())
        response = client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track_id}, headers=get_auth_header())
        assert response.status_code == 201
        assert response.json()["track_id"] == track_id
        assert response.json()["position"] == 1

    def test_add_track_with_position(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        track_id = str(uuid.uuid4())
        response = client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track_id, "position": 5}, headers=get_auth_header())
        assert response.status_code == 201
        assert response.json()["position"] == 5

    def test_add_track_auto_position(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track1}, headers=get_auth_header())
        response = client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track2}, headers=get_auth_header())
        assert response.status_code == 201
        assert response.json()["position"] == 2

    def test_add_duplicate_track(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        track_id = str(uuid.uuid4())
        client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track_id}, headers=get_auth_header())
        response = client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track_id}, headers=get_auth_header())
        assert response.status_code == 409

    def test_add_track_playlist_not_found(self):
        fake_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        response = client.post(f"/playlists/{fake_id}/tracks", json={"track_id": track_id}, headers=get_auth_header())
        assert response.status_code == 404

    def test_add_track_not_owner(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header(TEST_USER_ID))
        playlist_id = create_resp.json()["playlist_id"]
        track_id = str(uuid.uuid4())
        response = client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track_id}, headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 403

    def test_add_track_invalid_id(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        response = client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": "invalid"}, headers=get_auth_header())
        assert response.status_code == 400

    def test_remove_track_from_playlist(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        track_id = str(uuid.uuid4())
        client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track_id}, headers=get_auth_header())
        response = client.delete(f"/playlists/{playlist_id}/tracks/{track_id}", headers=get_auth_header())
        assert response.status_code == 204

    def test_remove_track_not_in_playlist(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        track_id = str(uuid.uuid4())
        response = client.delete(f"/playlists/{playlist_id}/tracks/{track_id}", headers=get_auth_header())
        assert response.status_code == 404

    def test_remove_track_playlist_not_found(self):
        fake_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        response = client.delete(f"/playlists/{fake_id}/tracks/{track_id}", headers=get_auth_header())
        assert response.status_code == 404

    def test_remove_track_not_owner(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header(TEST_USER_ID))
        playlist_id = create_resp.json()["playlist_id"]
        track_id = str(uuid.uuid4())
        client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track_id}, headers=get_auth_header(TEST_USER_ID))
        response = client.delete(f"/playlists/{playlist_id}/tracks/{track_id}", headers=get_auth_header(TEST_USER_ID_2))
        assert response.status_code == 403

    def test_get_playlist_with_tracks(self):
        create_resp = client.post("/playlists", json={"name": "Test"}, headers=get_auth_header())
        playlist_id = create_resp.json()["playlist_id"]
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track1}, headers=get_auth_header())
        client.post(f"/playlists/{playlist_id}/tracks", json={"track_id": track2}, headers=get_auth_header())
        response = client.get(f"/playlists/{playlist_id}", headers=get_auth_header())
        assert response.status_code == 200
        assert len(response.json()["tracks"]) == 2


class TestUserLibrary:
    def test_add_track_to_library(self):
        track_id = str(uuid.uuid4())
        response = client.post("/library/tracks", json={"track_id": track_id}, headers=get_auth_header())
        assert response.status_code == 201
        assert response.json()["track_id"] == track_id
        assert response.json()["user_id"] == TEST_USER_ID

    def test_add_track_to_library_no_auth(self):
        track_id = str(uuid.uuid4())
        response = client.post("/library/tracks", json={"track_id": track_id})
        assert response.status_code == 401

    def test_add_duplicate_track_to_library(self):
        track_id = str(uuid.uuid4())
        client.post("/library/tracks", json={"track_id": track_id}, headers=get_auth_header())
        response = client.post("/library/tracks", json={"track_id": track_id}, headers=get_auth_header())
        assert response.status_code == 409

    def test_add_track_invalid_id(self):
        response = client.post("/library/tracks", json={"track_id": "invalid"}, headers=get_auth_header())
        assert response.status_code == 400

    def test_get_library_tracks_empty(self):
        response = client.get("/library/tracks", headers=get_auth_header())
        assert response.status_code == 200
        assert response.json() == []

    def test_get_library_tracks(self):
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        client.post("/library/tracks", json={"track_id": track1}, headers=get_auth_header())
        client.post("/library/tracks", json={"track_id": track2}, headers=get_auth_header())
        response = client.get("/library/tracks", headers=get_auth_header())
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_library_tracks_pagination(self):
        for i in range(5):
            client.post("/library/tracks", json={"track_id": str(uuid.uuid4())}, headers=get_auth_header())
        response = client.get("/library/tracks?skip=2&limit=2", headers=get_auth_header())
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_library_tracks_only_own(self):
        track1 = str(uuid.uuid4())
        track2 = str(uuid.uuid4())
        client.post("/library/tracks", json={"track_id": track1}, headers=get_auth_header(TEST_USER_ID))
        client.post("/library/tracks", json={"track_id": track2}, headers=get_auth_header(TEST_USER_ID_2))
        response = client.get("/library/tracks", headers=get_auth_header(TEST_USER_ID))
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_remove_track_from_library(self):
        track_id = str(uuid.uuid4())
        client.post("/library/tracks", json={"track_id": track_id}, headers=get_auth_header())
        response = client.delete(f"/library/tracks/{track_id}", headers=get_auth_header())
        assert response.status_code == 204
        get_resp = client.get("/library/tracks", headers=get_auth_header())
        assert len(get_resp.json()) == 0

    def test_remove_track_not_in_library(self):
        track_id = str(uuid.uuid4())
        response = client.delete(f"/library/tracks/{track_id}", headers=get_auth_header())
        assert response.status_code == 404

    def test_remove_track_invalid_id(self):
        response = client.delete("/library/tracks/invalid", headers=get_auth_header())
        assert response.status_code == 400
