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
            echo ""
            echo "API 状态:"
            if curl -s http://localhost:8082/health > /dev/null 2>&1; then
                echo "✅ 健康: $(curl -s http://localhost:8082/health)"
            else
                echo "❌ API 无响应"
            fi
        else
            echo "❌ 服务未运行"
        fi
        ;;
    logs)
        tail -f cc-nim.log 2>/dev/null || echo "日志文件不存在"
        ;;
    install)
        ./install_and_start.sh
        ;;
    *)
        echo "用法: ./manage.sh {start|stop|restart|status|logs|install}"
        echo ""
        echo "命令说明:"
        echo "  start      - 启动服务"
        echo "  stop       - 停止服务"
        echo "  restart    - 重启服务"
        echo "  status     - 查看状态"
        echo "  logs       - 查看日志"
        echo "  install    - 一键部署（含开机自启）"
        echo ""
        echo "示例:"
        echo "  ./manage.sh install    # 首次部署或重装"
        echo "  ./manage.sh status     # 查看运行状态"
        echo "  ./manage.sh logs       # 查看实时日志"
        ;;
esac
