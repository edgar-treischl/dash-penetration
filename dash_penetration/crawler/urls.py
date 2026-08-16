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

    Performs the following normalizations: lowercase scheme and domain, default to
    https if no scheme, remove fragment (#), sort query parameters, and remove
    trailing slash from path (except for root).

    Parameters
    ----------
    url : str
        URL to normalize

    Returns
    -------
    str
        Normalized URL string

    Raises
    ------
    ValueError
        If URL is invalid or empty
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

    Parameters
    ----------
    url : str
        URL to extract domain from

    Returns
    -------
    str
        Domain string (e.g., "example.com")

    Raises
    ------
    ValueError
        If URL is invalid
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

    Parameters
    ----------
    url1 : str
        First URL
    url2 : str
        Second URL

    Returns
    -------
    bool
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

    Parameters
    ----------
    url : str
        URL to extract from

    Returns
    -------
    tuple of (str, str)
        Tuple of (path, query_string)

    Raises
    ------
    ValueError
        If URL is invalid
    """
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    return parsed.path, parsed.query


class URLCache:
    """
    Cache for tracking seen URLs and detecting duplicates.

    Efficiently stores URLs and checks for duplicates by normalizing URLs before
    storage, using a set for O(1) lookups, and maintaining count of each unique URL.
    """

    def __init__(self):
        """Initialize empty URL cache."""
        self._seen: Set[str] = set()
        self._url_count: dict[str, int] = {}

    def add(self, url: str) -> bool:
        """
        Add a URL to cache if not already seen.

        Parameters
        ----------
        url : str
            URL to add

        Returns
        -------
        bool
            True if URL was new (not in cache), False if duplicate

        Raises
        ------
        ValueError
            If URL is invalid
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

        Parameters
        ----------
        url : str
            URL to check

        Returns
        -------
        bool
            True if URL is in cache, False otherwise

        Raises
        ------
        ValueError
            If URL is invalid
        """
        normalized = normalize_url(url)
        return normalized in self._seen

    def get_count(self, url: str) -> int:
        """
        Get the number of times a URL has been added to cache.

        Parameters
        ----------
        url : str
            URL to check

        Returns
        -------
        int
            Count of how many times URL was added (0 if not seen)

        Raises
        ------
        ValueError
            If URL is invalid
        """
        normalized = normalize_url(url)
        return self._url_count.get(normalized, 0)

    def get_all_urls(self) -> list[str]:
        """
        Get all unique URLs seen.

        Returns
        -------
        list of str
            List of all normalized URLs in cache
        """
        return sorted(list(self._seen))

    def get_size(self) -> int:
        """
        Get the number of unique URLs in cache.

        Returns
        -------
        int
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

        Parameters
        ----------
        url : str
            URL to check

        Returns
        -------
        bool
            True if URL is in cache, False otherwise

        Raises
        ------
        ValueError
            If URL is invalid
        """
        return self.has_seen(url)

    def __len__(self) -> int:
        """Return the number of unique URLs in cache."""
        return self.get_size()
