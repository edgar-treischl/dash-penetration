"""
API endpoint discovery plugin for identifying API endpoints.

Detects potential API endpoints using multiple heuristics:
- Path patterns: /api/*, /v1/*, /v2/*, /rest/*, /graphql
- Common API domains: api.*, apis.*, rest.*
- HTTP methods: Endpoints returning JSON are likely APIs
- Status codes: 200-299 responses with JSON content-type
- Naming patterns: RESTful path conventions (plurals, resource IDs)

Useful for mapping attack surfaces and identifying backend services.
"""

from dataclasses import dataclass, field
from urllib.parse import urlparse
import re


@dataclass
class APIEndpoint:
    """Metadata about a discovered API endpoint."""

    url: str
    """Full URL of the API endpoint."""

    method: str = "GET"
    """HTTP method (GET, POST, PUT, DELETE, etc.)."""

    content_type: str = ""
    """Content-type of response if known."""

    endpoint_type: str = ""
    """Type: rest, graphql, soap, etc."""

    path_pattern: str = ""
    """The normalized path pattern."""

    version: str = ""
    """API version if detectable (e.g., v1, v2)."""

    is_authenticated: bool = False
    """Whether endpoint likely requires authentication."""

    def to_dict(self) -> dict:
        """Export endpoint as dictionary."""
        return {
            "url": self.url,
            "method": self.method,
            "content_type": self.content_type,
            "type": self.endpoint_type,
            "pattern": self.path_pattern,
            "version": self.version,
            "authenticated": self.is_authenticated,
        }


@dataclass
class APIDiscoveryResult:
    """Result of API endpoint discovery analysis."""

    endpoints: list[APIEndpoint] = field(default_factory=list)
    """List of discovered API endpoints."""

    rest_endpoints: list[APIEndpoint] = field(default_factory=list)
    """Endpoints matching REST patterns."""

    graphql_endpoints: list[APIEndpoint] = field(default_factory=list)
    """GraphQL endpoints."""

    versions_detected: set[str] = field(default_factory=set)
    """Detected API versions."""

    by_method: dict[str, list[APIEndpoint]] = field(default_factory=dict)
    """Endpoints grouped by HTTP method."""

    def total_endpoints(self) -> int:
        """Return total API endpoints found."""
        return len(self.endpoints)

    def rest_count(self) -> int:
        """Return count of REST endpoints."""
        return len(self.rest_endpoints)

    def graphql_count(self) -> int:
        """Return count of GraphQL endpoints."""
        return len(self.graphql_endpoints)

    def get_urls(self) -> list[str]:
        """Return sorted list of all endpoint URLs."""
        return sorted({e.url for e in self.endpoints})

    def to_dict(self) -> dict:
        """Export result as dictionary."""
        return {
            "total_endpoints": self.total_endpoints(),
            "rest_endpoints": self.rest_count(),
            "graphql_endpoints": self.graphql_count(),
            "versions": sorted(self.versions_detected),
            "endpoints": [e.to_dict() for e in self.endpoints],
            "by_method": {
                method: [e.to_dict() for e in endpoints]
                for method, endpoints in sorted(self.by_method.items())
            },
        }


class APIDiscovery:
    """
    Discovers API endpoints from crawled content.

    Uses multiple heuristics to identify potential API endpoints:
    - Path patterns (/api/*, /v1/*, /graphql, etc.)
    - Common API domain patterns
    - HTTP methods and content-types
    - Response characteristics
    """

    # Common API path patterns
    API_PATH_PATTERNS = [
        r"/api/",
        r"/apis/",
        r"/rest/",
        r"/v\d+/",  # /v1, /v2, etc.
        r"/graphql",
        r"/api\.php",
        r"/api\.aspx",
        r"/api\.jsp",
        r"/api\.json",
    ]

    # GraphQL indicators
    GRAPHQL_PATTERNS = [
        "graphql",
        "apollo",
        "schema",
    ]

    # Common API domain patterns
    API_DOMAIN_PATTERNS = [
        r"^api\.",
        r"^apis\.",
        r"^rest\.",
        r"^gateway\.",
        r"^backend\.",
        r"-api\.",
    ]

    def __init__(self, base_url: str):
        """
        Initialize APIDiscovery.

        Args:
            base_url: The starting URL for API detection
        """
        if not base_url:
            raise ValueError("base_url cannot be empty")

        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc.lower()

    def analyze(
        self,
        links: list[str],
        status_codes: dict[str, int] | None = None,
        content_types: dict[str, str] | None = None,
    ) -> APIDiscoveryResult:
        """
        Analyze links for API endpoint patterns.

        Args:
            links: List of discovered URLs
            status_codes: Optional mapping of URL to HTTP status code
            content_types: Optional mapping of URL to content-type header

        Returns:
            APIDiscoveryResult with discovered endpoints
        """
        if status_codes is None:
            status_codes = {}
        if content_types is None:
            content_types = {}

        result = APIDiscoveryResult()
        endpoints = set()  # Deduplicate

        for link in links:
            if not link:
                continue

            # Check if link matches API patterns
            api_endpoint = self._analyze_url(
                link,
                status_codes.get(link, 200),
                content_types.get(link, ""),
            )

            if api_endpoint:
                endpoints.add(link)
                result.endpoints.append(api_endpoint)

                # Categorize by type
                if api_endpoint.endpoint_type == "graphql":
                    result.graphql_endpoints.append(api_endpoint)
                else:
                    result.rest_endpoints.append(api_endpoint)

                # Track version
                if api_endpoint.version:
                    result.versions_detected.add(api_endpoint.version)

                # Group by method
                if api_endpoint.method not in result.by_method:
                    result.by_method[api_endpoint.method] = []
                result.by_method[api_endpoint.method].append(api_endpoint)

        return result

    def _analyze_url(
        self, url: str, status_code: int = 200, content_type: str = ""
    ) -> "APIEndpoint | None":
        """
        Analyze single URL for API characteristics.

        Returns APIEndpoint if matched, None otherwise.
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        domain = parsed.netloc.lower()

        # Check path patterns
        is_api_path = any(re.search(pattern, path) for pattern in self.API_PATH_PATTERNS)

        # Check domain patterns
        is_api_domain = any(re.match(pattern, domain) for pattern in self.API_DOMAIN_PATTERNS)

        # Check for GraphQL
        is_graphql = any(pattern in path for pattern in self.GRAPHQL_PATTERNS)

        # Check content type (JSON is strong indicator of API)
        is_json_response = "json" in content_type.lower()

        # Consider it an API if it matches multiple heuristics
        if not (is_api_path or is_api_domain or is_graphql or is_json_response):
            return None

        endpoint = APIEndpoint(url=url)

        # Detect API type
        if is_graphql:
            endpoint.endpoint_type = "graphql"
        else:
            endpoint.endpoint_type = "rest"

        # Detect version
        version_match = re.search(r"/v(\d+)", path)
        if version_match:
            endpoint.version = f"v{version_match.group(1)}"

        # Set content type
        if content_type:
            endpoint.content_type = content_type

        # Infer method from path patterns (defaults to GET)
        if any(p in path for p in ["post", "create", "submit"]) or path.endswith("/"):
            endpoint.method = "POST"

        # Check if likely requires auth (common auth-related paths)
        auth_indicators = ["auth", "login", "token", "bearer", "oauth"]
        if any(indicator in path for indicator in auth_indicators):
            endpoint.is_authenticated = True

        return endpoint

    def get_by_version(
        self,
        links: list[str],
        version: str,
    ) -> list[APIEndpoint]:
        """
        Get API endpoints matching a specific version.

        Args:
            links: List of discovered URLs
            version: API version to filter (e.g., 'v1', 'v2')

        Returns:
            List of matching APIEndpoint objects
        """
        result = self.analyze(links)
        return [e for e in result.endpoints if e.version == version]

    def get_by_type(
        self,
        links: list[str],
        endpoint_type: str,
    ) -> list[APIEndpoint]:
        """
        Get endpoints of a specific type.

        Args:
            links: List of discovered URLs
            endpoint_type: Type to filter ('rest', 'graphql', etc.)

        Returns:
            List of matching APIEndpoint objects
        """
        result = self.analyze(links)
        return [e for e in result.endpoints if e.endpoint_type == endpoint_type]

    def filter_json_likely(self, links: list[str]) -> list[str]:
        """
        Filter URLs that are likely to return JSON (API candidates).

        Args:
            links: List of discovered URLs

        Returns:
            List of URLs matching API patterns
        """
        result = self.analyze(links)
        return result.get_urls()
