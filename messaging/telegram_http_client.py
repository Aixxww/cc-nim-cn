"""
Custom Telegram HTTP Client using aiohttp without connection pooling.

This client bypasses httpx/httpcore to avoid connection pool issues in proxy environments.
"""

import asyncio
import json
import logging
from typing import Optional, Any, Dict, Union
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientTimeout, ClientSession, TCPConnector

logger = logging.getLogger(__name__)


class TelegramAIOHTTPClient:
    """
    Async HTTP client for Telegram Bot API using aiohttp without connection pooling.

    This client creates a new connection for each request, avoiding the connection
    pool issues that occur with httpx/httpcore in proxy environments.
    """

    def __init__(
        self,
        connector_limit: int = 0,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        total_timeout: float = 30.0,
    ):
        """
        Initialize the HTTP client.

        Args:
            connector_limit: Maximum number of connections (0 = no limit, effectively disables pooling)
            connect_timeout: Timeout for establishing connection
            read_timeout: Timeout for reading response
            total_timeout: Total timeout for the request
        """
        # Configure connector with no connection pooling
        # limit=0 means no connection limit (creates new connection each time)
        # use_dns_cache=False to avoid DNS caching issues
        # ttl_dns_cache=0 to disable DNS cache
        self.connector = TCPConnector(
            limit=connector_limit,  # 0 = no connection pooling
            use_dns_cache=False,     # Disable DNS caching
            ttl_dns_cache=0,         # DNS cache TTL
            force_close=True,        # Force close connections after use
            enable_cleanup_closed=True,  # Clean up closed connections
        )

        self.timeout = ClientTimeout(
            connect=connect_timeout,
            sock_read=read_timeout,
            total=total_timeout,
        )

        # We'll create a new session for each request to ensure fresh connections
        self._session: Optional[ClientSession] = None

        logger.info(
            f"TelegramAIOHTTPClient initialized with connection_limit={connector_limit}, "
            f"connect_timeout={connect_timeout}s, read_timeout={read_timeout}s"
        )

    async def _get_session(self) -> ClientSession:
        """Get or create a client session."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                json_serialize=json.dumps,
            )
        return self._session

    async def close(self) -> None:
        """Close the client session and connector."""
        if self._session and not self._session.closed:
            await self._session.close()

        # Close the connector as well
        if self.connector:
            await self.connector.close()

        logger.info("TelegramAIOHTTPClient closed")

    async def post_json(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        POST JSON data to the specified URL.

        Args:
            url: The URL to post to
            json_data: JSON data to send
            headers: Additional headers
            proxy: Proxy URL (e.g., http://proxy:8080)
            timeout: Request timeout (overrides default)

        Returns:
            Parsed JSON response

        Raises:
            aiohttp.ClientError: If the request fails
        """
        session = await self._get_session()

        # Merge headers
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        # Prepare JSON data
        data = json.dumps(json_data) if json_data else None

        # Configure proxy
        proxy_auth = None
        if proxy:
            # Handle proxy with authentication if needed
            if "@" in proxy:
                # Format: http://user:pass@host:port
                proxy_url = proxy.split("@")[1]
                auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                    proxy_auth = aiohttp.BasicAuth(login=username, password=password)
                proxy = f"http://{proxy_url}"

        try:
            async with session.post(
                url,
                data=data,
                headers=request_headers,
                proxy=proxy,
                proxy_auth=proxy_auth,
                timeout=timeout or self.timeout,
            ) as response:
                response_text = await response.text()

                # Check for HTTP errors
                if response.status >= 400:
                    raise aiohttp.ClientError(
                        f"HTTP {response.status}: {response_text}"
                    )

                # Parse JSON response
                try:
                    result = json.loads(response_text)
                    return result
                except json.JSONDecodeError as e:
                    raise aiohttp.ClientError(
                        f"Invalid JSON response: {response_text}"
                    ) from e

        except asyncio.TimeoutError as e:
            raise aiohttp.ClientError(f"Request timeout: {url}") from e
        except Exception as e:
            raise aiohttp.ClientError(f"Request failed: {e}") from e

    async def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bytes:
        """
        POST data to the specified URL.

        Args:
            url: The URL to post to
            data: Data to send (dict will be form-encoded, bytes sent as-is)
            headers: Additional headers
            proxy: Proxy URL
            timeout: Request timeout

        Returns:
            Response content as bytes

        Raises:
            aiohttp.ClientError: If the request fails
        """
        session = await self._get_session()

        # Prepare data
        post_data = None
        if isinstance(data, dict):
            post_data = urlencode(data)
            post_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        elif isinstance(data, bytes):
            post_data = data
            post_headers = {}
        else:
            post_headers = {}

        # Merge headers
        request_headers = post_headers
        if headers:
            request_headers.update(headers)

        # Configure proxy
        proxy_auth = None
        if proxy:
            if "@" in proxy:
                proxy_url = proxy.split("@")[1]
                auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                    proxy_auth = aiohttp.BasicAuth(login=username, password=password)
                proxy = f"http://{proxy_url}"

        try:
            async with session.post(
                url,
                data=post_data,
                headers=request_headers,
                proxy=proxy,
                proxy_auth=proxy_auth,
                timeout=timeout or self.timeout,
            ) as response:
                return await response.read()

        except asyncio.TimeoutError as e:
            raise aiohttp.ClientError(f"Request timeout: {url}") from e
        except Exception as e:
            raise aiohttp.ClientError(f"Request failed: {e}") from e

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> bytes:
        """
        GET request to the specified URL.

        Args:
            url: The URL to get
            params: URL parameters
            headers: Additional headers
            proxy: Proxy URL
            timeout: Request timeout

        Returns:
            Response content as bytes

        Raises:
            aiohttp.ClientError: If the request fails
        """
        session = await self._get_session()

        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Configure proxy
        proxy_auth = None
        if proxy:
            if "@" in proxy:
                proxy_url = proxy.split("@")[1]
                auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                    proxy_auth = aiohttp.BasicAuth(login=username, password=password)
                proxy = f"http://{proxy_url}"

        try:
            async with session.get(
                url,
                params=params,
                headers=request_headers,
                proxy=proxy,
                proxy_auth=proxy_auth,
                timeout=timeout or self.timeout,
            ) as response:
                return await response.read()

        except asyncio.TimeoutError as e:
            raise aiohttp.ClientError(f"Request timeout: {url}") from e
        except Exception as e:
            raise aiohttp.ClientError(f"Request failed: {e}") from e

    async def download_file(
        self,
        url: str,
        destination: str,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Download a file from URL to destination.

        Args:
            url: The URL to download from
            destination: Local file path to save to
            headers: Additional headers
            proxy: Proxy URL
            timeout: Request timeout

        Raises:
            aiohttp.ClientError: If the download fails
        """
        session = await self._get_session()

        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Configure proxy
        proxy_auth = None
        if proxy:
            if "@" in proxy:
                proxy_url = proxy.split("@")[1]
                auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                    proxy_auth = aiohttp.BasicAuth(login=username, password=password)
                proxy = f"http://{proxy_url}"

        try:
            async with session.get(
                url,
                headers=request_headers,
                proxy=proxy,
                proxy_auth=proxy_auth,
                timeout=timeout or self.timeout,
            ) as response:
                if response.status >= 400:
                    raise aiohttp.ClientError(
                        f"HTTP {response.status}: {await response.text()}"
                    )

                # Save to file
                with open(destination, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        except asyncio.TimeoutError as e:
            raise aiohttp.ClientError(f"Download timeout: {url}") from e
        except Exception as e:
            raise aiohttp.ClientError(f"Download failed: {e}") from e


class NonPoolingHTTPRequest:
    """
    HTTP Request class that integrates with python-telegram-bot's BaseRequest interface.

    This class wraps our custom aiohttp client to provide a compatible interface
    for python-telegram-bot.
    """

    def __init__(self, proxy_url: Optional[str] = None):
        """
        Initialize the HTTP request handler.

        Args:
            proxy_url: Optional proxy URL to use for all requests
        """
        self.client = TelegramAIOHTTPClient(
            connector_limit=0,  # Disable connection pooling
            connect_timeout=10.0,
            read_timeout=30.0,
        )
        self.proxy = proxy_url
        self._is_closed = False

        logger.info(f"NonPoolingHTTPRequest initialized with proxy: {proxy_url}")

    async def initialize(self) -> None:
        """Initialize the HTTP client session."""
        if not self._is_closed:
            logger.info("NonPoolingHTTPRequest initialized")

    async def shutdown(self) -> None:
        """Shutdown the HTTP client session."""
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
        POST request compatible with python-telegram-bot's request interface.

        Args:
            url: The URL to post to
            data: The data to send (will be JSON-encoded)
            read_timeout: Timeout for reading response
            write_timeout: Timeout for writing request (ignored, use connect_timeout)
            connect_timeout: Timeout for connection
            pool_timeout: Timeout for getting connection from pool (ignored, we don't use pools)

        Returns:
            The parsed JSON response
        """
        # Handle request_data if provided (from python-telegram-bot)
        if request_data is not None:
            # Extract data from request_data if it has parameters attribute
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
                proxy=self.proxy,
                timeout=timeout,
            )
            # Log the result for debugging
            logger.debug(f"API Response: {result}")

            # Return the result field if the response has 'ok': True
            # python-telegram-bot expects the actual result, not the full response
            if isinstance(result, dict) and result.get('ok') and 'result' in result:
                return result['result']
            elif isinstance(result, dict) and not result.get('ok'):
                # If not ok, return the error (python-telegram-bot will handle it)
                return result
            else:
                # Fallback: return the result as-is
                return result
        except Exception as e:
            # Wrap in a form that python-telegram-bot can handle
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
        Generic request method compatible with python-telegram-bot's interface.

        This is the main method that python-telegram-bot will call.
        """
        if method.upper() != "POST":
            raise ValueError(f"Only POST method is supported, got {method}")

        # Extract data from request_data if it's in the expected format
        data = None
        if request_data is not None:
            # Try to extract parameters from request_data
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
        """
        Retrieve data from URL (used for file downloads).

        Args:
            url: The URL to retrieve from

        Returns:
            The content as bytes
        """
        return await self.client.get(url, proxy=self.proxy)

    async def shutdown(self) -> None:
        """Shutdown the client."""
        await self.client.close()
