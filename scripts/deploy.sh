#!/bin/bash
set -e

echo "=== Vibes FM Deployment Script ==="
echo "Deploying to Raspberry Pi..."

# Configuration
DEPLOY_HOST="${DEPLOY_HOST:-raspberrypi.local}"
DEPLOY_USER="${DEPLOY_USER:-pi}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/vibes-fm}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if SSH is available
check_ssh() {
    print_status "Checking SSH connection to $DEPLOY_HOST..."
    if ssh -q -o ConnectTimeout=5 "$DEPLOY_USER@$DEPLOY_HOST" exit; then
        print_status "SSH connection successful"
    else
        print_error "Cannot connect to $DEPLOY_HOST"
        exit 1
    fi
}

# Sync files to remote
sync_files() {
    print_status "Syncing files to $DEPLOY_HOST:$DEPLOY_PATH..."
    rsync -avz --delete \
        --exclude '.git' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude 'node_modules' \
        --exclude '.pytest_cache' \
        --exclude 'dist' \
        --exclude '.env.local' \
        ./ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/"
}

# Deploy with Docker Compose
deploy_docker() {
    print_status "Deploying with Docker Compose..."
    ssh "$DEPLOY_USER@$DEPLOY_HOST" << EOF
        cd $DEPLOY_PATH
        docker compose pull
        docker compose build
        docker compose up -d
        docker compose ps
EOF
}

# Health check
health_check() {
    print_status "Running health checks..."
    sleep 10
    
    services=("auth-service:8002" "user-service:8001" "catalog-service:8003" "streaming-service:8004" "library-playlist-service:8005" "playback-history-service:8006")
    
    for service in "${services[@]}"; do
        name="${service%%:*}"
        port="${service##*:}"
        if curl -sf "http://$DEPLOY_HOST:$port/health" > /dev/null 2>&1; then
            print_status "$name is healthy"
        else
            print_warning "$name health check failed"
        fi
    done
}

# Main deployment flow
main() {
    print_status "Starting deployment..."
    
    check_ssh
    sync_files
    deploy_docker
    health_check
    
    print_status "Deployment complete!"
    echo ""
    echo "Access the application at: http://$DEPLOY_HOST"
}

# Run main function
main "$@"
