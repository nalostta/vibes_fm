# VIBES.FM Developer Tools

This directory contains development tools and utilities for the VIBES.FM project. These tools are **dev-only** and are not deployed to production.

## Developer Dashboard

A web-based dashboard for monitoring and managing development services.

### Features

- **Module Status Monitoring**: View real-time status of all configured services
- **Health Checks**: Automatic HTTP health checks for services with configured endpoints
- **Start/Stop/Restart Controls**: Manage services directly from the UI
- **Live Log Streaming**: Stream logs from any service in real-time via SSE
- **Dark Theme UI**: Modern, responsive interface with tabbed navigation

### Quick Start

```bash
# From the repository root
cd /path/to/vibes_fm

# Start all development services
docker compose -f docker-compose.dev.yml up -d

# Access the dashboard
open http://localhost:7331

# Access the Next.js app
open http://localhost:3000

# Stop all services
docker compose -f docker-compose.dev.yml down
```

### Available Services

| Service | Port | Description |
|---------|------|-------------|
| dashboard | 7331 | Developer Dashboard UI and API |
| web | 3000 | Next.js development server |

### Dashboard API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Dashboard health check |
| GET | `/api/modules` | List all modules with status |
| GET | `/api/modules/:name/status` | Get specific module status |
| POST | `/api/modules/:name/start` | Start a module |
| POST | `/api/modules/:name/stop` | Stop a module |
| POST | `/api/modules/:name/restart` | Restart a module |
| GET | `/api/modules/:name/logs` | SSE stream of module logs |

### Configuration

Modules are configured in `devtools/modules.json`. Each module entry supports:

```json
{
  "name": "service-name",
  "displayName": "Human Readable Name",
  "service": "docker-compose-service-name",
  "description": "Description of the service",
  "healthCheck": {
    "enabled": true,
    "url": "http://service:port/health",
    "interval": 5000
  },
  "ports": ["host:container"]
}
```

### Adding New Modules

1. Add the service to `docker-compose.dev.yml`
2. Add the module configuration to `devtools/modules.json`
3. Restart the dashboard to pick up changes

### Security Notes

- The dashboard binds to `127.0.0.1` by default (localhost only)
- Docker socket access is required for container management
- This is strictly dev tooling - do not expose to public networks

### Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation and execution plan.

## Directory Structure

```
devtools/
├── ARCHITECTURE.md      # Architecture and execution plan
├── README.md            # This file
├── modules.json         # Module configuration
├── web.Dockerfile       # Dockerfile for Next.js dev server
└── dashboard/
    ├── Dockerfile       # Dashboard container image
    ├── package.json     # Node.js dependencies
    ├── public/
    │   └── index.html   # Dashboard UI
    └── src/
        └── server.js    # Express backend
```
