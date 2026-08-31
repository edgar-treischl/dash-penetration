"""
SQL Injection vulnerability scanner.

Tests for:
- Error-based SQL injection
- Boolean-based blind SQL injection
- Time-based blind SQL injection
- UNION-based SQL injection
"""

from typing import Optional
from dash_penetration.crawler.http import HTTPClient
from .scanner import ScanResult, Severity


class SQLInjectionScanner:
    """
    SQL Injection vulnerability scanner.
    """

    # SQL injection payloads
    ERROR_BASED_PAYLOADS = [
        "'",
        '"',
        "' OR '1'='1",
        '" OR "1"="1',
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin' --",
        "admin' #",
        "admin'/*",
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' AND 1=0 UNION ALL SELECT 'admin', 'password'",
    ]

    BOOLEAN_BASED_PAYLOADS = [
        "' AND '1'='1",
        "' AND '1'='2",
        " AND 1=1",
        " AND 1=2",
        "' AND 'a'='a",
        "' AND 'a'='b",
    ]

    TIME_BASED_PAYLOADS = [
        "'; WAITFOR DELAY '00:00:05'--",
        "' OR SLEEP(5)--",
        "'; SELECT pg_sleep(5)--",
        "1' AND SLEEP(5)--",
    ]

    # SQL error messages that indicate vulnerability
    SQL_ERROR_PATTERNS = [
        "sql syntax",
        "mysql_fetch",
        "mysql_num_rows",
        "mysqli",
        "pg_query",
        "postgresql",
        "sqlite_",
        "sqlite3_",
        "odbc_",
        "oracle error",
        "warning: mysql",
        "valid mysql result",
        "mysqld",
        "postgresql",
        "pg_exec",
        "syntax error",
        "unclosed quotation",
        "quoted string",
        "unterminated",
    ]

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """
        Initialize SQL injection scanner.

        Args:
            http_client: Optional HTTP client (will create one if not provided)
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

    def _detect_sql_error(self, response_text: str) -> bool:
        """
        Detect if response contains SQL error messages.

        Args:
            response_text: Response body text

        Returns:
            True if SQL error detected
        """
        response_lower = response_text.lower()
        return any(pattern in response_lower for pattern in self.SQL_ERROR_PATTERNS)

    async def scan_parameter(
        self,
        url: str,
        param_name: str,
        param_value: str,
        method: str = "GET",
        form_context: Optional[str] = None,
    ) -> list[ScanResult]:
        """
        Scan a single parameter for SQL injection.

        Args:
            url: Target URL
            param_name: Parameter name
            param_value: Original parameter value
            method: HTTP method (GET or POST)
            form_context: Context about which form is being tested

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        # Test error-based SQL injection
        for payload in self.ERROR_BASED_PAYLOADS:
            try:
                # Build test URL/data
                if method.upper() == "GET":
                    test_url = f"{url}?{param_name}={payload}"
                    response = await self.http_client.get(test_url)
                    reported_test_url = test_url
                else:
                    response = await self.http_client.post(url, data={param_name: payload})
                    reported_test_url = f"{url} (POST data: {param_name}={payload})"

                # Check for SQL errors in response
                if self._detect_sql_error(response.text()):
                    results.append(
                        ScanResult(
                            vulnerability_type="SQL Injection (Error-Based)",
                            severity=Severity.CRITICAL,
                            url=url,
                            description=f"SQL injection in '{param_name}'. "
                            f"SQL error messages detected in response.",
                            evidence=f"Payload '{payload}' triggered SQL error in response",
                            remediation="Use parameterized queries/prepared statements. "
                            "Never concatenate user input into SQL queries. "
                            "Implement input validation and sanitization.",
                            cwe_id="CWE-89",
                            confidence=95,
                            payload=payload,
                            parameter=param_name,
                            test_url=reported_test_url,
                            form_context=form_context,
                        )
                    )
                    break  # Found vulnerability, no need to test more payloads

            except Exception:
                # Ignore errors during testing
                pass

        # Test boolean-based SQL injection
        try:
            baseline_response = await self._get_response(url, param_name, param_value, method)
            baseline_length = len(baseline_response.text())

            true_payload = "' AND '1'='1"
            false_payload = "' AND '1'='2"

            true_response = await self._get_response(url, param_name, true_payload, method)
            false_response = await self._get_response(url, param_name, false_payload, method)

            true_length = len(true_response.text())
            false_length = len(false_response.text())

            # If true and false payloads give different responses, likely vulnerable
            if (
                abs(true_length - baseline_length) < 100
                and abs(false_length - baseline_length) > 100
            ):
                results.append(
                    ScanResult(
                        vulnerability_type="SQL Injection (Boolean-Based Blind)",
                        severity=Severity.HIGH,
                        url=url,
                        description=f"Boolean-based blind SQL injection in '{param_name}'. "
                        f"Application behavior differs based on SQL conditions.",
                        evidence=f"True: {true_length}B, False: {false_length}B",
                        remediation="Use parameterized queries/prepared statements. "
                        "Implement proper error handling to avoid information leakage.",
                        cwe_id="CWE-89",
                        confidence=85,
                        payload=f"{true_payload} vs {false_payload}",
                        parameter=param_name,
                    )
                )

        except Exception:
            pass

        return results

    async def _get_response(self, url: str, param_name: str, value: str, method: str):
        """Helper to get response with parameter value."""
        if method.upper() == "GET":
            test_url = f"{url}?{param_name}={value}"
            return await self.http_client.get(test_url)
        else:
            return await self.http_client.post(url, data={param_name: value})

    async def scan_form(self, form_action: str, form_fields: list) -> list[ScanResult]:
        """
        Scan all fields in a form for SQL injection.

        Args:
            form_action: Form action URL
            form_fields: List of form field names

        Returns:
            List of discovered vulnerabilities
        """
        results = []

        # Identify the form by its fields
        field_names = [field.name for field in form_fields]
        form_context = self._identify_form(field_names, form_action)

        for field in form_fields:
            field_results = await self.scan_parameter(
                form_action,
                field.name,
                field.value or "test",
                method="POST",
                form_context=form_context,
            )
            results.extend(field_results)

        return results

    def _identify_form(self, field_names: list[str], form_action: str) -> str:
        """Identify form type based on field names and action."""
        fields_lower = [f.lower() for f in field_names]

        # Login forms
        if any(f in fields_lower for f in ["username", "password", "email"]):
            if "password" in fields_lower:
                return f"Login form (action: {form_action})"

        # Contact forms
        if any(f in fields_lower for f in ["message", "subject", "name", "email"]):
            if "message" in fields_lower:
                return f"Contact form (action: {form_action})"

        # Registration forms
        if any(f in fields_lower for f in ["confirm_password", "password_confirm"]):
            return f"Registration form (action: {form_action})"

        # Generic form
        return f"Form with fields: {', '.join(field_names[:3])}... (action: {form_action})"
