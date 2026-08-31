
---
title: "Step 4: Scope Validation"
guide-section: "Getting Started"
---

**Status:** ✅ Complete  
**Module:** `dash_penetration.crawler.scope`  
**Tests:** 42 comprehensive tests  

## Overview

Scope validation ensures that web crawler operations stay within authorized target domains and paths. This is critical for preventing accidental crawling of unintended targets or sensitive areas during authorized penetration testing.

---

## Implementation Summary

### What was built:

**`crawler/scope.py`** — Full scope validation module with:
- **`Scope` class** with support for:
  - Multiple allowed domains with subdomain matching
  - Flexible path whitelisting (allowed_paths)
  - Path blacklisting (disallowed_paths) with priority over whitelisting
  - Configuration deserialization (`from_dict()` / `to_dict()`)
  - Domain and path validation methods

### Key Features:

| Feature | Details |
|---------|---------|
| **Domain Matching** | Exact + subdomain support (e.g., `api.example.com` matches scope `example.com`) |
| **Path Control** | Whitelist + blacklist with priority rules |
| **Case Insensitivity** | Domains and paths normalized to lowercase |
| **Port Handling** | Preserves ports in domain matching |
| **Serialization** | Convert scope to/from dict for config storage |

### Test Coverage:

- **42 comprehensive tests** covering:
  - Domain validation (exact, subdomain, ports, case sensitivity)
  - Path validation (whitelisting, blacklisting, priorities)
  - Combined scope checking
  - Configuration serialization/deserialization
  - Edge cases and error handling

### Dependencies:

- Only uses Python stdlib (`urllib.parse`, `typing`)
- No external dependencies required

---

## Usage Guide

### Basic Usage

#### Create a Scope

```python
from dash_penetration.crawler import Scope

# Simple scope: allow example.com and all subdomains
scope = Scope(allowed_domains=["example.com"])

# Multiple domains
scope = Scope(
    allowed_domains=["example.com", "api.example.com"]
)

# With path restrictions
scope = Scope(
    allowed_domains=["example.com"],
    allowed_paths=["/api", "/public"],
    disallowed_paths=["/admin", "/private"]
)
```

### Domain Validation

```python
scope = Scope(allowed_domains=["example.com"])

# ✅ Exact domain match
scope.is_domain_allowed("https://example.com/path")  # True

# ✅ Subdomain match
scope.is_domain_allowed("https://api.example.com/path")  # True
scope.is_domain_allowed("https://v2.api.example.com/path")  # True

# ❌ Different domain
scope.is_domain_allowed("https://other.com/path")  # False
```

### Path Validation

#### No Path Restrictions (Allow All)

```python
scope = Scope(allowed_domains=["example.com"])

# All paths allowed
scope.is_path_allowed("https://example.com/api/users")  # True
scope.is_path_allowed("https://example.com/admin")  # True
scope.is_path_allowed("https://example.com/private")  # True
```

#### Whitelist Specific Paths

```python
scope = Scope(
    allowed_domains=["example.com"],
    allowed_paths=["/api", "/public"]
)

# ✅ Paths matching whitelist
scope.is_path_allowed("https://example.com/api/users")  # True
scope.is_path_allowed("https://example.com/public/docs")  # True

# ❌ Paths not in whitelist
scope.is_path_allowed("https://example.com/admin")  # False
scope.is_path_allowed("https://example.com/other")  # False
```

#### Blacklist Specific Paths

```python
scope = Scope(
    allowed_domains=["example.com"],
    disallowed_paths=["/admin", "/private"]
)

# ✅ Paths not blacklisted
scope.is_path_allowed("https://example.com/api/users")  # True
scope.is_path_allowed("https://example.com/public")  # True

# ❌ Paths in blacklist
scope.is_path_allowed("https://example.com/admin/dashboard")  # False
scope.is_path_allowed("https://example.com/private/data")  # False
```

#### Combined Whitelist + Blacklist

When both are specified, **disallowed_paths takes priority**:

```python
scope = Scope(
    allowed_domains=["example.com"],
    allowed_paths=["/api", "/admin"],
    disallowed_paths=["/admin/sensitive"]
)

# ✅ In whitelist and not blacklisted
scope.is_path_allowed("https://example.com/api/users")  # True
scope.is_path_allowed("https://example.com/admin/general")  # True

# ❌ Blacklisted even though in whitelist
scope.is_path_allowed("https://example.com/admin/sensitive/data")  # False
```

### Combined Scope Checking

```python
scope = Scope(
    allowed_domains=["example.com"],
    disallowed_paths=["/admin"]
)

# Check both domain and path in one call
scope.is_in_scope("https://example.com/api/users")  # True
scope.is_in_scope("https://api.example.com/api/users")  # True
scope.is_in_scope("https://example.com/admin/users")  # False
scope.is_in_scope("https://other.com/api/users")  # False
```

### Configuration Management

#### Load from Dictionary

```python
config = {
    "allowed_domains": ["example.com", "api.example.com"],
    "allowed_paths": ["/api", "/public"],
    "disallowed_paths": ["/admin"]
}

scope = Scope.from_dict(config)
```

#### Save to Dictionary

```python
scope = Scope(
    allowed_domains=["example.com"],
    allowed_paths=["/api"],
    disallowed_paths=["/admin"]
)

config = scope.to_dict()
# {
#     "allowed_domains": ["example.com"],
#     "allowed_paths": ["/api"],
#     "disallowed_paths": ["/admin"]
# }
```

#### Round-trip Serialization

```python
original = Scope(
    allowed_domains=["example.com"],
    allowed_paths=["/api"],
    disallowed_paths=["/admin"]
)

# Serialize → Deserialize
restored = Scope.from_dict(original.to_dict())

# Same behavior
assert original.is_in_scope("https://example.com/api/users") == \
       restored.is_in_scope("https://example.com/api/users")
```

---

## API Reference

### `Scope` Class

#### Constructor

```python
Scope(
    allowed_domains: list[str],
    allowed_paths: Optional[list[str]] = None,
    disallowed_paths: Optional[list[str]] = None
)
```

**Parameters:**
- `allowed_domains` (required): List of base domains (e.g., `['example.com']`)
- `allowed_paths` (optional): List of path prefixes to allow (e.g., `['/api', '/public']`)
- `disallowed_paths` (optional): List of path prefixes to disallow (e.g., `['/admin', '/private']`)

**Raises:**
- `ValueError`: If `allowed_domains` is empty

#### Methods

##### `is_domain_allowed(url: str) -> bool`

Check if a URL's domain is in the allowed list.

```python
scope = Scope(allowed_domains=["example.com"])
assert scope.is_domain_allowed("https://api.example.com/path") == True
```

##### `is_path_allowed(url: str) -> bool`

Check if a URL's path is allowed.

```python
scope = Scope(
    allowed_domains=["example.com"],
    allowed_paths=["/api"]
)
assert scope.is_path_allowed("https://example.com/api/users") == True
```

##### `is_in_scope(url: str) -> bool`

Check if a URL is within scope (both domain and path).

```python
scope = Scope(
    allowed_domains=["example.com"],
    allowed_paths=["/api"]
)
assert scope.is_in_scope("https://example.com/api/users") == True
```

##### `from_dict(config: dict) -> Scope`

Create a Scope from a configuration dictionary.

```python
scope = Scope.from_dict({
    "allowed_domains": ["example.com"],
    "allowed_paths": ["/api"],
    "disallowed_paths": ["/admin"]
})
```

##### `to_dict() -> dict`

Serialize Scope to a dictionary.

```python
config = scope.to_dict()
```

##### `parse_domain_from_url(url: str) -> str` (static)

Extract domain from URL (including port if present).

```python
domain = Scope.parse_domain_from_url("https://api.example.com:8080/path")
# Returns: "api.example.com:8080"
```

---

## Real-World Examples

### Example 1: Simple Single Domain

```python
scope = Scope(allowed_domains=["example.com"])

# Crawl only example.com and its subdomains
if scope.is_in_scope(url):
    crawler.crawl(url)
```

### Example 2: Multi-Domain with Path Restrictions

```python
scope = Scope(
    allowed_domains=["example.com", "api.example.com"],
    allowed_paths=["/api", "/v2"],
    disallowed_paths=["/api/admin", "/api/internal"]
)

# Only crawl:
# - https://example.com/api/...
# - https://api.example.com/v2/...
# But NOT:
# - https://example.com/ui/...
# - https://api.example.com/api/admin/...
```

### Example 3: Production API with Exclusions

```python
scope = Scope(
    allowed_domains=["api.production.com"],
    disallowed_paths=[
        "/admin",
        "/internal",
        "/debug",
        "/metrics",
        "/health-check"
    ]
)

# Crawl everything EXCEPT sensitive endpoints
```

### Example 4: Load from Configuration File

```python
import json
from dash_penetration.crawler import Scope

# Load from JSON config
with open("scope.json") as f:
    config = json.load(f)

scope = Scope.from_dict(config)

# Use in crawler
for url in discover_urls():
    if scope.is_in_scope(url):
        process(url)
```

**Example `scope.json`:**
```json
{
    "allowed_domains": ["example.com", "api.example.com"],
    "allowed_paths": ["/api", "/public"],
    "disallowed_paths": ["/admin", "/internal"]
}
```

---

## Testing

Run scope validation tests:

```bash
uv run pytest tests/test_scope.py -v
```

**Test Summary:**
- ✅ 42 comprehensive tests
- ✅ Domain validation (exact, subdomain, ports, case sensitivity)
- ✅ Path validation (whitelisting, blacklisting, priorities)
- ✅ Combined scope checking
- ✅ Configuration serialization/deserialization
- ✅ Edge cases and error handling

---

## Next Steps

The Scope Validation module is complete and ready for integration into the crawler engine (Step 9). The next phase is:

**Step 5: HTTP Client** (`crawler/http.py`)
- Wrap httpx for consistent error handling
- Implement timeout and redirect handling
- Add retry logic for failed requests

---

## Dependencies

Scope validation uses only Python standard library:
- `urllib.parse` — URL parsing
- `typing` — Type hints
- `re` — (Available, not currently used)

**No external dependencies required.**

---

## Integration Notes

The Scope class is designed to work seamlessly with:
- **URL Normalization (Step 3)** — Normalized URLs are passed to scope validators
- **Crawler Engine (Step 9)** — Engine uses `is_in_scope()` before adding URLs to queue
- **CLI (Step 10)** — Scope configuration passed via CLI or config file

Example integration in engine:

```python
from dash_penetration.crawler import Scope, normalize_url

scope = Scope.from_dict(config)
discovered_urls = [...]

for url in discovered_urls:
    normalized = normalize_url(url)
    if scope.is_in_scope(normalized):
        queue.add(normalized)
```

---

## Architecture

```
crawler/
├── urls.py (Step 3) ─→ normalize URLs
├── scope.py (Step 4) ─→ validate scope ✅
├── http.py (Step 5, pending)
├── parser.py (Step 6, pending)
└── engine.py (Step 9, pending)

discovery/ (Step 7, pending)
output/ (Step 8, pending)
cli.py (Step 10, pending)
```

**Dependency Graph:**
```
Step 1: Setup
  ↓
Step 2: Models
  ├─→ Step 3: URL Handling ✅
  ├─→ Step 4: Scope Validation ✅ ← YOU ARE HERE
  │   ↓
  │  Step 9: Engine (depends on 3, 4)
  │   ↓
  ├─→ Step 5: HTTP Client (pending)
  ├─→ Step 6: Parser (pending)
  ├─→ Step 7: Discovery (pending)
  └─→ Step 8: Output (pending)
      ↓
   Step 10: CLI & Integration
      ↓
   Step 11: Polish
```

---

## Summary

✅ **Phase 4: Scope Validation** is complete with:
- Robust domain and path validation
- Flexible configuration (whitelist + blacklist)
- Full serialization support
- 42 comprehensive tests
- Zero external dependencies
- Production-ready code

Ready for Step 5: HTTP Client implementation.
