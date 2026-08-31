"""Tests for crawler/http.py"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from datetime import timedelta

from dash_penetration.crawler.http import (
    HTTPClient,
    HTTPResponse,
    HTTPError,
    HTTPConnectionError,
    HTTPTimeoutError,
    HTTPSSLError,
    HTTPTooManyRedirectsError,
    HTTPStatusError,
)


class TestHTTPResponse:
    """Test HTTPResponse data class."""

    def test_response_creation(self):
        """Test creating an HTTPResponse."""
        response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"Hello World",
            headers={"content-type": "text/html"},
        )
        assert response.url == "https://example.com"
        assert response.status_code == 200
        assert response.content == b"Hello World"

    def test_response_text(self):
        """Test extracting text from response."""
        response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"Hello World",
            headers={},
        )
        assert response.text() == "Hello World"

    def test_response_content_type_extraction(self):
        """Test content-type extraction from headers."""
        response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"<html></html>",
            headers={"content-type": "text/html; charset=utf-8"},
        )
        assert response.content_type == "text/html"

    def test_response_content_length_from_headers(self):
        """Test content-length extraction from headers."""
        response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"test",
            headers={"content-length": "1234"},
        )
        assert response.content_length == 1234

    def test_response_content_length_fallback(self):
        """Test content-length falls back to content size."""
        response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"test",
            headers={},
        )
        assert response.content_length == 4

    def test_response_is_html(self):
        """Test is_html() detection."""
        html_response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"<html></html>",
            headers={"content-type": "text/html"},
        )
        assert html_response.is_html()

        json_response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b'{"key": "value"}',
            headers={"content-type": "application/json"},
        )
        assert not json_response.is_html()

    def test_response_is_json(self):
        """Test is_json() detection."""
        json_response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b'{"key": "value"}',
            headers={"content-type": "application/json"},
        )
        assert json_response.is_json()

        html_response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"<html></html>",
            headers={"content-type": "text/html"},
        )
        assert not html_response.is_json()

    def test_response_text_decoding_fallback(self):
        """Test text() handles invalid UTF-8 with fallback."""
        response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=b"\x80\x81\x82",  # Invalid UTF-8
            headers={},
        )
        text = response.text()
        assert isinstance(text, str)  # Should not raise, returns fallback string


class TestHTTPClientInit:
    """Test HTTPClient initialization."""

    def test_client_creation_with_defaults(self):
        """Test creating client with default settings."""
        client = HTTPClient()
        assert client.timeout == 10.0
        assert client.follow_redirects is True
        assert client.max_redirects == 5
        assert client.verify_ssl is True
        assert client.max_retries == 2

    def test_client_creation_with_custom_settings(self):
        """Test creating client with custom settings."""
        client = HTTPClient(
            timeout=30.0,
            follow_redirects=False,
            max_redirects=3,
            verify_ssl=False,
            max_retries=5,
        )
        assert client.timeout == 30.0
        assert client.follow_redirects is False
        assert client.max_redirects == 3
        assert client.verify_ssl is False
        assert client.max_retries == 5

    def test_client_creation_with_custom_user_agent(self):
        """Test creating client with custom User-Agent."""
        custom_ua = "CustomBot/1.0"
        client = HTTPClient(user_agent=custom_ua)
        assert client.user_agent == custom_ua


@pytest.mark.asyncio
class TestHTTPClientConnect:
    """Test HTTPClient connection management."""

    async def test_connect(self):
        """Test connecting the client."""
        client = HTTPClient()
        assert client._client is None
        await client.connect()
        assert client._client is not None
        await client.close()

    async def test_close(self):
        """Test closing the client."""
        client = HTTPClient()
        await client.connect()
        assert client._client is not None
        await client.close()
        assert client._client is None

    async def test_context_manager(self):
        """Test using client as async context manager."""
        async with HTTPClient() as client:
            assert client._client is not None
        # After exit, client should be closed
        assert client._client is None

    async def test_ensure_client_connects_if_needed(self):
        """Test _ensure_client() connects if not already connected."""
        client = HTTPClient()
        assert client._client is None
        await client._ensure_client()
        assert client._client is not None
        await client.close()


@pytest.mark.asyncio
class TestHTTPClientFetch:
    """Test HTTPClient fetch method with mocked responses."""

    async def test_successful_get_request(self):
        """Test successful GET request."""
        async with HTTPClient() as client:
            # Mock the httpx.AsyncClient.request method
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 200
            mock_httpx_response.content = b"Hello World"
            mock_httpx_response.url = "https://example.com"
            mock_httpx_response.headers = {"content-type": "text/html"}
            mock_httpx_response.elapsed = timedelta(milliseconds=100)

            client._client.request = AsyncMock(return_value=mock_httpx_response)

            response = await client.get("https://example.com")

            assert response.status_code == 200
            assert response.content == b"Hello World"
            assert response.is_html()
            client._client.request.assert_called_once()

    async def test_successful_post_request(self):
        """Test successful POST request."""
        async with HTTPClient() as client:
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 201
            mock_httpx_response.content = b'{"id": 123}'
            mock_httpx_response.url = "https://example.com/api"
            mock_httpx_response.headers = {"content-type": "application/json"}
            mock_httpx_response.elapsed = timedelta(milliseconds=50)

            client._client.request = AsyncMock(return_value=mock_httpx_response)

            response = await client.post("https://example.com/api", json={"test": "data"})

            assert response.status_code == 201
            assert response.is_json()
            client._client.request.assert_called_once()

    async def test_head_request(self):
        """Test HEAD request."""
        async with HTTPClient() as client:
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 200
            mock_httpx_response.content = b""
            mock_httpx_response.url = "https://example.com"
            mock_httpx_response.headers = {"content-type": "text/html"}
            mock_httpx_response.elapsed = timedelta(milliseconds=20)

            client._client.request = AsyncMock(return_value=mock_httpx_response)

            response = await client.head("https://example.com")

            assert response.status_code == 200
            assert response.content == b""

    async def test_rate_limit_detection(self):
        """Test detection of rate limiting (429 status)."""
        async with HTTPClient() as client:
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 429
            mock_httpx_response.content = b"Rate limited"
            mock_httpx_response.url = "https://example.com"
            mock_httpx_response.headers = {"retry-after": "60"}
            mock_httpx_response.elapsed = timedelta(milliseconds=100)

            client._client.request = AsyncMock(return_value=mock_httpx_response)

            response = await client.get("https://example.com")

            # Should return response even with 429 status
            assert response.status_code == 429

    async def test_connection_error(self):
        """Test handling of connection errors."""
        async with HTTPClient(max_retries=0) as client:
            client._client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

            with pytest.raises(HTTPConnectionError, match="Failed to connect"):
                await client.get("https://example.com")

    async def test_connection_error_with_retries(self):
        """Test retry behavior on connection errors."""
        async with HTTPClient(max_retries=2) as client:
            # Fail twice, then succeed
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 200
            mock_httpx_response.content = b"Success"
            mock_httpx_response.url = "https://example.com"
            mock_httpx_response.headers = {}
            mock_httpx_response.elapsed = timedelta(milliseconds=100)

            client._client.request = AsyncMock(
                side_effect=[
                    httpx.ConnectError("Error 1"),
                    httpx.ConnectError("Error 2"),
                    mock_httpx_response,
                ]
            )

            response = await client.get("https://example.com")

            assert response.status_code == 200
            assert response.content == b"Success"
            assert client._client.request.call_count == 3

    async def test_timeout_error(self):
        """Test handling of timeout errors."""
        async with HTTPClient(max_retries=0) as client:
            client._client.request = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            with pytest.raises(HTTPTimeoutError, match="Timeout fetching"):
                await client.get("https://example.com")

    async def test_ssl_error(self):
        """Test handling of SSL errors."""
        async with HTTPClient() as client:
            # In httpx, SSL errors are wrapped in RequestError
            error = httpx.RequestError("SSL: CERTIFICATE_VERIFY_FAILED")
            client._client.request = AsyncMock(side_effect=error)

            with pytest.raises(HTTPSSLError, match="SSL error"):
                await client.get("https://example.com")

    async def test_too_many_redirects(self):
        """Test handling of too many redirects."""
        async with HTTPClient() as client:
            client._client.request = AsyncMock(
                side_effect=httpx.TooManyRedirects("Redirect loop detected")
            )

            with pytest.raises(HTTPTooManyRedirectsError, match="Too many redirects"):
                await client.get("https://example.com")

    async def test_generic_http_error(self):
        """Test handling of generic HTTP errors."""
        async with HTTPClient() as client:
            client._client.request = AsyncMock(side_effect=httpx.HTTPError("Generic HTTP error"))

            with pytest.raises(HTTPError, match="HTTP error fetching"):
                await client.get("https://example.com")

    async def test_redirect_following_override(self):
        """Test override of follow_redirects setting."""
        async with HTTPClient(follow_redirects=True) as client:
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 200
            mock_httpx_response.content = b"Followed"
            mock_httpx_response.url = "https://example.com/redirected"
            mock_httpx_response.headers = {}
            mock_httpx_response.elapsed = timedelta(milliseconds=100)

            client._client.request = AsyncMock(return_value=mock_httpx_response)

            # Override to not follow redirects
            response = await client.get("https://example.com", follow_redirects=False)

            assert response.status_code == 200
            # Verify follow_redirects=False was passed
            call_kwargs = client._client.request.call_args[1]
            assert call_kwargs["follow_redirects"] is False


@pytest.mark.asyncio
class TestHTTPClientConvenience:
    """Test convenience methods."""

    async def test_get_json(self):
        """Test get_json() parsing JSON responses."""
        async with HTTPClient() as client:
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 200
            mock_httpx_response.content = b'{"key": "value", "number": 42}'
            mock_httpx_response.url = "https://example.com/api"
            mock_httpx_response.headers = {"content-type": "application/json"}
            mock_httpx_response.elapsed = timedelta(milliseconds=100)

            client._client.request = AsyncMock(return_value=mock_httpx_response)

            data = await client.get_json("https://example.com/api")

            assert data == {"key": "value", "number": 42}

    async def test_get_json_invalid_json(self):
        """Test get_json() raises on invalid JSON."""
        async with HTTPClient() as client:
            mock_httpx_response = MagicMock()
            mock_httpx_response.status_code = 200
            mock_httpx_response.content = b"Not JSON"
            mock_httpx_response.url = "https://example.com/api"
            mock_httpx_response.headers = {"content-type": "text/html"}
            mock_httpx_response.elapsed = timedelta(milliseconds=100)

            client._client.request = AsyncMock(return_value=mock_httpx_response)

            with pytest.raises(ValueError, match="Invalid JSON"):
                await client.get_json("https://example.com/api")


class TestHTTPStatusError:
    """Test HTTPStatusError exception."""

    def test_http_status_error_creation(self):
        """Test creating HTTPStatusError."""
        error = HTTPStatusError(404, "https://example.com/notfound", "Not Found")
        assert error.status_code == 404
        assert error.url == "https://example.com/notfound"
        assert "404" in str(error)


@pytest.mark.asyncio
class TestHTTPClientErrorMessages:
    """Test error message clarity."""

    async def test_connection_error_message_includes_url(self):
        """Test connection error message includes URL."""
        async with HTTPClient(max_retries=0) as client:
            client._client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

            with pytest.raises(HTTPConnectionError) as exc_info:
                await client.get("https://example.com/api")

            assert "example.com" in str(exc_info.value)

    async def test_timeout_error_message_includes_url(self):
        """Test timeout error message includes URL."""
        async with HTTPClient(max_retries=0) as client:
            client._client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(HTTPTimeoutError) as exc_info:
                await client.get("https://example.com/api")

            assert "example.com" in str(exc_info.value)
