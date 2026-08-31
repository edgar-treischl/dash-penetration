"""
Vulnerability scanner module for web application security testing.

Detects common vulnerabilities:
- SQL Injection
- Cross-Site Scripting (XSS)
- CSRF (Cross-Site Request Forgery)
- Authentication weaknesses
- Security header issues
- Information disclosure
- Open Redirects
"""

from .sql_injection import SQLInjectionScanner
from .xss import XSSScanner
from .csrf import CSRFScanner
from .auth import AuthenticationScanner
from .headers import SecurityHeadersScanner
from .info_disclosure import InformationDisclosureScanner
from .open_redirects import OpenRedirectScanner
from .scanner import VulnerabilityScanner, ScanResult, Severity

__all__ = [
    "VulnerabilityScanner",
    "ScanResult",
    "Severity",
    "SQLInjectionScanner",
    "XSSScanner",
    "CSRFScanner",
    "AuthenticationScanner",
    "SecurityHeadersScanner",
    "InformationDisclosureScanner",
    "OpenRedirectScanner",
]
