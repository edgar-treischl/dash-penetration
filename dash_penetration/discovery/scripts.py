"""
Script discovery plugin for tracking JavaScript resources.

Categorizes discovered scripts:
- External scripts: URLs pointing to JavaScript files
- Inline scripts: JavaScript code embedded in HTML
- Third-party domains: External script hosts
- Known frameworks: Detects popular JS frameworks/libraries

Useful for identifying JavaScript attack surfaces and dependencies.
"""

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class ScriptReference:
    """Metadata about a discovered script."""

    src: str
    """External script URL (empty for inline scripts)."""

    is_external: bool = True
    """Whether script is external (True) or inline (False)."""

    size: int = 0
    """Size in bytes (for inline scripts, the code size)."""

    framework: str = ""
    """Detected framework/library name if recognizable."""

    is_third_party: bool = False
    """Whether script is hosted on a different domain."""


@dataclass
class ScriptDiscoveryResult:
    """Result of script discovery analysis."""

    external_scripts: list[ScriptReference] = field(default_factory=list)
    """List of external script resources."""

    inline_scripts: list[ScriptReference] = field(default_factory=list)
    """List of inline script blocks."""

    third_party_domains: set[str] = field(default_factory=set)
    """Set of external domains hosting scripts."""

    detected_frameworks: dict[str, int] = field(default_factory=dict)
    """Frameworks detected and their occurrence count."""

    def total_scripts(self) -> int:
        """Return total count of all scripts."""
        return len(self.external_scripts) + len(self.inline_scripts)

    def external_count(self) -> int:
        """Return count of external scripts."""
        return len(self.external_scripts)

    def inline_count(self) -> int:
        """Return count of inline scripts."""
        return len(self.inline_scripts)

    def third_party_count(self) -> int:
        """Return count of third-party domains."""
        return len(self.third_party_domains)

    def get_external_urls(self) -> list[str]:
        """Return list of external script URLs."""
        return sorted([s.src for s in self.external_scripts if s.src])

    def to_dict(self) -> dict:
        """Export result as dictionary."""
        return {
            "total_scripts": self.total_scripts(),
            "external_scripts": self.external_count(),
            "inline_scripts": self.inline_count(),
            "external_urls": self.get_external_urls(),
            "third_party_domains": sorted(self.third_party_domains),
            "detected_frameworks": dict(sorted(self.detected_frameworks.items())),
            "summary": {
                "total": self.total_scripts(),
                "external": self.external_count(),
                "inline": self.inline_count(),
                "third_party_domains": self.third_party_count(),
                "frameworks": len(self.detected_frameworks),
            },
        }


class ScriptDiscovery:
    """
    Analyzes JavaScript resources discovered during crawling.

    Categorizes scripts by type (external/inline), detects frameworks,
    and identifies third-party script dependencies.
    """

    # Common JavaScript frameworks and CDN patterns
    FRAMEWORK_PATTERNS = {
        "jQuery": ["jquery"],
        "React": ["react", "react.js"],
        "Vue": ["vue", "vuejs"],
        "Angular": ["angular"],
        "Bootstrap": ["bootstrap"],
        "Lodash": ["lodash"],
        "D3": ["d3", "d3.js"],
        "Three.js": ["three", "three.js"],
        "Babel": ["babel"],
        "Webpack": ["webpack"],
        "TypeScript": ["typescript"],
        "Chart.js": ["chart", "chartjs"],
        "Moment.js": ["moment"],
        "GSAP": ["gsap"],
        "Axios": ["axios"],
        "Fetch": ["fetch-polyfill"],
    }

    def __init__(self, base_url: str):
        """
        Initialize ScriptDiscovery.

        Args:
            base_url: The starting URL for identifying third-party scripts
        """
        if not base_url:
            raise ValueError("base_url cannot be empty")

        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc.lower()

    def analyze(
        self,
        external_scripts: list[str],
        inline_scripts: list[str] | None = None,
    ) -> ScriptDiscoveryResult:
        """
        Analyze discovered scripts.

        Args:
            external_scripts: List of external script URLs
            inline_scripts: List of inline script code blocks (optional)

        Returns:
            ScriptDiscoveryResult with categorized scripts
        """
        if inline_scripts is None:
            inline_scripts = []

        result = ScriptDiscoveryResult()

        # Process external scripts
        for url in external_scripts:
            if not url:
                continue

            script_ref = ScriptReference(
                src=url,
                is_external=True,
                size=len(url),
            )

            # Detect if third-party
            script_domain = urlparse(url).netloc.lower()
            if script_domain and script_domain != self.base_domain:
                script_ref.is_third_party = True
                result.third_party_domains.add(script_domain)

            # Detect framework
            framework = self._detect_framework(url)
            if framework:
                script_ref.framework = framework
                result.detected_frameworks[framework] = (
                    result.detected_frameworks.get(framework, 0) + 1
                )

            result.external_scripts.append(script_ref)

        # Process inline scripts
        for code in inline_scripts:
            if not code:
                continue

            script_ref = ScriptReference(
                src="",
                is_external=False,
                size=len(code),
            )

            # Detect framework from inline code
            framework = self._detect_framework(code)
            if framework:
                script_ref.framework = framework
                result.detected_frameworks[framework] = (
                    result.detected_frameworks.get(framework, 0) + 1
                )

            result.inline_scripts.append(script_ref)

        return result

    def _detect_framework(self, text: str) -> str:
        """
        Detect frameworks from URL or code snippet.

        Args:
            text: URL or code to analyze

        Returns:
            Framework name if detected, empty string otherwise
        """
        text_lower = text.lower()

        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return framework

        return ""

    def get_all_external_urls(
        self,
        external_scripts: list[str],
        inline_scripts: list[str] | None = None,
    ) -> list[str]:
        """
        Get all external script URLs.

        Args:
            external_scripts: List of external script URLs
            inline_scripts: List of inline script code blocks (optional)

        Returns:
            Sorted list of unique external URLs
        """
        result = self.analyze(external_scripts, inline_scripts)
        return result.get_external_urls()

    def get_third_party_domains(
        self,
        external_scripts: list[str],
        inline_scripts: list[str] | None = None,
    ) -> list[str]:
        """
        Get all third-party domains hosting scripts.

        Args:
            external_scripts: List of external script URLs
            inline_scripts: List of inline script code blocks (optional)

        Returns:
            Sorted list of third-party domains
        """
        result = self.analyze(external_scripts, inline_scripts)
        return sorted(result.third_party_domains)

    def filter_by_domain(self, urls: list[str], domain: str) -> list[str]:
        """
        Filter scripts by hosting domain.

        Args:
            urls: List of script URLs to filter
            domain: Domain to match

        Returns:
            List of URLs hosted on the specified domain
        """
        domain_lower = domain.lower()
        return [url for url in urls if url and urlparse(url).netloc.lower() == domain_lower]

    def filter_by_framework(
        self,
        external_scripts: list[str],
        framework: str,
    ) -> list[str]:
        """
        Filter external scripts by detected framework.

        Args:
            external_scripts: List of external script URLs
            framework: Framework name to filter by

        Returns:
            List of URLs containing the framework
        """
        framework_lower = framework.lower()
        return [url for url in external_scripts if url and framework_lower in url.lower()]
