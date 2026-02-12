#!/usr/bin/env python3
"""
直接启动 Telegram Bot 的可靠方式
"""

import os
import sys
import subprocess
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def start_bot():
    """启动 Bot"""
    logger.info("正在启动 Telegram Bot（自定义 HTTP 客户端）")
    
    # 确保在正确目录
    os.chdir('/Users/WiNo/cc-nim')
    
    # 加载环境变量
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')
        logger.info("✅ 环境变量已加载")
    else:
        logger.error("❌ .env 文件未找到")
        return False
    
    # 检查关键变量
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.error("❌ TELEGRAM_BOT_TOKEN 未设置")
        return False
    
    # 启动 Bot
    try:
        logger.info("🚀 运行: .venv/bin/python api/app.py")
        logger.info("=" * 50)
        
        # 使用 subprocess 启动并用 tee 实时输出
        cmd = [".venv/bin/python", "api/app.py"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 实时输出日志
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
        
        process.wait()
        return process.returncode == 0
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Bot 已停止")
        return True
    except Exception as e:
        logger.error(f"启动失败: {e}")
        return False

if __name__ == "__main__":
    success = start_bot()
    sys.exit(0 if success else 1)

