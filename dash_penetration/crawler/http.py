"""
HTTP client wrapper for web crawler.

Provides consistent error handling, timeouts, redirects, and response validation.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, UTC

import httpx

logger = logging.getLogger(__name__)


@dataclass
class HTTPResponse:
    """Represents an HTTP response from a request."""

    url: str
    status_code: int
    content: bytes
    headers: dict
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    elapsed_ms: float = 0.0
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Extract and store content type and length from headers."""
        if not self.content_type:
            self.content_type = self.headers.get("content-type", "").split(";")[0]
        if self.content_length is None:
            try:
                header_length = self.headers.get("content-length")
                if header_length:
                    self.content_length = int(header_length)
                else:
                    self.content_length = len(self.content) if self.content else 0
            except (ValueError, TypeError):
                self.content_length = len(self.content) if self.content else 0
        if not self.timestamp:
            self.timestamp = datetime.now(UTC)

    def text(self) -> str:
        """Decode content as text (UTF-8, with fallback)."""
        try:
            return self.content.decode("utf-8")
        except UnicodeDecodeError:
            return self.content.decode("utf-8", errors="replace")

    def is_html(self) -> bool:
        """Check if response is HTML."""
        return self.content_type and "text/html" in self.content_type

    def is_json(self) -> bool:
        """Check if response is JSON."""
        return self.content_type and "application/json" in self.content_type


class HTTPError(Exception):
    """Base HTTP error."""

    pass


class HTTPConnectionError(HTTPError):
    """Network/connection error."""

    pass


class HTTPTimeoutError(HTTPError):
    """Request timeout."""

    pass


class HTTPSSLError(HTTPError):
    """SSL/certificate error."""

    pass


class HTTPTooManyRedirectsError(HTTPError):
    """Too many redirects."""

    pass


class HTTPStatusError(HTTPError):
    """HTTP error status code (4xx, 5xx)."""

    def __init__(self, status_code: int, url: str, message: str = ""):
        self.status_code = status_code
        self.url = url
        super().__init__(f"HTTP {status_code}: {url} - {message}")


class HTTPClient:
    """
    Async HTTP client wrapper for consistent error handling and configuration.

    Wraps httpx.AsyncClient with:
    - Automatic retry on transient errors
    - Consistent timeout handling
    - Response validation
    - Rate limit detection (429)
    - SSL certificate validation control (for learning)
    """

    def __init__(
        self,
        timeout: float = 10.0,
        follow_redirects: bool = True,
        max_redirects: int = 5,
        verify_ssl: bool = True,
        user_agent: Optional[str] = None,
        max_retries: int = 2,
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds (default 10s)
            follow_redirects: Whether to follow redirects (default True)
            max_redirects: Maximum number of redirects (default 5)
            verify_ssl: Whether to verify SSL certificates (default True)
            user_agent: Custom User-Agent header (default httpx default)
            max_retries: Number of retries for transient errors (default 2)
        """
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        self.verify_ssl = verify_ssl
        self.user_agent = (
            user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self):
        """Initialize the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=self.follow_redirects,
                verify=self.verify_ssl,
                headers={"User-Agent": self.user_agent},
            )
            logger.debug("HTTP client connected")

    async def close(self):
        """Close the async HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("HTTP client closed")

    async def _ensure_client(self):
        """Ensure client is connected."""
        if self._client is None:
            await self.connect()

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        follow_redirects: Optional[bool] = None,
        **kwargs,
    ) -> HTTPResponse:
        """
        Fetch a URL with error handling and retries.

        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            follow_redirects: Override default redirect behavior
            **kwargs: Additional httpx request arguments (headers, data, etc.)

        Returns:
            HTTPResponse object

        Raises:
            HTTPConnectionError: Network/connection error
            HTTPTimeoutError: Request timeout
            HTTPSSLError: SSL certificate error
            HTTPTooManyRedirectsError: Too many redirects
            HTTPStatusError: HTTP error status (if raise_for_status=True in kwargs)
        """
        await self._ensure_client()

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    url,
                    follow_redirects=(
                        follow_redirects if follow_redirects is not None else self.follow_redirects
                    ),
                    **kwargs,
                )

                # Log response
                logger.debug(f"{method} {url} -> {response.status_code}")

                # Create HTTPResponse object
                http_response = HTTPResponse(
                    url=str(response.url),
                    status_code=response.status_code,
                    content=response.content,
                    headers=dict(response.headers),
                    elapsed_ms=response.elapsed.total_seconds() * 1000,
                )

                # Check for rate limiting
                if response.status_code == 429:
                    logger.warning(f"Rate limited (429) on {url}")
                    # Don't raise, return response for caller to handle

                return http_response

            except httpx.ConnectError as e:
                logger.error(f"Connection error on {url} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries:
                    raise HTTPConnectionError(f"Failed to connect to {url}: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

            except httpx.TimeoutException as e:
                logger.error(f"Timeout on {url} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries:
                    raise HTTPTimeoutError(f"Timeout fetching {url}: {e}") from e
                await asyncio.sleep(0.5 * (attempt + 1))

            except httpx.TooManyRedirects as e:
                logger.error(f"Too many redirects on {url}: {e}")
                raise HTTPTooManyRedirectsError(f"Too many redirects on {url}: {e}") from e

            except (httpx.RequestError, httpx.TransportError) as e:
                # SSL errors and other transport errors
                if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                    logger.error(f"SSL error on {url}: {e}")
                    raise HTTPSSLError(f"SSL error fetching {url}: {e}") from e
                logger.error(f"Request error on {url}: {e}")
                raise HTTPError(f"HTTP error fetching {url}: {e}") from e

            except httpx.HTTPError as e:
                logger.error(f"HTTP error on {url}: {e}")
                raise HTTPError(f"HTTP error fetching {url}: {e}") from e

    async def get(self, url: str, **kwargs) -> HTTPResponse:
        """
        Perform a GET request.

        Args:
            url: URL to fetch
            **kwargs: Additional httpx request arguments

        Returns:
            HTTPResponse object
        """
        return await self.fetch(url, method="GET", **kwargs)

    async def post(self, url: str, **kwargs) -> HTTPResponse:
        """
        Perform a POST request.

        Args:
            url: URL to fetch
            **kwargs: Additional httpx request arguments (data, json, etc.)

        Returns:
            HTTPResponse object
        """
        return await self.fetch(url, method="POST", **kwargs)

    async def head(self, url: str, **kwargs) -> HTTPResponse:
        """
        Perform a HEAD request.

        Args:
            url: URL to fetch
            **kwargs: Additional httpx request arguments

        Returns:
            HTTPResponse object
        """
        return await self.fetch(url, method="HEAD", **kwargs)

    async def get_json(self, url: str, **kwargs) -> dict:
        """
        Perform a GET request and parse JSON response.

        Args:
            url: URL to fetch
            **kwargs: Additional httpx request arguments

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response is not valid JSON
        """
        response = await self.get(url, **kwargs)
        try:
            import json

            return json.loads(response.text())
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid JSON from {url}: {e}") from e
