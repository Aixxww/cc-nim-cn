#!/usr/bin/env python3
"""
Quick test script for the Telegram bot with custom HTTP client.

This script tests the actual Telegram bot functionality.
Usage: ./test_telegram_bot.py
"""

import asyncio
import os
import sys
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from messaging.telegram import TelegramPlatform

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_telegram_bot():
    """Test the Telegram bot with custom HTTP client."""
    print("🤖 Testing Telegram Bot with Custom HTTP Client")
    print("=" * 55)

    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        return False

    user_id = os.getenv("ALLOWED_TELEGRAM_USER_ID")
    if not user_id:
        print("⚠️  ALLOWED_TELEGRAM_USER_ID not set (optional)")

    # Check proxy settings
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or \
            os.getenv("https_proxy") or os.getenv("http_proxy")

    if proxy:
        print(f"📡 Using proxy: {proxy}")
    else:
        print("📡 No proxy configured")

    print(f"📱 Bot token: {bot_token[:10]}...")
    if user_id:
        print(f"👤 Allowed user: {user_id}")

    # Create Telegram platform instance
    telegram = TelegramPlatform()

    try:
        print("\n🔄 Starting Telegram bot...")
        await telegram.start()
        print("✅ Bot started successfully!")

        if user_id:
            print(f"\n💬 Sending test message to user {user_id}...")
            try:
                message_id = await telegram.send_message(
                    user_id,
                    "🧪 **Bot Test Passed!**\n\n"
                    "Custom HTTP client is working correctly:\n"
                    "• No connection pooling\n"
                    "• Fresh connection per request\n"
                    "• No pool timeout errors\n",
                    parse_mode="Markdown"
                )
                print(f"✅ Message sent successfully (ID: {message_id})")
            except Exception as e:
                print(f"❌ Failed to send message: {e}")
                logger.exception("Send message failed")
        else:
            print("\n⏭️  Skipping message test (no user ID)")

        print("\n⏳ Bot will run for 30 seconds. Press Ctrl+C to stop early...")
        await asyncio.sleep(30)

        return True

    except Exception as e:
        print(f"❌ Bot test failed: {e}")
        logger.exception("Bot test failed")
        return False

    finally:
        print("\n🛑 Shutting down bot...")
        try:
            await telegram.stop()
            print("✅ Bot stopped successfully")
        except Exception as e:
            print(f"❌ Error stopping bot: {e}")


async def main():
    """Main test runner."""
    try:
        success = await test_telegram_bot()

        print("\n" + "=" * 55)
        if success:
            print("✅ Telegram bot test completed successfully!")
            return 0
        else:
            print("❌ Telegram bot test failed")
            return 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
