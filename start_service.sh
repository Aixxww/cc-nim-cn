#!/bin/bash
# cc-nim 服务启动脚本
# 用途: 启动 cc-nim API 代理 + Telegram Bot

cd "$(dirname "$0")"

echo "🚀 启动 cc-nim 服务..."
echo "======================================"

# 激活虚拟环境
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 错误: 找不到 .venv，请先运行: uv venv"
    exit 1
fi

# 检查环境变量
if [ ! -f .env ]; then
    echo "❌ 错误: 找不到 .env 文件"
    exit 1
fi

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

# 检查必要的配置
if [ -z "$NVIDIA_NIM_API_KEY" ]; then
    echo "❌ 错误: NVIDIA_NIM_API_KEY 未配置"
    exit 1
fi

# 检查端口占用
PORT=8082
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 警告: 端口 $PORT 已被占用"
    echo "请先运行: ./stop_service.sh"
    exit 1
fi

# 启动服务
echo ""
echo "📋 配置信息:"
echo "  端口: $PORT"
echo "  模型: ${MODEL:-moonshotai/kimi-k2-thinking}"
echo "  Telegram Bot: ${TELEGRAM_BOT_TOKEN:+已配置}"
echo "  代理: ${HTTPS_PROXY:-未配置}"
echo ""
echo "🎯 启动服务..."

# 使用 uv 启动（确保在项目中运行）
if command -v uv &> /dev/null; then
    uv run uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info
else
    .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info
fi
