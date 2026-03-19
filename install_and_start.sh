#!/bin/bash
# Claude NIM Bridge - One-click Install and Start Script

set -e

cd "$(dirname "$0")"

PROJECT_NAME="claude-nim-bridge"
PORT=8082

echo "======================================"
echo "  Claude NIM Bridge - Install"
echo "======================================"
echo ""

# 1. Stop any existing services
echo "📋 Step 1: Stopping old services..."
for pid in $(pgrep -f "uvicorn.*server:app" 2>/dev/null); do
    kill $pid 2>/dev/null
done
sleep 2
echo "✅ Old services stopped"
echo ""

# 2. Load environment variables
if [ -f .env ]; then
    set -a && source .env && set +a
    echo "✅ Environment variables loaded"
fi
echo ""

# 3. Start background service
echo "📋 Step 2: Starting background service..."
nohup .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info > service.log 2>&1 &
SERVICE_PID=$!
echo $SERVICE_PID > service.pid
sleep 5
echo "✅ Background service started (PID: $SERVICE_PID)"
echo ""

# 4. Verify service (with retry)
echo "⏳ Waiting for service to start..."
for i in {1..10}; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo "✅ Service verification successful"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️ Service verification timeout, but may have started"
        tail -20 service.log 2>/dev/null
    fi
    sleep 1
done
echo ""

# 5. Configure auto-start (LaunchAgent)
echo "📋 Step 3: Configuring auto-start..."
CONFIG_FILE="com.claude-nim-bridge.plist"

if [ -f "$CONFIG_FILE.example" ]; then
    # Create and configure LaunchAgent
    mkdir -p ~/Library/LaunchAgents

    PROJECT_DIR=$(pwd)
    CURRENT_USER=$(whoami)

    # Copy example and replace paths
    sed "s|/Users/YOUR_USERNAME/claude-nim-bridge|$PROJECT_DIR|g" "$CONFIG_FILE.example" | \
    sed "s|/Users/YOUR_USERNAME/.claude-nim-bridge|$PROJECT_DIR|g" | \
    sed "s|YOUR_USERNAME|$CURRENT_USER|g" > ~/Library/LaunchAgents/$CONFIG_FILE

    echo "✅ LaunchAgent configured: ~/Library/LaunchAgents/$CONFIG_FILE"

    # Unload old one if exists
    launchctl unload ~/Library/LaunchAgents/$CONFIG_FILE 2>/dev/null || true
    sleep 1

    # Load new one
    if launchctl load ~/Library/LaunchAgents/$CONFIG_FILE 2>/dev/null; then
        echo "✅ Auto-start configured successfully"
        echo ""
        echo "⚠️ Note: Make sure your NVIDIA_NIM_API_KEY is set in:"
        echo "   1. ~/.claude-nim-bridge/.env (recommended)"
        echo "   2. ~/Library/LaunchAgents/$CONFIG_FILE"
    else
        echo "⚠️ LaunchAgent load failed"
    fi
else
    echo "⚠️ $CONFIG_FILE.example not found"
fi
echo ""

echo "======================================"
echo "  ✅ Installation Complete!"
echo "======================================"
echo ""
echo "📋 Service Info:"
echo "  PID: $SERVICE_PID"
echo "  Port: $PORT"
echo "  Log: service.log"
echo ""
echo "🔧 Management Commands:"
echo "  Status:  ./manage.sh status"
echo "  Logs:    ./manage.sh logs"
echo "  Restart: ./manage.sh restart"
echo "  Stop:    ./manage.sh stop"
echo ""
echo "🚀 Auto-start:"
echo "  LaunchAgent configured, will auto-start on login"
echo "  Manual: launchctl {start|stop|unload} com.claude-nim-bridge"
echo ""
echo "🔍 Test the service:"
echo "  curl http://localhost:$PORT/health"
echo ""
echo "⚙️ Configure Claude Code:"
echo "  export ANTHROPIC_AUTH_TOKEN=ccnim"
echo "  export ANTHROPIC_BASE_URL=http://localhost:$PORT"
echo "  claude"
echo ""
