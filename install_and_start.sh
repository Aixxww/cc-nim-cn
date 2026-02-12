#!/bin/bash
# cc-nim 后台服务安装和启动脚本

cd "$(dirname "$0")"

echo "======================================"
echo "  cc-nim 后台服务安装和启动"
echo "======================================"
echo ""

# 1. 强制停止所有运行中的服务
echo "📋 第一步：停止旧服务..."
for pid in $(pgrep -f "uvicorn.*server:app" 2>/dev/null); do
    kill $pid 2>/dev/null
done
sleep 2
echo "✅ 旧服务已停止"
echo ""

# 2. 清理旧日志
rm -f cc-nim.log launchd.log launchd.err

# 3. 加载环境变量
if [ -f .env ]; then
    set -a && source .env && set +a
    echo "✅ 环境变量已加载"
fi
echo ""

# 4. 启动后台服务
echo "📋 第二步：启动后台服务..."
nohup .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8082 --log-level info >> cc-nim.log 2>&1 &
CC_NIM_PID=$!
echo $CC_NIM_PID > cc-nim.pid
sleep 5
echo "✅ 后台服务已启动 (PID: $CC_NIM_PID)"
echo ""

# 5. 验证服务（重试机制）
echo "⏳ 等待服务启动..."
for i in {1..10}; do
    if curl -s http://localhost:8082/health > /dev/null 2>&1; then
        echo "✅ 服务验证成功"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️ 服务验证超时，但可能已启动"
        cat cc-nim.log 2>/dev/null
    fi
    sleep 1
done
echo ""

# 6. 配置开机自启
echo "📋 第三步：配置开机自启..."
if [ -f "com.cc-nim.plist" ]; then
    mkdir -p ~/Library/LaunchAgents
    cp com.cc-nim.plist ~/Library/LaunchAgents/

    # 卸载旧的
    launchctl unload ~/Library/LaunchAgents/com.cc-nim.plist 2>/dev/null
    sleep 1

    # 加载新的
    if launchctl load ~/Library/LaunchAgents/com.cc-nim.plist 2>/dev/null; then
        echo "✅ 开机自启已配置"
    else
        echo "⚠️ LaunchAgent 加载失败"
    fi
else
    echo "⚠️ 未找到 com.cc-nim.plist"
fi
echo ""

echo "======================================"
echo "  ✅ 部署完成！"
echo "======================================"
echo ""
echo "📋 服务信息:"
echo "  PID: $CC_NIM_PID"
echo "  端口: 8082"
echo "  日志: cc-nim.log"
echo ""
echo "🔧 管理命令:"
echo "  查看状态: ./manage.sh status"
echo "  查看日志: ./manage.sh logs"
echo "  重启服务: ./manage.sh restart"
echo ""
echo "🚀 开机自启:"
echo "  LaunchAgent 已配置，电脑重启后自动启动"
echo "  手动管理: launchctl {start|stop|unload} com.cc-nim"
echo ""
