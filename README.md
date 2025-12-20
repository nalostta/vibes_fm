# VIBES.FM - Music Streaming Platform

A microservices-based music streaming platform built with FastAPI, React, and modern DevOps practices. This project implements a scalable architecture for music discovery, streaming, and personalization.

## Table of Contents

- [Introduction](#introduction)
- [Architecture Overview](#architecture-overview)
- [Implemented Features](#implemented-features)
- [Testing Status](#testing-status)
- [Getting Started](#getting-started)
- [Testing Instructions](#testing-instructions)
- [Future Plans](#future-plans)

## Introduction

VIBES.FM is a personal music streaming platform designed for discovering and enjoying music. The platform is built using a microservices architecture, enabling independent scaling and deployment of each service. The backend services are implemented in Python using FastAPI, while the frontend is a React application with TypeScript and Tailwind CSS.

The project follows a phased development approach, with each phase building upon the previous one to create a complete music streaming experience. The current implementation includes user authentication, music catalog management, streaming capabilities, playlist management, and playback history tracking.

## Architecture Overview

The platform consists of the following components:

### Backend Services

The backend is composed of six independent microservices, each responsible for a specific domain:

**Auth Service** handles user authentication including registration, login, JWT token generation, validation, and refresh. It uses bcrypt for password hashing and python-jose for JWT operations.

**User Service** manages user profiles, including CRUD operations for user data, password changes, and premium status management. It integrates with the Auth Service for authentication.

**Catalog Service** maintains the music catalog with support for artists, albums, tracks, and genres. It provides search functionality across all content types and manages relationships between entities.

**Streaming Service** handles playback authorization and generates signed CDN URLs using HMAC-SHA256 for secure streaming. It manages playback sessions and provides signature verification for CDN edge servers.

**Library & Playlist Service** enables users to create and manage playlists with privacy controls, add tracks to playlists with custom ordering, and maintain a personal library of saved tracks.

**Playback History Service** records high-volume playback events with duration and source tracking, provides paginated history retrieval with filtering options, and generates listening statistics including total plays, duration, and top tracks.

### Frontend Application

The frontend is a React application built with TypeScript and Vite, featuring a Spotify-like user interface with Tailwind CSS styling. It includes pages for Home, Search, Library, Playlist, Album, Artist, Login, and Register. The application uses React Router for navigation and React Context for state management (Auth and Player contexts).

### Infrastructure

The infrastructure layer includes Docker Compose for local development and deployment, Nginx as an API gateway for routing requests to appropriate services, and a monitoring stack with Prometheus for metrics, Grafana for visualization, Loki for log aggregation, and Promtail for log shipping.

### CI/CD Pipeline

GitHub Actions workflows automate testing for all backend services, frontend build verification, Docker image building, and deployment automation with health checks.

## Implemented Features

### Phase 1.1 - Core Data Models

Database schemas for all microservices have been implemented, including User model with authentication and profile fields, Catalog models (Artist, Album, Track, Genre) with relationships, Library models (Playlist, PlaylistTrack, UserLibrary), and PlaybackHistory model optimized for high-volume writes. The implementation includes Docker Compose configuration for local development, shared database configuration module, and comprehensive unit tests for all models.

### Phase 2 - Authentication & User Management

The Auth Service provides registration with email/username validation, login with JWT token generation, token validation and refresh endpoints, and bcrypt password hashing. The User Service offers profile CRUD operations, password change functionality, premium status management, and paginated user listing for admin purposes.

### Phase 3 - Content & Streaming

The Catalog Service includes CRUD endpoints for artists, genres, albums, and tracks, search functionality across all content types, track-artist and track-genre relationship management, and album-track associations. The Streaming Service provides playback authorization with signed CDN URLs, HMAC-SHA256 signature generation, playback session management (start/end tracking), and signature verification endpoint for CDN edge servers.

### Phase 4 - Personalization & Library

The Library & Playlist Service enables playlist CRUD with public/private visibility, track management within playlists with ordering, user library (saved tracks) management, and collaborative playlist support. The Playback History Service records playback events with metadata, provides paginated history with date range filters, and generates listening statistics and analytics.

### Phase 5 - Frontend Application

The React frontend features a responsive Spotify-like UI with dark theme, authentication flow with protected routes, music browsing (Home, Search, Albums, Artists), playlist management interface, audio player with queue management, and integration with all backend services via API layer.

### Phase 6 - CI/CD & Observability

The CI/CD pipeline includes GitHub Actions workflow for automated testing, frontend build verification, Docker image building, and deployment script for Raspberry Pi. The observability stack provides Prometheus metrics collection, Grafana dashboards with pre-configured visualizations, Loki log aggregation, and Promtail log shipping from Docker containers.

## Testing Status

The project includes comprehensive unit tests for all backend services. Below is the testing status for each module:

### Auth Service
- **Test File:** `services/auth-service/tests/test_auth_service.py`
- **Test Count:** 17 tests
- **Status:** All tests passing
- **Coverage:** Password hashing, JWT token operations, registration, login, token validation

### User Service
- **Test Files:** `services/user-service/tests/test_user_model.py`, `services/user-service/tests/test_user_service.py`
- **Test Count:** 30 tests (10 model + 20 service)
- **Status:** Tests defined, collection issues when running with other services (SQLAlchemy metadata conflicts)
- **Coverage:** User model operations, profile CRUD, authorization, pagination

### Catalog Service
- **Test Files:** `services/catalog-service/tests/test_catalog_model.py`, `services/catalog-service/tests/test_catalog_service.py`
- **Test Count:** 51 tests (15 model + 36 service)
- **Status:** Tests defined, collection issues when running with other services (SQLAlchemy metadata conflicts)
- **Coverage:** Artist, Album, Track, Genre CRUD, search functionality, relationships

### Streaming Service
- **Test File:** `services/streaming-service/tests/test_streaming_service.py`
- **Test Count:** 30 tests
- **Status:** All tests passing
- **Coverage:** Signed URL generation, signature verification, playback sessions

### Library & Playlist Service
- **Test Files:** `services/library-playlist-service/tests/test_playlist_model.py`, `services/library-playlist-service/tests/test_library_playlist_service.py`
- **Test Count:** 62 tests (18 model + 44 service)
- **Status:** Tests defined, collection issues when running with other services (SQLAlchemy metadata conflicts)
- **Coverage:** Playlist CRUD, track management, user library, privacy controls

### Playback History Service
- **Test Files:** `services/playback-history-service/tests/test_playback_history_model.py`, `services/playback-history-service/tests/test_playback_history_service.py`
- **Test Count:** 48 tests (15 model + 33 service)
- **Status:** Tests defined, collection issues when running with other services (SQLAlchemy metadata conflicts)
- **Coverage:** Playback event recording, history retrieval, statistics

### Total Test Count: 238 tests

**Note:** Some tests experience SQLAlchemy metadata conflicts when run together due to shared Base class definitions. Tests pass when run individually per service. This is a known issue with the test configuration that can be resolved by isolating test runs or refactoring the shared database configuration.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL (for production) or SQLite (for development/testing)

### Installation

Clone the repository and checkout the devin branch:

```bash
git clone https://github.com/nalostta/vibes_fm.git
cd vibes_fm
git checkout devin
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

### Running with Docker Compose

Start all services:

```bash
docker-compose up -d
```

Start the monitoring stack:

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Running Services Individually

Each service can be run independently for development:

```bash
cd services/auth-service
uvicorn app.main:app --reload --port 8001
```

Run the frontend development server:

```bash
cd frontend
npm run dev
```

## Testing Instructions

### Running All Tests

To run all tests (note: some tests may have collection conflicts):

```bash
pytest -v
```

### Running Tests Per Service

For reliable test execution, run tests for each service individually:

**Auth Service:**
```bash
cd services/auth-service
python -m pytest tests/ -v
```

**User Service:**
```bash
cd services/user-service
python -m pytest tests/ -v
```

**Catalog Service:**
```bash
cd services/catalog-service
python -m pytest tests/ -v
```

**Streaming Service:**
```bash
cd services/streaming-service
python -m pytest tests/ -v
```

**Library & Playlist Service:**
```bash
cd services/library-playlist-service
python -m pytest tests/ -v
```

**Playback History Service:**
```bash
cd services/playback-history-service
python -m pytest tests/ -v
```

### Running Tests with Coverage

```bash
pytest --cov=services --cov-report=html
```

### Frontend Testing

```bash
cd frontend
npm run test
```

## Future Plans

The following features and improvements are planned for future development phases:

### Phase 7 - Enhanced Search & Discovery
- Implement full-text search with Elasticsearch
- Add recommendation engine based on listening history
- Create personalized playlists (Daily Mix, Discover Weekly)
- Implement genre-based radio stations

### Phase 8 - Social Features
- User following/followers system
- Collaborative playlists with real-time updates
- Activity feed showing friends' listening activity
- Share tracks/playlists to social media

### Phase 9 - Mobile Applications
- React Native mobile app for iOS and Android
- Offline playback support
- Background audio playback
- Push notifications for new releases

### Phase 10 - Advanced Audio Features
- Audio quality selection (128kbps, 256kbps, 320kbps, lossless)
- Crossfade between tracks
- Equalizer settings
- Lyrics display with sync

### Phase 11 - Analytics & Insights
- Artist analytics dashboard
- User listening insights (Wrapped-style)
- Admin dashboard for platform metrics
- A/B testing framework

### Phase 12 - Performance & Scalability
- Implement Redis caching layer
- Add CDN integration for audio delivery
- Database sharding for high-volume tables
- Kubernetes deployment configuration

### Technical Debt & Improvements
- Resolve SQLAlchemy metadata conflicts in test suite
- Add integration tests for service-to-service communication
- Implement API versioning
- Add OpenAPI documentation for all endpoints
- Set up end-to-end testing with Playwright

## License

This project is proprietary software. All rights reserved.

## Contributing

Contributions are welcome. Please ensure all tests pass before submitting a pull request.

## Contact

For questions or support, please open an issue on GitHub.
