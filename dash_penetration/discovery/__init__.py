"""
Discovery plugins for categorizing and analyzing crawled web content.

This module provides specialized discovery plugins that extract and categorize
specific types of information from HTML pages:

- LinkDiscovery: Categorize internal vs external links
- FormDiscovery: Extract form endpoints and parameters

Each plugin processes a Page object and produces structured discovery results
that feed into the vulnerability scanner.
"""

from .links import LinkDiscovery, LinkDiscoveryResult
from .forms import FormDiscovery, FormDiscoveryResult, FormEndpoint, FormField

__all__ = [
    "LinkDiscovery",
    "LinkDiscoveryResult",
    "FormDiscovery",
    "FormDiscoveryResult",
    "FormEndpoint",
    "FormField",
]
