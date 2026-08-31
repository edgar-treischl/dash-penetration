
---
title: "Step 7: Discovery Plugins"
guide-section: "Getting Started"
---

## Overview

Discovery plugins analyze crawled web content and extract specific types of information to build a comprehensive endpoint inventory. Each plugin focuses on a particular category of reconnaissance data:

- **LinkDiscovery** — Categorize links into internal vs external
- **FormDiscovery** — Extract form endpoints and identify data entry points
- **ScriptDiscovery** — Track JavaScript resources and detect frameworks
- **APIDiscovery** — Identify API endpoints and versions

Together, these plugins transform raw HTML into structured reconnaissance data for the crawler engine.

## Architecture

Discovery plugins follow a plugin pattern:

1. **Input:** Raw lists of URLs, links, or form data from parser
2. **Processing:** Apply discovery heuristics and categorization logic
3. **Output:** Structured result dataclasses with statistics and filtering

```
HTMLParser
    ↓
    ├─→ Links → LinkDiscovery → {internal, external, dynamic}
    ├─→ Forms → FormDiscovery → {endpoints, methods, parameters}
    ├─→ Scripts → ScriptDiscovery → {external, inline, frameworks}
    └─→ All → APIDiscovery → {endpoints, versions, types}
         ↓
         Endpoint Inventory
```

## LinkDiscovery

Categorizes discovered links by scope and relationship to base domain.

### Basic Usage

```python
from dash_penetration.discovery import LinkDiscovery

# Initialize with target domain
discoverer = LinkDiscovery("https://example.com")

# Analyze a list of discovered links
links = [
    "https://example.com/page1",
    "https://example.com/search?q=test",
    "https://google.com/search",
    "https://example.com/page#section",
]

result = discoverer.analyze(links)

# Access categorized links
print(f"Internal: {result.internal_count()}")      # 2
print(f"External: {result.external_count()}")      # 1
print(f"Dynamic: {result.dynamic_count()}")        # 2
print(f"Total: {result.total_links()}")            # 4
```

### Scope Validation

Integrate with Scope module to validate links:

```python
from dash_penetration.crawler import Scope
from dash_penetration.discovery import LinkDiscovery

scope = Scope(
    allowed_domains=["example.com"],
    disallowed_paths=["/admin", "/internal"]
)

discoverer = LinkDiscovery("https://example.com", scope=scope)

links = [
    "https://example.com/page",
    "https://example.com/admin",
    "https://notallowed.com",
]

result = discoverer.analyze(links)
print(f"Violations: {result.violation_count()}")  # 2
```

### Link Filtering

```python
links = [
    "https://example.com/page1",
    "https://cdn.example.com/asset.js",
    "https://google.com",
    "https://example.com/search?q=test",
]

# Get only internal links
internal = discoverer.filter_internal(links)

# Get only external links
external = discoverer.filter_external(links)

# Get only dynamic links (with query params or fragments)
dynamic = discoverer.filter_dynamic(links)
```

### Grouping by Domain

```python
links = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://api.example.com/users",
    "https://google.com",
]

by_domain = discoverer.analyze_by_domain(links)
# Output:
# {
#   "api.example.com": ["https://api.example.com/users"],
#   "example.com": ["https://example.com/page1", "https://example.com/page2"],
#   "google.com": ["https://google.com"]
# }
```

### Result Export

```python
result = discoverer.analyze(links)
data = result.to_dict()

# Output:
# {
#   "internal_links": ["https://example.com/page1"],
#   "external_links": ["https://google.com"],
#   "dynamic_links": ["https://example.com/search?q=test"],
#   "scope_violations": [],
#   "summary": {
#     "total_links": 4,
#     "internal": 2,
#     "external": 1,
#     "dynamic": 2,
#     "violations": 0
#   }
# }
```

## FormDiscovery

Analyzes form endpoints and parameters from parsed HTML.

### Basic Usage

```python
from dash_penetration.crawler.parser import Form, FormInput
from dash_penetration.discovery import FormDiscovery

# Create discoverer
discoverer = FormDiscovery()

# Parse forms (typically from HTMLParser)
forms = [
    Form(
        action="https://example.com/login",
        method="POST",
        inputs=[
            FormInput(name="username", input_type="text"),
            FormInput(name="password", input_type="password", required=True),
        ]
    ),
    Form(
        action="https://example.com/search",
        method="GET",
        inputs=[
            FormInput(name="q", input_type="text", required=True),
        ]
    ),
]

result = discoverer.analyze(forms)

# Access form statistics
print(f"Total forms: {result.total_forms}")           # 2
print(f"GET forms: {result.get_forms}")               # 1
print(f"POST forms: {result.post_forms}")             # 1
print(f"Required fields: {result.required_fields}")   # 2
print(f"Optional fields: {result.optional_fields}")   # 1
```

### Finding Specific Forms

```python
# Find forms by HTTP method
post_forms = discoverer.find_by_method(forms, "POST")

# Get all unique form action endpoints
endpoints = discoverer.get_all_endpoints(forms)
# Output: ["https://example.com/login", "https://example.com/search"]
```

### Parameter Analysis

```python
# Extract all parameter names and their frequency
params = discoverer.get_all_parameters(forms)
# Output:
# {
#   "password": 1,
#   "q": 1,
#   "username": 1
# }

# This is useful for identifying common authentication patterns,
# search parameters, etc.
```

### Form Endpoint Details

```python
result = discoverer.analyze(forms)

for endpoint in result.forms:
    print(f"Action: {endpoint.action}")
    print(f"Method: {endpoint.method}")
    print(f"Total fields: {endpoint.field_count()}")
    print(f"Required: {endpoint.required_count()}")
    print(f"Optional: {endpoint.optional_count()}")
    print(f"Field names: {endpoint.get_field_names()}")
    print()
```

### Result Export

```python
result = discoverer.analyze(forms)
data = result.to_dict()

# Output:
# {
#   "total_forms": 2,
#   "get_forms": 1,
#   "post_forms": 1,
#   "endpoints": ["https://example.com/login", "https://example.com/search"],
#   "field_summary": {"required": 2, "optional": 1},
#   "forms": [
#     {
#       "action": "https://example.com/login",
#       "method": "POST",
#       "field_count": 2,
#       "required_fields": 1,
#       "optional_fields": 1,
#       "fields": [
#         {"name": "username", "type": "text", "required": false},
#         {"name": "password", "type": "password", "required": true}
#       ]
#     },
#     ...
#   ]
# }
```

## ScriptDiscovery

Tracks JavaScript resources and detects frameworks.

### Basic Usage

```python
from dash_penetration.discovery import ScriptDiscovery

discoverer = ScriptDiscovery("https://example.com")

external_scripts = [
    "https://cdn.example.com/jquery-3.6.0.js",
    "https://cdn.example.com/app.js",
    "https://google.com/analytics.js",
    "https://cdn.cloudflare.com/bootstrap.js",
]

inline_scripts = [
    "console.log('tracking');",
    "import React from 'react';",
]

result = discoverer.analyze(external_scripts, inline_scripts)

# Access statistics
print(f"Total scripts: {result.total_scripts()}")           # 6
print(f"External: {result.external_count()}")               # 4
print(f"Inline: {result.inline_count()}")                   # 2
print(f"Third-party domains: {result.third_party_count()}")  # 2
print(f"Frameworks: {result.detected_frameworks}")          # {"jQuery": 1, "React": 1}
```

### Framework Detection

The plugin detects popular JavaScript frameworks and libraries:

- jQuery
- React / Vue / Angular
- Bootstrap
- D3 / Three.js
- Chart.js / Moment.js
- Lodash / Axios
- TypeScript / Babel / Webpack
- GSAP / Fetch

```python
# Get external URLs
urls = discoverer.get_all_external_urls(external_scripts, inline_scripts)

# Get third-party domains (hosts that don't match base domain)
third_party = discoverer.get_third_party_domains(external_scripts, inline_scripts)
# Output: ["cdn.cloudflare.com", "google.com"]

# Filter by domain
cdn_scripts = discoverer.filter_by_domain(external_scripts, "cdn.cloudflare.com")

# Filter by framework
jquery_scripts = discoverer.filter_by_framework(external_scripts, "jquery")
```

### Result Export

```python
result = discoverer.analyze(external_scripts, inline_scripts)
data = result.to_dict()

# Output:
# {
#   "total_scripts": 6,
#   "external_scripts": 4,
#   "inline_scripts": 2,
#   "external_urls": ["https://cdn.cloudflare.com/bootstrap.js", ...],
#   "third_party_domains": ["cdn.cloudflare.com", "google.com"],
#   "detected_frameworks": {"jQuery": 1, "React": 1},
#   "summary": {
#     "total": 6,
#     "external": 4,
#     "inline": 2,
#     "third_party_domains": 2,
#     "frameworks": 2
#   }
# }
```

## APIDiscovery

Identifies potential API endpoints using multiple heuristics.

### Basic Usage

```python
from dash_penetration.discovery import APIDiscovery

discoverer = APIDiscovery("https://example.com")

links = [
    "https://example.com/page",
    "https://example.com/api/users",
    "https://api.example.com/v1/products",
    "https://example.com/graphql",
    "https://example.com/v2/auth/login",
]

result = discoverer.analyze(links)

print(f"Total endpoints: {result.total_endpoints()}")      # 4
print(f"REST endpoints: {result.rest_count()}")            # 3
print(f"GraphQL endpoints: {result.graphql_count()}")      # 1
print(f"Detected versions: {result.versions_detected}")    # {"v1", "v2"}
```

### API Detection Heuristics

The plugin uses multiple patterns to identify APIs:

#### Path Patterns
- `/api/` — Standard API prefix
- `/v1/`, `/v2/`, etc. — Versioned APIs
- `/graphql` — GraphQL endpoints
- `/rest/` — REST API prefix

#### Domain Patterns
- `api.domain.com` — API subdomain
- `apis.domain.com` — APIs subdomain
- `gateway.domain.com` — API gateway

#### Content-Type
- `application/json` — Strong API indicator

#### Naming Patterns
- `auth`, `login`, `token` — Authentication endpoints
- RESTful path conventions

### Filtering by Version

```python
links = [
    "https://example.com/v1/users",
    "https://example.com/v2/users",
    "https://example.com/v1/products",
]

v1_apis = discoverer.get_by_version(links, "v1")
# Output: 2 endpoints (users, products)

v2_apis = discoverer.get_by_version(links, "v2")
# Output: 1 endpoint (users)
```

### Filtering by Type

```python
links = [
    "https://example.com/graphql",
    "https://example.com/api/users",
    "https://example.com/rest/products",
]

graphql_apis = discoverer.get_by_type(links, "graphql")
# Output: 1 endpoint

rest_apis = discoverer.get_by_type(links, "rest")
# Output: 2 endpoints
```

### With Response Metadata

```python
links = [
    "https://example.com/data",
    "https://example.com/page",
]

# Provide status codes and content types
status_codes = {
    "https://example.com/data": 200,
    "https://example.com/page": 200,
}

content_types = {
    "https://example.com/data": "application/json",
    "https://example.com/page": "text/html",
}

result = discoverer.analyze(links, status_codes, content_types)
# JSON endpoint is identified as API candidate
```

### Result Export

```python
result = discoverer.analyze(links)
data = result.to_dict()

# Output:
# {
#   "total_endpoints": 4,
#   "rest_endpoints": 3,
#   "graphql_endpoints": 1,
#   "versions": ["v1", "v2"],
#   "endpoints": [
#     {
#       "url": "https://example.com/api/users",
#       "method": "GET",
#       "content_type": "",
#       "type": "rest",
#       "pattern": "/api/users",
#       "version": "",
#       "authenticated": false
#     },
#     ...
#   ],
#   "by_method": {
#     "GET": [...],
#     "POST": [...]
#   }
# }
```

## Real-World Integration Example

Complete example showing all discovery plugins working together:

```python
from dash_penetration.crawler import HTTPClient, HTMLParser, Scope
from dash_penetration.discovery import (
    LinkDiscovery,
    FormDiscovery,
    ScriptDiscovery,
    APIDiscovery,
)
import asyncio


async def discover_target(target_url: str):
    """Discover all aspects of a target website."""
    
    scope = Scope(allowed_domains=["example.com"])
    http_client = HTTPClient()
    parser = HTMLParser(target_url)
    
    # Initialize discoverers
    link_disc = LinkDiscovery(target_url, scope=scope)
    form_disc = FormDiscovery()
    script_disc = ScriptDiscovery(target_url)
    api_disc = APIDiscovery(target_url)
    
    # Fetch and parse homepage
    response = await http_client.fetch(target_url)
    parsed = parser.extract_all()
    
    # Run all discoverers
    link_results = link_disc.analyze(parsed["links"])
    form_results = form_disc.analyze(parsed["forms"])
    script_results = script_disc.analyze(
        parsed["scripts"],
        parsed["inline_scripts"]
    )
    api_results = api_disc.analyze(link_results.internal_links)
    
    # Build reconnaissance report
    report = {
        "target": target_url,
        "links": link_results.to_dict(),
        "forms": form_results.to_dict(),
        "scripts": script_results.to_dict(),
        "apis": api_results.to_dict(),
    }
    
    return report


# Run discovery
asyncio.run(discover_target("https://example.com"))
```

## Testing

All discovery plugins have comprehensive test coverage:

```bash
# Run discovery tests
uv run pytest tests/test_discovery.py -v

# Run specific plugin tests
uv run pytest tests/test_discovery.py::TestLinkDiscovery -v
uv run pytest tests/test_discovery.py::TestFormDiscovery -v
uv run pytest tests/test_discovery.py::TestScriptDiscovery -v
uv run pytest tests/test_discovery.py::TestAPIDiscovery -v
```

**Test Coverage:**
- 14 LinkDiscovery tests
- 9 FormDiscovery tests
- 13 ScriptDiscovery tests
- 13 APIDiscovery tests
- **Total: 49 discovery tests**

## Implementation Notes

### Performance Considerations

- LinkDiscovery uses case-insensitive domain comparison
- ScriptDiscovery caches framework detection patterns
- All discoverers work with in-memory lists (suitable for single pages)
- Parallelization of multi-page crawls happens at engine level

### Security Considerations

- Scope validation prevents crawling unauthorized targets
- API detection helps identify authentication endpoints
- Third-party script tracking reveals external dependencies
- Form analysis identifies data entry points for testing

### Extension Points

To add custom discovery plugins:

1. Create result dataclass (e.g., `CustomResult`)
2. Create discoverer class with `analyze()` method
3. Implement `to_dict()` for export
4. Add to `discovery/__init__.py`
5. Write comprehensive tests

Example:

```python
from dataclasses import dataclass, field

@dataclass
class CustomResult:
    custom_data: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {"custom_data": self.custom_data}

class CustomDiscovery:
    def analyze(self, data: list[str]) -> CustomResult:
        # Custom analysis logic
        return CustomResult(custom_data=data)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│          Crawled Content (Page Object)              │
├─────────────────────────────────────────────────────┤
│  Links  │  Forms  │  Scripts  │  Meta  │  Content  │
└────┬────────┬────────┬────────────┬──────────────┘
     │        │        │            │
     ▼        ▼        ▼            ▼
  LinkD     FormD    ScriptD      APID
  iscov     iscov    iscov        iscov
   ery       ery      ery         ery
     │        │        │            │
     └────────┴────────┴────────────┘
            ▼
  ┌──────────────────────────────────┐
  │   Reconnaissance Inventory       │
  ├──────────────────────────────────┤
  │ • Internal/External Links        │
  │ • Form Endpoints & Parameters    │
  │ • JavaScript Resources           │
  │ • API Endpoints & Versions       │
  │ • Third-party Dependencies       │
  └──────────────────────────────────┘
```

## Key Takeaways

- **Modular Design** — Each discoverer focuses on one reconnaissance aspect
- **Structured Output** — All results are dataclasses with standardized exports
- **Scope-Aware** — LinkDiscovery integrates with Scope for authorization control
- **Extensible** — Easy to add new discovery plugins for additional analysis
- **Well-Tested** — 49 comprehensive tests covering all functionality
- **Production-Ready** — Used by crawler engine to build endpoint inventory

The discovery plugins transform parsed HTML into actionable reconnaissance data that feeds the crawler engine and security testing workflows.
