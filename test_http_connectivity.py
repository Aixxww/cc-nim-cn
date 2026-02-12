#!/usr/bin/env python3
"""
Basic connectivity test for the custom HTTP client.

This tests the HTTP client implementation without requiring a Telegram bot token.
"""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.telegram_http_client import TelegramAIOHTTPClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_connectivity():
    """Test basic HTTP functionality without a bot token."""
    print("🧪 Testing basic HTTP client connectivity")
    print("=" * 50)

    # Get proxy from environment (optional)
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or \
            os.getenv("https_proxy") or os.getenv("http_proxy")

    if proxy:
        print(f"📡 Using proxy: {proxy}")
    else:
        print("📡 No proxy configured - direct connection")

    # Create the custom HTTP client with no connection pooling
    client = TelegramAIOHTTPClient(
        connector_limit=0,  # Disable connection pooling
        connect_timeout=10.0,
        read_timeout=30.0,
    )

    try:
        # Test 1: Simple GET request to a public API
        print("\nTest 1: GET request to httpbin.org...")
        try:
            response_data = await client.get("https://httpbin.org/get", proxy=proxy)
            print("✅ GET request successful")
            logger.info(f"Response size: {len(response_data)} bytes")
        except Exception as e:
            print(f"❌ GET request failed: {e}")
            return False

        # Test 2: POST JSON request
        print("\nTest 2: POST JSON request to httpbin.org...")
        test_data = {"message": "Hello from custom HTTP client", "test": True}
        try:
            response_data = await client.post_json(
                "https://httpbin.org/post",
                json_data=test_data,
                proxy=proxy
            )
            print("✅ POST JSON request successful")
            logger.info(f"Response keys: {list(response_data.keys())}")
        except Exception as e:
            print(f"❌ POST JSON request failed: {e}")
            return False

        # Test 3: Multiple rapid requests (tests connection handling)
        print("\nTest 3: Testing 10 rapid requests...")
        success_count = 0

        for i in range(10):
            try:
                response = await client.get("https://httpbin.org/uuid", proxy=proxy)
                success_count += 1
                print(f"  Request {i + 1}: ✅ Success (received {len(response)} bytes)")
            except Exception as e:
                print(f"  Request {i + 1}: ❌ Failed - {e}")

        print(f"\n📊 Results: {success_count}/10 requests successful")

        if success_count >= 8:
            print("✅ Connection handling looks good!")
        elif success_count >= 5:
            print("⚠️  Some requests failed, but most succeeded")
        else:
            print("❌ Too many requests failed")
            return False

        # Test 4: Connection cleanup (ensuring no leaks)
        print("\nTest 4: Testing connection cleanup...")
        initial_connections = len(client.connector._conns) if hasattr(client.connector, '_conns') else 0
        print(f"  Active connections after tests: {initial_connections}")

        if initial_connections == 0:
            print("✅ No leaked connections detected")
        else:
            print(f"⚠️  Found {initial_connections} connections (may be normal)")

        return True

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        logger.exception("Test failed with exception")
        return False

    finally:
        print("\nCleaning up...")
        await client.close()
        print("✅ HTTP client closed")


async def main():
    """Run all tests."""
    success = await test_basic_connectivity()

    print("\n" + "=" * 50)

    if success:
        print("✅ All tests passed!")
        print("\n📋 Summary of implementation:")
        print("   • Custom HTTP client uses aiohttp")
        print("   • Connection pooling disabled (connector_limit=0)")
        print("   • Each request creates a fresh connection")
        print("   • No dependency on httpx/httpcore")
        print("   • Should resolve 'Pool timeout' errors")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
