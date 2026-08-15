"""
Tests for URL normalization, deduplication, and caching.
"""

import pytest
from dash_penetration.crawler.urls import (
    normalize_url,
    extract_domain,
    is_duplicate,
    extract_path_and_query,
    URLCache,
)


class TestNormalizeURL:
    """Test URL normalization."""

    def test_basic_url_normalization(self):
        """Test normalizing a basic URL."""
        assert normalize_url("https://example.com/path") == "https://example.com/path"

    def test_scheme_defaults_to_https(self):
        """Test that missing scheme defaults to https."""
        assert normalize_url("example.com/path").startswith("https://")

    def test_scheme_lowercased(self):
        """Test that scheme is lowercased."""
        assert normalize_url("HTTP://example.com").startswith("http://")
        assert normalize_url("HTTPS://example.com").startswith("https://")

    def test_domain_lowercased(self):
        """Test that domain is lowercased."""
        assert "example.com" in normalize_url("https://EXAMPLE.COM/path")
        assert "subdomain.example.com" in normalize_url("https://SUBDOMAIN.EXAMPLE.COM/path")

    def test_fragment_removed(self):
        """Test that fragments are removed."""
        url1 = "https://example.com/path#section1"
        url2 = "https://example.com/path#section2"
        assert normalize_url(url1) == normalize_url(url2)
        assert "#" not in normalize_url(url1)

    def test_query_params_sorted(self):
        """Test that query parameters are sorted."""
        url1 = "https://example.com/path?z=3&a=1&m=2"
        url2 = "https://example.com/path?a=1&m=2&z=3"
        assert normalize_url(url1) == normalize_url(url2)

    def test_trailing_slash_removed_non_root(self):
        """Test that trailing slashes are removed from non-root paths."""
        assert normalize_url("https://example.com/path/") == ("https://example.com/path")

    def test_root_path_preserved(self):
        """Test that root path slash is preserved."""
        normalized = normalize_url("https://example.com")
        assert normalized.endswith("/")

    def test_port_preserved(self):
        """Test that port numbers are preserved."""
        assert ":8080" in normalize_url("https://example.com:8080/path")
        assert ":3000" in normalize_url("https://example.com:3000/api")

    def test_encoded_characters_handled(self):
        """Test that encoded characters are handled correctly."""
        url = "https://example.com/path%20with%20spaces"
        normalized = normalize_url(url)
        assert "example.com" in normalized

    def test_empty_query_params_preserved(self):
        """Test that empty query params are preserved."""
        normalized = normalize_url("https://example.com?key=&other=value")
        assert "key=" in normalized

    def test_invalid_scheme_raises_error(self):
        """Test that invalid scheme raises ValueError."""
        with pytest.raises(ValueError, match="Invalid scheme"):
            normalize_url("ftp://example.com/path")

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            normalize_url("")
        with pytest.raises(ValueError, match="non-empty string"):
            normalize_url(None)

    def test_url_without_domain_raises_error(self):
        """Test that URL without domain raises ValueError."""
        with pytest.raises(ValueError, match="no domain found"):
            normalize_url("https://")

    def test_complex_url_normalization(self):
        """Test normalization of complex URL."""
        url = "HTTPS://USER:PASS@EXAMPLE.COM:443/Path/To/Resource?z=3&a=1#section"
        normalized = normalize_url(url)
        assert normalized.startswith("https://")
        assert "example.com" in normalized
        assert "/Path/To/Resource" in normalized
        assert "#section" not in normalized


class TestExtractDomain:
    """Test domain extraction."""

    def test_basic_domain_extraction(self):
        """Test extracting domain from basic URL."""
        assert extract_domain("https://example.com/path") == "example.com"

    def test_subdomain_extraction(self):
        """Test extracting subdomain-only (not full domain)."""
        # Extract takes the whole netloc minus port
        result = extract_domain("https://api.example.com/path")
        assert result == "api.example.com"

    def test_domain_lowercased(self):
        """Test that domain is lowercased."""
        assert extract_domain("https://EXAMPLE.COM") == "example.com"
        assert extract_domain("https://API.EXAMPLE.COM") == "api.example.com"

    def test_port_removed(self):
        """Test that port is removed."""
        assert extract_domain("https://example.com:8080/path") == "example.com"
        assert extract_domain("http://example.com:3000") == "example.com"

    def test_url_without_scheme_assumed_https(self):
        """Test that URL without scheme is assumed https."""
        assert extract_domain("example.com/path") == "example.com"

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            extract_domain("")

    def test_url_without_domain_raises_error(self):
        """Test that URL without domain raises ValueError."""
        with pytest.raises(ValueError, match="no domain found"):
            extract_domain("https://")


class TestIsDuplicate:
    """Test duplicate URL detection."""

    def test_exact_duplicates(self):
        """Test that exact URLs are detected as duplicates."""
        url = "https://example.com/path"
        assert is_duplicate(url, url) is True

    def test_case_insensitive_duplicates(self):
        """Test that URLs differing only in case are duplicates."""
        assert is_duplicate("https://EXAMPLE.COM/path", "https://example.com/path") is True

    def test_query_param_order_duplicates(self):
        """Test that URLs with differently ordered params are duplicates."""
        assert is_duplicate("https://example.com?a=1&b=2", "https://example.com?b=2&a=1") is True

    def test_fragment_duplicates(self):
        """Test that URLs differing only in fragment are duplicates."""
        assert (
            is_duplicate(
                "https://example.com/path#section1",
                "https://example.com/path#section2",
            )
            is True
        )

    def test_trailing_slash_duplicates(self):
        """Test that URLs differing in trailing slash are duplicates."""
        assert is_duplicate("https://example.com/path/", "https://example.com/path") is True

    def test_different_schemes_not_duplicates(self):
        """Test that different schemes are not duplicates."""
        assert is_duplicate("https://example.com/path", "http://example.com/path") is False

    def test_different_domains_not_duplicates(self):
        """Test that different domains are not duplicates."""
        assert is_duplicate("https://example.com/path", "https://other.com/path") is False

    def test_different_paths_not_duplicates(self):
        """Test that different paths are not duplicates."""
        assert is_duplicate("https://example.com/path1", "https://example.com/path2") is False

    def test_different_query_not_duplicates(self):
        """Test that different query params are not duplicates."""
        assert is_duplicate("https://example.com?a=1", "https://example.com?a=2") is False

    def test_invalid_urls_return_false(self):
        """Test that invalid URLs return False (not duplicates)."""
        assert is_duplicate("not a url", "also not a url") is False
        assert is_duplicate("https://example.com", "invalid") is False


class TestExtractPathAndQuery:
    """Test path and query extraction."""

    def test_extract_path_only(self):
        """Test extracting path from URL without query."""
        path, query = extract_path_and_query("https://example.com/api/users")
        assert path == "/api/users"
        assert query == ""

    def test_extract_query_only(self):
        """Test extracting query from URL."""
        path, query = extract_path_and_query("https://example.com?id=123")
        assert path == "/"
        assert "id=123" in query

    def test_extract_path_and_query(self):
        """Test extracting both path and query."""
        path, query = extract_path_and_query("https://example.com/search?q=test&page=1")
        assert path == "/search"
        assert "q=test" in query
        assert "page=1" in query


class TestURLCache:
    """Test URLCache class."""

    def test_cache_creation(self):
        """Test creating an empty cache."""
        cache = URLCache()
        assert cache.get_size() == 0
        assert len(cache) == 0

    def test_add_new_url(self):
        """Test adding a new URL to cache."""
        cache = URLCache()
        result = cache.add("https://example.com/path")
        assert result is True
        assert cache.get_size() == 1

    def test_add_duplicate_url(self):
        """Test adding a duplicate URL returns False."""
        cache = URLCache()
        cache.add("https://example.com/path")
        result = cache.add("https://example.com/path")
        assert result is False
        assert cache.get_size() == 1

    def test_add_normalized_duplicate(self):
        """Test that normalized duplicates are detected."""
        cache = URLCache()
        cache.add("https://example.com/path")
        result = cache.add("HTTPS://EXAMPLE.COM/path#section")
        assert result is False
        assert cache.get_size() == 1

    def test_has_seen(self):
        """Test checking if URL has been seen."""
        cache = URLCache()
        cache.add("https://example.com/path")
        assert cache.has_seen("https://example.com/path") is True
        assert cache.has_seen("HTTPS://EXAMPLE.COM/path") is True
        assert cache.has_seen("https://example.com/other") is False

    def test_get_count(self):
        """Test getting count of URL additions."""
        cache = URLCache()
        assert cache.get_count("https://example.com") == 0
        cache.add("https://example.com")
        assert cache.get_count("https://example.com") == 1
        cache.add("https://example.com")
        assert cache.get_count("https://example.com") == 2

    def test_get_all_urls(self):
        """Test getting all URLs from cache."""
        cache = URLCache()
        cache.add("https://example.com/path1")
        cache.add("https://example.com/path2")
        cache.add("https://example.com/path1")  # Duplicate
        urls = cache.get_all_urls()
        assert len(urls) == 2
        assert "https://example.com/path1" in urls
        assert "https://example.com/path2" in urls

    def test_clear_cache(self):
        """Test clearing the cache."""
        cache = URLCache()
        cache.add("https://example.com/path")
        assert cache.get_size() == 1
        cache.clear()
        assert cache.get_size() == 0

    def test_cache_contains_operator(self):
        """Test using 'in' operator with cache."""
        cache = URLCache()
        cache.add("https://example.com/path")
        assert "https://example.com/path" in cache
        assert "https://example.com/other" not in cache

    def test_cache_len_operator(self):
        """Test using len() on cache."""
        cache = URLCache()
        assert len(cache) == 0
        cache.add("https://example.com/path1")
        assert len(cache) == 1
        cache.add("https://example.com/path2")
        assert len(cache) == 2
        cache.add("https://example.com/path1")  # Duplicate
        assert len(cache) == 2

    def test_cache_multiple_operations(self):
        """Test cache with multiple operations."""
        cache = URLCache()

        # Add several URLs
        urls = [
            "https://example.com/",
            "https://example.com/users",
            "https://example.com/posts",
            "https://example.com/users?page=1",
            "https://example.com/users?page=2",
        ]

        for url in urls:
            cache.add(url)

        # Check results
        assert cache.get_size() == 5
        assert cache.has_seen("https://example.com")
        assert cache.get_count("https://example.com/users") == 1

        # Try adding duplicates
        assert cache.add("https://EXAMPLE.COM/users") is False
        assert cache.add("https://example.com/users?page=1") is False
        assert cache.get_size() == 5

        # Add new URL
        assert cache.add("https://example.com/new") is True
        assert cache.get_size() == 6

    def test_cache_invalid_url_raises_error(self):
        """Test that invalid URLs raise errors."""
        cache = URLCache()
        with pytest.raises(ValueError, match="no domain found"):
            cache.add("https://")
        with pytest.raises(ValueError, match="no domain found"):
            cache.has_seen("http://")
