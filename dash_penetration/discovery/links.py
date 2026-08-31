"""
Link discovery plugin for categorizing internal vs external links.

Categorizes discovered links into:
- Internal: links within the same domain/scope
- External: links to different domains
- Dynamic: links with query parameters or fragments

Provides metrics on link distribution and scope adherence.
"""

from dataclasses import dataclass, field
from typing import Set
from urllib.parse import urlparse

from dash_penetration.crawler import Scope


@dataclass
class LinkDiscoveryResult:
    """Result of link discovery analysis."""

    internal_links: Set[str] = field(default_factory=set)
    """URLs pointing to the same domain."""

    external_links: Set[str] = field(default_factory=set)
    """URLs pointing to external domains."""

    dynamic_links: Set[str] = field(default_factory=set)
    """Links with query parameters or fragments."""

    scope_violations: Set[str] = field(default_factory=set)
    """Links that violate scope rules if scope is provided."""

    def total_links(self) -> int:
        """Return total unique links discovered."""
        return len(self.internal_links | self.external_links | self.dynamic_links)

    def internal_count(self) -> int:
        """Return count of internal links."""
        return len(self.internal_links)

    def external_count(self) -> int:
        """Return count of external links."""
        return len(self.external_links)

    def dynamic_count(self) -> int:
        """Return count of dynamic links."""
        return len(self.dynamic_links)

    def violation_count(self) -> int:
        """Return count of scope violations."""
        return len(self.scope_violations)

    def to_dict(self) -> dict:
        """Export result as dictionary."""
        return {
            "internal_links": sorted(self.internal_links),
            "external_links": sorted(self.external_links),
            "dynamic_links": sorted(self.dynamic_links),
            "scope_violations": sorted(self.scope_violations),
            "summary": {
                "total_links": self.total_links(),
                "internal": self.internal_count(),
                "external": self.external_count(),
                "dynamic": self.dynamic_count(),
                "violations": self.violation_count(),
            },
        }


class LinkDiscovery:
    """
    Analyzes links discovered during crawling.

    Categorizes links by type (internal/external/dynamic) and
    checks against scope rules if provided.
    """

    def __init__(self, base_url: str, scope: "Scope | None" = None):
        """
        Initialize LinkDiscovery.

        Args:
            base_url: The starting URL for internal link detection
            scope: Optional Scope object to validate links against
        """
        if not base_url:
            raise ValueError("base_url cannot be empty")

        self.base_url = base_url
        self.scope = scope
        self.base_domain = urlparse(base_url).netloc.lower()

    def analyze(self, links: list[str]) -> LinkDiscoveryResult:
        """
        Analyze a list of links and categorize them.

        Args:
            links: List of absolute URLs to analyze

        Returns:
            LinkDiscoveryResult with categorized links
        """
        if not links:
            return LinkDiscoveryResult()

        result = LinkDiscoveryResult()

        for link in links:
            if not link:
                continue

            # Check if dynamic (has query params or fragment)
            if "?" in link or "#" in link:
                result.dynamic_links.add(link)
            else:
                # Categorize by domain
                link_domain = urlparse(link).netloc.lower()

                if link_domain == self.base_domain:
                    result.internal_links.add(link)
                else:
                    result.external_links.add(link)

            # Check scope if provided
            if self.scope and not self.scope.is_in_scope(link):
                result.scope_violations.add(link)

        return result

    def analyze_by_domain(self, links: list[str]) -> dict[str, list[str]]:
        """
        Group links by their domain.

        Args:
            links: List of absolute URLs to group

        Returns:
            Dictionary mapping domain to list of links
        """
        if not links:
            return {}

        domains = {}
        for link in links:
            if not link:
                continue

            domain = urlparse(link).netloc.lower()
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(link)

        return {k: v for k, v in sorted(domains.items())}

    def filter_internal(self, links: list[str]) -> list[str]:
        """
        Return only internal links.

        Args:
            links: List of absolute URLs to filter

        Returns:
            List of internal links only
        """
        if not links:
            return []

        return [
            link for link in links if link and urlparse(link).netloc.lower() == self.base_domain
        ]

    def filter_external(self, links: list[str]) -> list[str]:
        """
        Return only external links.

        Args:
            links: List of absolute URLs to filter

        Returns:
            List of external links only
        """
        if not links:
            return []

        return [
            link for link in links if link and urlparse(link).netloc.lower() != self.base_domain
        ]

    def filter_dynamic(self, links: list[str]) -> list[str]:
        """
        Return only dynamic links (with query params or fragments).

        Args:
            links: List of absolute URLs to filter

        Returns:
            List of dynamic links only
        """
        if not links:
            return []

        return [link for link in links if link and ("?" in link or "#" in link)]
