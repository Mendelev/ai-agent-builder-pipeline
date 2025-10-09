#!/bin/bash

# Celery Worker Startup Script for R3 (Requirement Refinement)

echo "=========================================="
echo "  Starting Celery Worker (q_analyst)"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment is activated, if not try to activate it
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f "$SCRIPT_DIR/venv/bin/activate" ]]; then
        echo "ℹ️  Activating virtual environment..."
        source "$SCRIPT_DIR/venv/bin/activate"
    else
        echo "⚠️  Virtual environment not found!"
        echo "   Create it first: python3 -m venv venv"
        echo "   Then activate: source venv/bin/activate"
        exit 1
    fi
fi

# Check if Redis is running (works with Docker or local)
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

if command -v redis-cli &> /dev/null; then
    # Use redis-cli if available
    if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
        echo "⚠️  Redis is not running on $REDIS_HOST:$REDIS_PORT!"
        echo "   Start Redis: redis-server"
        echo "   Or with Docker: docker run -d -p 6379:6379 redis:alpine"
        echo "   Or check docker-compose: docker-compose up -d"
        exit 1
    fi
else
    # Fallback: Check if port is open using Python (always available in venv)
    if ! python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('$REDIS_HOST', $REDIS_PORT)); s.close()" 2>/dev/null; then
        echo "⚠️  Cannot connect to Redis on $REDIS_HOST:$REDIS_PORT!"
        echo "   Make sure Redis is running:"
        echo "   - Docker: docker-compose up -d"
        echo "   - Or: docker run -d -p 6379:6379 redis:alpine"
        exit 1
    fi
fi

echo "✓ Virtual environment: $VIRTUAL_ENV"
echo "✓ Redis is accessible on $REDIS_HOST:$REDIS_PORT"
echo ""

# Worker configuration
QUEUE="q_analyst"
CONCURRENCY=2
LOGLEVEL="info"

echo "Configuration:"
echo "  Queue: $QUEUE"
echo "  Concurrency: $CONCURRENCY"
echo "  Log Level: $LOGLEVEL"
echo ""

# Start worker
echo "Starting worker..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Press Ctrl+C to stop worker gracefully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

celery -A app.celery_app worker \
    --queues="$QUEUE" \
    --concurrency="$CONCURRENCY" \
    --loglevel="$LOGLEVEL"
