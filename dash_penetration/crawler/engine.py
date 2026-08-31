"""
Main crawler engine orchestrating the entire crawl workflow.

The CrawlEngine manages URL queue, concurrency, rate limiting, and discovery
to perform a complete web crawl within defined scope and constraints.
"""

import asyncio
import logging
from datetime import datetime, UTC
from collections import deque
from urllib.parse import urlparse
from typing import Optional, Set

from .models import (
    CrawlResult,
    Page,
    Endpoint,
    HTTPMethod,
    DiscoverySource,
)
from .urls import URLCache, normalize_url
from .scope import Scope
from .http import HTTPClient, HTTPError
from .parser import HTMLParser
from ..discovery.links import LinkDiscovery
from ..discovery.forms import FormDiscovery
from ..discovery.scripts import ScriptDiscovery
from ..discovery.api import APIDiscovery

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for controlling request rate."""

    def __init__(self, rate: float):
        """
        Initialize rate limiter.

        Args:
            rate: Requests per second (e.g., 10.0 for 10 req/s)
        """
        self.rate = rate
        self.tokens = rate
        self.last_update = None

    async def acquire(self):
        """Acquire a token; wait if necessary."""
        while self.tokens < 1:
            # Refill tokens based on elapsed time
            now = datetime.now(UTC).timestamp()
            if self.last_update is None:
                self.last_update = now
            elapsed = now - self.last_update
            self.tokens += elapsed * self.rate
            self.last_update = now

            if self.tokens < 1:
                await asyncio.sleep(0.01)  # Small sleep to avoid busy waiting

        self.tokens -= 1


class CrawlEngine:
    """
    Main crawler engine orchestrating URL discovery and crawling.

    Manages:
    - URL queue and deduplication
    - Concurrency with semaphore
    - Rate limiting with token bucket
    - Page fetching and parsing
    - Discovery plugin execution
    - Result aggregation
    """

    def __init__(
        self,
        target_url: str,
        scope: Scope,
        rate_limit: float = 10.0,
        max_concurrency: int = 5,
        timeout: float = 10.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize the crawler engine.

        Args:
            target_url: Initial URL to start crawling from
            scope: Scope object defining allowed domains/paths
            rate_limit: Requests per second (default 10)
            max_concurrency: Maximum parallel requests (default 5)
            timeout: HTTP request timeout in seconds (default 10)
            verify_ssl: Whether to verify SSL certificates (default True)
        """
        self.target_url = target_url
        self.scope = scope
        self.rate_limit = rate_limit
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Initialize crawl state
        self._url_queue: deque = deque()
        self._url_cache = URLCache()
        self._seen_urls: Set[str] = set()
        self._processing: Set[str] = set()
        self._result = CrawlResult(
            target_url=target_url,
            scope_domains=scope.allowed_domains,
            start_time=datetime.now(UTC),
        )

        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._rate_limiter = RateLimiter(rate_limit)

        # HTTP client (initialized in __aenter__)
        self._http_client: Optional[HTTPClient] = None

        # Discovery plugins (initialized per-page with base_url)
        # self._link_discovery, etc. initialized in _handle_page

        # Parser (initialized per-page with base_url)
        # self._parser initialized in _handle_page

        logger.debug(f"CrawlEngine initialized for {target_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = HTTPClient(
            timeout=self.timeout,
            follow_redirects=True,
            verify_ssl=self.verify_ssl,
        )
        await self._http_client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.close()

    def _add_to_queue(self, url: str, discovery_source: DiscoverySource) -> bool:
        """
        Add a URL to the crawl queue if in scope and not seen before.

        Args:
            url: URL to add
            discovery_source: How the URL was discovered

        Returns:
            True if URL was added to queue, False if duplicate or out of scope
        """
        try:
            # Normalize the URL
            normalized = normalize_url(url)
        except (ValueError, Exception) as e:
            logger.debug(f"Invalid URL {url}: {e}")
            self._result.errors.append(f"Invalid URL: {url}")
            return False

        # Check if already seen
        if normalized in self._seen_urls:
            return False

        # Check scope
        if not self.scope.is_in_scope(normalized):
            logger.debug(f"URL out of scope: {normalized}")
            return False

        # Add to queue and cache
        self._seen_urls.add(normalized)
        self._url_queue.append((normalized, discovery_source))
        logger.debug(f"Added to queue: {normalized} (source: {discovery_source.value})")
        return True

    async def _handle_page(self, url: str, discovery_source: DiscoverySource) -> Optional[Page]:
        """
        Fetch and process a single page.

        Args:
            url: URL to fetch
            discovery_source: How the URL was discovered

        Returns:
            Page object if successful, None if failed

        Raises:
            Various HTTPError exceptions on network issues
        """
        try:
            # Respect rate limit
            await self._rate_limiter.acquire()

            logger.info(f"Fetching: {url}")

            # Fetch the page
            response = await self._http_client.get(url)

            # Create Page object
            page = Page(
                url=response.url,
                method=HTTPMethod.GET,
                status_code=response.status_code,
                content_type=response.content_type or "unknown",
                headers=response.headers,
                timestamp=response.timestamp,
                discovered_by=discovery_source,
                content_length=response.content_length,
            )

            logger.debug(f"Fetched {url}: {response.status_code}")

            # Extract path from response URL (handle redirects)
            parsed_url = urlparse(response.url)
            path = parsed_url.path or "/"
            query = parsed_url.query

            # Create Endpoint
            endpoint = Endpoint(
                method=HTTPMethod.GET,
                path=f"{path}{'?' + query if query else ''}",
                status_code=response.status_code,
                content_type=response.content_type or "unknown",
            )

            # Parse HTML if applicable
            if response.is_html() and response.content:
                try:
                    html_text = response.text()

                    # Initialize parser with response URL (handles redirects)
                    parser = HTMLParser(response.url)

                    # Extract links
                    links = parser.extract_links(html_text)
                    if links:
                        link_discovery = LinkDiscovery(response.url, self.scope)
                        link_result = link_discovery.analyze(links)

                        # Add internal links to queue
                        for link in link_result.internal_links:
                            self._add_to_queue(link, DiscoverySource.LINK)
                            endpoint.links.append(link)

                        # Track external links (don't crawl, just record)
                        for link in link_result.external_links:
                            endpoint.links.append(link)

                    # Extract and analyze forms
                    forms = parser.extract_forms(html_text)
                    if forms:
                        form_discovery = FormDiscovery(response.url, self.scope)
                        form_result = form_discovery.analyze(forms)

                        if form_result and form_result.endpoints:
                            for form_ep in form_result.endpoints:
                                # Add form action to queue
                                self._add_to_queue(form_ep.action, DiscoverySource.FORM)

                                # Add form to endpoint
                                from .models import Form as ModelForm, FormField

                                form_obj = ModelForm(
                                    action=form_ep.action,
                                    method=HTTPMethod(form_ep.method.upper()),
                                    fields=[
                                        FormField(
                                            name=f.name,
                                            field_type=f.field_type,
                                            value=f.value,
                                            required=f.required,
                                        )
                                        for f in form_ep.fields
                                    ],
                                )
                                endpoint.forms.append(form_obj)

                    # Extract scripts
                    scripts = parser.extract_scripts(html_text)
                    if scripts:
                        script_discovery = ScriptDiscovery(response.url)
                        script_result = script_discovery.analyze(scripts)

                        if script_result:
                            for script_ref in script_result.scripts:
                                if script_ref.src:
                                    self._add_to_queue(script_ref.src, DiscoverySource.SCRIPT)
                                    endpoint.scripts.append(script_ref.src)

                    # Detect API endpoints
                    api_discovery = APIDiscovery(response.url, self.scope)
                    api_result = api_discovery.analyze(html_text)
                    if api_result and api_result.endpoints:
                        endpoint.is_api = True
                        for api_ep in api_result.endpoints:
                            self._add_to_queue(api_ep.path, DiscoverySource.API)

                except Exception as e:
                    logger.warning(f"Error parsing HTML from {url}: {e}")

            # Add endpoint to result
            self._result.add_endpoint(endpoint)
            self._result.pages_crawled += 1

            return page

        except HTTPError as e:
            error_msg = f"HTTP error fetching {url}: {e}"
            logger.error(error_msg)
            self._result.errors.append(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error fetching {url}: {e}"
            logger.error(error_msg)
            self._result.errors.append(error_msg)
            return None

    async def _process_queue(self):
        """Worker coroutine that processes URLs from the queue."""
        while self._url_queue or self._processing:
            # Check if queue has items
            if not self._url_queue:
                await asyncio.sleep(0.1)
                continue

            # Get next URL
            url, discovery_source = self._url_queue.popleft()

            # Skip if already processing
            if url in self._processing:
                continue

            # Acquire semaphore for concurrency control
            async with self._semaphore:
                self._processing.add(url)
                try:
                    await self._handle_page(url, discovery_source)
                finally:
                    self._processing.discard(url)

    async def crawl(self) -> CrawlResult:
        """
        Execute the complete crawl workflow.

        Returns:
            CrawlResult containing all discovered endpoints and metadata

        Raises:
            ValueError: If target_url is invalid or out of scope
            HTTPError: On network errors during crawl
        """
        if not self._http_client:
            raise RuntimeError("CrawlEngine must be used as async context manager")

        logger.info(f"Starting crawl of {self.target_url}")

        # Validate target URL is in scope
        if not self.scope.is_in_scope(self.target_url):
            raise ValueError(f"Target URL {self.target_url} is out of scope")

        # Add initial URL to queue
        self._add_to_queue(self.target_url, DiscoverySource.INITIAL)

        try:
            # Process queue until empty
            await self._process_queue()

            # Set end time
            self._result.end_time = datetime.now(UTC)

            # Log summary
            logger.info(
                f"Crawl complete: {self._result.pages_crawled} pages, "
                f"{len(self._result.endpoints)} unique endpoints"
            )

            return self._result

        except Exception as e:
            logger.error(f"Crawl failed: {e}", exc_info=True)
            self._result.errors.append(f"Crawl failed: {e}")
            self._result.end_time = datetime.now(UTC)
            raise

    def get_progress(self) -> dict:
        """
        Get current crawl progress.

        Returns:
            Dictionary with progress information
        """
        return {
            "pages_crawled": self._result.pages_crawled,
            "unique_endpoints": len(self._result.endpoints),
            "queue_size": len(self._url_queue),
            "processing": len(self._processing),
            "errors": len(self._result.errors),
        }
