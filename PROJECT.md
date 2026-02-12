# cc-nim 项目说明

> Claude Code + NVIDIA NIM + Telegram Bot

---

## 项目结构

```
cc-nim/
├── README.md                      # 项目主文档（中文）
├── DEPLOY_GUIDE.md                # 详细部署指南（中文）
├── DEPLOYMENT.md                  # 部署文档
├── IMPLEMENTATION_COMPLETE.md     # 实施完成报告
├── IMPLEMENTATION_SUMMARY.md      # 实施摘要
├── README_TELEGRAM_HTTP_CLIENT.md # Telegram HTTP 客户端说明
├── LICENSE                        # MIT 许可证
│
├── manage.sh                      # 主管理脚本（推荐使用）
├── start_service.sh               # 启动服务
├── stop_service.sh                # 停止服务
├── deploy.sh                      # 部署脚本
├── configure_env.sh               # 环境配置脚本
│
├── server.py                      # uvicorn 入口
├── quickstart.py                  # 快速启动工具
├── setup_logging.py               # 日志配置工具
├── start_bot.py                   # 启动 Bot
│
├── test_import.py                 # 导入测试
├── test_http_connectivity.py      # HTTP 连通性测试
├── test_telegram_bot.py           # Bot 端到端测试
├── test_telegram_direct.py        # Bot 直接测试
├── test_telegram_http_client.py   # HTTP 客户端测试
│
├── .env.example                   # 环境变量示例
├── .gitignore                     # Git 忽略规则
├── .python-version                # Python 版本 3.10
├── pyproject.toml                 # 项目配置
├── nvidia_nim_models.json         # NVIDIA 可用模型列表
│
├── api/                           # FastAPI 应用
│   ├── __init__.py
│   ├── app.py                     # 应用配置和生命周期
│   ├── dependencies.py            # 依赖注入
│   ├── models.py                  # API 模型
│   ├── request_utils.py           # 请求工具
│   └── routes.py                  # API 路由
│
├── cli/                           # CLI 会话管理
│   ├── __init__.py
│   ├── manager.py                 # 会话管理器
│   ├── session.py                 # 会话处理
│   └── subprocess.py              # 子进程管理
│
├── messaging/                     # 消息平台
│   ├── __init__.py
│   ├── base.py                    # 基础消息平台
│   ├── event_parser.py            # 事件解析器
│   ├── handler.py                 # 消息处理器
│   ├── limiter.py                 # 限流器
│   ├── models.py                  # 消息模型
│   ├── session.py                 # 会话存储
│   ├── telegram.py                # Telegram Bot 集成
│   ├── telegram_http_client.py    # 自定义 HTTP 客户端（解决代理问题）
│   ├── tree_data.py               # 对话树数据
│   ├── tree_processor.py          # 对话树处理器
│   ├── tree_queue.py              # 对话树队列
│   └── tree_repository.py         # 对话树仓库
│
├── providers/                     # API 提供商
│   ├── __init__.py
│   ├── base.py                    # 基础提供商
│   ├── exceptions.py              # 异常定义
│   └── nvidia.py                  # NVIDIA NIM 集成
│
├── config/                        # 配置
│   ├── __init__.py
│   └── settings.py                # Pydantic 配置
│
├── tests/                         # 测试
│   └── ...
│
└── .venv/                         # 虚拟环境（忽略）
    └── ...
```

---

## 核心功能

### 1. API 代理
- 将 Anthropic API 请求转换为 NVIDIA NIM 格式
- 支持流式响应
- 速率限制管理

### 2. Telegram Bot 远程控制
- 通过手机发送任务给 Claude Code
- 支持多会话管理
- 对话树管理

### 3. 自定义 HTTP 客户端
- 解决代理环境下的连接池耗尽问题
- 基于 aiohttp 实现
- 支持代理认证

---

## 快速开始

### 安装

```bash
cd cc-nim
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，设置 NVIDIA_NIM_API_KEY
```

### 启动

```bash
./manage.sh start
```

### 使用 Claude Code

```bash
ANTHROPIC_AUTH_TOKEN=ccnim \
ANTHROPIC_BASE_URL=http://localhost:8082 \
claude
```

---

## 上传到 GitHub 步骤

### 1. 设置远程仓库

```bash
cd /Users/WiNo/cc-nim
git remote -v

# 如果需要添加/修改远程仓库
git remote set-url origin https://github.com/your-username/cc-nim.git
# 或使用 SSH
git remote set-url origin git@github.com:your-username/cc-nim.git
```

### 2. 提交更改

```bash
# 查看状态
git status

# 添加所有文件
git add .

# 提交
git commit -m "feat: 完善中文文档和服务管理脚本

- 更新 README.md 为中文完整文档
- 创建详细部署指南 DEPLOY_GUIDE.md
- 添加服务管理脚本 manage.sh
- 解决代理环境连接池问题
- 优化项目结构"
```

### 3. 推送到 GitHub

```bash
# 推送到主分支
git push origin main

# 或使用其他分支名（如 master）
git push origin master
```

### 4. 如果是首次推送

```bash
# 初始化并推送
git init
git add .
git commit -m "Initial commit: cc-nim v2.0.0"
git branch -M main
git remote add origin https://github.com/your-username/cc-nim.git
git push -u origin main
```

---

## 重要提示

### 上传前检查清单

- [ ] `.env` 文件已删除（确保不包含敏感信息）
- [ ] `.gitignore` 已配置正确
- [ ] 虚拟环境 `.venv/` 已忽略
- [ ] 日志文件已清理
- [ ] 所有文档已更新

### 敏感信息保护

以下文件/目录已配置为忽略：

- `.env` - 包含 API 密钥和 Token
- `.venv/` - 虚拟环境
- `*.log` - 日志文件
- `agent_workspace/` - 工作空间数据

---

## 版本信息

| 项目 | 版本 |
|------|------|
| cc-nim | 2.0.0 |
| Python | 3.10+ |
| FastAPI | 0.x |
| telegram | 21.x |

---

## 联系方式

- 原项目: https://github.com/Alishahryar1/cc-nim
- NVIDIA NIM: https://build.nvidia.com/
