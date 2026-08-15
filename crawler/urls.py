"""
URL normalization, deduplication, and caching for crawling.
"""

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Tuple, Set
import logging

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """
    Normalize a URL for consistent comparison and deduplication.

    Performs the following normalizations:
    - Lowercase scheme and domain
    - Default to https if no scheme
    - Remove fragment (#)
    - Sort query parameters
    - Remove trailing slash from path (except for root)

    Args:
        url: URL to normalize

    Returns:
        Normalized URL string

    Raises:
        ValueError: If URL is invalid or empty
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    url = url.strip()

    # Add https if no scheme
    if "://" not in url:
        url = "https://" + url

    parsed = urlparse(url)

    # Validate scheme
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Invalid scheme: {scheme}")

    # Lowercase domain
    netloc = parsed.netloc.lower()
    if not netloc:
        raise ValueError("Invalid URL: no domain found")

    # Normalize path (remove trailing slash except for root)
    path = parsed.path
    if path and path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Parse and sort query parameters
    query = ""
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        # Sort params by key, then flatten to query string
        sorted_params = sorted(params.items())
        query = urlencode(sorted_params, doseq=True)

    # Reconstruct without fragment
    normalized = urlunparse((scheme, netloc, path or "/", "", query, ""))

    return normalized


def extract_domain(url: str) -> str:
    """
    Extract the root domain from a URL.

    Args:
        url: URL to extract domain from

    Returns:
        Domain string (e.g., "example.com")

    Raises:
        ValueError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    url = url.strip()
    parsed = urlparse(url)

    # If no scheme, assume https
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    netloc = parsed.netloc.lower()
    if not netloc:
        raise ValueError("Invalid URL: no domain found")

    # Remove port if present
    domain = netloc.split(":")[0]
    return domain


def is_duplicate(url1: str, url2: str) -> bool:
    """
    Check if two URLs are duplicates after normalization.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if URLs are duplicates, False otherwise
    """
    try:
        norm1 = normalize_url(url1)
        norm2 = normalize_url(url2)
        return norm1 == norm2
    except ValueError:
        # If either URL is invalid, they're not duplicates
        return False


def extract_path_and_query(url: str) -> Tuple[str, str]:
    """
    Extract path and query string from a URL.

    Args:
        url: URL to extract from

    Returns:
        Tuple of (path, query_string)

    Raises:
        ValueError: If URL is invalid
    """
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    return parsed.path, parsed.query


class URLCache:
    """
    Cache for tracking seen URLs and detecting duplicates.

    Efficiently stores URLs and checks for duplicates by:
    - Normalizing URLs before storage
    - Using a set for O(1) lookups
    - Maintaining count of each unique URL
    """

    def __init__(self):
        """Initialize empty URL cache."""
        self._seen: Set[str] = set()
        self._url_count: dict[str, int] = {}

    def add(self, url: str) -> bool:
        """
        Add a URL to cache if not already seen.

        Args:
            url: URL to add

        Returns:
            True if URL was new (not in cache), False if duplicate

        Raises:
            ValueError: If URL is invalid
        """
        normalized = normalize_url(url)

        if normalized in self._seen:
            self._url_count[normalized] += 1
            return False

        self._seen.add(normalized)
        self._url_count[normalized] = 1
        return True

    def has_seen(self, url: str) -> bool:
        """
        Check if URL has been seen before.

        Args:
            url: URL to check

        Returns:
            True if URL is in cache, False otherwise

        Raises:
            ValueError: If URL is invalid
        """
        normalized = normalize_url(url)
        return normalized in self._seen

    def get_count(self, url: str) -> int:
        """
        Get the number of times a URL has been added to cache.

        Args:
            url: URL to check

        Returns:
            Count of how many times URL was added (0 if not seen)

        Raises:
            ValueError: If URL is invalid
        """
        normalized = normalize_url(url)
        return self._url_count.get(normalized, 0)

    def get_all_urls(self) -> list[str]:
        """
        Get all unique URLs seen.

        Returns:
            List of all normalized URLs in cache
        """
        return sorted(list(self._seen))

    def get_size(self) -> int:
        """
        Get the number of unique URLs in cache.

        Returns:
            Count of unique URLs
        """
        return len(self._seen)

    def clear(self) -> None:
        """Clear all cached URLs."""
        self._seen.clear()
        self._url_count.clear()

    def __contains__(self, url: str) -> bool:
        """
        Support 'in' operator to check if URL is in cache.

        Args:
            url: URL to check

        Returns:
            True if URL is in cache, False otherwise

        Raises:
            ValueError: If URL is invalid
        """
        return self.has_seen(url)

    def __len__(self) -> int:
        """Return the number of unique URLs in cache."""
        return self.get_size()
