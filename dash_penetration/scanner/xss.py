"""
Cross-Site Scripting (XSS) vulnerability scanner.

Tests for:
- Reflected XSS
- Stored XSS (basic detection)
- DOM-based XSS (with JavaScript analysis)
"""

from typing import Optional
from dash_penetration.crawler.http import HTTPClient
from .scanner import ScanResult, Severity


class XSSScanner:
    """
    Cross-Site Scripting (XSS) vulnerability scanner.
    """

    # XSS test payloads
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input autofocus onfocus=alert('XSS')>",
        "'\"><script>alert('XSS')</script>",
        "<script>alert(String.fromCharCode(88,83,83))</script>",
        "<img src=x onerror=alert(document.domain)>",
        "<svg/onload=alert('XSS')>",
        "<<SCRIPT>alert('XSS');//<</SCRIPT>",
        "<script>alert`XSS`</script>",
        "<img src=\"javascript:alert('XSS')\">",
        "<marquee onstart=alert('XSS')>",
    ]

    # Encoded payloads
    ENCODED_PAYLOADS = [
        "%3Cscript%3Ealert('XSS')%3C/script%3E",
        "&#60;script&#62;alert('XSS')&#60;/script&#62;",
        "&lt;script&gt;alert('XSS')&lt;/script&gt;",
    ]

    # DOM-based XSS patterns
    DOM_XSS_SINKS = [
        "innerHTML",
        "outerHTML",
        "document.write",
        "document.writeln",
        "eval(",
        "setTimeout(",
        "setInterval(",
        "Function(",
        "location.href",
        "location.replace",
    ]

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """
        Initialize XSS scanner.

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

    def _detect_xss_reflection(
        self, payload: str, response_text: str, encoded: bool = False
    ) -> bool:
        """
        Check if payload is reflected in response without proper encoding.

        Args:
            payload: XSS payload
            response_text: Response body
            encoded: Whether payload is encoded

        Returns:
            True if vulnerable reflection detected
        """
        if not encoded:
            # Check for exact reflection
            if payload in response_text:
                return True

            # Check for partial reflection (without encoding)
            dangerous_chars = ["<script", "onerror", "onload", "javascript:"]
            return any(char in response_text.lower() for char in dangerous_chars)
        else:
            # For encoded payloads, check if they get decoded
            return payload in response_text

    async def scan_parameter(
        self,
        url: str,
        param_name: str,
        param_value: str,
        method: str = "GET",
    ) -> list[ScanResult]:
        """
        Scan a parameter for XSS vulnerabilities.

        Args:
            url: Target URL
            param_name: Parameter name
            param_value: Original parameter value
            method: HTTP method

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        # Test each payload
        for payload in self.XSS_PAYLOADS:
            try:
                if method.upper() == "GET":
                    test_url = f"{url}?{param_name}={payload}"
                    response = await self.http_client.get(test_url)
                else:
                    response = await self.http_client.post(url, data={param_name: payload})

                response_text = response.text()

                # Check if payload is reflected
                if self._detect_xss_reflection(payload, response_text):
                    results.append(
                        ScanResult(
                            vulnerability_type="Cross-Site Scripting (Reflected XSS)",
                            severity=Severity.HIGH,
                            url=url,
                            description=f"Reflected XSS vulnerability in parameter '{param_name}'. "
                            f"User input is reflected in the response without proper sanitization.",
                            evidence=f"Payload '{payload}' was reflected in response",
                            remediation="Implement proper output encoding/escaping. "
                            "Use Content-Security-Policy headers. "
                            "Sanitize user input on both client and server side. "
                            "Use modern frameworks that auto-escape by default.",
                            cwe_id="CWE-79",
                            confidence=90,
                            payload=payload,
                            parameter=param_name,
                        )
                    )
                    break  # Found vulnerability

            except Exception:
                pass

        # Test encoded payloads
        for payload in self.ENCODED_PAYLOADS[:3]:  # Test first 3
            try:
                if method.upper() == "GET":
                    test_url = f"{url}?{param_name}={payload}"
                    response = await self.http_client.get(test_url)
                else:
                    response = await self.http_client.post(url, data={param_name: payload})

                response_text = response.text()

                if "<script" in response_text.lower() or "alert" in response_text:
                    results.append(
                        ScanResult(
                            vulnerability_type="Cross-Site Scripting (Encoded XSS)",
                            severity=Severity.HIGH,
                            url=url,
                            description=f"XSS via encoded payload in parameter '{param_name}'",
                            evidence=f"Encoded payload '{payload}' executed in response",
                            remediation="Implement proper output encoding at multiple levels. "
                            "Decode and re-encode user input appropriately.",
                            cwe_id="CWE-79",
                            confidence=85,
                            payload=payload,
                            parameter=param_name,
                        )
                    )
                    break

            except Exception:
                pass

        return results

    async def scan_form(self, form_action: str, form_fields: list) -> list[ScanResult]:
        """
        Scan all fields in a form for XSS.

        Args:
            form_action: Form action URL
            form_fields: List of form fields

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        for field in form_fields:
            field_results = await self.scan_parameter(
                form_action,
                field.name,
                field.value or "test",
                method="POST",
            )
            results.extend(field_results)

        return results

    def scan_javascript_code(self, js_code: str, url: str) -> list[ScanResult]:
        """
        Scan JavaScript code for DOM-based XSS patterns.

        Args:
            js_code: JavaScript source code
            url: URL where JS was found

        Returns:
            List of discovered potential vulnerabilities
        """
        results = []

        # Check for dangerous sinks
        found_sinks = []
        for sink in self.DOM_XSS_SINKS:
            if sink in js_code:
                found_sinks.append(sink)

        if found_sinks:
            results.append(
                ScanResult(
                    vulnerability_type="Cross-Site Scripting (DOM-Based XSS - Potential)",
                    severity=Severity.MEDIUM,
                    url=url,
                    description=f"Potential DOM-based XSS detected. "
                    f"Dangerous JavaScript sinks found: {', '.join(found_sinks)}",
                    evidence=f"Found dangerous sinks: {', '.join(found_sinks)}",
                    remediation="Avoid using dangerous sinks with user-controlled data. "
                    "Use textContent instead of innerHTML. "
                    "Sanitize data before inserting into DOM. "
                    "Use DOMPurify or similar libraries.",
                    cwe_id="CWE-79",
                    confidence=60,  # Lower confidence, needs manual review
                    payload=None,
                    parameter=None,
                )
            )

        return results
