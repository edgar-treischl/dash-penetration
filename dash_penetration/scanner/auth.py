"""
Authentication vulnerabilities scanner.
"""

from typing import Optional
from dash_penetration.crawler.http import HTTPClient
from .scanner import ScanResult, Severity


class AuthenticationScanner:
    """Authentication vulnerabilities scanner."""

    # Common weak credentials
    WEAK_CREDENTIALS = [
        ("admin", "admin"),
        ("admin", "password"),
        ("admin", "123456"),
        ("root", "root"),
        ("test", "test"),
        ("user", "user"),
        ("guest", "guest"),
    ]

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """Initialize authentication scanner."""
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

    async def scan_login_form(
        self, login_url: str, username_field: str = "username", password_field: str = "password"
    ) -> list[ScanResult]:
        """
        Scan login form for authentication weaknesses.

        Args:
            login_url: Login endpoint URL
            username_field: Username field name
            password_field: Password field name

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        # Test for weak credentials (limit to first 3)
        for username, password in self.WEAK_CREDENTIALS[:3]:
            try:
                response = await self.http_client.post(
                    login_url,
                    data={username_field: username, password_field: password},
                )

                # Check if login succeeded
                # Look for positive success indicators (not just absence of errors)
                if response.status_code in (200, 302):
                    response_text = response.text().lower()

                    # Skip if this is a React/Vue/Angular SPA (returns static HTML shell)
                    is_spa = any(
                        marker in response_text
                        for marker in ['<div id="root"', '<div id="app"', "ng-app", "vue-app"]
                    )

                    if is_spa:
                        # SPA detected - authentication happens client-side, can't test this way
                        continue

                    # Look for positive success indicators
                    success_indicators = [
                        "welcome",
                        "dashboard",
                        "logout",
                        "logged in",
                        "login successful",
                        "session",
                    ]

                    has_success = any(
                        indicator in response_text for indicator in success_indicators
                    )
                    has_failure = any(
                        err in response_text for err in ["invalid", "error", "failed", "incorrect"]
                    )

                    # Only flag if we see clear success indicators
                    if has_success and not has_failure:
                        results.append(
                            ScanResult(
                                vulnerability_type="Weak Authentication Credentials",
                                severity=Severity.CRITICAL,
                                url=login_url,
                                description=f"Weak credentials accepted: {username}/{password}",
                                evidence=f"Login successful with: {username}/{password}",
                                remediation="Enforce strong password policies. "
                                "Change default credentials. Implement account "
                                "lockout after failed attempts.",
                                cwe_id="CWE-521",
                                confidence=95,
                            )
                        )
                        break  # Found weak creds, stop testing

            except Exception:
                pass

        # Test for username enumeration
        try:
            # Test with valid-looking username
            response1 = await self.http_client.post(
                login_url,
                data={username_field: "admin", password_field: "wrongpassword123"},
            )

            # Test with invalid username
            response2 = await self.http_client.post(
                login_url,
                data={
                    username_field: "nonexistentuser9876543",
                    password_field: "wrongpassword123",
                },
            )

            # Different error messages = username enumeration
            if response1.text() != response2.text():
                results.append(
                    ScanResult(
                        vulnerability_type="Username Enumeration",
                        severity=Severity.MEDIUM,
                        url=login_url,
                        description="Login form reveals whether usernames exist through "
                        "different error messages",
                        evidence="Different responses for valid vs invalid usernames",
                        remediation="Use generic error messages for all login failures. "
                        "Return identical responses for both invalid username and "
                        "invalid password.",
                        cwe_id="CWE-203",
                        confidence=80,
                    )
                )

        except Exception:
            pass

        return results
