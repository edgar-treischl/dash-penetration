"""
Crawler module for HTTP client, HTML parsing, and scope validation.
"""

from .scope import Scope
from .http import (
    HTTPClient,
    HTTPResponse,
    HTTPError,
    HTTPConnectionError,
    HTTPTimeoutError,
    HTTPSSLError,
    HTTPTooManyRedirectsError,
    HTTPStatusError,
)
from .parser import HTMLParser, Form, FormInput, ScriptReference

__all__ = [
    "Scope",
    "HTTPClient",
    "HTTPResponse",
    "HTTPError",
    "HTTPConnectionError",
    "HTTPTimeoutError",
    "HTTPSSLError",
    "HTTPTooManyRedirectsError",
    "HTTPStatusError",
    "HTMLParser",
    "Form",
    "FormInput",
    "ScriptReference",
]
