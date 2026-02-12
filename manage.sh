#!/bin/bash
# cc-nim 服务管理脚本

cd "$(dirname "$0")"

case "$1" in
    start)
        ./start_service.sh
        ;;
    stop)
        ./stop_service.sh
        ;;
    restart)
        ./stop_service.sh
        sleep 1
        ./start_service.sh
        ;;
    status)
        echo "📊 cc-nim 服务状态"
        echo "===================="
        PIDS=$(ps aux | grep "uvicorn.*server:app" | grep -v grep)
        if [ -n "$PIDS" ]; then
            echo "✅ 服务正在运行:"
            echo "$PIDS"
            echo ""
            echo "端口状态:"
            if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1; then
                lsof -Pi :8082 -sTCP:LISTEN
            else
                echo "⚠️ 端口 8082 未监听"
            fi
        else
            echo "❌ 服务未运行"
        fi
        ;;
    logs)
        tail -f server.log
        ;;
    test-bot)
        echo "🧪 测试 Telegram Bot..."
        .venv/bin/python test_telegram_bot.py
        ;;
    *)
        echo "用法: ./manage.sh {start|stop|restart|status|logs|test-bot}"
        echo ""
        echo "命令说明:"
        echo "  start      - 启动服务"
        echo "  stop       - 停止服务"
        echo "  restart    - 重启服务"
        echo "  status     - 查看状态"
        echo "  logs       - 查看日志"
        echo "  test-bot   - 测试 Telegram Bot"
        ;;
esac
