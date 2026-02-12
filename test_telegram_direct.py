#!/usr/bin/env python3
"""Direct Telegram API test to verify connectivity without custom client"""
import sys
import os
sys.path.append('.')

# Load .env file
from dotenv import load_dotenv
load_dotenv()

import asyncio
from messaging.telegram import TelegramPlatform
from telegram.request import HTTPXRequest

async def test_direct():
    """Test with original HTTPXRequest to verify bot token and connectivity"""
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return

    print(f"✓ Found bot token: {bot_token[:10]}...")

    try:
        # Use original HTTPXRequest
        request = HTTPXRequest(
            connection_pool_size=0,  # Disable pooling
            connect_timeout=30.0,
            read_timeout=60.0,
        )

        # Build Application
        from telegram.ext import Application
        builder = Application.builder().token(bot_token).request(request)
        app = builder.build()

        # Try to get bot info (simple API call)
        await app.bot.initialize()
        bot_info = await app.bot.get_me()
        print(f"✅ Bot connected successfully! Bot info: {bot_info.username}")
        print("✅ Message: Bot token is valid and can connect to Telegram")

        await app.bot.shutdown()

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_direct())
