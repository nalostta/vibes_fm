"""
Streaming Service - FastAPI Application

Handles playback authorization and returns signed CDN URLs for audio streaming.
This service:
- Validates user authentication
- Checks if the requested track exists
- Generates time-limited signed URLs for CDN access
- Publishes playback events for the Playback History Service
"""
import os
import sys
import uuid
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID as PyUUID

from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path for shared imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.auth.security import decode_access_token

# Import schemas - use dynamic import to handle both package and direct execution
import importlib.util
_schemas_path = os.path.join(os.path.dirname(__file__), "schemas.py")
_schemas_spec = importlib.util.spec_from_file_location("streaming_schemas", _schemas_path)
_schemas_module = importlib.util.module_from_spec(_schemas_spec)
_schemas_spec.loader.exec_module(_schemas_module)
StreamRequest = _schemas_module.StreamRequest
StreamResponse = _schemas_module.StreamResponse
PlaybackStartRequest = _schemas_module.PlaybackStartRequest
PlaybackStartResponse = _schemas_module.PlaybackStartResponse
PlaybackEndRequest = _schemas_module.PlaybackEndRequest
PlaybackEndResponse = _schemas_module.PlaybackEndResponse
ErrorResponse = _schemas_module.ErrorResponse

# Configuration
CDN_BASE_URL = os.getenv("CDN_BASE_URL", "https://cdn.vibes.fm")
CDN_SIGNING_KEY = os.getenv("CDN_SIGNING_KEY", "cdn-signing-key-change-in-production")
STREAM_URL_EXPIRY_MINUTES = int(os.getenv("STREAM_URL_EXPIRY_MINUTES", "60"))

# In-memory storage for playback sessions (would use Redis in production)
playback_sessions = {}

# In-memory track database for testing (would query Catalog Service in production)
mock_tracks = {}

# Initialize FastAPI app
app = FastAPI(
    title="Streaming Service",
    description="Audio streaming service with signed CDN URLs and playback tracking",
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


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validate JWT token and return current user.
    
    In production, this would also check token revocation in Redis.
    """
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


def generate_signed_url(track_id: str, audio_url: str, expires_at: datetime) -> str:
    """
    Generate a signed CDN URL with expiration.
    
    This creates a time-limited URL that the CDN can validate.
    In production, this would use the CDN provider's signing mechanism
    (e.g., CloudFront signed URLs, Cloudflare signed URLs).
    """
    expiry_timestamp = int(expires_at.timestamp())
    
    # Create signature payload
    payload = f"{track_id}:{audio_url}:{expiry_timestamp}"
    
    # Generate HMAC signature
    signature = hmac.new(
        CDN_SIGNING_KEY.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Base64 encode the signature (URL-safe)
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    # Construct signed URL
    if audio_url.startswith("http"):
        base_url = audio_url
    else:
        base_url = f"{CDN_BASE_URL}/{audio_url}"
    
    signed_url = f"{base_url}?expires={expiry_timestamp}&signature={signature_b64}"
    
    return signed_url


def verify_signed_url(track_id: str, audio_url: str, expires_timestamp: int, signature: str) -> bool:
    """
    Verify a signed URL signature.
    
    Used by the CDN edge to validate requests.
    """
    # Check expiration
    if datetime.utcnow().timestamp() > expires_timestamp:
        return False
    
    # Recreate signature payload
    payload = f"{track_id}:{audio_url}:{expires_timestamp}"
    
    # Generate expected signature
    expected_signature = hmac.new(
        CDN_SIGNING_KEY.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    expected_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
    
    # Constant-time comparison
    return hmac.compare_digest(signature, expected_b64)


def get_track_info(track_id: str) -> Optional[dict]:
    """
    Get track information from Catalog Service.
    
    In production, this would make an HTTP request to the Catalog Service.
    For MVP/testing, we use mock data.
    """
    # Check mock tracks first
    if track_id in mock_tracks:
        return mock_tracks[track_id]
    
    # Return a default mock track for any valid UUID
    try:
        PyUUID(track_id)
        return {
            "track_id": track_id,
            "title": "Mock Track",
            "audio_url": f"audio/{track_id}.mp3",
            "duration_ms": 180000
        }
    except ValueError:
        return None


def add_mock_track(track_id: str, title: str, audio_url: str, duration_ms: int = 180000):
    """Add a mock track for testing."""
    mock_tracks[track_id] = {
        "track_id": track_id,
        "title": title,
        "audio_url": audio_url,
        "duration_ms": duration_ms
    }


def clear_mock_tracks():
    """Clear all mock tracks."""
    mock_tracks.clear()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "streaming-service"}


@app.post(
    "/stream",
    response_model=StreamResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
def get_stream_url(
    request: StreamRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a signed streaming URL for a track.
    
    This endpoint:
    1. Validates the user's authentication
    2. Checks if the track exists
    3. Generates a time-limited signed URL
    
    The signed URL can be used directly by the client's audio player.
    """
    # Validate track_id format
    try:
        PyUUID(request.track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    # Get track info from Catalog Service
    track = get_track_info(request.track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(minutes=STREAM_URL_EXPIRY_MINUTES)
    
    # Generate signed URL
    stream_url = generate_signed_url(
        track_id=request.track_id,
        audio_url=track["audio_url"],
        expires_at=expires_at
    )
    
    return StreamResponse(
        track_id=request.track_id,
        stream_url=stream_url,
        expires_at=expires_at.isoformat(),
        quality=request.quality
    )


@app.post(
    "/playback/start",
    response_model=PlaybackStartResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
def start_playback(
    request: PlaybackStartRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Notify the service that playback has started.
    
    This creates a playback session that can be used to track
    listening duration for the Playback History Service.
    """
    # Validate track_id format
    try:
        PyUUID(request.track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    # Verify track exists
    track = get_track_info(request.track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Create playback session
    session_id = str(uuid.uuid4())
    started_at = datetime.utcnow()
    
    playback_sessions[session_id] = {
        "session_id": session_id,
        "user_id": current_user.get("sub"),
        "track_id": request.track_id,
        "source": request.source,
        "started_at": started_at,
        "ended": False
    }
    
    return PlaybackStartResponse(
        track_id=request.track_id,
        session_id=session_id,
        started_at=started_at.isoformat()
    )


@app.post(
    "/playback/end",
    response_model=PlaybackEndResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
def end_playback(
    request: PlaybackEndRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Notify the service that playback has ended.
    
    This records the playback duration and publishes an event
    to the Playback History Service (via Redis Pub/Sub in production).
    """
    session = playback_sessions.get(request.session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playback session not found"
        )
    
    # Verify the session belongs to the current user
    if session["user_id"] != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to end this playback session"
        )
    
    if session["ended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playback session already ended"
        )
    
    # Mark session as ended
    session["ended"] = True
    session["play_duration_ms"] = request.play_duration_ms
    session["ended_at"] = datetime.utcnow()
    
    # In production, publish event to Redis for Playback History Service
    # redis_client.publish("playback_events", json.dumps({
    #     "user_id": session["user_id"],
    #     "track_id": session["track_id"],
    #     "play_duration_ms": request.play_duration_ms,
    #     "source": session["source"],
    #     "listened_at": session["started_at"].isoformat()
    # }))
    
    return PlaybackEndResponse(
        session_id=request.session_id,
        recorded=True
    )


@app.get(
    "/playback/session/{session_id}",
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
def get_playback_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get details of a playback session."""
    session = playback_sessions.get(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playback session not found"
        )
    
    # Verify the session belongs to the current user
    if session["user_id"] != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this playback session"
        )
    
    return {
        "session_id": session["session_id"],
        "track_id": session["track_id"],
        "source": session["source"],
        "started_at": session["started_at"].isoformat(),
        "ended": session["ended"],
        "play_duration_ms": session.get("play_duration_ms"),
        "ended_at": session["ended_at"].isoformat() if session.get("ended_at") else None
    }


@app.post("/verify-signature")
def verify_url_signature(
    track_id: str,
    audio_url: str,
    expires: int,
    signature: str
):
    """
    Verify a signed URL signature.
    
    This endpoint is used by the CDN edge to validate requests.
    In production, this would be implemented at the CDN level.
    """
    is_valid = verify_signed_url(track_id, audio_url, expires, signature)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired signature"
        )
    
    return {"valid": True}
