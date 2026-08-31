"""
Security headers vulnerability scanner.
"""

from typing import Optional
from dash_penetration.crawler.http import HTTPClient
from .scanner import ScanResult, Severity


class SecurityHeadersScanner:
    """Security headers vulnerability scanner."""

    # Required security headers and their purposes
    SECURITY_HEADERS = {
        "content-security-policy": {
            "severity": Severity.HIGH,
            "description": "Prevents XSS, clickjacking, and other code injection attacks",
        },
        "x-frame-options": {
            "severity": Severity.MEDIUM,
            "description": "Prevents clickjacking attacks",
        },
        "x-content-type-options": {
            "severity": Severity.LOW,
            "description": "Prevents MIME-sniffing attacks",
        },
        "strict-transport-security": {
            "severity": Severity.MEDIUM,
            "description": "Enforces HTTPS connections",
        },
        "x-xss-protection": {
            "severity": Severity.LOW,
            "description": "Legacy XSS protection (deprecated but still useful)",
        },
        "referrer-policy": {
            "severity": Severity.LOW,
            "description": "Controls referrer information leakage",
        },
        "permissions-policy": {
            "severity": Severity.INFO,
            "description": "Controls browser features and APIs",
        },
    }

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """Initialize security headers scanner."""
        self.http_client = http_client
        self._own_client = http_client is None

    async def __aenter__(self):
        if self._own_client:
            self.http_client = HTTPClient()
            await self.http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._own_client and self.http_client:
            await self.http_client.__aexit__(exc_type, exc_val, exc_tb)

    async def scan_url(self, url: str) -> list[ScanResult]:
        """
        Scan URL for missing security headers.

        Args:
            url: Target URL

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        try:
            response = await self.http_client.get(url)
            headers = {k.lower(): v for k, v in response.headers.items()}

            # Check for missing security headers
            for header_name, header_info in self.SECURITY_HEADERS.items():
                if header_name not in headers:
                    # Determine where to configure based on hosting
                    config_location = self._get_config_location(url, header_name)
                    results.append(
                        ScanResult(
                            vulnerability_type="Missing Security Header",
                            severity=header_info["severity"],
                            url=url,
                            description=f"Missing security header: {header_name}. "
                            f"{header_info['description']}",
                            evidence=f"Header '{header_name}' not present in response",
                            remediation=f"Add '{header_name}' header to all responses. "
                            f"Configure your web server or application framework appropriately.",
                            cwe_id="CWE-693",
                            confidence=100,
                            form_context=config_location,
                            test_url=f"GET {url}",
                        )
                    )

            # Check for insecure configurations
            if "x-frame-options" in headers:
                value = headers["x-frame-options"].lower()
                if value not in ["deny", "sameorigin"]:
                    config_location = self._get_config_location(url, "x-frame-options")
                    results.append(
                        ScanResult(
                            vulnerability_type="Insecure Security Header Configuration",
                            severity=Severity.MEDIUM,
                            url=url,
                            description=f"X-Frame-Options has insecure value: {value}",
                            evidence=f"X-Frame-Options: {headers['x-frame-options']}",
                            remediation="Set X-Frame-Options to 'DENY' or 'SAMEORIGIN'",
                            cwe_id="CWE-693",
                            confidence=100,
                            form_context=config_location,
                            test_url=f"GET {url}",
                        )
                    )

        except Exception:
            pass

        return results

    def _get_config_location(self, url: str, header_name: str) -> str:
        """Determine where to configure the security header based on hosting."""
        # Parse hosting info from URL
        if "gitlab" in url.lower() and "pages" in url.lower():
            return "GitLab Pages: Configure in _headers file or .gitlab-ci.yml (site-wide setting)"
        elif "github" in url.lower() and "pages" in url.lower():
            return "GitHub Pages: Configure in _headers file in repository root (site-wide setting)"
        elif "cloudflare" in url.lower() or "workers" in url.lower():
            return "Cloudflare Workers: Set headers in worker response (site-wide setting)"
        elif "vercel" in url.lower():
            return "Vercel: Configure in vercel.json or next.config.js headers (site-wide setting)"
        elif "netlify" in url.lower():
            return "Netlify: Configure in _headers or netlify.toml (site-wide setting)"
        else:
            return f"Infrastructure/CDN: Configure {header_name} header at server/CDN level"
