# Claude NIM Bridge / Claude NIM 桥接服务

> Use NVIDIA's free NIM API (40 req/min) as a drop-in replacement for Anthropic API with Claude Code
>
> 使用 NVIDIA 的免费 NIM API（40 请求/分钟）替代 Anthropic API 运行 Claude Code

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)]()

---

## Features / 功能特性 | [中文](#中文文档)

| Feature / 功能 | Description / 说明 |
|----------------|-------------------|
| 🚀 **Free API / 免费 API** | Use NVIDIA NIM free tier (40 req/min) / 使用 NVIDIA NIM 免费套餐（40 请求/分钟）|
| 🔄 **API Proxy / API 代理** | Translation from Anthropic API format to NVIDIA NIM format / 将 Anthropic API 请求转换为 NVIDIA NIM 格式 |
| ⚡ **Streaming Support / 流式支持** | Full support for Anthropic-style streaming responses / 完整支持 Anthropic 格式的流式响应 |
| 🎯 **Reasoning Models / 推理模型** | Support for thinking/reasoning model outputs / 支持带思维链输出的推理模型 |
| 🛡️ **Smart Optimization / 优化处理** | Intelligent skipping of quota checks and title generation requests / 智能跳过配额检查和标题生成请求 |
| 📦 **Lightweight / 精简设计** | Pure proxy mode, minimal dependencies / 纯代理模式，极简依赖 |

---

## Quick Start / 快速开始

### 1. Get NVIDIA API Key / 获取 NVIDIA API 密钥

Visit / 访问 [build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys) to get your free API key / 获取免费 API 密钥。

### 2. Install Dependencies / 安装依赖

```bash
# Requires Python 3.10+ / 需要 Python 3.10+
cd /path/to/claude-nim-bridge

# Using uv (recommended) / 使用 uv（推荐）
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .

# Or using pip / 或使用 pip
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Configure Environment Variables / 配置环境变量

```bash
cp .env.example .env
```

Edit `.env` file / 编辑 `.env` 文件：

```env
NVIDIA_NIM_API_KEY=nvapi-your-key
MODEL=moonshotai/kimi-k2-thinking
```

### 4. Start the Service / 启动服务

```bash
# Direct start / 直接启动
uvicorn api.app:app --host 0.0.0.0 --port 8082

# Or use script / 或使用脚本
./run.sh
```

### 5. Use Claude Code / 使用 Claude Code

```bash
ANTHROPIC_AUTH_TOKEN=ccnim \
ANTHROPIC_BASE_URL=http://localhost:8082 \
claude
```

Or configure in `~/.claude/settings.json`:

```json
{
  "apiBase": "http://localhost:8082",
  "apiKey": "ccnim"
}
```

---

## Service Management / 服务管理

### Unified Management Script / 统一管理脚本

```bash
cd /path/to/claude-nim-bridge

# Start / 启动
./manage.sh start

# Stop / 停止
./manage.sh stop

# Restart / 重启
./manage.sh restart

# Status / 状态
./manage.sh status

# Logs / 日志
./manage.sh logs

# Install with auto-start / 安装并配置开机自启
./manage.sh install

# Uninstall / 卸载
./manage.sh uninstall
```

### Platform Support / 平台支持

| Platform / 平台 | Auto-start Method / 开机自启方式 | Requirements / 要求 |
|------------------|----------------------------------|-------------------|
| **macOS** | LaunchAgent | No additional requirements |
| **Linux** | systemd | Requires sudo for install/uninstall |
| **Windows** | Manual (WIP) | Use WSL or manual start |

### Quick Commands / 快速命令

```bash
# Start background service / 启动后台服务
./start_service.sh      # macOS/Linux
./run.sh                # Foreground / 前台运行

# Quick check / 快速检查
curl http://localhost:8082/health
```

---

## Available Models / 可用模型

View full list at / 查看完整列表: [build.nvidia.com/explore/discover](https://build.nvidia.com/explore/discover)

Recommended models / 推荐模型：

| Model ID / 模型 ID | Type / 类型 | Description / 说明 |
|--------------------|-------------|--------------------|
| `moonshotai/kimi-k2-thinking` | Reasoning / 推理模型 | Strong reasoning capability, default choice / 强大的推理能力，默认选择 |
| `moonshotai/kimi-k2.5` | General / 通用模型 | Balanced performance / 平衡的性能与速度 |
| `z-ai/glm4.7` | Chinese optimized / 中文优化 | Optimized for Chinese content / 针对中文内容优化 |
| `minimaxai/minimax-m2.1` | Efficient / 高效模型 | Fast response for simple tasks / 快速响应，适合简单任务 |

Update model list / 更新模型列表：

```bash
curl "https://integrate.api.nvidia.com/v1/models" > nvidia_nim_models.json
```

---

## API Endpoints / API 端点

| Endpoint / 端点 | Method / 方法 | Description / 说明 |
|------------------|----------------|---------------------|
| `/v1/messages` | POST | Create message (streaming/non-streaming) / 发送消息（流式/非流式）|
| `/v1/messages/count_tokens` | POST | Count tokens / 计算 Token 数量 |
| `/health` | GET | Health check / 健康检查 |
| `/` | GET | Service info / 服务信息 |

---

## Project Structure / 项目结构

```
claude-nim-bridge/
├── manage.sh              # Main management script / 主管理脚本
├── start_service.sh       # Start script / 启动脚本
├── stop_service.sh        # Stop script / 停止脚本
├── run.sh                 # Run script / 运行脚本
├── server.py              # Uvicorn entry point / uvicorn 入口
├── api/                   # FastAPI application / FastAPI 应用
│   ├── app.py            # App configuration / 应用配置
│   ├── routes.py         # API routes / API 路由
│   ├── models.py         # Pydantic models / Pydantic 模型
│   ├── dependencies.py   # Dependency injection / 依赖注入
│   └── request_utils.py  # Request utilities / 请求工具
├── providers/             # Provider implementations / 提供商实现
│   ├── nvidia_nim/       # NVIDIA NIM integration
│   │   ├── client.py     # API client / API 客户端
│   │   ├── converter.py  # Format conversion / 格式转换
│   │   └── provider.py   # Provider implementation / 提供商实现
│   └── utils/            # Utilities / 工具类
│       └── sse_builder.py # SSE streaming builder / SSE 流式构建
├── config/                # Configuration / 配置
│   └── settings.py       # Pydantic settings / Pydantic 配置
├── tests/                 # Tests / 测试
├── .env                   # Environment variables (create this) / 环境变量（需创建）
├── .env.example           # Environment variables template / 环境变量示例
└── pyproject.toml         # Project configuration / 项目配置
```

---

## Configuration / 配置参数

| Parameter / 参数 | Description / 说明 | Default / 默认值 | Required / 必需 |
|------------------|-------------------|------------------|----------------|
| `NVIDIA_NIM_API_KEY` | NVIDIA API Key / NVIDIA API 密钥 | - | Yes / 是 |
| `MODEL` | Default model ID / 默认模型 ID | `moonshotai/kimi-k2-thinking` | No / 否 |
| `NVIDIA_NIM_RATE_LIMIT` | Rate limit per window / 每时间窗口请求限制 | `40` | No / 否 |
| `NVIDIA_NIM_RATE_WINDOW` | Rate window in seconds / 时间窗口（秒）| `60` | No / 否 |
| `FAST_PREFIX_DETECTION` | Enable prefix detection / 启用前缀检测 | `true` | No / 否 |
| `ENABLE_NETWORK_PROBE_MOCK` | Enable network probe mock / 启用网络探测模拟 | `true` | No / 否 |
| `ENABLE_TITLE_GENERATION_SKIP` | Skip title generation / 跳过标题生成 | `true` | No / 否 |

Full configuration reference / 完整配置参考: See `.env.example` / 参见 `.env.example`

---

## Troubleshooting / 故障排查

### Port Already Occupied / 端口被占用

```bash
# Check process using the port / 查看占用端口的进程
lsof -i :8082

# Stop service / 停止服务
./stop_service.sh
```

### Request Failed / 请求失败

```bash
# View logs / 查看日志
tail -f server.log

# Verify API Key / 验证 API Key
curl https://integrate.api.nvidia.com/v1/models \
  -H "Authorization: Bearer $NVIDIA_NIM_API_KEY"
```

More troubleshooting details / 更多故障排查详情: See the documentation repository / 参见文档仓库 [cc-nim-book](https://github.com/aixxww/cc-nim-book)

---

## Python SDK Usage / Python SDK 使用

```python
import anthropic

client = anthropic.Anthropic(
    api_key="ccnim",
    base_url="http://localhost:8082"
)

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, please introduce yourself"}
    ]
)

print(response.content[0].text)
```

---

## Documentation / 文档

For detailed documentation / 完整文档，请访问：

- 📚 **Documentation Repository / 文档仓库**: [https://github.com/aixxww/cc-nim-book](https://github.com/aixxww/cc-nim-book)
  - [Quick Start / 快速开始](https://github.com/aixxww/cc-nim-book/blob/main/01-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B.md)
  - [Configuration / 配置说明](https://github.com/aixxww/cc-nim-book/blob/main/02-%E9%85%8D%E7%BD%AE%E8%AF%B4%E6%98%8E.md)
  - [Usage Guide / 使用指南](https://github.com/aixxww/cc-nim-book/blob/main/03-%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md)
  - [API Reference / API 参考](https://github.com/aixxww/cc-nim-book/blob/main/04-API%E5%8F%82%E8%80%83.md)
  - [Troubleshooting / 故障排查](https://github.com/aixxww/cc-nim-book/blob/main/05-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5.md)
  - [Architecture / 架构设计](https://github.com/aixxww/cc-nim-book/blob/main/06-%E6%9E%B6%E6%9E%84%E8%AE%BE%E8%AE%A1.md)

---

## Auto-start / 开机自启

### macOS (LaunchAgent)

```bash
# Install and configure / 安装并配置
./manage.sh install

# Manual setup / 手动设置
cp com.claude-nim-bridge.plist.example ~/Library/LaunchAgents/com.claude-nim-bridge.plist
# Edit the plist file with your settings / 编辑 plist 文件填入配置
launchctl load ~/Library/LaunchAgents/com.claude-nim-bridge.plist
launchctl start com.claude-nim-bridge

# Uninstall / 卸载
./manage.sh uninstall
```

### Linux (systemd)

```bash
# Install and configure / 安装并配置
sudo ./manage.sh install

# Manual setup / 手动设置
sudo cp claude-nim-bridge.service.example /etc/systemd/system/claude-nim-bridge.service
# Edit the service file with your paths and API key / 编辑服务文件填入路径和密钥
sudo systemctl daemon-reload
sudo systemctl enable claude-nim-bridge
sudo systemctl start claude-nim-bridge

# View logs / 查看日志
sudo journalctl -u claude-nim-bridge -f

# Uninstall / 卸载
sudo ./manage.sh uninstall
```

---

## Comparison / 对比

| Feature / 特性 | Anthropic Official / 官方 API | Claude NIM Bridge |
|----------------|-------------------------------|-------------------|
| Cost / 费用 | Pay-per-use / 按使用收费 | Free / 完全免费 |
| Rate Limit / 速率限制 | Depends on plan / 取决于套餐 | 40 req/min |
| Model Selection / 模型选择 | Claude 3/4 Series / Claude 3/4 系列 | NVIDIA NIM Platform Models / NVIDIA NIM 平台模型 |
| Streaming / 流式 | ✅ | ✅ |

---

## License / 许可证

MIT License - See [LICENSE](LICENSE) file / 详见 [LICENSE](LICENSE) 文件

---

## Changelog / 更新日志

### v2.2.0 (2026-03-19)

- ✅ **Simplified Project / 精简项目** - Removed Telegram Bot and CLI integration, pure proxy mode / 移除 Telegram Bot 和 CLI 集成，专注纯代理模式
- ✅ **Fixed Log Leak / 修复日志泄漏** - Disabled SSE event debug logging to prevent log file growth / 禁用 SSE 事件调试日志，防止日志文件膨胀
- ✅ **Optimized Log Level / 优化日志级别** - Default INFO level, reduced verbose output / 默认使用 INFO 级别，减少冗余输出
- ✅ **Fixed Client Cleanup / 修复客户端清理** - Correctly close AsyncOpenAI client / 正确关闭 AsyncOpenAI 客户端
- ✅ **Bilingual Documentation / 双语文档** - Added English and Chinese documentation / 添加中英双语文档

### v2.1.0 (2026-02-12)

- ✅ **Fixed Connection Pool Issue / 修复连接池问题** - Solved connection leak in proxy environments / 彻底解决代理环境下的连接泄漏
- ✅ Long-term stability improvement / 长期运行稳定性大幅提升

### v2.0.0 (2026-02-12)

- ✅ Initial release with custom HTTP client / 初始版本发布，包含自定义 HTTP 客户端

---

## Credits / 原项目

Based on / 基于 [Alishahryar1/cc-nim](https://github.com/Alishahryar1/cc-nim) - forked and significantly improved / 分支并大幅改进

---

## GitHub Repositories / GitHub 仓库

- **Main Project / 主项目**: [https://github.com/aixxww/claude-nim-bridge](https://github.com/aixxww/claude-nim-bridge)
- **Documentation / 文档**: [https://github.com/aixxww/cc-nim-book](https://github.com/aixxww/cc-nim-book)
