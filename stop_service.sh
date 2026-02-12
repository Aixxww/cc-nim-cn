#!/bin/bash
# cc-nim 服务停止脚本

echo "🛑 停止 cc-nim 服务..."

# 查找并停止所有相关进程
PIDS=$(ps aux | grep "uvicorn.*server:app" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "ℹ️ 没有正在运行的 cc-nim 服务"
    exit 0
fi

echo "正在停止以下进程:"
ps aux | grep "uvicorn.*server:app" | grep -v grep

# 停止进程
kill $PIDS

# 等待进程结束
sleep 2

# 强制杀死仍在运行的进程
REMAINING=$(ps aux | grep "uvicorn.*server:app" | grep -v grep | awk '{print $2}')
if [ -n "$REMAINING" ]; then
    echo "强制结束残留进程..."
    kill -9 $REMAINING
    sleep 1
fi

# 检查端口
if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 警告: 端口 8082 仍被占用"
    lsof -Pi :8082 -sTCP:LISTEN
else
    echo "✅ 服务已停止，端口 8082 已释放"
fi
