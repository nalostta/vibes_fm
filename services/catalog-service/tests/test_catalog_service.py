"""
Unit tests for Catalog Service API endpoints.
"""
import os
import sys
import uuid
import pytest
from datetime import datetime
from typing import Optional, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from uuid import UUID

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

import shared.database as db_module
db_module.engine = test_engine
db_module.SessionLocal = TestSessionLocal

from shared.database import Base
import importlib.util

catalog_spec = importlib.util.spec_from_file_location("catalog", os.path.join(PROJECT_ROOT, "services", "catalog-service", "app", "models", "catalog.py"))
catalog_module = importlib.util.module_from_spec(catalog_spec)
catalog_spec.loader.exec_module(catalog_module)
Artist, Album, Track, Genre = catalog_module.Artist, catalog_module.Album, catalog_module.Track, catalog_module.Genre

class ArtistCreate(BaseModel):
    name: str
    bio: Optional[str] = None
    image_url: Optional[str] = None

class ArtistUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None

class GenreCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GenreUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class AlbumCreate(BaseModel):
    title: str
    artist_id: str
    release_date: Optional[datetime] = None
    cover_image_url: Optional[str] = None

class AlbumUpdate(BaseModel):
    title: Optional[str] = None
    artist_id: Optional[str] = None

class TrackCreate(BaseModel):
    title: str
    album_id: Optional[str] = None
    duration_ms: Optional[int] = None
    track_number: Optional[int] = None
    artist_ids: Optional[List[str]] = None
    genre_ids: Optional[List[str]] = None

class TrackUpdate(BaseModel):
    title: Optional[str] = None
    duration_ms: Optional[int] = None
    track_number: Optional[int] = None

app = FastAPI()

def get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "healthy", "service": "catalog-service"}

@app.post("/artists", status_code=201)
def create_artist(req: ArtistCreate, db: Session = Depends(get_db)):
    a = Artist(name=req.name, bio=req.bio, image_url=req.image_url)
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"artist_id": str(a.artist_id), "name": a.name, "bio": a.bio, "image_url": a.image_url}

@app.get("/artists")
def list_artists(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    return [{"artist_id": str(a.artist_id), "name": a.name, "bio": a.bio} for a in db.query(Artist).offset((page-1)*page_size).limit(page_size).all()]

@app.get("/artists/{aid}")
def get_artist(aid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(aid)
    except:
        raise HTTPException(400, "Invalid ID")
    a = db.query(Artist).filter(Artist.artist_id == uid).first()
    if not a:
        raise HTTPException(404, "Not found")
    return {"artist_id": str(a.artist_id), "name": a.name, "bio": a.bio}

@app.put("/artists/{aid}")
def update_artist(aid: str, req: ArtistUpdate, db: Session = Depends(get_db)):
    try:
        uid = UUID(aid)
    except:
        raise HTTPException(400, "Invalid ID")
    a = db.query(Artist).filter(Artist.artist_id == uid).first()
    if not a:
        raise HTTPException(404, "Not found")
    if req.name:
        a.name = req.name
    if req.bio:
        a.bio = req.bio
    db.commit()
    db.refresh(a)
    return {"artist_id": str(a.artist_id), "name": a.name, "bio": a.bio}

@app.delete("/artists/{aid}", status_code=204)
def delete_artist(aid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(aid)
    except:
        raise HTTPException(400, "Invalid ID")
    a = db.query(Artist).filter(Artist.artist_id == uid).first()
    if not a:
        raise HTTPException(404, "Not found")
    db.delete(a)
    db.commit()

@app.post("/genres", status_code=201)
def create_genre(req: GenreCreate, db: Session = Depends(get_db)):
    if db.query(Genre).filter(Genre.name == req.name).first():
        raise HTTPException(409, "Exists")
    g = Genre(name=req.name, description=req.description)
    db.add(g)
    db.commit()
    db.refresh(g)
    return {"genre_id": str(g.genre_id), "name": g.name, "description": g.description}

@app.get("/genres")
def list_genres(db: Session = Depends(get_db)):
    return [{"genre_id": str(g.genre_id), "name": g.name} for g in db.query(Genre).all()]

@app.get("/genres/{gid}")
def get_genre(gid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(gid)
    except:
        raise HTTPException(400, "Invalid ID")
    g = db.query(Genre).filter(Genre.genre_id == uid).first()
    if not g:
        raise HTTPException(404, "Not found")
    return {"genre_id": str(g.genre_id), "name": g.name}

@app.put("/genres/{gid}")
def update_genre(gid: str, req: GenreUpdate, db: Session = Depends(get_db)):
    try:
        uid = UUID(gid)
    except:
        raise HTTPException(400, "Invalid ID")
    g = db.query(Genre).filter(Genre.genre_id == uid).first()
    if not g:
        raise HTTPException(404, "Not found")
    if req.name:
        if db.query(Genre).filter(Genre.name == req.name, Genre.genre_id != uid).first():
            raise HTTPException(409, "Exists")
        g.name = req.name
    if req.description:
        g.description = req.description
    db.commit()
    db.refresh(g)
    return {"genre_id": str(g.genre_id), "name": g.name}

@app.delete("/genres/{gid}", status_code=204)
def delete_genre(gid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(gid)
    except:
        raise HTTPException(400, "Invalid ID")
    g = db.query(Genre).filter(Genre.genre_id == uid).first()
    if not g:
        raise HTTPException(404, "Not found")
    db.delete(g)
    db.commit()

@app.post("/albums", status_code=201)
def create_album(req: AlbumCreate, db: Session = Depends(get_db)):
    try:
        aid = UUID(req.artist_id)
    except:
        raise HTTPException(400, "Invalid ID")
    if not db.query(Artist).filter(Artist.artist_id == aid).first():
        raise HTTPException(404, "Artist not found")
    alb = Album(title=req.title, artist_id=aid, release_date=req.release_date, cover_image_url=req.cover_image_url)
    db.add(alb)
    db.commit()
    db.refresh(alb)
    return {"album_id": str(alb.album_id), "title": alb.title, "artist_id": str(alb.artist_id)}

@app.get("/albums")
def list_albums(artist_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Album)
    if artist_id:
        try:
            q = q.filter(Album.artist_id == UUID(artist_id))
        except:
            raise HTTPException(400, "Invalid ID")
    return [{"album_id": str(a.album_id), "title": a.title, "artist_id": str(a.artist_id)} for a in q.all()]

@app.get("/albums/{alid}")
def get_album(alid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(alid)
    except:
        raise HTTPException(400, "Invalid ID")
    alb = db.query(Album).filter(Album.album_id == uid).first()
    if not alb:
        raise HTTPException(404, "Not found")
    tracks = [{"track_id": str(t.track_id), "title": t.title, "track_number": t.track_number} for t in sorted(alb.tracks, key=lambda x: x.track_number or 0)]
    return {"album_id": str(alb.album_id), "title": alb.title, "artist_id": str(alb.artist_id), "tracks": tracks}

@app.put("/albums/{alid}")
def update_album(alid: str, req: AlbumUpdate, db: Session = Depends(get_db)):
    try:
        uid = UUID(alid)
    except:
        raise HTTPException(400, "Invalid ID")
    alb = db.query(Album).filter(Album.album_id == uid).first()
    if not alb:
        raise HTTPException(404, "Not found")
    if req.title:
        alb.title = req.title
    db.commit()
    db.refresh(alb)
    return {"album_id": str(alb.album_id), "title": alb.title}

@app.delete("/albums/{alid}", status_code=204)
def delete_album(alid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(alid)
    except:
        raise HTTPException(400, "Invalid ID")
    alb = db.query(Album).filter(Album.album_id == uid).first()
    if not alb:
        raise HTTPException(404, "Not found")
    db.delete(alb)
    db.commit()

@app.post("/tracks", status_code=201)
def create_track(req: TrackCreate, db: Session = Depends(get_db)):
    album_uuid = None
    if req.album_id:
        try:
            album_uuid = UUID(req.album_id)
        except:
            raise HTTPException(400, "Invalid ID")
        if not db.query(Album).filter(Album.album_id == album_uuid).first():
            raise HTTPException(404, "Album not found")
    t = Track(title=req.title, album_id=album_uuid, duration_ms=req.duration_ms, track_number=req.track_number)
    if req.artist_ids:
        for aid in req.artist_ids:
            try:
                a = db.query(Artist).filter(Artist.artist_id == UUID(aid)).first()
                if a:
                    t.artists.append(a)
            except:
                pass
    if req.genre_ids:
        for gid in req.genre_ids:
            try:
                g = db.query(Genre).filter(Genre.genre_id == UUID(gid)).first()
                if g:
                    t.genres.append(g)
            except:
                pass
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"track_id": str(t.track_id), "title": t.title, "album_id": str(t.album_id) if t.album_id else None, "duration_ms": t.duration_ms, "artists": [{"artist_id": str(a.artist_id), "name": a.name} for a in t.artists], "genres": [{"genre_id": str(g.genre_id), "name": g.name} for g in t.genres]}

@app.get("/tracks")
def list_tracks(page: int = 1, page_size: int = 20, album_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Track)
    if album_id:
        try:
            q = q.filter(Track.album_id == UUID(album_id))
        except:
            raise HTTPException(400, "Invalid ID")
    return [{"track_id": str(t.track_id), "title": t.title, "album_id": str(t.album_id) if t.album_id else None} for t in q.offset((page-1)*page_size).limit(page_size).all()]

@app.get("/tracks/{tid}")
def get_track(tid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(tid)
    except:
        raise HTTPException(400, "Invalid ID")
    t = db.query(Track).filter(Track.track_id == uid).first()
    if not t:
        raise HTTPException(404, "Not found")
    return {"track_id": str(t.track_id), "title": t.title, "artists": [{"artist_id": str(a.artist_id)} for a in t.artists], "genres": [{"genre_id": str(g.genre_id)} for g in t.genres]}

@app.put("/tracks/{tid}")
def update_track(tid: str, req: TrackUpdate, db: Session = Depends(get_db)):
    try:
        uid = UUID(tid)
    except:
        raise HTTPException(400, "Invalid ID")
    t = db.query(Track).filter(Track.track_id == uid).first()
    if not t:
        raise HTTPException(404, "Not found")
    if req.title:
        t.title = req.title
    if req.duration_ms:
        t.duration_ms = req.duration_ms
    db.commit()
    db.refresh(t)
    return {"track_id": str(t.track_id), "title": t.title, "duration_ms": t.duration_ms}

@app.delete("/tracks/{tid}", status_code=204)
def delete_track(tid: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(tid)
    except:
        raise HTTPException(400, "Invalid ID")
    t = db.query(Track).filter(Track.track_id == uid).first()
    if not t:
        raise HTTPException(404, "Not found")
    db.delete(t)
    db.commit()

@app.post("/tracks/{tid}/artists/{aid}")
def add_artist(tid: str, aid: str, db: Session = Depends(get_db)):
    try:
        tuid, auid = UUID(tid), UUID(aid)
    except:
        raise HTTPException(400, "Invalid ID")
    t = db.query(Track).filter(Track.track_id == tuid).first()
    a = db.query(Artist).filter(Artist.artist_id == auid).first()
    if not t or not a:
        raise HTTPException(404, "Not found")
    if a not in t.artists:
        t.artists.append(a)
        db.commit()
    return {"artists": [{"artist_id": str(x.artist_id)} for x in t.artists]}

@app.delete("/tracks/{tid}/artists/{aid}")
def remove_artist(tid: str, aid: str, db: Session = Depends(get_db)):
    try:
        tuid, auid = UUID(tid), UUID(aid)
    except:
        raise HTTPException(400, "Invalid ID")
    t = db.query(Track).filter(Track.track_id == tuid).first()
    a = db.query(Artist).filter(Artist.artist_id == auid).first()
    if not t or not a:
        raise HTTPException(404, "Not found")
    if a in t.artists:
        t.artists.remove(a)
        db.commit()
    return {"artists": [{"artist_id": str(x.artist_id)} for x in t.artists]}

@app.post("/tracks/{tid}/genres/{gid}")
def add_genre(tid: str, gid: str, db: Session = Depends(get_db)):
    try:
        tuid, guid = UUID(tid), UUID(gid)
    except:
        raise HTTPException(400, "Invalid ID")
    t = db.query(Track).filter(Track.track_id == tuid).first()
    g = db.query(Genre).filter(Genre.genre_id == guid).first()
    if not t or not g:
        raise HTTPException(404, "Not found")
    if g not in t.genres:
        t.genres.append(g)
        db.commit()
    return {"genres": [{"genre_id": str(x.genre_id)} for x in t.genres]}

@app.delete("/tracks/{tid}/genres/{gid}")
def remove_genre(tid: str, gid: str, db: Session = Depends(get_db)):
    try:
        tuid, guid = UUID(tid), UUID(gid)
    except:
        raise HTTPException(400, "Invalid ID")
    t = db.query(Track).filter(Track.track_id == tuid).first()
    g = db.query(Genre).filter(Genre.genre_id == guid).first()
    if not t or not g:
        raise HTTPException(404, "Not found")
    if g in t.genres:
        t.genres.remove(g)
        db.commit()
    return {"genres": [{"genre_id": str(x.genre_id)} for x in t.genres]}

@app.get("/search")
def search(q: str, limit: int = 20, db: Session = Depends(get_db)):
    term = f"%{q}%"
    tracks = [{"track_id": str(t.track_id), "title": t.title} for t in db.query(Track).filter(Track.title.ilike(term)).limit(limit).all()]
    albums = [{"album_id": str(a.album_id), "title": a.title} for a in db.query(Album).filter(Album.title.ilike(term)).limit(limit).all()]
    artists = [{"artist_id": str(a.artist_id), "name": a.name} for a in db.query(Artist).filter(or_(Artist.name.ilike(term), Artist.bio.ilike(term))).limit(limit).all()]
    return {"tracks": tracks, "albums": albums, "artists": artists}

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

class TestHealth:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

class TestArtists:
    def test_create(self):
        r = client.post("/artists", json={"name": "Artist1", "bio": "Bio"})
        assert r.status_code == 201
        assert r.json()["name"] == "Artist1"

    def test_list(self):
        client.post("/artists", json={"name": "A1"})
        client.post("/artists", json={"name": "A2"})
        r = client.get("/artists")
        assert len(r.json()) >= 2

    def test_get(self):
        c = client.post("/artists", json={"name": "GetArtist"})
        aid = c.json()["artist_id"]
        r = client.get(f"/artists/{aid}")
        assert r.json()["name"] == "GetArtist"

    def test_get_404(self):
        r = client.get(f"/artists/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_get_invalid(self):
        r = client.get("/artists/invalid")
        assert r.status_code == 400

    def test_update(self):
        c = client.post("/artists", json={"name": "Old"})
        aid = c.json()["artist_id"]
        r = client.put(f"/artists/{aid}", json={"name": "New"})
        assert r.json()["name"] == "New"

    def test_delete(self):
        c = client.post("/artists", json={"name": "Del"})
        aid = c.json()["artist_id"]
        r = client.delete(f"/artists/{aid}")
        assert r.status_code == 204

class TestGenres:
    def test_create(self):
        r = client.post("/genres", json={"name": "Rock"})
        assert r.status_code == 201

    def test_duplicate(self):
        client.post("/genres", json={"name": "Pop"})
        r = client.post("/genres", json={"name": "Pop"})
        assert r.status_code == 409

    def test_list(self):
        client.post("/genres", json={"name": "Jazz"})
        r = client.get("/genres")
        assert len(r.json()) >= 1

    def test_get(self):
        c = client.post("/genres", json={"name": "Blues"})
        gid = c.json()["genre_id"]
        r = client.get(f"/genres/{gid}")
        assert r.json()["name"] == "Blues"

    def test_update(self):
        c = client.post("/genres", json={"name": "Old"})
        gid = c.json()["genre_id"]
        r = client.put(f"/genres/{gid}", json={"name": "New"})
        assert r.json()["name"] == "New"

    def test_delete(self):
        c = client.post("/genres", json={"name": "Del"})
        gid = c.json()["genre_id"]
        r = client.delete(f"/genres/{gid}")
        assert r.status_code == 204

class TestAlbums:
    def test_create(self):
        a = client.post("/artists", json={"name": "AlbArtist"}).json()
        r = client.post("/albums", json={"title": "Album1", "artist_id": a["artist_id"]})
        assert r.status_code == 201

    def test_create_no_artist(self):
        r = client.post("/albums", json={"title": "X", "artist_id": str(uuid.uuid4())})
        assert r.status_code == 404

    def test_list(self):
        a = client.post("/artists", json={"name": "LA"}).json()
        client.post("/albums", json={"title": "A1", "artist_id": a["artist_id"]})
        r = client.get("/albums")
        assert len(r.json()) >= 1

    def test_list_by_artist(self):
        a1 = client.post("/artists", json={"name": "A1"}).json()
        a2 = client.post("/artists", json={"name": "A2"}).json()
        client.post("/albums", json={"title": "X", "artist_id": a1["artist_id"]})
        client.post("/albums", json={"title": "Y", "artist_id": a2["artist_id"]})
        r = client.get(f"/albums?artist_id={a1['artist_id']}")
        assert len(r.json()) == 1

    def test_get_with_tracks(self):
        a = client.post("/artists", json={"name": "TA"}).json()
        alb = client.post("/albums", json={"title": "TA", "artist_id": a["artist_id"]}).json()
        client.post("/tracks", json={"title": "T1", "album_id": alb["album_id"], "track_number": 1})
        r = client.get(f"/albums/{alb['album_id']}")
        assert len(r.json()["tracks"]) == 1

    def test_update(self):
        a = client.post("/artists", json={"name": "UA"}).json()
        alb = client.post("/albums", json={"title": "Old", "artist_id": a["artist_id"]}).json()
        r = client.put(f"/albums/{alb['album_id']}", json={"title": "New"})
        assert r.json()["title"] == "New"

    def test_delete(self):
        a = client.post("/artists", json={"name": "DA"}).json()
        alb = client.post("/albums", json={"title": "Del", "artist_id": a["artist_id"]}).json()
        r = client.delete(f"/albums/{alb['album_id']}")
        assert r.status_code == 204

class TestTracks:
    def test_create(self):
        r = client.post("/tracks", json={"title": "Track1", "duration_ms": 180000})
        assert r.status_code == 201

    def test_create_with_album(self):
        a = client.post("/artists", json={"name": "TA"}).json()
        alb = client.post("/albums", json={"title": "A", "artist_id": a["artist_id"]}).json()
        r = client.post("/tracks", json={"title": "T", "album_id": alb["album_id"]})
        assert r.json()["album_id"] == alb["album_id"]

    def test_create_no_album(self):
        r = client.post("/tracks", json={"title": "T", "album_id": str(uuid.uuid4())})
        assert r.status_code == 404

    def test_list(self):
        client.post("/tracks", json={"title": "T1"})
        r = client.get("/tracks")
        assert len(r.json()) >= 1

    def test_get(self):
        c = client.post("/tracks", json={"title": "GT"})
        tid = c.json()["track_id"]
        r = client.get(f"/tracks/{tid}")
        assert r.json()["title"] == "GT"

    def test_update(self):
        c = client.post("/tracks", json={"title": "Old"})
        tid = c.json()["track_id"]
        r = client.put(f"/tracks/{tid}", json={"title": "New"})
        assert r.json()["title"] == "New"

    def test_delete(self):
        c = client.post("/tracks", json={"title": "Del"})
        tid = c.json()["track_id"]
        r = client.delete(f"/tracks/{tid}")
        assert r.status_code == 204

    def test_add_artist(self):
        a = client.post("/artists", json={"name": "FA"}).json()
        t = client.post("/tracks", json={"title": "T"}).json()
        r = client.post(f"/tracks/{t['track_id']}/artists/{a['artist_id']}")
        assert len(r.json()["artists"]) == 1

    def test_remove_artist(self):
        a = client.post("/artists", json={"name": "RA"}).json()
        t = client.post("/tracks", json={"title": "T", "artist_ids": [a["artist_id"]]}).json()
        r = client.delete(f"/tracks/{t['track_id']}/artists/{a['artist_id']}")
        assert len(r.json()["artists"]) == 0

    def test_add_genre(self):
        g = client.post("/genres", json={"name": "TG"}).json()
        t = client.post("/tracks", json={"title": "T"}).json()
        r = client.post(f"/tracks/{t['track_id']}/genres/{g['genre_id']}")
        assert len(r.json()["genres"]) == 1

    def test_remove_genre(self):
        g = client.post("/genres", json={"name": "RG"}).json()
        t = client.post("/tracks", json={"title": "T", "genre_ids": [g["genre_id"]]}).json()
        r = client.delete(f"/tracks/{t['track_id']}/genres/{g['genre_id']}")
        assert len(r.json()["genres"]) == 0

class TestSearch:
    def test_search_tracks(self):
        client.post("/tracks", json={"title": "Searchable"})
        r = client.get("/search?q=Searchable")
        assert len(r.json()["tracks"]) >= 1

    def test_search_albums(self):
        a = client.post("/artists", json={"name": "SA"}).json()
        client.post("/albums", json={"title": "SearchAlbum", "artist_id": a["artist_id"]})
        r = client.get("/search?q=SearchAlbum")
        assert len(r.json()["albums"]) >= 1

    def test_search_artists(self):
        client.post("/artists", json={"name": "SearchArtist"})
        r = client.get("/search?q=SearchArtist")
        assert len(r.json()["artists"]) >= 1

    def test_search_empty(self):
        r = client.get("/search?q=ZZZZZZZ")
        assert len(r.json()["tracks"]) == 0
