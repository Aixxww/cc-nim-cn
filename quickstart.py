#!/usr/bin/env python3
"""
Telegram Bot 快速启动脚本

一键配置并启动 Telegram Bot，包含所有自定义 HTTP 客户端功能
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def print_header():
    """打印标题"""
    print("🚀 Telegram Bot 快速启动工具")
    print("=" * 50)
    print()


def check_virtual_environment():
    """检查虚拟环境"""
    print("📦 检查虚拟环境...")

    venv_path = ".venv"
    if Path(venv_path).exists():
        print("✓ 找到虚拟环境: .venv")
        return True
    else:
        print("⚠️  未找到虚拟环境")
        create_venv = input("是否创建虚拟环境？(y/n，默认y): ").strip().lower() or "y"

        if create_venv == "y":
            print("→ 创建虚拟环境...")
            result = subprocess.run([sys.executable, "-m", "venv", venv_path], capture_output=True)
            if result.returncode == 0:
                print("✓ 虚拟环境创建成功")
                return True
            else:
                print("❌ 创建虚拟环境失败")
                return False
        else:
            print("ℹ️  跳过虚拟环境创建")
            return True


def install_dependencies():
    """安装依赖"""
    print("📚 安装依赖...")

    # 检查 requirements.txt
    if Path("requirements.txt").exists():
        print("→ 安装 requirements.txt 中的依赖...")
        pip_cmd = ".venv/bin/pip" if Path(".venv").exists() else "pip"
        result = subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], capture_output=True)
        if result.returncode == 0:
            print("✓ 依赖安装成功")
        else:
            print("❌ 依赖安装失败")
            print(result.stderr.decode())
    else:
        print("⚠️  未找到 requirements.txt")

    # 确保 aiohttp 已安装
    print("→ 检查 aiohttp...")
    python_cmd = ".venv/bin/python" if Path(".venv").exists() else "python"
    result = subprocess.run([python_cmd, "-c", "import aiohttp; print('OK')"], capture_output=True)
    if result.returncode == 0:
        print("✓ aiohttp 已安装")
    else:
        print("→ 安装 aiohttp...")
        pip_cmd = ".venv/bin/pip" if Path(".venv").exists() else "pip"
        result = subprocess.run([pip_cmd, "install", "aiohttp"], capture_output=True)
        if result.returncode == 0:
            print("✓ aiohttp 安装成功")
        else:
            print("❌ aiohttp 安装失败")


def configure_environment():
    """配置环境"""
    print("⚙️  配置环境...")

    # 运行配置脚本
    if Path("configure_env.sh").exists():
        print("→ 运行环境配置...")
        result = subprocess.run(["bash", "configure_env.sh"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ 环境配置完成")
            # 如果创建了 .env 文件，需要 source
            if Path(".env").exists():
                print("→ 加载 .env 文件...")
                with open(".env", "r") as f:
                    for line in f:
                        if "=" in line and not line.startswith("#"):
                            key, value = line.strip().split("=", 1)
                            os.environ[key] = value.strip('"')
                print("✓ .env 文件已加载")
        else:
            print("❌ 环境配置失败")
    else:
        print("⚠️  未找到 configure_env.sh")


def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    print()

    python_cmd = ".venv/bin/python" if Path(".venv").exists() else "python"

    # 运行连通性测试
    if Path("test_http_connectivity.py").exists():
        print("测试 1: HTTP 连通性测试")
        print("-" * 30)
        result = subprocess.run([python_cmd, "test_http_connectivity.py"], capture_output=False)
        print()

        if result.returncode == 0:
            print("✓ HTTP 连通性测试通过")
        else:
            print("❌ HTTP 连通性测试失败")
            return False
    else:
        print("⚠️  未找到 HTTP 连通性测试脚本")

    # 如果配置了 bot token，运行 full bot 测试
    if "TELEGRAM_BOT_TOKEN" in os.environ:
        if Path("test_telegram_bot.py").exists():
            print("测试 2: Telegram Bot 功能测试")
            print("-" * 30)
            print("这将启动 bot 30 秒进行测试...")
            print("按 Ctrl+C 可提前停止")
            print()

            result = subprocess.run([python_cmd, "test_telegram_bot.py"], capture_output=False)
            print()

            if result.returncode == 0:
                print("✓ Telegram Bot 测试通过")
            else:
                print("❌ Telegram Bot 测试失败")
                return False
        else:
            print("⚠️  未找到 Telegram Bot 测试脚本")
    else:
        print("⚠️  未配置 TELEGRAM_BOT_TOKEN，跳过完整 bot 测试")

    return True


def create_launch_script():
    """创建启动脚本"""
    print("📝 创建启动脚本...")

    launch_script = '''#!/bin/bash
# Telegram Bot 启动脚本

echo "🚀 启动 Telegram Bot with 自定义 HTTP 客户端"
echo "============================================"

# 检查环境变量
if [ -z "${TELEGRAM_BOT_TOKEN}" ]; then
    echo "❌ 错误: TELEGRAM_BOT_TOKEN 未设置"
    exit 1
fi

# 如果存在 .env 文件，加载它
if [ -f ".env" ]; then
    echo "📄 加载 .env 文件..."
    source .env
    echo "✓ 环境变量已加载"
fi

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "📦 激活虚拟环境..."
    source .venv/bin/activate
fi

# 启动应用
    echo "🖥️  启动应用..."
    echo "日志级别: ${LOG_LEVEL:-INFO}"
echo "代理: ${HTTPS_PROXY:-未配置}"
echo

# 运行主应用
# 注意：请修改此行以指向您的实际应用入口
python main.py "$@"
'''

    with open("launch.sh", "w") as f:
        f.write(launch_script)

    # 设置执行权限
    os.chmod("launch.sh", 0o755)

    print("✓ 启动脚本已创建: launch.sh")


def main():
    """主函数"""
    print_header()

    # 步骤 1: 检查环境
    if not check_virtual_environment():
        print("\n❌ 虚拟环境检查失败")
        sys.exit(1)

    print()

    # 步骤 2: 安装依赖
    try:
        install_dependencies()
    except Exception as e:
        print(f"\n❌ 依赖安装失败: {e}")
        sys.exit(1)

    print()

    # 步骤 3: 配置环境
    try:
        configure_environment()
    except Exception as e:
        print(f"\n❌ 环境配置失败: {e}")
        sys.exit(1)

    print()

    # 步骤 4: 询问是否运行测试
    print("🧪 是否运行测试验证配置？")
    run_test_choice = input("运行测试 (y/n，默认y): ").strip().lower() or "y"

    if run_test_choice == "y":
        if not run_tests():
            print("\n❌ 测试失败，请检查配置")
            sys.exit(1)
    else:
        print("⏭️  跳过测试")

    print()

    # 步骤 5: 创建启动脚本
    try:
        create_launch_script()
    except Exception as e:
        print(f"\n⚠️  创建启动脚本失败: {e}")

    print()
    print("=" * 50)
    print("🎉 快速启动配置完成！")
    print()
    print("📋 总结:")
    print("   ✓ 虚拟环境检查完毕")
    print("   ✓ 依赖已安装")
    print("   ✓ 环境变量已配置")
    print("   ✓ 测试已运行（可选）")
    print("   ✓ 启动脚本已创建")
    print()
    print("🚀 启动您的 bot:")
    print("   1. 配置完成后: source .env")
    print("   2. 或手动运行: python your_app.py")
    print("   3. 或使用脚本: ./launch.sh")
    print()
    print("📊 监控和调试:")
    print("   • 查看日志输出是否有错误")
    print("   • 运行 python monitor_bot.py --log-file your.log 监控连接问题")
    print("   • 检查日志中是否出现 'NonPoolingHTTPRequest' 确认使用自定义客户端")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 启动过程已中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
