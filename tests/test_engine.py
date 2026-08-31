"""
Integration tests for the CrawlEngine.

Tests the complete crawl workflow with mocked HTTP responses.
"""

import pytest
import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from dash_penetration.crawler.engine import CrawlEngine, RateLimiter
from dash_penetration.crawler.scope import Scope
from dash_penetration.crawler.http import HTTPResponse
from dash_penetration.crawler.models import DiscoverySource


# Sample HTML responses
SIMPLE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
    <a href="/page1">Page 1</a>
    <a href="/page2">Page 2</a>
    <form action="/submit" method="POST">
        <input name="username" type="text" required>
        <input name="password" type="password" required>
    </form>
</body>
</html>
"""

API_JSON_RESPONSE = '{"status": "ok", "data": []}'

REDIRECT_HTML = """
<html>
<head><title>Redirect Page</title></head>
<body>
    <a href="/final">Final</a>
</body>
</html>
"""


@pytest.fixture
def scope():
    """Fixture for scope configuration."""
    return Scope(
        allowed_domains=["example.com"],
        allowed_paths=None,
        disallowed_paths=None,
    )


@pytest.fixture
def target_url():
    """Fixture for target URL."""
    return "https://example.com"


@pytest.mark.asyncio
async def test_crawl_engine_initialization(scope, target_url):
    """Test engine initialization."""
    engine = CrawlEngine(target_url, scope)
    assert engine.target_url == target_url
    assert engine.scope == scope
    assert engine.max_concurrency == 5
    assert engine.rate_limit == 10.0


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter token bucket."""
    limiter = RateLimiter(rate=10.0)  # 10 req/s

    # First request should be immediate
    start = datetime.now(UTC).timestamp()
    await limiter.acquire()
    elapsed1 = datetime.now(UTC).timestamp() - start

    # Should be very fast (< 100ms)
    assert elapsed1 < 0.1

    # Consume remaining tokens
    for _ in range(9):
        await limiter.acquire()

    # Next request should wait
    start = datetime.now(UTC).timestamp()
    await limiter.acquire()
    elapsed2 = datetime.now(UTC).timestamp() - start

    # Should wait ~100ms (1/10 second)
    assert elapsed2 >= 0.05  # Some tolerance


@pytest.mark.asyncio
async def test_add_to_queue_valid_url(scope, target_url):
    """Test adding valid URL to queue."""
    engine = CrawlEngine(target_url, scope)

    # Add valid in-scope URL
    added = engine._add_to_queue("https://example.com/page", DiscoverySource.LINK)
    assert added is True
    assert len(engine._url_queue) == 1


@pytest.mark.asyncio
async def test_add_to_queue_duplicate_url(scope, target_url):
    """Test that duplicates are not added to queue."""
    engine = CrawlEngine(target_url, scope)

    # Add URL twice
    added1 = engine._add_to_queue("https://example.com/page", DiscoverySource.LINK)
    added2 = engine._add_to_queue("https://example.com/page", DiscoverySource.LINK)

    assert added1 is True
    assert added2 is False  # Duplicate
    assert len(engine._url_queue) == 1


@pytest.mark.asyncio
async def test_add_to_queue_out_of_scope(scope, target_url):
    """Test that out-of-scope URLs are rejected."""
    engine = CrawlEngine(target_url, scope)

    # Try to add out-of-scope URL
    added = engine._add_to_queue("https://evil.com/page", DiscoverySource.LINK)
    assert added is False
    assert len(engine._url_queue) == 0


@pytest.mark.asyncio
async def test_add_to_queue_invalid_url(scope, target_url):
    """Test that invalid URLs are rejected."""
    engine = CrawlEngine(target_url, scope)

    # Try to add invalid URL
    added = engine._add_to_queue("not a valid url!", DiscoverySource.LINK)
    assert added is False
    assert len(engine._url_queue) == 0


@pytest.mark.asyncio
async def test_add_to_queue_subdomain_allowed(scope, target_url):
    """Test that subdomains are allowed by default."""
    engine = CrawlEngine(target_url, scope)

    # Add URL from subdomain
    added = engine._add_to_queue("https://api.example.com/endpoint", DiscoverySource.LINK)
    assert added is True


@pytest.mark.asyncio
async def test_crawl_single_page(scope, target_url):
    """Test crawling a single page."""
    with patch("dash_penetration.crawler.engine.HTTPClient") as MockHTTPClient:
        # Create mock HTTP response
        mock_response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=SIMPLE_HTML.encode(),
            headers={"content-type": "text/html"},
            content_type="text/html",
        )

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.close = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        MockHTTPClient.return_value = mock_client_instance

        # Mock discovery plugins
        with (
            patch("dash_penetration.crawler.engine.LinkDiscovery") as MockLinkDiscovery,
            patch("dash_penetration.crawler.engine.FormDiscovery") as MockFormDiscovery,
            patch("dash_penetration.crawler.engine.ScriptDiscovery") as MockScriptDiscovery,
            patch("dash_penetration.crawler.engine.APIDiscovery") as MockAPIDiscovery,
        ):

            # Setup mock discoveries (return None/empty results)
            MockLinkDiscovery.return_value.discover = MagicMock(return_value=None)
            MockFormDiscovery.return_value.discover = MagicMock(return_value=None)
            MockScriptDiscovery.return_value.discover = MagicMock(return_value=None)
            MockAPIDiscovery.return_value.discover = MagicMock(return_value=None)

            # Run crawl
            async with CrawlEngine(target_url, scope) as engine:
                result = await engine.crawl()

            # Verify results
            assert result.pages_crawled == 1
            assert len(result.endpoints) > 0
            assert result.target_url == target_url


@pytest.mark.asyncio
async def test_crawl_respects_concurrency(scope, target_url):
    """Test that crawl respects max concurrency."""
    call_count = 0
    max_concurrent = 0
    current_concurrent = 0

    async def mock_get(url, **kwargs):
        nonlocal call_count, max_concurrent, current_concurrent
        call_count += 1
        current_concurrent += 1
        max_concurrent = max(max_concurrent, current_concurrent)
        await asyncio.sleep(0.01)  # Simulate work
        current_concurrent -= 1
        return HTTPResponse(
            url=url,
            status_code=200,
            content=b"test",
            headers={},
        )

    with patch("dash_penetration.crawler.engine.HTTPClient") as MockHTTPClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get = mock_get
        mock_client_instance.close = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        MockHTTPClient.return_value = mock_client_instance

        with (
            patch("dash_penetration.crawler.engine.LinkDiscovery") as MockLinkDiscovery,
            patch("dash_penetration.crawler.engine.FormDiscovery") as MockFormDiscovery,
            patch("dash_penetration.crawler.engine.ScriptDiscovery") as MockScriptDiscovery,
            patch("dash_penetration.crawler.engine.APIDiscovery") as MockAPIDiscovery,
        ):

            MockLinkDiscovery.return_value.discover = MagicMock(return_value=None)
            MockFormDiscovery.return_value.discover = MagicMock(return_value=None)
            MockScriptDiscovery.return_value.discover = MagicMock(return_value=None)
            MockAPIDiscovery.return_value.discover = MagicMock(return_value=None)

            # Add multiple URLs to queue
            engine = CrawlEngine(target_url, scope, max_concurrency=3)
            async with engine:
                for i in range(10):
                    engine._add_to_queue(f"https://example.com/page{i}", DiscoverySource.INITIAL)

                # Mock HTTP client
                engine._http_client = MockHTTPClient.return_value

                result = await engine.crawl()

            # Verify concurrency was respected
            assert max_concurrent <= 3  # Should not exceed max_concurrency
            assert result.pages_crawled > 0


@pytest.mark.asyncio
async def test_crawl_respects_rate_limit(scope, target_url):
    """Test that crawl respects rate limiting."""
    request_times = []

    async def mock_get(url, **kwargs):
        request_times.append(datetime.now(UTC).timestamp())
        return HTTPResponse(
            url=url,
            status_code=200,
            content=b"test",
            headers={},
        )

    with patch("dash_penetration.crawler.engine.HTTPClient") as MockHTTPClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get = mock_get
        mock_client_instance.close = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        MockHTTPClient.return_value = mock_client_instance

        with (
            patch("dash_penetration.crawler.engine.LinkDiscovery") as MockLinkDiscovery,
            patch("dash_penetration.crawler.engine.FormDiscovery") as MockFormDiscovery,
            patch("dash_penetration.crawler.engine.ScriptDiscovery") as MockScriptDiscovery,
            patch("dash_penetration.crawler.engine.APIDiscovery") as MockAPIDiscovery,
        ):

            MockLinkDiscovery.return_value.discover = MagicMock(return_value=None)
            MockFormDiscovery.return_value.discover = MagicMock(return_value=None)
            MockScriptDiscovery.return_value.discover = MagicMock(return_value=None)
            MockAPIDiscovery.return_value.discover = MagicMock(return_value=None)

            # Crawl with low rate limit (2 req/s)
            engine = CrawlEngine(target_url, scope, rate_limit=2.0)
            async with engine:
                for i in range(5):
                    engine._add_to_queue(f"https://example.com/page{i}", DiscoverySource.INITIAL)

                engine._http_client = MockHTTPClient.return_value
                result = await engine.crawl()

            # Verify rate limiting: 5 requests over 2 req/s = ~2.5 seconds
            if len(request_times) > 1:
                total_time = request_times[-1] - request_times[0]
                # Allow some tolerance
                expected_min_time = (len(request_times) - 1) / 2.0
                assert total_time >= expected_min_time * 0.8  # 80% of expected
                assert result.pages_crawled > 0


@pytest.mark.asyncio
async def test_crawl_scope_enforcement(scope, target_url):
    """Test that crawl enforces scope during discovery."""
    with patch("dash_penetration.crawler.engine.HTTPClient") as MockHTTPClient:
        # Response with link to out-of-scope domain
        html = """
        <html>
        <body>
            <a href="https://evil.com/attack">Evil</a>
            <a href="/safe">Safe</a>
        </body>
        </html>
        """

        mock_response = HTTPResponse(
            url="https://example.com",
            status_code=200,
            content=html.encode(),
            headers={"content-type": "text/html"},
            content_type="text/html",
        )

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.close = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        MockHTTPClient.return_value = mock_client_instance

        # Don't mock discovery plugins - let them run naturally
        # The engine's scope checking will filter out evil.com
        async with CrawlEngine(target_url, scope) as engine:
            result = await engine.crawl()

        # Verify only safe URL was added to queue (evil.com should be rejected)
        assert "https://example.com/safe" in engine._seen_urls
        assert "https://evil.com/attack" not in engine._seen_urls
        assert result.pages_crawled >= 0


@pytest.mark.asyncio
async def test_get_progress(scope, target_url):
    """Test progress tracking."""
    engine = CrawlEngine(target_url, scope)

    progress = engine.get_progress()
    assert progress["pages_crawled"] == 0
    assert progress["unique_endpoints"] == 0
    assert progress["queue_size"] == 0
    assert progress["errors"] == 0

    # Add some data
    engine._add_to_queue("https://example.com/page1", DiscoverySource.INITIAL)
    engine._add_to_queue("https://example.com/page2", DiscoverySource.LINK)

    progress = engine.get_progress()
    assert progress["queue_size"] == 2


@pytest.mark.asyncio
async def test_crawl_target_url_out_of_scope():
    """Test that crawl fails if target URL is out of scope."""
    scope = Scope(allowed_domains=["example.com"])
    target_url = "https://evil.com"

    async with CrawlEngine(target_url, scope) as engine:
        with pytest.raises(ValueError, match="out of scope"):
            await engine.crawl()


@pytest.mark.asyncio
async def test_crawl_without_context_manager():
    """Test that crawl fails if not used as context manager."""
    scope = Scope(allowed_domains=["example.com"])
    engine = CrawlEngine("https://example.com", scope)

    with pytest.raises(RuntimeError, match="async context manager"):
        await engine.crawl()
