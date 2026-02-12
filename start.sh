#!/bin/bash
echo "🎯 启动 Telegram Bot （自定义 HTTP 客户端）"
echo "============================="
. .venv/bin/activate
source .env
python api/app.py
