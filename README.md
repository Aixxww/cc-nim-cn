# cc-nim - Claude Code 与 NVIDIA NIM 结合

> 用 NVIDIA 的免费 API（40 req/min）运行 Claude Code CLI，支持 Telegram Bot 远程控制

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)]()

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 🚀 **免费 API** | 使用 NVIDIA NIM 免费套餐（40 req/min）|
| 💬 **Telegram Bot** | 手机远程控制 Claude Code |
| 🔄 **API 代理** | 将 Anthropic API 请求转换为 NVIDIA NIM 格式 |
| ⚡ **高并发** | 支持多 CLI 会话同时运行 |
| 🛡️ **自定义 HTTP 客户端** | 解决代理环境下的连接池问题 |

---

## 快速开始

### 1. 获取 NVIDIA API Key

访问 [build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys) 获取免费 API Key。

### 2. 安装依赖

```bash
# 需要 Python 3.10+
cd /path/to/cc-nim

# 使用 uv 安装
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
NVIDIA_NIM_API_KEY=nvapi-你的密钥
MODEL=moonshotai/kimi-k2-thinking
```

### 4. 启动服务

```bash
./manage.sh start
```

### 5. 使用 Claude Code

```bash
ANTHROPIC_AUTH_TOKEN=ccnim \
ANTHROPIC_BASE_URL=http://localhost:8082 \
claude
```

---

## Telegram Bot 集成

### 创建 Telegram Bot

1. 在 Telegram 中发送 `/newbot` 给 [@BotFather](https://t.me/BotFather)
2. 跟随提示创建 bot，复制 **HTTP API Token**
3. 发送 `/myid` 给 [@userinfobot](https://t.me/userinfobot) 获取你的用户 ID

### 配置 Bot

在 `.env` 中添加：

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
ALLOWED_TELEGRAM_USER_ID=你的用户ID
CLAUDE_WORKSPACE=./agent_workspace
ALLOWED_DIR=/Users/你的用户名/projects
```

### 使用 Bot

| 操作 | 说明 |
|------|------|
| `/start` | 初始化 Bot |
| 发送任意文本 | 让 Claude Code 执行任务 |
| `/stop` | 取消正在运行的任务 |

---

## 服务管理

```bash
cd /path/to/cc-nim

# 启动服务
./manage.sh start

# 停止服务
./manage.sh stop

# 查看状态
./manage.sh status

# 查看日志
./manage.sh logs
```

---

## 可用模型

查看完整模型列表：[build.nvidia.com/explore/discover](https://build.nvidia.com/explore/discover)

推荐模型：

| 模型 | 说明 |
|------|------|
| `moonshotai/kimi-k2-thinking` | 默认，推理能力强 |
| `moonshotai/kimi-k2.5` | 通用模型 |
| `z-ai/glm4.7` | 中文优化 |
| `minimaxai/minimax-m2.1` | 高效模型 |

更新模型列表：

```bash
curl "https://integrate.api.nvidia.com/v1/models" > nvidia_nim_models.json
```

---

## 后台运行（生产环境）

### 一键安装和启动（推荐）

```bash
cd /Users/WiNo/cc-nim
./install_and_start.sh
```

这个脚本会：
- 停止所有旧服务
- 启动后台服务
- 配置 macOS 开机自启（LaunchAgent）

### 使用 screen

```bash
screen -S cc-nim
./manage.sh start
# 按 Ctrl+A, D 分离会话

# 重新连接
screen -r cc-nim
```

### 使用 systemd（Linux）

创建 `/etc/systemd/system/cc-nim.service`:

```ini
[Unit]
Description=cc-nim Claude Code Proxy
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/cc-nim
Environment="PATH=/path/to/cc-nim/.venv/bin"
ExecStart=/path/to/cc-nim/manage.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cc-nim
sudo systemctl start cc-nim
sudo systemctl status cc-nim
```

---

## 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `NVIDIA_NIM_API_KEY` | NVIDIA API 密钥 | （必需）|
| `MODEL` | 使用的模型 | `moonshotai/kimi-k2-thinking` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `""` |
| `ALLOWED_TELEGRAM_USER_ID` | 允许的 Telegram 用户 ID | `""` |
| `ALLOWED_DIR` | Claude 允许访问的目录 | `""` |
| `CLAUDE_WORKSPACE` | Agent 工作空间 | `./agent_workspace` |
| `MAX_CLI_SESSIONS` | 最大并发会话数 | `10` |
| `NVIDIA_NIM_RATE_LIMIT` | API 请求速率限制 | `40` |
| `HTTPS_PROXY` | HTTPS 代理地址 | `""` |

---

## 项目结构

```
cc-nim/
├── manage.sh              # 主管理脚本
├── start_service.sh       # 启动脚本
├── stop_service.sh        # 停止脚本
├── server.py              # uvicorn 入口
├── api/                   # FastAPI 应用
│   ├── app.py            # 应用配置
│   └── routes.py         # API 路由
├── messaging/             # 消息平台
│   ├── telegram.py       # Telegram Bot 集成
│   └── telegram_http_client.py  # 自定义 HTTP 客户端
├── cli/                   # CLI 会话管理
│   └── manager.py        # 会话管理器
├── providers/             # API 提供商
│   └── nvidia.py         # NVIDIA NIM 集成
├── config/                # 配置
│   └── settings.py       # Pydantic 配置
├── .env                   # 环境变量（需创建）
├── .env.example           # 环境变量示例
├── requirements.txt       # Python 依赖
└── DEPLOY_GUIDE.md        # 详细部署指南
```

---

## 故障排查

### Bot 无法接收消息

```bash
# 检查日志
tail -f server.log

# 清理代理连接
./manage.sh stop
sleep 2
./manage.sh start
```

### 端口被占用

```bash
# 查看占用进程
lsof -i :8082

# 停止服务
./manage.sh stop
```

### 连接池超时

确保 `.env` 中配置了正确的代理：
```env
HTTPS_PROXY=http://127.0.0.1:7897
HTTP_PROXY=http://127.0.0.1:7897
```

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 原项目

基于 [Alishahryar1/cc-nim](https://github.com/Alishahryar1/cc-nim) 改进

---

## 更新日志

### v2.0.0 (2026-02-12)

- ✅ 添加自定义 HTTP 客户端，解决代理环境连接池问题
- ✅ 优化服务管理脚本
- ✅ 完善中文文档
- ✅ 生产环境部署支持
