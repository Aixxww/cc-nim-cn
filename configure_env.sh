#!/bin/bash
# Telegram Bot环境变量配置脚本
# 使用方法：./configure_env.sh

set -e

echo "🤖 Telegram Bot 环境配置工具"
echo "================================"
echo

# 检查是否为交互模式
if [ -t 0 ]; then
    INTERACTIVE=true
else
    INTERACTIVE=false
fi

# 获取用户输入的函数
get_input() {
    local prompt="$1"
    local default="$2"
    local current="$3"

    if [ "$INTERACTIVE" = true ]; then
        if [ -n "$current" ]; then
            read -p "$prompt [$current]: " value
        elif [ -n "$default" ]; then
            read -p "$prompt [$default]: " value
        else
            read -p "$prompt: " value
        fi
    else
        value=""
    fi

    # 如果用户没有输入，使用当前值或默认值
    if [ -z "$value" ]; then
        if [ -n "$current" ]; then
            value="$current"
        else
            value="$default"
        fi
    fi

    echo "$value"
}

# 配置 Telegram Bot Token
CURRENT_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
BOT_TOKEN=$(get_input "请输入 Telegram Bot Token" "" "$CURRENT_BOT_TOKEN")

if [ -z "$BOT_TOKEN" ]; then
    echo
    echo "⚠️  警告：未提供 Bot Token"
    echo "   您可以在运行前手动设置：export TELEGRAM_BOT_TOKEN='your-token'"
    echo
else
    export TELEGRAM_BOT_TOKEN="$BOT_TOKEN"
    echo "✓ Bot Token 已配置"
fi

# 配置允许的用户 ID
CURRENT_USER_ID="${ALLOWED_TELEGRAM_USER_ID:-}"
USER_ID=$(get_input "请输入允许访问的用户 ID (可选)" "" "$CURRENT_USER_ID")

if [ -n "$USER_ID" ]; then
    export ALLOWED_TELEGRAM_USER_ID="$USER_ID"
    echo "✓ 用户 ID 已配置"
else
    echo "ℹ️  未设置用户 ID，bot 将接受所有用户的消息"
fi

# 配置代理
CURRENT_PROXY="${HTTPS_PROXY:-${HTTP_PROXY:-}}"
PROXY=$(get_input "请输入代理地址 (可选，例如: http://proxy:8080)" "" "$CURRENT_PROXY")

if [ -n "$PROXY" ]; then
    export HTTPS_PROXY="$PROXY"
    export HTTP_PROXY="$PROXY"
    echo "✓ 代理已配置: $PROXY"
else
    echo "ℹ️  未配置代理"
fi

# 显示总结
echo
echo "📋 配置总结："
echo "==============="
echo "Bot Token: $(if [ -n "$BOT_TOKEN" ]; then echo "✓已设置"; else echo "✗未设置"; fi)"
echo "User ID: $(if [ -n "$USER_ID" ]; then echo "$USER_ID"; else echo "✗未设置 (接受所有用户)"; fi)"
echo "Proxy: $(if [ -n "$PROXY" ]; then echo "$PROXY"; else echo "✗未设置"; fi)"
echo
echo "💡 提示："
echo "   使用 'source ./configure_env.sh' 持久化环境变量到当前 shell"
echo "   或使用 'export' 手动设置变量"
echo

# 保存到文件选项
if [ "$INTERACTIVE" = true ]; then
    read -p "是否保存配置到 .env 文件？(y/n): " save_choice
    if [ "$save_choice" = "y" ]; then
        cat > .env << EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN="${BOT_TOKEN}"
ALLOWED_TELEGRAM_USER_ID="${USER_ID}"

# Proxy Configuration (optional)
HTTPS_PROXY="${PROXY}"
HTTP_PROXY="${PROXY}"
EOF
        echo "✓ 配置已保存到 .env"
        echo
        echo "💡 使用方法："
        echo "   1. 运行 'source .env' 加载配置"
        echo "   2. 运行 'python your_app.py' 启动bot"
    fi
fi

# 提供下一步建议
echo
echo "🚀 下一步建议："
echo "   1. 运行 './test_http_connectivity.py' 测试HTTP连接"
echo "   2. 运行 './test_telegram_bot.py' 测试完整bot功能"
echo "   3. 查看 IMPLEMENTATION_SUMMARY.md 获取详细信息"
echo
