# 🚀 Telegram Bot 部署指南

## 📋 部署前检查清单

✅ **测试已完成**
- [x] HTTP 连通性测试通过 (10/10)
- [x] Telegram Bot E2E 测试通过
- [x] 消息发送成功 (ID: 115)
- [x] 无连接泄漏

✅ **环境配置**
- [x] TELEGRAM_BOT_TOKEN 已配置
- [x] .env 文件已创建
- [x] 虚拟环境 (.venv) 已设置
- [x] 依赖已安装

## 🎯 快速启动

### 开发环境（推荐首次部署）

```bash
# 1. 启动脚本（已在前台运行，日志实时输出）
./start_dev.sh

# 2. 检查日志（另一个终端）
tail -f server.log

# 3. 测试消息（通过 Telegram 发送消息给 Bot）
# 4. 按 Ctrl+C 停止
```

### 生产环境（后台运行）

```bash
# 使用 screen（推荐）
screen -S telegram-bot
./start_dev.sh
# 按 Ctrl+A 然后按 D 分离会话

# 重新连接到会话
screen -r telegram-bot

# 停止 Bot
# 在 screen 会话中按 Ctrl+C
```

### 生产环境（系统服务）

#### 创建系统服务文件

```bash
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/.venv/bin
ExecStart=$PWD/.venv/bin/python $PWD/api/app.py
Restart=always
RestartSec=10
StandardOutput=append:$PWD/server.log
StandardError=append:$PWD/server.log

[Install]
WantedBy=multi-user.target
EOF
```

#### 管理服务

```bash
# 启动服务
sudo systemctl start telegram-bot

# 查看状态
sudo systemctl status telegram-bot

# 查看日志
sudo journalctl -u telegram-bot -f

# 停止服务
sudo systemctl stop telegram-bot

# 启用开机自启
sudo systemctl enable telegram-bot
```

### Docker 部署（可选）

#### 创建 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 创建 Python 虚拟环境
RUN python -m venv .venv

# 安装 Python 依赖
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

# 暴露端口（如果有HTTP接口）
EXPOSE 8000

# 启动应用
CMD [".venv/bin/python", "api/app.py"]
```

#### 构建和运行

```bash
# 构建镜像
docker build -t telegram-bot .

# 运行容器
docker run -d \
  --name telegram-bot \
  --env-file .env \
  -v $(pwd)/server.log:/app/server.log \
  telegram-bot

# 查看日志
docker logs -f telegram-bot
```

## 🔍 验证部署

### 1. 检查进程

```bash
# 查看 Python 进程
ps aux | grep python

# 查看端口（如果有HTTP接口）
netstat -tulpn | grep python
```

### 2. 检查日志

```bash
# 实时查看日志
tail -f server.log

# 过滤错误
grep "ERROR" server.log

# 过滤警告
grep "WARNING" server.log

# 过滤连接池错误（不应该出现）
grep -E "Pool timeout|Connection pool" server.log
```

### 3. 检查资源使用

```bash
# 查看 CPU 和内存使用
top -p $(pgrep -f "app.py")

# 查看 Python 进程详情
ps -p $(pgrep -f "app.py") -o pid,ppid,%cpu,%mem,cmd
```

### 4. 测试 Bot 功能

在 Telegram 中：
1. 找到你的 Bot
2. 发送 `/start` 命令
3. 发送一条普通消息
4. 检查日志是否有响应

## 📍 日志解读

### ✅ 正常日志示例

```
2026-02-12 03:36:43,298 - messaging.limiter - INFO - GlobalRateLimiter initialized
2026-02-12 03:36:43,299 - messaging.limiter - INFO - GlobalRateLimiter worker started
2026-02-12 03:36:44,323 - messaging.telegram - INFO - Telegram platform started (Bot API)
```

### ⚠️ 需要关注的日志

```
# 不应该出现这些错误
❌ ERROR - Connection pool is full
❌ ERROR - Pool timeout
❌ ERROR - httpcore errors

# 如果出现，说明自定义HTTP客户端未生效
```

### ✅ 自定义 HTTP 客户端已生效的标志

```
INFO - Using custom NonPoolingHTTPRequest with proxy: http://127.0.0.1:7897
INFO - TelegramAIOHTTPClient initialized with connection_limit=0
INFO - NonPoolingHTTPRequest initialized with proxy: http://127.0.0.1:7897
```

## 🚨 故障排查

### 问题：Bot 启动失败

**可能原因：**
- Token 无效或过期
- 代理配置错误
- 端口被占用

**解决方法：**
```bash
# 检查 token
grep TELEGRAM_BOT_TOKEN .env

# 测试 token
curl -X GET "https://api.telegram.org/bot<TOKEN>/getMe"

# 检查代理
echo $HTTPS_PROXY

# 临时禁用代理进行测试
unset HTTPS_PROXY
unset HTTP_PROXY
```

### 问题：连接池错误仍然存在

**可能原因：**
- 自定义 HTTP 客户端未生效
- Updater 仍在使用 httpx

**解决方法：**
```bash
# 检查日志
# 应该在启动时看到 "NonPoolingHTTPRequest"
# 如果没有，检查 .env 和 app.py

# 重启应用
sudo systemctl restart telegram-bot
```

### 问题：内存使用过高

**可能原因：**
- 连接未正确关闭
- 日志级别设置过低

**解决方法：**
```bash
# 检查连接
# 不应该有大量 TIME_WAIT 连接
netstat -an | grep :443 | wc -l

# 调整日志级别
# 修改 app.py 中的 logging.basicConfig(level=logging.INFO)
```

## 🎨 部署最佳实践

### 1. 使用进程管理器

```bash
# 安装 supervisord
sudo apt-get install supervisor

# 创建配置文件
sudo tee /etc/supervisor/conf.d/telegram-bot.conf > /dev/null <<EOF
[program:telegram-bot]
directory=$PWD
command=$PWD/.venv/bin/python $PWD/api/app.py
autostart=true
autorestart=true
stderr_logfile=$PWD/server.err.log
stdout_logfile=$PWD/server.log
EOF

# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update

# 管理服务
sudo supervisorctl start telegram-bot
sudo supervisorctl status telegram-bot
```

### 2. 设置日志轮转

```bash
sudo tee /etc/logrotate.d/telegram-bot > /dev/null <<EOF
${PWD}/server.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $(whoami) $(whoami)
    postrotate
        systemctl reload telegram-bot 2>/dev/null || true
    endscript
}
EOF
```

### 3. 监控和告警

建议设置：
- CPU 使用率超过 70%
- 内存使用超过 80%
- 进程挂掉自动重启
- 日志中出现 "ERROR" 关键字

## 🎉 生产就绪

当前代码已通过测试：
- ✅ HTTP 请求无连接池问题
- ✅ Telegram Bot 端到端测试通过
- ✅ 代理环境正常工作
- ✅ 资源清理正确

**可以安全部署到生产环境！**

---

**部署完成时间**: 2026-02-12
**状态**: ✅ PRODUCTION READY

如有任何问题，请参考 `IMPLEMENTATION_COMPLETE.md` 文档。
