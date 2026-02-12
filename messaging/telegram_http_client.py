"""
Custom Telegram HTTP Client using aiohttp with TRUE no-pooling mode.

This client creates a new connection for each request, completely bypassing
any connection pooling mechanism to avoid issues in proxy environments.
"""

import asyncio
import json
import logging
import weakref
from typing import Optional, Any, Dict, Union
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientSession, ClientTimeout, BasicAuth

logger = logging.getLogger(__name__)


class NonPoolingHTTPClient:
    """
    HTTP client with TRUE no-pooling mode.

    Key differences from the old implementation:
    - Creates a NEW ClientSession for EACH request
    - Creates a NEW TCPConnector for EACH request
    - No shared connections, no reused sessions
    - Each connection is closed immediately after use
    """

    def __init__(
        self,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        total_timeout: float = 30.0,
    ):
        """
        Initialize the HTTP client.

        Note: No persistent session is created. Each request gets its own session.
        """
        self.timeout = ClientTimeout(
            connect=connect_timeout,
            sock_read=read_timeout,
            total=total_timeout,
        )
        self._closed = False

        logger.info(
            f"NonPoolingHTTPClient initialized (no shared connections) "
            f"connect_timeout={connect_timeout}s, read_timeout={read_timeout}s"
        )

    def _create_session(
        self,
        proxy_url: Optional[str] = None,
    ) -> ClientSession:
        """
        Create a fresh ClientSession for a single request.

        Each session has its own connector, ensuring no connection reuse.
        """
        # Create connector with minimal settings - connection will be closed immediately
        connector_kwargs = {
            "force_close": True,  # Force close immediately after use
            "enable_cleanup_closed": True,  # Clean up closed connections
            "limit": 1,  # Only 1 connection allowed per session
            "ssl": False,  # Disable SSL verification for proxy compatibility
        }

        # Parse proxy URL if provided
        proxy = proxy_url
        proxy_auth = None
        if proxy and "@" in proxy:
            # Handle proxy authentication
            # Format: http://user:pass@host:port
            proxy_clean = proxy.split("@")[1]
            auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
                proxy_auth = BasicAuth(login=username, password=password)
            proxy = f"http://{proxy_clean}"

        return ClientSession(
            timeout=self.timeout,
            json_serialize=json.dumps,
            connector=aiohttp.TCPConnector(**connector_kwargs),
            trust_env=True,  # Read from http_proxy/https_proxy env vars
        )

    async def close(self) -> None:
        """Mark client as closed (no-op since we don't have persistent sessions)."""
        self._closed = True
        logger.info("NonPoolingHTTPClient closed (no persistent sessions to close)")

    async def _execute_request(
        self,
        method: str,
        url: str,
        data: Optional[Union[Dict[str, Any], bytes, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        proxy_url: Optional[str] = None,
    ) -> Any:
        """
        Execute an HTTP request with a fresh session.

        This is the core method - ensures each request uses completely new connections.
        """
        if self._closed:
            raise RuntimeError("Client has been closed")

        # Parse proxy for authentication
        proxy = proxy_url
        proxy_auth = None
        if proxy and "@" in proxy:
            proxy_clean = proxy.split("@")[1]
            auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
                proxy_auth = BasicAuth(login=username, password=password)
            proxy = f"http://{proxy_clean}"

        # Create a fresh session for THIS REQUEST ONLY
        # This is the key to avoiding connection pool issues
        async with self._create_session(proxy_url) as session:
            # Prepare request
            kwargs = {
                "headers": headers,
            }

            # Only add proxy if it's set, otherwise let trust_env handle it
            if proxy:
                kwargs["proxy"] = proxy
                if proxy_auth:
                    kwargs["proxy_auth"] = proxy_auth

            # For HTTPS URLs, ensure proxy authentication is properly set
            if proxy and url.startswith("https://"):
                if proxy_auth:
                    kwargs["proxy_auth"] = proxy_auth

            if params:
                kwargs["params"] = params

            if data is not None:
                if isinstance(data, dict):
                    if headers and "application/json" in headers.get("Content-Type", ""):
                        kwargs["json"] = data
                    else:
                        kwargs["data"] = urlencode(data)
                elif isinstance(data, (str, bytes)):
                    kwargs["data"] = data

            # Execute request
            try:
                if method.upper() == "GET":
                    async with session.get(url, **kwargs) as response:
                        return await self._handle_response(response)

                elif method.upper() == "POST":
                    async with session.post(url, **kwargs) as response:
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"Unsupported method: {method}")

            except asyncio.TimeoutError as e:
                raise aiohttp.ClientError(f"Request timeout: {url}") from e
            except Exception as e:
                raise aiohttp.ClientError(f"Request failed: {e}") from e
            finally:
                # Session is closed here by the async with statement
                # No connection will be reused
                pass

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
    ) -> Any:
        """
        Handle HTTP response.

        Returns JSON for successful requests, raises for errors.
        """
        if response.status >= 400:
            try:
                error_text = await response.text()
            except:
                error_text = f"HTTP {response.status}"
            raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")

        # Parse JSON response
        try:
            text = await response.text()
            if text:
                return json.loads(text)
            return {}
        except json.JSONDecodeError as e:
            # If not JSON, return text
            text = await response.text()
            if text:
                return text
            return {}

    async def post_json(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST JSON data."""
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        logger.info(f"POST request: {url}, proxy: {proxy_url}")

        result = await self._execute_request(
            "POST",
            url,
            data=json_data,
            headers=request_headers,
            proxy_url=proxy_url,
        )

        return result if isinstance(result, dict) else {}

    async def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy_url: Optional[str] = None,
    ) -> bytes:
        """POST data."""
        result = await self._execute_request(
            "POST",
            url,
            data=data,
            headers=headers,
            proxy_url=proxy_url,
        )

        if isinstance(result, bytes):
            return result
        elif isinstance(result, str):
            return result.encode()
        else:
            return json.dumps(result).encode()

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy_url: Optional[str] = None,
    ) -> bytes:
        """GET request."""
        result = await self._execute_request(
            "GET",
            url,
            params=params,
            headers=headers,
            proxy_url=proxy_url,
        )

        if isinstance(result, bytes):
            return result
        elif isinstance(result, str):
            return result.encode()
        else:
            return json.dumps(result).encode()


class NonPoolingHTTPRequest:
    """
    HTTP Request interface for python-telegram-bot with NO pooling.

    Integrates with python-telegram-bot's BaseRequest interface using
    our truly non-pooling client.
    """

    def __init__(self, proxy_url: Optional[str] = None):
        """
        Initialize with optional proxy.

        Args:
            proxy_url: Proxy URL (e.g., http://proxy:port or http://user:pass@proxy:port)
        """
        self.client = NonPoolingHTTPClient(
            connect_timeout=15.0,  # Increased for slower networks
            read_timeout=30.0,
            total_timeout=30.0,
        )
        self.proxy = proxy_url
        self._is_closed = False

        logger.info(f"NonPoolingHTTPRequest initialized with proxy: {proxy_url}")

    async def initialize(self) -> None:
        """Initialize (no-op - no persistent session)."""
        if not self._is_closed:
            logger.info("NonPoolingHTTPRequest initialized (no persistent session)")

    async def shutdown(self) -> None:
        """Shutdown the client."""
        if self._is_closed:
            logger.debug("NonPoolingHTTPRequest already shut down")
            return

        self._is_closed = True
        await self.client.close()
        logger.info("NonPoolingHTTPRequest shut down")

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        read_timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        pool_timeout: Optional[float] = None,
        request_data: Optional[Any] = None,
    ) -> Any:
        """
        POST request compatible with python-telegram-bot.

        Args:
            url: URL to post to
            data: Data to send
            read_timeout: Read timeout
            write_timeout: Write timeout (ignored)
            connect_timeout: Connection timeout
            pool_timeout: Pool timeout (ignored - we don't use pools)
            request_data: Additional request data

        Returns:
            The 'result' field from Telegram API response
        """
        # Handle request_data format from python-telegram-bot
        if request_data is not None:
            if hasattr(request_data, "parameters"):
                data = request_data.parameters
            elif hasattr(request_data, "data"):
                data = request_data.data

        # Use the most restrictive timeout
        timeout = None
        if read_timeout or connect_timeout:
            timeout = min(
                filter(None, [read_timeout, connect_timeout]),
                default=30.0
            )

        try:
            result = await self.client.post_json(
                url,
                json_data=data,
                proxy_url=self.proxy,
            )

            # Return the 'result' field if the response has 'ok': True
            # This is what python-telegram-bot expects
            if isinstance(result, dict) and result.get('ok') and 'result' in result:
                return result['result']
            elif isinstance(result, dict) and not result.get('ok'):
                # Error response - return as-is for telegram-bot to handle
                return result
            else:
                # Fallback
                return result

        except Exception as e:
            # Wrap for python-telegram-bot handling
            raise Exception(f"HTTP request failed: {e}") from e

    async def do_request(
        self,
        url: str,
        method: str = "POST",
        request_data: Optional[Any] = None,
        read_timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        pool_timeout: Optional[float] = None,
    ) -> Any:
        """
        Generic request method for python-telegram-bot.
        """
        if method.upper() != "POST":
            raise ValueError(f"Only POST method is supported, got {method}")

        data = None
        if request_data is not None:
            if hasattr(request_data, "parameters"):
                data = request_data.parameters
            elif isinstance(request_data, dict):
                data = request_data

        return await self.post(
            url,
            data=data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
        )

    async def retrieve(self, url: str) -> bytes:
        """Retrieve data from URL (used for file downloads)."""
        return await self.client.get(url, proxy_url=self.proxy)


# Track active requests for debugging
_active_requests = weakref.WeakSet()


async def _track_request(func):
    """Decorator to track active requests."""
    async def wrapper(*args, **kwargs):
        req_id = id(args)
        _active_requests.add(req_id)
        try:
            return await func(*args, **kwargs)
        finally:
            _active_requests.discard(req_id)
    return wrapper
