"""
Open Redirect vulnerability scanner.

Tests for open redirect vulnerabilities where user-supplied URLs
are used in redirects without proper validation, allowing attackers
to redirect users to malicious sites for phishing attacks.
"""

from typing import Optional
from dash_penetration.crawler.http import HTTPClient
from .scanner import ScanResult, Severity


class OpenRedirectScanner:
    """
    Open Redirect vulnerability scanner.

    Detects when applications redirect users to attacker-controlled URLs
    without proper validation. Commonly used for phishing attacks.
    """

    # Common redirect parameter names
    REDIRECT_PARAMS = [
        "redirect",
        "url",
        "next",
        "return",
        "forward",
        "goto",
        "return_to",
        "returnUrl",
        "redirect_to",
        "continueTo",
        "exit",
        "exit_url",
        "target",
        "destination",
        "back",
    ]

    # Test payloads (external domains that indicate open redirect)
    TEST_PAYLOADS = [
        "https://attacker.com",
        "https://evil.example.com",
        "https://malicious.test",
        "http://attacker.com",
        "//attacker.com",
        "//evil.example.com",
    ]

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """
        Initialize Open Redirect scanner.

        Args:
            http_client: Optional HTTP client
        """
        self.http_client = http_client
        self._own_client = http_client is None

    async def __aenter__(self):
        """Async context manager entry."""
        if self._own_client:
            self.http_client = HTTPClient()
            await self.http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_client and self.http_client:
            await self.http_client.__aexit__(exc_type, exc_val, exc_tb)

    def _is_external_domain(self, original_url: str, redirect_target: str) -> bool:
        """
        Check if redirect target is to a different domain than original.

        Args:
            original_url: The original URL that was tested
            redirect_target: The URL in the Location header

        Returns:
            True if redirect is to external domain
        """
        from urllib.parse import urlparse

        # Parse URLs
        try:
            original_domain = urlparse(original_url).netloc.lower()
            target_domain = urlparse(redirect_target).netloc.lower() if redirect_target else ""
        except Exception:
            return False

        # Remove port numbers for comparison
        original_base = original_domain.split(":")[0]
        target_base = target_domain.split(":")[0]

        # Check if domains match (allow subdomains of same root)
        # e.g., example.com redirects to api.example.com = internal
        if original_base == target_base:
            return False

        # Check if target is a subdomain of original
        if target_base.endswith("." + original_base):
            return False

        # Check if original is a subdomain of target (e.g., api.example.com -> example.com)
        if original_base.endswith("." + target_base):
            return False

        # Different domain = external
        return bool(target_domain)

    async def scan_url(self, url: str) -> list[ScanResult]:
        """
        Scan a URL for open redirect vulnerabilities.

        Args:
            url: Target URL to scan

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        # Test each redirect parameter
        for param in self.REDIRECT_PARAMS:
            # Test each payload
            for payload in self.TEST_PAYLOADS:
                try:
                    # Build test URL with redirect parameter
                    separator = "&" if "?" in url else "?"
                    test_url = f"{url}{separator}{param}={payload}"

                    # Make request
                    response = await self.http_client.get(test_url, follow_redirects=False)

                    # Check for redirect response (3xx)
                    status = response.status_code
                    if status in [301, 302, 303, 307, 308]:
                        # Get Location header
                        location = response.headers.get("Location", "").lower()

                        # Check if it redirects to our payload domain
                        if location and self._is_external_domain(url, location):
                            # Verify it's actually our payload or the decoded version
                            if payload.lower() in location or payload.split("/")[-1] in location:
                                results.append(
                                    ScanResult(
                                        vulnerability_type="Open Redirect",
                                        severity=Severity.HIGH,
                                        url=url,
                                        description=f"Open redirect in '{param}'. "
                                        f"User input used to redirect without validation.",
                                        evidence=f"Parameter '{param}' with payload '{payload}' "
                                        f"redirected to {location}",
                                        remediation="Implement whitelist of allowed redirect URLs. "
                                        "Validate all destinations against whitelist. "
                                        "Use URL parsing to ensure same domain. "
                                        "Never redirect to user-supplied URLs without validation.",
                                        cwe_id="CWE-601",
                                        confidence=95,
                                        payload=payload,
                                        parameter=param,
                                        test_url=test_url,
                                        form_context=f"Open redirect on {url}",
                                    )
                                )
                                return results  # Found vulnerability, stop testing

                except Exception:
                    pass

        return results

    async def scan_form(self, form_action: str, form_fields: list) -> list[ScanResult]:
        """
        Scan form submission for open redirect vulnerabilities.

        The redirect typically happens AFTER form submission, so we test
        the form action URL for redirect parameters.

        Args:
            form_action: Form action URL
            form_fields: List of form fields

        Returns:
            List of discovered vulnerabilities
        """
        # Test the form action URL for open redirects
        return await self.scan_url(form_action)
