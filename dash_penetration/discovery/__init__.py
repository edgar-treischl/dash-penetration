"""
Discovery plugins for categorizing and analyzing crawled web content.

This module provides specialized discovery plugins that extract and categorize
specific types of information from HTML pages:

- LinkDiscovery: Categorize internal vs external links
- FormDiscovery: Extract form endpoints and parameters
- ScriptDiscovery: Identify JavaScript resources
- APIDiscovery: Detect API endpoints

Each plugin processes a Page object and produces structured discovery results
that feed into the crawler engine's endpoint inventory.
"""

from .links import LinkDiscovery, LinkDiscoveryResult
from .forms import FormDiscovery, FormDiscoveryResult, FormEndpoint, FormField
from .scripts import ScriptDiscovery, ScriptDiscoveryResult, ScriptReference
from .api import APIDiscovery, APIDiscoveryResult, APIEndpoint

__all__ = [
    "LinkDiscovery",
    "LinkDiscoveryResult",
    "FormDiscovery",
    "FormDiscoveryResult",
    "FormEndpoint",
    "FormField",
    "ScriptDiscovery",
    "ScriptDiscoveryResult",
    "ScriptReference",
    "APIDiscovery",
    "APIDiscoveryResult",
    "APIEndpoint",
]
