#!/bin/bash
# Claude NIM Bridge - Direct Run Script

cd "$(dirname "$0")"

# Activate virtual environment
if [ -d .venv ]; then
    source .venv/bin/activate
else
    echo "❌ Error: .venv directory not found"
    echo "Please run: uv venv && uv pip install -e ."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    set -a && source .env && set +a
    echo "✅ Environment variables loaded"
else
    echo "⚠️ Warning: .env file not found"
fi

# Export proxy settings
export HTTP_PROXY
export HTTPS_PROXY

echo "🚀 Starting Claude NIM Bridge..."
echo "   Port: 8082"
echo "   Press Ctrl+C to stop"
echo ""

python3 server.py
