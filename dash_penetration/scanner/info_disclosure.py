"""
Information disclosure vulnerability scanner.
"""

from typing import Optional
from dash_penetration.crawler.http import HTTPClient
from .scanner import ScanResult, Severity


class InformationDisclosureScanner:
    """Information disclosure vulnerability scanner."""

    # Sensitive paths to check
    SENSITIVE_PATHS = [
        "/.git/config",
        "/.env",
        "/.git/HEAD",
        "/package.json",
        "/composer.json",
        "/.gitignore",
        "/web.config",
        "/.htaccess",
        "/phpinfo.php",
        "/info.php",
        "/test.php",
        "/debug",
        "/console",
        "/.DS_Store",
        "/backup.sql",
        "/database.sql",
        "/.backup",
        "/config.json",
        "/config.yml",
        "/settings.json",
    ]

    # Sensitive patterns in responses
    SENSITIVE_PATTERNS = {
        "api_key": Severity.CRITICAL,
        "api-key": Severity.CRITICAL,
        "apikey": Severity.CRITICAL,
        "secret": Severity.HIGH,
        "password": Severity.CRITICAL,
        "passwd": Severity.CRITICAL,
        "private_key": Severity.CRITICAL,
        "access_token": Severity.HIGH,
        "database": Severity.MEDIUM,
        "connection string": Severity.HIGH,
        "jdbc:": Severity.MEDIUM,
    }

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """Initialize information disclosure scanner."""
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

    async def scan_url(self, base_url: str) -> list[ScanResult]:
        """
        Scan for information disclosure vulnerabilities.

        Args:
            base_url: Base URL to scan

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        # Remove trailing slash
        base_url = base_url.rstrip("/")

        # Check for sensitive files
        for path in self.SENSITIVE_PATHS:
            try:
                url = f"{base_url}{path}"
                response = await self.http_client.get(url)

                if response.status_code == 200 and len(response.content) > 0:
                    results.append(
                        ScanResult(
                            vulnerability_type="Information Disclosure (Sensitive File)",
                            severity=Severity.HIGH,
                            url=url,
                            description=f"Sensitive file accessible: {path}",
                            evidence=f"File returned HTTP 200 with {len(response.content)} bytes",
                            remediation="Remove or restrict access to sensitive files. "
                            "Configure web server to deny access to version control and config files.",
                            cwe_id="CWE-200",
                            confidence=95,
                        )
                    )

            except Exception:
                pass

        # Check main page for sensitive information
        try:
            response = await self.http_client.get(base_url)
            content = response.text().lower()

            for pattern, severity in self.SENSITIVE_PATTERNS.items():
                if pattern in content:
                    results.append(
                        ScanResult(
                            vulnerability_type="Information Disclosure (Sensitive Data)",
                            severity=severity,
                            url=base_url,
                            description=f"Sensitive pattern detected in response: '{pattern}'",
                            evidence=f"Response contains: '{pattern}'",
                            remediation="Remove sensitive information from responses. "
                            "Use environment variables for secrets. "
                            "Review error messages and debug information.",
                            cwe_id="CWE-200",
                            confidence=70,
                        )
                    )

        except Exception:
            pass

        return results

    async def check_swagger_ui(self, base_url: str) -> list[ScanResult]:
        """
        Check if Swagger/OpenAPI documentation is exposed.

        Args:
            base_url: Base URL

        Returns:
            List of findings
        """
        results = []
        endpoints = ["/", "/swagger", "/api-docs", "/openapi.json", "/swagger.json"]

        for endpoint in endpoints:
            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                response = await self.http_client.get(url)

                if response.status_code == 200:
                    content = response.text().lower()
                    if "swagger" in content or "openapi" in content:
                        results.append(
                            ScanResult(
                                vulnerability_type="Information Disclosure (API Documentation)",
                                severity=Severity.INFO,
                                url=url,
                                description="API documentation (Swagger/OpenAPI) exposed publicly",
                                evidence=f"Swagger/OpenAPI found at {url}",
                                remediation="Consider restricting access to API documentation in production. "
                                "Use authentication or IP whitelisting.",
                                cwe_id="CWE-200",
                                confidence=100,
                            )
                        )
                        break

            except Exception:
                pass

        return results
