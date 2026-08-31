"""
Tests for Open Redirect scanner.

Tests verify detection of open redirect vulnerabilities and prevention of false positives.
"""

import pytest
from dash_penetration.scanner.open_redirects import OpenRedirectScanner


class TestOpenRedirectScanner:
    """Test Open Redirect scanner functionality"""

    def test_scanner_initialization(self):
        """Test scanner can be initialized"""
        scanner = OpenRedirectScanner()
        assert scanner is not None
        assert hasattr(scanner, "REDIRECT_PARAMS")
        assert hasattr(scanner, "TEST_PAYLOADS")

    def test_redirect_params_list(self):
        """Test redirect parameter names are defined"""
        scanner = OpenRedirectScanner()
        assert len(scanner.REDIRECT_PARAMS) > 0
        assert "redirect" in scanner.REDIRECT_PARAMS
        assert "url" in scanner.REDIRECT_PARAMS
        assert "next" in scanner.REDIRECT_PARAMS
        assert "return" in scanner.REDIRECT_PARAMS

    def test_test_payloads_defined(self):
        """Test external domain payloads are defined"""
        scanner = OpenRedirectScanner()
        assert len(scanner.TEST_PAYLOADS) > 0
        assert any("attacker.com" in p for p in scanner.TEST_PAYLOADS)

    def test_is_external_domain_different_domain(self):
        """Test external domain detection for different domains"""
        scanner = OpenRedirectScanner()

        # Different domain should be external
        result = scanner._is_external_domain(
            "https://example.com/login", "https://attacker.com/phishing"
        )
        assert result is True

    def test_is_external_domain_same_domain(self):
        """Test same domain is not flagged as external"""
        scanner = OpenRedirectScanner()

        # Same domain should NOT be external
        result = scanner._is_external_domain(
            "https://example.com/login", "https://example.com/success"
        )
        assert result is False

    def test_is_external_domain_subdomain_redirect(self):
        """Test subdomain redirects are not flagged as external"""
        scanner = OpenRedirectScanner()

        # Subdomain redirect should NOT be external (internal network)
        result = scanner._is_external_domain(
            "https://api.example.com/login", "https://example.com/success"
        )
        assert result is False

    def test_is_external_domain_to_subdomain(self):
        """Test redirect to subdomain not flagged as external"""
        scanner = OpenRedirectScanner()

        # Redirect to subdomain should NOT be external
        result = scanner._is_external_domain(
            "https://example.com/login", "https://api.example.com/success"
        )
        assert result is False

    def test_is_external_domain_with_port(self):
        """Test external domain detection with port numbers"""
        scanner = OpenRedirectScanner()

        # Different domain with ports should be external
        result = scanner._is_external_domain(
            "https://example.com:8080/login", "https://attacker.com:8080/phishing"
        )
        assert result is True

    def test_is_external_domain_same_domain_different_port(self):
        """Test same domain with different port"""
        scanner = OpenRedirectScanner()

        # Same domain, different port, should NOT be external
        result = scanner._is_external_domain(
            "https://example.com:8080/login", "https://example.com:9090/success"
        )
        assert result is False

    def test_is_external_domain_case_insensitive(self):
        """Test domain comparison is case-insensitive"""
        scanner = OpenRedirectScanner()

        # Different domains, different cases, should still be external
        result = scanner._is_external_domain(
            "https://EXAMPLE.COM/login", "https://attacker.com/phishing"
        )
        assert result is True

    def test_is_external_domain_empty_location(self):
        """Test empty redirect location"""
        scanner = OpenRedirectScanner()

        # Empty location should NOT be flagged as external
        result = scanner._is_external_domain("https://example.com/login", "")
        assert result is False

    def test_is_external_domain_relative_redirect(self):
        """Test relative redirects are not external"""
        scanner = OpenRedirectScanner()

        # Relative redirect should NOT be external
        result = scanner._is_external_domain("https://example.com/login", "/success")
        assert result is False

    def test_is_external_domain_protocol_relative(self):
        """Test protocol-relative URLs"""
        scanner = OpenRedirectScanner()

        # Protocol-relative to different domain should be external
        result = scanner._is_external_domain("https://example.com/login", "//attacker.com/phishing")
        assert result is True

    def test_is_external_domain_protocol_relative_same_domain(self):
        """Test protocol-relative URL to same domain"""
        scanner = OpenRedirectScanner()

        # Protocol-relative to same domain should NOT be external
        result = scanner._is_external_domain("https://example.com/login", "//example.com/success")
        assert result is False
