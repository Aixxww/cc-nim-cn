#!/usr/bin/env python3
"""
Simple test script to verify Telegram bot can receive messages
"""
import asyncio
import os
import sys
import logging

# Load environment variables from .env
from pathlib import Path
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test bot connection
async def test_bot():
    try:
        # Import after setting env vars
        from telegram.ext import Application
        from telegram.error import TelegramError
        from messaging.telegram_http_client import NonPoolingHTTPRequest

        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not set!")
            return False

        # Create bot with custom http client using Application.builder
        proxy_url = os.getenv('HTTPS_PROXY')
        request = NonPoolingHTTPRequest(proxy_url=proxy_url)

        # Build Application with custom request
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(connection_pool_size=8, connect_timeout=30.0, read_timeout=30.0)
        builder = Application.builder().token(token).request(request)
        application = builder.build()

        # Get the bot
        bot = application.bot

        # Test getMe
        me = await bot.get_me()
        logger.info(f"Bot info: {me.username} (ID: {me.id})")

        # Test getUpdates (this will show if we can receive messages)
        updates = await bot.get_updates(timeout=5)
        logger.info(f"Found {len(updates)} pending updates")
        for update in updates:
            if update.message:
                user = update.message.from_user
                sender = user.username if user.username else f"{user.first_name} {user.last_name}"
                logger.info(f" - Message from {sender}: {update.message.text}")

        await request.shutdown()
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    sys.exit(0 if result else 1)
