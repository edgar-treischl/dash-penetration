"""
Tests for XSS scanner to prevent regression of false positives.

These tests verify that the XSS scanner correctly identifies true vulnerabilities
and doesn't flag normal HTML structure as vulnerable.
"""

from dash_penetration.scanner.xss import XSSScanner


class TestXSSScannerFalsePositives:
    """Test cases to prevent XSS false positives"""

    def test_detect_xss_reflection_exact_match_only(self):
        """Verify that XSS detection requires exact payload match"""
        scanner = XSSScanner()

        # HTML containing <script> tags (normal for SPA) but NOT user payload
        spa_html = """
        <!doctype html>
        <html>
        <head>
            <script type="module" src="/app.js"></script>
        </head>
        <body>
            <div id="root"></div>
        </body>
        </html>
        """

        payload = "<script>alert('XSS')</script>"

        # Should NOT detect XSS (payload not in response)
        result = scanner._detect_xss_reflection(payload, spa_html, encoded=False)
        assert result is False, "Should not flag normal HTML <script> tags as XSS"

    def test_detect_xss_reflection_with_real_payload(self):
        """Verify that XSS is detected when payload is actually reflected"""
        scanner = XSSScanner()

        payload = "<script>alert('XSS')</script>"

        # HTML that actually contains the reflected payload
        vulnerable_html = f"""
        <html>
        <body>
            <p>Welcome, {payload}</p>
        </body>
        </html>
        """

        # Should detect XSS (payload IS in response)
        result = scanner._detect_xss_reflection(payload, vulnerable_html, encoded=False)
        assert result is True, "Should detect XSS when payload is reflected"

    def test_detect_xss_reflection_does_not_match_partial_keywords(self):
        """Verify that partial keywords don't trigger false positives"""
        scanner = XSSScanner()

        # HTML with keywords but NOT user payload
        html_with_keywords = """
        <html>
        <body>
            <script>console.log('alert monitoring');</script>
            <div onclick="onload()">Content</div>
        </body>
        </html>
        """

        payload = "<script>alert('XSS')</script>"

        # Should NOT detect XSS (payload not reflected, only keywords present)
        result = scanner._detect_xss_reflection(payload, html_with_keywords, encoded=False)
        assert result is False, "Should not flag HTML with keywords but no actual payload"

    def test_detect_xss_reflection_encoded_payload(self):
        """Verify encoded payload detection"""
        scanner = XSSScanner()

        encoded_payload = "%3Cscript%3Ealert('XSS')%3C/script%3E"

        # HTML containing the encoded payload
        vulnerable_html = f"""
        <html>
        <body>
            <p>Your search: {encoded_payload}</p>
        </body>
        </html>
        """

        # Should detect XSS (encoded payload IS in response)
        result = scanner._detect_xss_reflection(encoded_payload, vulnerable_html, encoded=True)
        assert result is True, "Should detect encoded XSS when payload is reflected"

    def test_detect_xss_reflection_encoded_payload_not_present(self):
        """Verify encoded payload NOT flagged when not present"""
        scanner = XSSScanner()

        encoded_payload = "%3Cscript%3Ealert('XSS')%3C/script%3E"

        # HTML with <script> tags but NOT the encoded payload
        html_without_payload = """
        <html>
        <head>
            <script type="module" src="/app.js"></script>
        </head>
        <body>Test</body>
        </html>
        """

        # Should NOT detect XSS
        result = scanner._detect_xss_reflection(encoded_payload, html_without_payload, encoded=True)
        assert result is False, "Should not flag normal HTML just because it has <script> tags"


class TestXSSScannerIdentifyForm:
    """Test form identification"""

    def test_identify_login_form(self):
        """Test login form identification"""
        scanner = XSSScanner()

        field_names = ["username", "password"]
        form_action = "https://example.com/login"

        result = scanner._identify_form(field_names, form_action)
        assert "Login form" in result
        assert form_action in result

    def test_identify_contact_form(self):
        """Test contact form identification"""
        scanner = XSSScanner()

        field_names = ["name", "email", "message"]
        form_action = "https://example.com/contact"

        result = scanner._identify_form(field_names, form_action)
        assert "Contact form" in result

    def test_identify_registration_form(self):
        """Test registration form identification"""
        scanner = XSSScanner()

        field_names = ["username", "password", "password_confirm"]
        form_action = "https://example.com/register"

        result = scanner._identify_form(field_names, form_action)
        assert "Registration form" in result
