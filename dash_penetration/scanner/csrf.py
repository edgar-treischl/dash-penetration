"""
CSRF (Cross-Site Request Forgery) vulnerability scanner.
"""

from typing import Optional
from dash_penetration.crawler.http import HTTPClient
from .scanner import ScanResult, Severity


class CSRFScanner:
    """CSRF vulnerability scanner."""

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """Initialize CSRF scanner."""
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

    async def scan_form(
        self, form_action: str, form_method: str, form_html: str
    ) -> list[ScanResult]:
        """
        Scan a form for CSRF vulnerabilities.

        Args:
            form_action: Form action URL
            form_method: Form method (GET/POST)
            form_html: HTML content of the form

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        # Check for CSRF tokens
        csrf_patterns = [
            "csrf",
            "_token",
            "authenticity_token",
            "csrfmiddlewaretoken",
            "__requestverificationtoken",
        ]

        form_lower = form_html.lower()
        has_csrf_token = any(pattern in form_lower for pattern in csrf_patterns)

        # State-changing methods without CSRF protection
        if form_method.upper() in ["POST", "PUT", "DELETE", "PATCH"] and not has_csrf_token:
            results.append(
                ScanResult(
                    vulnerability_type="CSRF (Cross-Site Request Forgery)",
                    severity=Severity.HIGH,
                    url=form_action,
                    description=f"Form with method {form_method} lacks CSRF protection. "
                    f"Attackers can forge requests on behalf of authenticated users.",
                    evidence="No CSRF token found in form",
                    remediation="Implement CSRF tokens (Synchronizer Token Pattern). "
                    "Use SameSite cookie attribute. "
                    "Verify Origin/Referer headers. "
                    "Require re-authentication for sensitive actions.",
                    cwe_id="CWE-352",
                    confidence=85,
                )
            )

        # GET forms that perform state changes (anti-pattern)
        if form_method.upper() == "GET" and any(
            action_word in form_action.lower()
            for action_word in ["delete", "remove", "update", "create", "add"]
        ):
            results.append(
                ScanResult(
                    vulnerability_type="CSRF (Unsafe HTTP Method)",
                    severity=Severity.MEDIUM,
                    url=form_action,
                    description="Form uses GET method for state-changing operation. "
                    "GET requests should be idempotent and not modify server state.",
                    evidence=f"GET form with action: {form_action}",
                    remediation="Use POST/PUT/DELETE for state-changing operations. "
                    "Implement CSRF protection.",
                    cwe_id="CWE-352",
                    confidence=75,
                )
            )

        return results
