#!/bin/bash
# Claude NIM Bridge - Service Start Script

cd "$(dirname "$0")"

echo "🚀 Starting Claude NIM Bridge..."
echo "======================================"

# Load environment variables
if [ -f .env ]; then
    set -a && source .env && set +a
    echo "✅ Environment variables loaded"
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check port availability
PORT=8082
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ Warning: Port $PORT is already in use"
    echo "Please run: ./manage.sh stop"
    exit 1
fi

# Start service (background)
echo ""
echo "📋 Configuration:"
echo "  Port: $PORT"
echo "  Model: ${MODEL:-moonshotai/kimi-k2-thinking}"
echo "  Proxy: ${HTTPS_PROXY:-Not configured}"
echo ""
echo "🎯 Starting service (background)..."

# Export all environment variables for uvicorn
export HTTP_PROXY
export HTTPS_PROXY
export NVIDIA_NIM_API_KEY
export MODEL

nohup .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info >> service.log 2>&1 &
PID=$!
echo $PID > service.pid
sleep 2

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Service started (PID: $PID)"
    echo "   Logs: tail -f service.log"
else
    echo "❌ Service failed to start, check logs:"
    cat service.log 2>/dev/null
    exit 1
fi
