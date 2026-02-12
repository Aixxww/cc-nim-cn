#!/bin/bash
# 开发环境启动 - 终端保持在前台运行

echo "🚀 开发环境启动"
echo "=" * 50

# 加载环境变量
if [ -f .env ]; then
    source .env
    echo "✅ 已加载环境变量"
fi

# 激活虚拟环境
if [ -d .venv ]; then
    source .venv/bin/activate
    echo "✅ 已激活虚拟环境"
fi

# 检查依赖
echo "📦 检查依赖..."
python -c "import aiohttp; print('✅ aiohttp 正常')"
python -c "import messaging.telegram_http_client; print('✅ 自定义 HTTP 客户端正常')"

# 启动应用
echo ""
echo "🎯 启动 Bot..."
echo "查看实时日志: tail -f server.log"
echo "停止: Ctrl+C"
echo ""

python api/app.py
