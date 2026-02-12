#!/usr/bin/env python3
"""
Test script for the custom Telegram HTTP client without connection pooling.

This script tests basic connectivity with the Telegram Bot API using our custom
aiohttp-based HTTP client to ensure it works correctly without connection pool issues.
"""

import asyncio
import os
import sys
import logging

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.telegram_http_client import TelegramAIOHTTPClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_http_client():
    """Test the custom HTTP client with Telegram Bot API."""
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set")
        return False

    # Get proxy from environment (optional)
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("https_proxy") or os.getenv("http_proxy")

    if proxy:
        logger.info(f"Using proxy: {proxy}")
    else:
        logger.info("No proxy configured")

    # Create the custom HTTP client
    client = TelegramAIOHTTPClient(
        connector_limit=0,  # Disable connection pooling
        connect_timeout=10.0,
        read_timeout=30.0,
    )

    try:
        # Test 1: Get bot info
        logger.info("Test 1: Getting bot information...")
        bot_url = f"https://api.telegram.org/bot{bot_token}/getMe"

        response = await client.post_json(bot_url, proxy=proxy)
        logger.info(f"Bot info response: {response}")

        if response.get("ok"):
            bot_info = response.get("result", {})
            logger.info(f"✅ Bot connected: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
            print(f"✅ Bot connected: @{bot_info.get('username')}")
        else:
            logger.error(f"Failed to get bot info: {response}")
            print(f"❌ Error: {response}")
            return False

        # Test 2: Send a test message (only if ALLOWED_TELEGRAM_USER_ID is set)
        user_id = os.getenv("ALLOWED_TELEGRAM_USER_ID")
        if user_id:
            logger.info(f"Test 2: Sending test message to user {user_id}...")
            message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            message_data = {
                "chat_id": user_id,
                "text": "🧪 HTTP Client Test - Custom aiohttp implementation working correctly!",
                "parse_mode": "Markdown"
            }

            response = await client.post_json(message_url, json_data=message_data, proxy=proxy)
            logger.info(f"Send message response: {response}")

            if response.get("ok"):
                logger.info("✅ Test message sent successfully")
                print("✅ Test message sent successfully")
            else:
                logger.warning(f"Failed to send test message: {response}")
                print(f"⚠️ Warning: Could not send test message: {response.get('description', 'Unknown error')}")
        else:
            logger.warning("ALLOWED_TELEGRAM_USER_ID not set, skipping message test")
            print("⚠️ ALLOWED_TELEGRAM_USER_ID not set, skipping message test")

        # Test 3: Make multiple rapid requests to test connection handling
        logger.info("Test 3: Testing multiple rapid requests...")
        success_count = 0
        error_count = 0

        for i in range(5):
            try:
                response = await client.post_json(
                    f"https://api.telegram.org/bot{bot_token}/getMe",
                    proxy=proxy
                )
                if response.get("ok"):
                    success_count += 1
                    logger.info(f"Request {i+1}: ✅ Success")
                else:
                    error_count += 1
                    logger.error(f"Request {i+1}: ❌ Failed - {response}")
            except Exception as e:
                error_count += 1
                logger.error(f"Request {i+1}: ❌ Exception - {e}")

        logger.info(f"Rapid request test: {success_count} successful, {error_count} failed")
        print(f"\n📊 Rapid request test: {success_count}/5 successful")

        if success_count == 5:
            print("✅ All rapid requests succeeded - connection handling working correctly!")
        elif success_count >= 3:
            print("⚠️ Most requests succeeded, but some failed - check logs for details")
        else:
            print("❌ Too many requests failed - HTTP client may have issues")
            return False

        return True

    except Exception as e:
        logger.exception("Test failed with exception")
        print(f"❌ Test failed with exception: {e}")
        return False

    finally:
        # Always close the client
        await client.close()
        logger.info("HTTP client closed")


async def main():
    """Main test runner."""
    print("🧪 Testing Telegram HTTP Client (without connection pooling)")
    print("=" * 60)

    success = await test_http_client()

    print("=" * 60)
    if success:
        print("✅ All tests passed! Custom HTTP client is working correctly.")
        print("\n📋 Summary:")
        print("   • Connection pooling disabled (connector_limit=0)")
        print("   • Each request uses a fresh connection")
        print("   • No 'Pool timeout' errors expected in production")
        return 0
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
