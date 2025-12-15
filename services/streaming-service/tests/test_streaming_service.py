"""
Unit tests for Streaming Service API endpoints.

Tests cover:
- Stream URL generation with signed URLs
- Playback session management
- Authentication validation
- URL signature verification
- Error handling
"""
import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta

# Add project root to path for shared imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient

# Import main app
import importlib.util
main_spec = importlib.util.spec_from_file_location(
    "main",
    os.path.join(PROJECT_ROOT, "services", "streaming-service", "app", "main.py")
)
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)

app = main_module.app
add_mock_track = main_module.add_mock_track
clear_mock_tracks = main_module.clear_mock_tracks
playback_sessions = main_module.playback_sessions
generate_signed_url = main_module.generate_signed_url
verify_signed_url = main_module.verify_signed_url

# Import auth utilities
from shared.auth.security import create_access_token

client = TestClient(app)


def get_auth_header(user_id: str = None, username: str = "testuser") -> dict:
    """Generate authorization header with valid JWT token."""
    if user_id is None:
        user_id = str(uuid.uuid4())
    token = create_access_token(data={"sub": user_id, "username": username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up mock data and sessions after each test."""
    yield
    clear_mock_tracks()
    playback_sessions.clear()


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "streaming-service"


class TestStreamEndpoint:
    """Tests for stream URL generation endpoint."""
    
    def test_get_stream_url_success(self):
        """Test getting a stream URL for a valid track."""
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Test Track", "audio/test.mp3")
        
        response = client.post(
            "/stream",
            json={"track_id": track_id, "quality": "high"},
            headers=get_auth_header()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["track_id"] == track_id
        assert "stream_url" in data
        assert "expires_at" in data
        assert data["quality"] == "high"
        assert "signature=" in data["stream_url"]
    
    def test_get_stream_url_default_quality(self):
        """Test getting a stream URL with default quality."""
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Default Quality Track", "audio/default.mp3")
        
        response = client.post(
            "/stream",
            json={"track_id": track_id},
            headers=get_auth_header()
        )
        assert response.status_code == 200
        assert response.json()["quality"] == "high"
    
    def test_get_stream_url_low_quality(self):
        """Test getting a stream URL with low quality."""
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Low Quality Track", "audio/low.mp3")
        
        response = client.post(
            "/stream",
            json={"track_id": track_id, "quality": "low"},
            headers=get_auth_header()
        )
        assert response.status_code == 200
        assert response.json()["quality"] == "low"
    
    def test_get_stream_url_unauthorized(self):
        """Test getting a stream URL without authentication."""
        track_id = str(uuid.uuid4())
        
        response = client.post(
            "/stream",
            json={"track_id": track_id}
        )
        assert response.status_code == 401
    
    def test_get_stream_url_invalid_token(self):
        """Test getting a stream URL with invalid token."""
        track_id = str(uuid.uuid4())
        
        response = client.post(
            "/stream",
            json={"track_id": track_id},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    def test_get_stream_url_invalid_auth_format(self):
        """Test getting a stream URL with invalid auth header format."""
        track_id = str(uuid.uuid4())
        
        response = client.post(
            "/stream",
            json={"track_id": track_id},
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code == 401
    
    def test_get_stream_url_invalid_track_id(self):
        """Test getting a stream URL with invalid track ID format."""
        response = client.post(
            "/stream",
            json={"track_id": "invalid-uuid"},
            headers=get_auth_header()
        )
        assert response.status_code == 400
    
    def test_get_stream_url_mock_track_fallback(self):
        """Test that any valid UUID returns a mock track."""
        track_id = str(uuid.uuid4())
        
        response = client.post(
            "/stream",
            json={"track_id": track_id},
            headers=get_auth_header()
        )
        assert response.status_code == 200
        assert response.json()["track_id"] == track_id


class TestPlaybackStartEndpoint:
    """Tests for playback start notification endpoint."""
    
    def test_start_playback_success(self):
        """Test starting playback for a valid track."""
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Playback Track", "audio/playback.mp3")
        
        response = client.post(
            "/playback/start",
            json={"track_id": track_id, "source": "album"},
            headers=get_auth_header()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["track_id"] == track_id
        assert "session_id" in data
        assert "started_at" in data
    
    def test_start_playback_default_source(self):
        """Test starting playback with default source."""
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Default Source Track", "audio/default.mp3")
        
        response = client.post(
            "/playback/start",
            json={"track_id": track_id},
            headers=get_auth_header()
        )
        assert response.status_code == 200
    
    def test_start_playback_unauthorized(self):
        """Test starting playback without authentication."""
        track_id = str(uuid.uuid4())
        
        response = client.post(
            "/playback/start",
            json={"track_id": track_id}
        )
        assert response.status_code == 401
    
    def test_start_playback_invalid_track_id(self):
        """Test starting playback with invalid track ID format."""
        response = client.post(
            "/playback/start",
            json={"track_id": "invalid-uuid"},
            headers=get_auth_header()
        )
        assert response.status_code == 400


class TestPlaybackEndEndpoint:
    """Tests for playback end notification endpoint."""
    
    def test_end_playback_success(self):
        """Test ending playback for a valid session."""
        user_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "End Track", "audio/end.mp3")
        headers = get_auth_header(user_id=user_id)
        
        # Start playback
        start_response = client.post(
            "/playback/start",
            json={"track_id": track_id},
            headers=headers
        )
        session_id = start_response.json()["session_id"]
        
        # End playback
        response = client.post(
            "/playback/end",
            json={"session_id": session_id, "play_duration_ms": 120000},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["recorded"] is True
    
    def test_end_playback_session_not_found(self):
        """Test ending playback for non-existent session."""
        response = client.post(
            "/playback/end",
            json={"session_id": str(uuid.uuid4()), "play_duration_ms": 60000},
            headers=get_auth_header()
        )
        assert response.status_code == 404
    
    def test_end_playback_unauthorized(self):
        """Test ending playback without authentication."""
        response = client.post(
            "/playback/end",
            json={"session_id": str(uuid.uuid4()), "play_duration_ms": 60000}
        )
        assert response.status_code == 401
    
    def test_end_playback_wrong_user(self):
        """Test ending playback for another user's session."""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Wrong User Track", "audio/wrong.mp3")
        
        # Start playback as user1
        start_response = client.post(
            "/playback/start",
            json={"track_id": track_id},
            headers=get_auth_header(user_id=user1_id)
        )
        session_id = start_response.json()["session_id"]
        
        # Try to end as user2
        response = client.post(
            "/playback/end",
            json={"session_id": session_id, "play_duration_ms": 60000},
            headers=get_auth_header(user_id=user2_id)
        )
        assert response.status_code == 403
    
    def test_end_playback_already_ended(self):
        """Test ending playback for an already ended session."""
        user_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Already Ended Track", "audio/ended.mp3")
        headers = get_auth_header(user_id=user_id)
        
        # Start playback
        start_response = client.post(
            "/playback/start",
            json={"track_id": track_id},
            headers=headers
        )
        session_id = start_response.json()["session_id"]
        
        # End playback first time
        client.post(
            "/playback/end",
            json={"session_id": session_id, "play_duration_ms": 60000},
            headers=headers
        )
        
        # Try to end again
        response = client.post(
            "/playback/end",
            json={"session_id": session_id, "play_duration_ms": 60000},
            headers=headers
        )
        assert response.status_code == 400


class TestPlaybackSessionEndpoint:
    """Tests for playback session retrieval endpoint."""
    
    def test_get_session_success(self):
        """Test getting a playback session."""
        user_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Session Track", "audio/session.mp3")
        headers = get_auth_header(user_id=user_id)
        
        # Start playback
        start_response = client.post(
            "/playback/start",
            json={"track_id": track_id, "source": "playlist"},
            headers=headers
        )
        session_id = start_response.json()["session_id"]
        
        # Get session
        response = client.get(
            f"/playback/session/{session_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["track_id"] == track_id
        assert data["source"] == "playlist"
        assert data["ended"] is False
    
    def test_get_session_not_found(self):
        """Test getting a non-existent session."""
        response = client.get(
            f"/playback/session/{str(uuid.uuid4())}",
            headers=get_auth_header()
        )
        assert response.status_code == 404
    
    def test_get_session_wrong_user(self):
        """Test getting another user's session."""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Wrong User Session Track", "audio/wrong.mp3")
        
        # Start playback as user1
        start_response = client.post(
            "/playback/start",
            json={"track_id": track_id},
            headers=get_auth_header(user_id=user1_id)
        )
        session_id = start_response.json()["session_id"]
        
        # Try to get as user2
        response = client.get(
            f"/playback/session/{session_id}",
            headers=get_auth_header(user_id=user2_id)
        )
        assert response.status_code == 403
    
    def test_get_session_after_end(self):
        """Test getting a session after it has ended."""
        user_id = str(uuid.uuid4())
        track_id = str(uuid.uuid4())
        add_mock_track(track_id, "Ended Session Track", "audio/ended.mp3")
        headers = get_auth_header(user_id=user_id)
        
        # Start playback
        start_response = client.post(
            "/playback/start",
            json={"track_id": track_id},
            headers=headers
        )
        session_id = start_response.json()["session_id"]
        
        # End playback
        client.post(
            "/playback/end",
            json={"session_id": session_id, "play_duration_ms": 90000},
            headers=headers
        )
        
        # Get session
        response = client.get(
            f"/playback/session/{session_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ended"] is True
        assert data["play_duration_ms"] == 90000
        assert data["ended_at"] is not None


class TestSignedUrlGeneration:
    """Tests for signed URL generation and verification."""
    
    def test_generate_signed_url(self):
        """Test generating a signed URL."""
        track_id = str(uuid.uuid4())
        audio_url = "audio/test.mp3"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        signed_url = generate_signed_url(track_id, audio_url, expires_at)
        
        assert "expires=" in signed_url
        assert "signature=" in signed_url
        assert audio_url in signed_url
    
    def test_generate_signed_url_with_full_url(self):
        """Test generating a signed URL with full audio URL."""
        track_id = str(uuid.uuid4())
        audio_url = "https://cdn.example.com/audio/test.mp3"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        signed_url = generate_signed_url(track_id, audio_url, expires_at)
        
        assert signed_url.startswith("https://cdn.example.com")
    
    def test_verify_valid_signature(self):
        """Test verifying a valid signature."""
        track_id = str(uuid.uuid4())
        audio_url = "audio/test.mp3"
        expires_timestamp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        
        # Generate signature
        import hmac
        import hashlib
        import base64
        CDN_SIGNING_KEY = "cdn-signing-key-change-in-production"
        payload = f"{track_id}:{audio_url}:{expires_timestamp}"
        signature = hmac.new(
            CDN_SIGNING_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        
        is_valid = verify_signed_url(track_id, audio_url, expires_timestamp, signature_b64)
        assert is_valid is True
    
    def test_verify_expired_signature(self):
        """Test verifying an expired signature."""
        track_id = str(uuid.uuid4())
        audio_url = "audio/test.mp3"
        expires_timestamp = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        
        is_valid = verify_signed_url(track_id, audio_url, expires_timestamp, "any-signature")
        assert is_valid is False
    
    def test_verify_invalid_signature(self):
        """Test verifying an invalid signature."""
        track_id = str(uuid.uuid4())
        audio_url = "audio/test.mp3"
        expires_timestamp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        
        is_valid = verify_signed_url(track_id, audio_url, expires_timestamp, "invalid-signature")
        assert is_valid is False


class TestVerifySignatureEndpoint:
    """Tests for signature verification endpoint."""
    
    def test_verify_signature_valid(self):
        """Test verifying a valid signature via endpoint."""
        track_id = str(uuid.uuid4())
        audio_url = "audio/test.mp3"
        expires_timestamp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        
        # Generate valid signature
        import hmac
        import hashlib
        import base64
        CDN_SIGNING_KEY = "cdn-signing-key-change-in-production"
        payload = f"{track_id}:{audio_url}:{expires_timestamp}"
        signature = hmac.new(
            CDN_SIGNING_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        
        response = client.post(
            "/verify-signature",
            params={
                "track_id": track_id,
                "audio_url": audio_url,
                "expires": expires_timestamp,
                "signature": signature_b64
            }
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True
    
    def test_verify_signature_invalid(self):
        """Test verifying an invalid signature via endpoint."""
        response = client.post(
            "/verify-signature",
            params={
                "track_id": str(uuid.uuid4()),
                "audio_url": "audio/test.mp3",
                "expires": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                "signature": "invalid-signature"
            }
        )
        assert response.status_code == 403
    
    def test_verify_signature_expired(self):
        """Test verifying an expired signature via endpoint."""
        response = client.post(
            "/verify-signature",
            params={
                "track_id": str(uuid.uuid4()),
                "audio_url": "audio/test.mp3",
                "expires": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
                "signature": "any-signature"
            }
        )
        assert response.status_code == 403
