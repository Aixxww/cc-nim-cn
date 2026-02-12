# cc-nim 详细部署指南

> 本地部署 Claude Code + NVIDIA NIM 代理 + Telegram Bot

---

## 目录

1. [环境准备](#环境准备)
2. [安装部署](#安装部署)
3. [配置说明](#配置说明)
4. [服务管理](#服务管理)
5. [Claude Code 使用](#claude-code-使用)
6. [Telegram Bot 配置](#telegram-bot-配置)
7. [故障排查](#故障排查)
8. [生产环境部署](#生产环境部署)

---

## 环境准备

### 系统要求

| 组件 | 要求 |
|------|------|
| 操作系统 | macOS / Linux / Windows (WSL) |
| Python | 3.10+ |
| 内存 | 2GB+ |
| Claude Code CLI | 已安装 |

### 安装 Claude Code CLI

```bash
# macOS/Linux
curl -fsSL https://cdn.jsdelivr.net/npm/@anthropic-ai/claude-code/install.sh | sh

# 然后安装到 PATH
export PATH="$HOME/.local/bin:$PATH"
```

### 安装 uv（推荐）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 安装部署

### 1. 克隆/下载项目

```bash
cd ~
git clone https://github.com/Alishahryar1/cc-nim.git
cd cc-nim
```

### 2. 创建虚拟环境

```bash
# 使用 uv（推荐）
uv venv
source .venv/bin/activate

# 或使用 Python
python -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 使用 uv
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件（至少需要配置以下内容）：

```env
# NVIDIA NIM API Key（必需）
NVIDIA_NIM_API_KEY=nvapi-你的密钥

# 使用的模型
MODEL=moonshotai/kimi-k2-thinking
```

### 5. 验证安装

```bash
# 运行导入测试
python test_import.py

# 测试 API 连接
python -c "
from providers.nvidia import NvidiaProvider
import asyncio
async def test():
    provider = NvidiaProvider(api_key='你的key')
    models = await provider.get_models()
    print(f'找到 {len(models)} 个模型')
asyncio.run(test())
"
```

---

## 配置说明

### 环境变量完整列表

| 变量 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM API 密钥 | - | ✅ |
| `MODEL` | 使用的模型 | `moonshotai/kimi-k2-thinking` | ❌ |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `""` | ❌ |
| `ALLOWED_TELEGRAM_USER_ID` | 允许的 Telegram 用户 ID | `""` | ❌ |
| `ALLOWED_DIR` | Claude 允许访问的目录 | `""` | ❌ |
| `CLAUDE_WORKSPACE` | Agent 工作空间 | `./agent_workspace` | ❌ |
| `MAX_CLI_SESSIONS` | 最大并发会话数 | `10` | ❌ |
| `NVIDIA_NIM_RATE_LIMIT` | API 请求速率限制 | `40` | ❌ |
| `NVIDIA_NIM_RATE_WINDOW` | 速率限制时间窗口（秒）| `60` | ❌ |
| `HTTPS_PROXY` | HTTPS 代理地址 | `""` | ❌ |
| `HTTP_PROXY` | HTTP 代理地址 | `""` | ❌ |

### .env.example 示例

```env
# NVIDIA NIM 配置
NVIDIA_NIM_API_KEY=nvapi-YOUR_API_KEY
MODEL=moonshotai/kimi-k2-thinking
NVIDIA_NIM_RATE_LIMIT=40
NVIDIA_NIM_RATE_WINDOW=60

# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=
ALLOWED_TELEGRAM_USER_ID=

# 工作目录配置
CLAUDE_WORKSPACE=./agent_workspace
ALLOWED_DIR=

# 会话限制
MAX_CLI_SESSIONS=10

# 代理配置（如需要）
# HTTPS_PROXY=http://127.0.0.1:7897
# HTTP_PROXY=http://127.0.0.1:7897
```

---

## 服务管理

### 基本命令

```bash
cd /path/to/cc-nim

# 启动服务（前台运行，日志实时输出）
./manage.sh start

# 停止服务
./manage.sh stop

# 重启服务
./manage.sh restart

# 查看服务状态
./manage.sh status

# 查看实时日志（Ctrl+C 退出）
./manage.sh logs
```

### 命令说明

#### start_service.sh

启动服务脚本，会进行以下检查：
- ✅ 激活虚拟环境
- ✅ 检查 .env 文件
- ✅ 检查 NVIDIA_NIM_API_KEY
- ✅ 检查端口占用
- ✅ 启动 uvicorn 服务器

#### stop_service.sh

停止服务脚本，会：
- 停止所有 `uvicorn server:app` 进程
- 强制清理残留进程
- 确认端口释放

---

## Claude Code 使用

### 方式一：环境变量（临时）

```bash
cd ~
ANTHROPIC_AUTH_TOKEN=ccnim \
ANTHROPIC_BASE_URL=http://localhost:8082 \
claude
```

### 方式二：环境变量（永久）

添加到 `~/.zshrc` 或 `~/.bashrc`：

```bash
# Claude Code cc-nim 配置
export ANTHROPIC_AUTH_TOKEN=ccnim
export ANTHROPIC_BASE_URL=http://localhost:8082

# 或使用别名
alias cc="ANTHROPIC_AUTH_TOKEN=ccnim ANTHROPIC_BASE_URL=http://localhost:8082 claude"
```

然后：
```bash
source ~/.zshrc
cc
```

### 验证连接

启动 Claude Code 后，你应该能看到正常运行。发送消息时会调用 NVIDIA NIM API。

---

## Telegram Bot 配置

### 获取 Bot Token

1. 打开 Telegram，搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`
3. 按提示完成 bot 创建
4. 复制返回的 **HTTP API Token**

### 获取用户 ID

1. 打开 Telegram，搜索 [@userinfobot](https://t.me/userinfobot)
2. 发送 `/start`
3. 记录返回的用户 ID

### 配置 .env

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
ALLOWED_TELEGRAM_USER_ID=5210777244
CLAUDE_WORKSPACE=./agent_workspace
ALLOWED_DIR=/Users/yourname/projects
```

### 测试 Bot

```bash
# 重启服务使配置生效
./manage.sh restart

# 在 Telegram 中找到你的 Bot，发送 /start
# 应该收到: "🚀 Claude Code Proxy is online! (Bot API)"
```

### Bot 操作

| 命令 | 说明 |
|------|------|
| `/start` | 初始化 Bot，显示在线状态 |
| 任意文本 | 发送任务给 Claude Code |
| `/stop` | 取消正在运行的任务 |

---

## 故障排查

### 问题 1：端口被占用

**症状：**
```
⚠️ 警告: 端口 8082 已被占用
```

**解决：**
```bash
# 查看占用进程
lsof -i :8082

# 停止服务
./manage.sh stop

# 或强制释放端口
fuser -k 8082/tcp
```

### 问题 2：Bot 无法接收消息

**症状：**
- Bot 显示在线，但发送消息无响应
- 日志显示 "Pool timeout" 或 "Connection pool is full"

**原因：**
代理环境下连接池耗尽。

**解决：**
```bash
# 1. 停止服务
./manage.sh stop

# 2. 等待几秒清理连接
sleep 5

# 3. 重新启动
./manage.sh start
```

### 问题 3：API 认证失败

**症状：**
```
401 Unauthorized: Invalid API key
```

**解决：**
- 检查 `.env` 中的 `NVIDIA_NIM_API_KEY` 是否正确
- 访问 [build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys) 获取新 Key

### 问题 4：代理连接失败

**症状：**
```
Cannot connect to host api.telegram.org:443
```

**解决：**
- 确保代理软件（如 Clash）正在运行
- 检查 `.env` 中的代理设置：
  ```env
  HTTPS_PROXY=http://127.0.0.1:7897
  HTTP_PROXY=http://127.0.0.1:7897
  ```
- 测试代理连接：
  ```bash
  curl --proxy http://127.0.0.1:7897 https://api.telegram.org
  ```

### 问题 5：虚拟环境问题

**症状：**
```
ModuleNotFoundError: No module named 'xxx'
```

**解决：**
```bash
# 重新激活虚拟环境
source .venv/bin/activate

# 重新安装依赖
uv pip install -r requirements.txt

# 或重新创建虚拟环境
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 生产环境部署

### 使用 screen（推荐）

```bash
# 创建 screen 会话
screen -S cc-nim

# 启动服务
cd /path/to/cc-nim
./manage.sh start

# 分离会话: 按 Ctrl+A，然后按 D

# 重新连接
screen -r cc-nim

# 查看所有会话
screen -ls
```

### 使用 tmux

```bash
# 创建 tmux 会话
tmux new -s cc-nim

# 启动服务
cd /path/to/cc-nim
./manage.sh start

# 分离会话: 按 Ctrl+B，然后按 D

# 重新连接
tmux attach -t cc-nim

# 查看所有会话
tmux ls
```

### 使用 nohup

```bash
cd /path/to/cc-nim

# 后台运行
nohup ./manage.sh start > cc-nim.out 2>&1 &

# 记录 PID
echo $! > cc-nim.pid

# 查看日志
tail -f cc-nim.out

# 停止服务
kill $(cat cc-nim.pid)
```

### 使用 systemd（Linux）

#### 创建服务文件

```bash
sudo nano /etc/systemd/system/cc-nim.service
```

内容：

```ini
[Unit]
Description=cc-nim Claude Code Proxy
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/cc-nim
Environment="PATH=/home/your-username/cc-nim/.venv/bin"
ExecStart=/home/your-username/cc-nim/manage.sh start
ExecStop=/home/your-username/cc-nim/manage.sh stop
Restart=always
RestartSec=10
StandardOutput=append:/home/your-username/cc-nim/server.log
StandardError=append:/home/your-username/cc-nim/server.log

[Install]
WantedBy=multi-user.target
```

#### 管理服务

```bash
# 重载配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable cc-nim

# 启动服务
sudo systemctl start cc-nim

# 查看状态
sudo systemctl status cc-nim

# 查看日志
sudo journalctl -u cc-nim -f

# 停止服务
sudo systemctl stop cc-nim

# 重启服务
sudo systemctl restart cc-nim
```

### macOS LaunchAgent

#### 创建 plist 文件

```bash
nano ~/Library/LaunchAgents/com.cc-nim.plist
```

内容：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cc-nim</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourname/cc-nim/manage.sh</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yourname/cc-nim</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/yourname/cc-nim/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourname/cc-nim/launchd.err</string>
</dict>
</plist>
```

#### 管理服务

```bash
# 加载服务
launchctl load ~/Library/LaunchAgents/com.cc-nim.plist

# 启动服务
launchctl start com.cc-nim

# 停止服务
launchctl stop com.cc-nim

# 卸载服务
launchctl unload ~/Library/LaunchAgents/com.cc-nim.plist
```

---

## Docker 部署

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
RUN /root/.local/bin/uv venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install -r requirements.txt

# 暴露端口
EXPOSE 8082

# 启动应用
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8082"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t cc-nim .

# 运行容器
docker run -d \
  --name cc-nim \
  --env-file .env \
  -p 8082:8082 \
  cc-nim

# 查看日志
docker logs -f cc-nim

# 停止容器
docker stop cc-nim

# 重启容器
docker restart cc-nim
```

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-02-12 | v2.0.0 | 添加自定义 HTTP 客户端，优化服务脚本，完善中文文档 |

---

## 联系支持

- GitHub Issues: [Alishahryar1/cc-nim](https://github.com/Alishahryar1/cc-nim/issues)
- NVIDIA NIM: [build.nvidia.com](https://build.nvidia.com/)
