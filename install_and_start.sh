#!/bin/bash
# cc-nim 后台服务安装和启动脚本

cd "$(dirname "$0")"

echo "======================================"
echo "  cc-nim 后台服务安装和启动"
echo "======================================"
echo ""

# 1. 强制停止所有运行中的服务
echo "📋 第一步：强制停止旧服务..."
pkill -9 -f "uvicorn.*server:app" 2>/dev/null
pkill -9 -f "uv run uvicorn" 2>/dev/null

# 强制释放端口
sleep 1
if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "  发现端口被占用，强制释放..."
    fuser -k 8082/tcp 2>/dev/null || true
fi

sleep 2
echo "✅ 旧服务已强制停止"
echo ""

# 2. 清理旧日志
rm -f cc-nim.log launchd.log launchd.err

# 3. 启动后台服务
echo "📋 第二步：启动后台服务..."
nohup .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8082 --log-level info >> cc-nim.log 2>&1 &
CC_NIM_PID=$!
echo $CC_NIM_PID > cc-nim.pid
sleep 4
echo "✅ 后台服务已启动 (PID: $CC_NIM_PID)"
echo ""

# 4. 验证服务
echo "📋 第三步：验证服务..."
if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ 服务正在监听端口 8082"
    echo ""
    echo "📊 服务详情:"
    lsof -Pi :8082 -sTCP:LISTEN
    echo ""
else
    echo "❌ 服务启动失败，检查日志:"
    echo "---"
    cat cc-nim.log
    echo "---"
    exit 1
fi

# 5. 检查 Bot 状态
if grep -q "Telegram platform started" cc-nim.log 2>/dev/null; then
    echo "✅ Telegram Bot 已启动"
else
    echo "⚠️ 正在启动 Telegram Bot..."
    sleep 2
    if grep -q "Telegram platform started" cc-nim.log 2>/dev/null; then
        echo "✅ Telegram Bot 已启动"
    fi
fi
echo ""

# 6. 安装 LaunchAgent（开机自启）
echo "📋 第四步：配置开机自启..."
if [ -f "com.cc-nim.plist" ]; then
    mkdir -p ~/Library/LaunchAgents
    cp com.cc-nim.plist ~/Library/LaunchAgents/

    # 检查服务是否已加载
    if launchctl list 2>/dev/null | grep -q "com.cc-nim"; then
        echo "  卸载旧服务..."
        launchctl unload ~/Library/LaunchAgents/com.cc-nim.plist 2>/dev/null
        sleep 1
    fi

    # 加载服务
    launchctl load ~/Library/LaunchAgents/com.cc-nim.plist 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ 开机自启服务已配置"
        echo ""
        echo "  后续可用命令:"
        echo "    启动: launchctl start com.cc-nim"
        echo "    停止: launchctl stop com.cc-nim"
        echo "    卸载: launchctl unload ~/Library/LaunchAgents/com.cc-nim.plist"
    else
        echo "⚠️ LaunchAgent 加载失败（可能权限问题）"
    fi
else
    echo "⚠️ 未找到 com.cc-nim.plist，跳过开机自启配置"
fi
echo ""

# 7. 完成
echo "======================================"
echo "  ✅ cc-nim 服务部署完成！"
echo "======================================"
echo ""
echo "📋 服务信息:"
echo "  - PID: $CC_NIM_PID"
echo "  - 端口: 8082"
echo "  - 日志: cc-nim.log"
echo ""
echo "🔧 管理命令:"
echo ""
echo "1. 查看日志:"
echo "   tail -f cc-nim.log"
echo ""
echo "2. 查看服务状态:"
echo "   ./manage.sh status"
echo ""
echo "3. 重启服务:"
echo "   ./manage.sh restart"
echo ""
echo "4. 停止服务:"
echo "   ./manage.sh stop"
echo ""
echo "5. 关机/重启后自动启动"
echo "   (LaunchAgent 已配置)"
echo ""
