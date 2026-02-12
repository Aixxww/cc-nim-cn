#!/bin/bash
# cc-nim 服务启动脚本
# 用途: 启动 cc-nim API 代理 + Telegram Bot

cd "$(dirname "$0")"

echo "🚀 启动 cc-nim 服务..."
echo "======================================"

# 加载环境变量
if [ -f .env ]; then
    set -a && source .env && set +a
    echo "✅ 环境变量已加载"
else
    echo "❌ 错误: 找不到 .env 文件"
    exit 1
fi

# 检查端口占用
PORT=8082
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 警告: 端口 $PORT 已被占用"
    echo "请先运行: ./manage.sh stop"
    exit 1
fi

# 启动服务（后台）
echo ""
echo "📋 配置信息:"
echo "  端口: $PORT"
echo "  模型: ${MODEL:-moonshotai/kimi-k2-thinking}"
echo "  Telegram Bot: ${TELEGRAM_BOT_TOKEN:+已配置}"
echo "  代理: ${HTTPS_PROXY:-未配置}"
echo ""
echo "🎯 启动服务（后台）..."

nohup .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info >> service.log 2>&1 &
PID=$!
echo $PID > service.pid
sleep 2

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ 服务已启动 (PID: $PID)"
    echo "   日志: tail -f service.log"
else
    echo "❌ 服务启动失败，查看日志:"
    cat service.log 2>/dev/null
    exit 1
fi
