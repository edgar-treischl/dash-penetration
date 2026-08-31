"""
Scope validation for web crawler.

Ensures crawling stays within authorized target domains and paths.
"""

from typing import Optional
from urllib.parse import urlparse


class Scope:
    """Defines the scope of a crawl with allowed/disallowed domains and paths."""

    def __init__(
        self,
        allowed_domains: list[str],
        allowed_paths: Optional[list[str]] = None,
        disallowed_paths: Optional[list[str]] = None,
    ):
        """
        Initialize a Scope.

        Args:
            allowed_domains: List of base domains (e.g.,
                ['example.com', 'api.example.com'])
            allowed_paths: Optional list of path prefixes to allow
                (e.g., ['/api', '/public'])
            disallowed_paths: Optional list of path prefixes to disallow
                (e.g., ['/admin', '/private'])
        """
        if not allowed_domains:
            raise ValueError("At least one allowed domain is required")

        self.allowed_domains = [domain.lower().strip() for domain in allowed_domains]
        self.allowed_paths = [path.lower().strip() for path in (allowed_paths or [])]
        self.disallowed_paths = [path.lower().strip() for path in (disallowed_paths or [])]

    @staticmethod
    def parse_domain_from_url(url: str) -> str:
        """
        Extract domain from URL (with optional port).

        Args:
            url: Full URL

        Returns:
            Domain including port if present (e.g., 'example.com' or 'example.com:8080')

        Raises:
            ValueError: If URL is invalid or has no domain
        """
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError(f"Invalid URL: {url} (no domain found)")
            return parsed.netloc.lower()
        except Exception as e:
            raise ValueError(f"Failed to parse URL: {url}") from e

    def is_domain_allowed(self, url: str) -> bool:
        """
        Check if a URL's domain is in the allowed list.

        Supports exact domain matches and subdomain matches:
        - allowed_domains = ['example.com']
        - https://example.com ✅
        - https://api.example.com ✅
        - https://api.v2.example.com ✅
        - https://other.com ❌

        Args:
            url: Full URL to check

        Returns:
            True if domain is allowed, False otherwise
        """
        try:
            domain = self.parse_domain_from_url(url)
        except ValueError:
            return False

        # Extract just the hostname (remove port for matching)
        hostname = domain.split(":")[0]

        for allowed in self.allowed_domains:
            allowed_hostname = allowed.split(":")[0]

            # Exact match
            if hostname == allowed_hostname:
                return True

            # Subdomain match: hostname ends with .allowed_hostname
            if hostname.endswith(f".{allowed_hostname}"):
                return True

        return False

    def is_path_allowed(self, url: str) -> bool:
        """
        Check if a URL's path is allowed.

        Rules:
        1. If allowed_paths is set, path must match at least one prefix.
        2. If disallowed_paths is set, path must NOT match any prefix.

        Args:
            url: Full URL to check

        Returns:
            True if path is allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.lower() or "/"
        except Exception:
            return False

        # Check disallowed_paths first (exclusion rules take priority)
        for disallowed in self.disallowed_paths:
            if path.startswith(disallowed):
                return False

        # If allowed_paths is empty, allow all paths (unless disallowed above)
        if not self.allowed_paths:
            return True

        # Check allowed_paths (inclusion rules)
        for allowed in self.allowed_paths:
            if path.startswith(allowed):
                return True

        return False

    def is_in_scope(self, url: str) -> bool:
        """
        Check if a URL is within scope (both domain and path).

        Args:
            url: Full URL to check

        Returns:
            True if URL is in scope, False otherwise
        """
        return self.is_domain_allowed(url) and self.is_path_allowed(url)

    @staticmethod
    def from_dict(config: dict) -> "Scope":
        """
        Create a Scope from a configuration dictionary.

        Args:
            config: Dictionary with keys:
                - 'allowed_domains' (required): list of domains
                - 'allowed_paths' (optional): list of path prefixes
                - 'disallowed_paths' (optional): list of path prefixes

        Returns:
            Scope object

        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")

        allowed_domains = config.get("allowed_domains", [])
        if not allowed_domains:
            raise ValueError("'allowed_domains' is required in config")

        if not isinstance(allowed_domains, list):
            raise ValueError("'allowed_domains' must be a list")

        return Scope(
            allowed_domains=allowed_domains,
            allowed_paths=config.get("allowed_paths"),
            disallowed_paths=config.get("disallowed_paths"),
        )

    def to_dict(self) -> dict:
        """
        Serialize Scope to a dictionary.

        Returns:
            Dictionary representation of the scope
        """
        return {
            "allowed_domains": self.allowed_domains,
            "allowed_paths": self.allowed_paths or None,
            "disallowed_paths": self.disallowed_paths or None,
        }

    def __repr__(self) -> str:
        return (
            f"Scope(allowed_domains={self.allowed_domains}, "
            f"allowed_paths={self.allowed_paths}, "
            f"disallowed_paths={self.disallowed_paths})"
        )
