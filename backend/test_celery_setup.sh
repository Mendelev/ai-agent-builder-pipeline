#!/bin/bash

# Quick test script for Celery worker connectivity

echo "🔍 Testing Celery Worker Prerequisites..."
echo ""

# 1. Check Python/venv
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✓ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  Virtual environment not active"
    if [[ -f "venv/bin/activate" ]]; then
        echo "   To activate: source venv/bin/activate"
    fi
fi

# 2. Check Redis connection
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo ""
echo "🔍 Testing Redis connection ($REDIS_HOST:$REDIS_PORT)..."

if command -v redis-cli &> /dev/null; then
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
        echo "✓ Redis is accessible (via redis-cli)"
    else
        echo "✗ Redis not accessible via redis-cli"
    fi
else
    echo "ℹ️  redis-cli not installed (not required for Celery)"
fi

# Test via Python (more reliable)
if python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('$REDIS_HOST', $REDIS_PORT)); s.close()" 2>/dev/null; then
    echo "✓ Redis port $REDIS_PORT is accessible"
else
    echo "✗ Cannot connect to Redis on $REDIS_HOST:$REDIS_PORT"
    exit 1
fi

# 3. Check Celery installation
echo ""
echo "🔍 Testing Celery installation..."
if python3 -c "import celery" 2>/dev/null; then
    CELERY_VERSION=$(python3 -c "import celery; print(celery.__version__)" 2>/dev/null)
    echo "✓ Celery installed: v$CELERY_VERSION"
else
    echo "✗ Celery not installed"
    echo "   Install: pip install -r requirements.txt"
    exit 1
fi

# 4. Check app.celery_app module
echo ""
echo "🔍 Testing Celery app import..."
if python3 -c "from app.celery_app import celery_app; print('OK')" 2>/dev/null; then
    echo "✓ Celery app imports successfully"
else
    echo "✗ Cannot import app.celery_app"
    echo "   Check if app/__init__.py exists"
    exit 1
fi

# 5. Check if Celery can connect to broker
echo ""
echo "🔍 Testing Celery broker connection..."
BROKER_TEST=$(python3 -c "
from app.celery_app import celery_app
try:
    celery_app.connection().ensure_connection(max_retries=1)
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if [[ "$BROKER_TEST" == "OK" ]]; then
    echo "✓ Celery can connect to Redis broker"
else
    echo "✗ Celery cannot connect to broker:"
    echo "   $BROKER_TEST"
    echo ""
    echo "   Check your CELERY_BROKER_URL in .env"
    exit 1
fi

# 6. List registered tasks
echo ""
echo "🔍 Registered Celery tasks..."
python3 -c "
from app.celery_app import celery_app
tasks = sorted(celery_app.tasks.keys())
for task in tasks:
    if not task.startswith('celery.'):
        print(f'  ✓ {task}')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ All checks passed! Ready to start worker."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Run: ./start_worker.sh"
