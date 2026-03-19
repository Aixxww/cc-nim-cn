#!/bin/bash
# Claude NIM Bridge - Service Management Script
# Supports: macOS (LaunchAgent) and Linux (systemd)

cd "$(dirname "$0")"

# Project info
PROJECT_NAME="claude-nim-bridge"
PORT=8082
PYTHON_BIN=".venv/bin/python"
PID_FILE="service.pid"
LOG_FILE="service.log"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    LAUNCH_AGENT="com.claude-nim-bridge"
    LAUNCH_AGENT_PATH="$HOME/Library/LaunchAgents/$LAUNCH_AGENT.plist"
    SYSTEMCTL_CMD=""
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    SERVICE_NAME="claude-nim-bridge"
    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
    SYSTEMCTL_CMD="systemctl"
else
    OS="unknown"
    echo "Warning: Unknown OS type, using basic commands"
fi

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check service running
is_running() {
    if [ "$OS" == "linux" ] && [ -n "$SYSTEMCTL_CMD" ]; then
        $SYSTEMCTL_CMD is-active --quiet "$SERVICE_NAME"
        return $?
    else
        ps aux | grep "uvicorn.*server:app" | grep -v grep > /dev/null
        return $?
    fi
}

start_service() {
    if is_running; then
        print_warning "Service is already running"
        return 0
    fi

    print_info "Starting $PROJECT_NAME..."

    if [ "$OS" == "linux" ] && [ -n "$SYSTEMCTL_CMD" ]; then
        # Use systemd on Linux
        $SYSTEMCTL_CMD start "$SERVICE_NAME"
        if [ $? -eq 0 ]; then
            print_success "Service started via systemd"
        else
            print_error "Failed to start service"
            return 1
        fi
    else
        # Start manually (macOS or fallback)
        nohup .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info > $LOG_FILE 2>&1 &
        PID=$!
        echo $PID > $PID_FILE
        sleep 2

        if ps -p $PID > /dev/null 2>&1; then
            print_success "Service started (PID: $PID)"
        else
            print_error "Service failed to start"
            return 1
        fi
    fi

    # Verify service is responding
    sleep 2
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        print_success "API is responding"
    else
        print_warning "API not responding yet, check logs"
    fi
}

stop_service() {
    if ! is_running; then
        print_info "Service is not running"
        return 0
    fi

    print_info "Stopping $PROJECT_NAME..."

    if [ "$OS" == "linux" ] && [ -n "$SYSTEMCTL_CMD" ]; then
        # Use systemd on Linux
        $SYSTEMCTL_CMD stop "$SERVICE_NAME"
        print_success "Service stopped via systemd"
    else
        # Stop manually (macOS or fallback)
        PIDS=$(ps aux | grep "uvicorn.*server:app" | grep -v grep | awk '{print $2}')
        if [ -n "$PIDS" ]; then
            kill $PIDS 2>/dev/null
            sleep 2

            # Force kill if still running
            REMAINING=$(ps aux | grep "uvicorn.*server:app" | grep -v grep | awk '{print $2}')
            if [ -n "$REMAINING" ]; then
                kill -9 $REMAINING 2>/dev/null
            fi
            print_success "Service stopped"
        fi
    fi

    rm -f $PID_FILE 2>/dev/null
}

restart_service() {
    print_info "Restarting $PROJECT_NAME..."
    stop_service
    sleep 1
    start_service
}

show_status() {
    echo ""
    echo "=============================================="
    echo "  $PROJECT_NAME - Status"
    echo "=================================================="
    echo "  OS: $OS"
    echo "  Port: $PORT"
    echo "=================================================="
    echo ""

    if [ "$OS" == "linux" ] && [ -n "$SYSTEMCTL_CMD" ]; then
        # Use systemd status
        $SYSTEMCTL_CMD status "$SERVICE_NAME" --no-pager -l
    else
        # Manual status check
        PIDS=$(ps aux | grep "uvicorn.*server:app" | grep -v grep)
        if [ -n "$PIDS" ]; then
            print_success "Service is running:"
            echo "$PIDS"
            echo ""

            if [ -f "$PID_FILE" ]; then
                echo "  PID File: $(cat $PID_FILE)"
            fi

            if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo ""
                print_success "Port $PORT is listening:"
                lsof -Pi :$PORT -sTCP:LISTEN
            else
                echo ""
                print_warning "Port $PORT is not listening"
            fi

            echo ""
            # API health check
            if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
                print_success "API Health: $(curl -s http://localhost:$PORT/health)"
            else
                print_warning "API is not responding"
            fi

            if [ -f "$LAUNCH_AGENT_PATH" ]; then
                echo ""
                print_info "LaunchAgent: Configured at $LAUNCH_AGENT_PATH"
            fi
        else
            print_error "Service is not running"
            echo ""
            if [ -f "$PID_FILE" ]; then
                print_warning "PID file exists but process not found ($(cat $PID_FILE))"
            fi
        fi
    fi
    echo ""
}

show_logs() {
    LOG_PATH="$LOG_FILE"

    if [ "$OS" == "linux" ] && [ -n "$SYSTEMCTL_CMD" ]; then
        # Try systemd journal
        if journalctl -u "$SERVICE_NAME" -n 10 --no-pager > /dev/null 2>&1; then
            echo "📋 Following systemd logs (Ctrl+C to exit):"
            journalctl -u "$SERVICE_NAME" -f
            return 0
        fi
    fi

    # Fallback to log file
    if [ -f "$LOG_PATH" ]; then
        echo "📋 Following log file (Ctrl+C to exit):"
        tail -f "$LOG_PATH"
    else
        print_error "Log file not found: $LOG_PATH"
    fi
}

install_service() {
    print_info "Installing $PROJECT_NAME service..."

    if [ "$OS" == "macos" ]; then
        # macOS: Use LaunchAgent
        print_info "Configuring macOS LaunchAgent..."

        PROJECT_DIR=$(pwd)
        CURRENT_USER=$(whoami)

        if [ ! -f ".env" ]; then
            print_warning ".env file not found, copying from example..."
            cp .env.example .env
            print_warning "Please edit .env with your NVIDIA_NIM_API_KEY"
        fi

        # Create LaunchAgent from example
        if [ -f "com.claude-nim-bridge.plist.example" ]; then
            mkdir -p "$HOME/Library/LaunchAgents"
            sed "s|/Users/YOUR_USERNAME/claude-nim-bridge|$PROJECT_DIR|g" \
                com.claude-nim-bridge.plist.example | \
            sed "s|/Users/YOUR_USERNAME/.claude-nim-bridge|$PROJECT_DIR|g" | \
            sed "s|YOUR_USERNAME|$CURRENT_USER|g" > "$LAUNCH_AGENT_PATH"

            # Unload old if exists
            launchctl unload "$LAUNCH_AGENT_PATH" 2>/dev/null || true
            sleep 1

            # Load new
            if launchctl load "$LAUNCH_AGENT_PATH" 2>/dev/null; then
                print_success "LaunchAgent installed: $LAUNCH_AGENT_PATH"
            else
                print_error "Failed to load LaunchAgent"
                return 1
            fi
        fi

        # Start the service
        print_info "Starting service..."
        launchctl start "$LAUNCH_AGENT" 2>/dev/null || start_service

    elif [ "$OS" == "linux" ]; then
        # Linux: Use systemd
        print_info "Configuring systemd service..."

        PROJECT_DIR=$(pwd)
        CURRENT_USER=$(whoami)

        if [ -f ".env" ]; then
            print_info "Loading environment from .env file..."
            set -a && source .env && set +a
        fi

        # Read service file
        SERVICE_FILE_CONTENT=$(cat "$SERVICE_NAME.service.example")

        # Create the service file with real paths
        cat | sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Claude NIM Bridge - Anthropic to NVIDIA NIM Proxy
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info
Restart=on-failure
RestartSec=5
StartLimitInterval=0

# Resource limits
LimitNOFILE=65536

# Logging
StandardOutput=append:$PROJECT_DIR/systemd-output.log
StandardError=append:$PROJECT_DIR/systemd-error.log
SyslogIdentifier=claude-nim-bridge

# Environment
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="NVIDIA_NIM_API_KEY=${NVIDIA_NIM_API_KEY:-}"
Environment="MODEL=${MODEL:-moonshotai/kimi-k2-thinking}"
Environment="NVIDIA_NIM_RATE_LIMIT=${NVIDIA_NIM_RATE_LIMIT:-40}"

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd
        sudo systemctl daemon-reload

        # Enable service
        if sudo systemctl enable "$SERVICE_NAME" 2>/dev/null; then
            print_success "Service enabled for auto-start on boot"
        fi

        # Start service
        if sudo systemctl start "$SERVICE_NAME"; then
            print_success "Service started"
        else
            print_error "Failed to start service"
            return 1
        fi

    else
        print_error "Unsupported OS for auto-install: $OS"
        return 1
    fi

    # Wait and verify
    sleep 3
    show_status
}

uninstall_service() {
    print_info "Uninstalling $PROJECT_NAME service..."

    if [ "$OS" == "macos" ]; then
        if [ -f "$LAUNCH_AGENT_PATH" ]; then
            launchctl unload "$LAUNCH_AGENT_PATH" 2>/dev/null || true
            rm -f "$LAUNCH_AGENT_PATH"
            print_success "LaunchAgent removed"
        fi
    elif [ "$OS" == "linux" ] && [ -n "$SYSTEMCTL_CMD" ]; then
        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        sudo rm -f "$SERVICE_FILE"
        sudo systemctl daemon-reload
        print_success "Systemd service removed"
    fi

    stop_service
    print_success "Service uninstallation complete"
}

# Main command dispatcher
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    *)
        echo "Usage: ./manage.sh {start|stop|restart|status|logs|install|uninstall}"
        echo ""
        echo "Commands:"
        echo "  start      - Start service"
        echo "  stop       - Stop service"
        echo "  restart    - Restart service"
        echo "  status     - Show service status"
        echo "  logs       - Follow service logs"
        echo "  install    - Install service with auto-start"
        echo "  uninstall  - Remove service and auto-start"
        echo ""
        echo "Detected OS: $OS"
        echo ""
        echo "Platform-specific notes:"
        if [ "$OS" == "macos" ]; then
            echo "  • Uses LaunchAgent for auto-start"
            echo "  • Config file: $LAUNCH_AGENT_PATH"
        elif [ "$OS" == "linux" ]; then
            echo "  • Uses systemd for service management"
            echo "  • Config file: $SERVICE_FILE"
            echo "  • Requires sudo for install/uninstall"
        fi
        ;;
esac
