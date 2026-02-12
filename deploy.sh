#!/bin/bash
# 部署 Telegram Bot

echo "🚀 开始部署 Telegram Bot"
echo "============================"

# 加载环境变量
if [ -f .env ]; then
    source .env
    echo "✅ 环境变量已加载"
    echo "   Bot: $(echo $TELEGRAM_BOT_TOKEN | cut -c1-15)..."
    if [ -n "$HTTPS_PROXY" ]; then
        echo "   Proxy: $HTTPS_PROXY"
    fi
else
    echo "❌ .env 文件未找到"
    exit 1
fi

# 启动 Bot
echo ""
echo "📡 启动 Bot 服务..."
echo "   运行命令: .venv/bin/python api/app.py"

nohup .venv/bin/python api/app.py > server.log 2>&1 &
PID=$!

echo ""
echo "✅ Bot 已启动!"
echo "   PID: $PID"
echo "   日志文件: $(pwd)/server.log"
echo ""
echo "📊 监控 Bot:"
echo "   查看日志: tail -f server.log"
echo "   停止 Bot: kill $PID"
echo ""
echo "📝 验证 Bot 是否正常工作:"
echo "   1. tail -f server.log | grep -E '(telegram|NonPooling| Custom)'"
echo "   2. 在 Telegram 中给 Bot 发送消息"
echo "   3. 检查日志是否显示 Custom HTTP client 消息"