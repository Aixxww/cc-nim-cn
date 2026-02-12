#!/usr/bin/env python3
"""
Telegram Bot 日志配置工具

配置详细的日志记录以帮助监控和调试连接问题
"""

import os
import sys

def setup_telegram_logging():
    """创建日志配置文件"""

    print("🔧 Telegram Bot 日志配置工具")
    print("=" * 40)
    print()

    # 询问日志级别
    print("选择日志级别:")
    print("1. INFO (推荐 - 显示重要信息)")
    print("2. DEBUG (详细 - 显示所有调试信息)")
    print("3. WARNING (仅显示警告和错误)")

    choice = input("\n请输入选择 (1-3，默认1): ").strip() or "1"

    if choice == "2":
        log_level = "DEBUG"
    elif choice == "3":
        log_level = "WARNING"
    else:
        log_level = "INFO"

    print(f"\n✓ 日志级别设置为: {log_level}")

    # 询问日志文件
    log_file = input("是否保存日志到文件？(y/n，默认n): ").strip().lower() or "n"

    if log_file == "y":
        log_file_path = input("请输入日志文件路径 (默认: telegram_bot.log): ").strip() or "telegram_bot.log"
        print(f"✓ 日志将保存到: {log_file_path}")
    else:
        log_file_path = None
        print("✓ 日志仅输出到控制台")

    # 生成日志配置
    config_content = f"""# Telegram Bot Logging Configuration
# 设置环境变量以启用此配置:
# export PYTHONPATH="${{PYTHONPATH}}:$(pwd)"

import logging
import sys

# Telegram HTTP 客户端日志配置
def setup_logging():
    """配置日志记录"""

    # 日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Handler 配置
    handlers = []

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    handlers.append(console_handler)

    # 文件输出（如果配置了）
    {f'file_handler = logging.FileHandler("{log_file_path}")\n    file_handler.setFormatter(log_format)\n    handlers.append(file_handler)' if log_file == "y" else '# 未配置文件日志'}

    # 配置根日志记录器
    logging.basicConfig(
        level=logging.{log_level},
        handlers=handlers,
        force=True  # 重置现有配置
    )

    # 特定模块的日志级别
    {f'logging.getLogger("messaging.telegram_http_client").setLevel(logging.{log_level})' if log_level == "DEBUG" else 'logging.getLogger("messaging.telegram_http_client").setLevel(logging.INFO)'}
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    return True

# 如果使用此配置，在应用启动时调用 setup_logging()
"""

    # 保存配置文件
    config_file = "logging_config.py"
    with open(config_file, "w") as f:
        f.write(config_content)

    print(f"\n✓ 日志配置文件已创建: {config_file}")
    print()
    print("💡 使用方法:")
    print(f"   1. 在主脚本中导入: from {config_file.replace('.py', '')} import setup_logging")
    print("   2. 在应用启动时调用: setup_logging()")
    print("   3. 或直接运行配置: export PYTHONPATH='${PYTHONPATH}:$(pwd)' && python your_app.py")
    print()
    print("📋 配置内容:")
    print("-" * 40)

    # 显示配置文件的前一部分
    with open(config_file) as f:
        print("\n".join(f.read().split("\n")[:20]))

    print("-" * 40)
    print()
    print("✨ 日志配置完成！这将帮助您:")
    print("   • 监控 HTTP 连接行为")
    print("   • 调试代理连接问题")
    print("   • 追踪 'Pool timeout' 错误的出现")
    print()

    return config_file


def create_monitoring_script():
    """创建监控脚本"""

    script_content = '''#!/usr/bin/env python3
"""
Telegram Bot 监控脚本

实时监控日志文件，检测连接池问题
"""

import sys
import re
import time
from pathlib import Path

def monitor_log_file(log_file="telegram_bot.log"):
    """监控日志文件中的连接问题"""

    if not Path(log_file).exists():
        print(f"错误: 日志文件 {log_file} 不存在")
        return

    print(f"🔍 监控日志文件: {log_file}")
    print("按 Ctrl+C 停止监控\n")

    # 连接池错误模式
    error_patterns = {
        "pool_timeout": r"pool timeout",
        "connection_pool_full": r"Connection pool is full",
        "httpcore_error": r"httpcore.*Exception",
        "httpx_error": r"httpx.*Exception",
    }

    error_counts = {key: 0 for key in error_patterns}

    try:
        with open(log_file, 'r') as f:
            # 移动到文件末尾
            f.seek(0, 2)

            while True:
                line = f.readline()

                if not line:
                    time.sleep(0.1)
                    continue

                # 检查是否有连接池相关错误
                found_error = False
                for error_type, pattern in error_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        error_counts[error_type] += 1
                        found_error = True
                        print(f"⚠️  检测到 {error_type}: {error_counts[error_type]} 次")

                # 显示已知良好的日志模式
                if "NonPoolingHTTPRequest" in line:
                    print("📡 使用自定义 HTTP 客户端 (无连接池)")

                elif "TelegramAIOHTTPClient" in line:
                    print("🔗 HTTP 客户端活动")

    except KeyboardInterrupt:
        print("\n\n📊 错误统计:")
        for error_type, count in error_counts.items():
            if count > 0:
                print(f"  {error_type}: {count}")

        print("\n✨ 如果使用自定义 HTTP 客户端后这些错误为 0，说明问题已解决！")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="监控 Telegram Bot 日志")
    parser.add_argument("--log-file", default="telegram_bot.log", help="日志文件路径")

    args = parser.parse_args()
    monitor_log_file(args.log_file)
'''

    script_file = "monitor_bot.py"
    with open(script_file, "w") as f:
        f.write(script_content)

    # 设置执行权限
    import os
    os.chmod(script_file, 0o755)

    print(f"✓ 监控脚本已创建: {script_file}")
    print()
    print("💡 使用方法:")
    print("   python monitor_bot.py --log-file telegram_bot.log")
    print("   或在终端中直接运行: ./monitor_bot.py")
    print()
    print("这个功能将帮助您实时监控连接池错误")

    return script_file


if __name__ == "__main__":
    try:
        # 设置日志
        log_config = setup_telegram_logging()

        # 询问是否创建监控脚本
        print()
        create_monitor = input("是否创建日志监控脚本？(y/n，默认y): ").strip().lower() or "y"
        if create_monitor == "y":
            monitor_script = create_monitoring_script()
            print()
            print("=" * 40)
            print("🎉 所有配置完成！")
            print("📋 总结:")
            print(f"   • 日志配置: {log_config}")
            print(f"   • 监控脚本: {monitor_script}")
            print()
            print("🔧 使用步骤:")
            print("   1. 导入并调用 setup_logging()")
            print("   2. 运行应用并输出到文件")
            print("   3. 使用 monitor_bot.py 监控错误")
        else:
            print()
            print("✓ 日志配置完成！")

    except KeyboardInterrupt:
        print("\n\n🛑 配置已取消")
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
'''

    with open("setup_logging.py", "w") as f:
        f.write(script_content)

    print("✓ 日志配置工具已创建: setup_logging.py")
    print()
    print("🔧 运行日志配置:")
    print("   python setup_logging.py")
    print()
    print("这将帮助您:")
    print("   • 配置详细的日志记录")
    print("   • 创建日志文件")
    print("   • 设置实时监控脚本")
    print("   • 追踪连接池问题")


if __name__ == "__main__":
    setup_telegram_logging()
'''

    with open("setup_logging.py", "w") as f:
        f.write(script_content)

    print("✓ 日志配置工具已创建: setup_logging.py")
    print()
    print("🔧 运行日志配置:")
    print("   python setup_logging.py")
    print()
    print("这将帮助您:")
    print("   • 配置详细的日志记录")
    print("   • 创建日志文件")
    print("   • 设置实时监控脚本")
    print("   • 追踪连接池问题")


if __name__ == "__main__":
    setup_telegram_logging()
