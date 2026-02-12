#!/usr/bin/env python3
"""Test import our custom telegram module"""
import sys
sys.path.append('.')

try:
    from messaging.telegram import TelegramPlatform
    print("✓ Successfully imported TelegramPlatform")

    # Check if NonPoolingHTTPRequest is available
    from messaging.telegram_http_client import NonPoolingHTTPRequest
    print("✓ Successfully imported NonPoolingHTTPRequest")

    # Check if modules are in proper state
    from messaging import telegram
    if telegram.TELEGRAM_AVAILABLE:
        print("✓ TELEGRAM_AVAILABLE = True")
    else:
        print("✗ TELEGRAM_AVAILABLE = False")

    print("\n所有导入检查通过！")

except ImportError as e:
    print(f"✗ 导入错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"✗ 其他错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
