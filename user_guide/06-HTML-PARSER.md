
---
title: "Step 6: HTML Parser"
guide-section: "Getting Started"
---



## Overview

The HTML Parser module uses `selectolax` for fast, efficient HTML parsing and extraction of links, forms, scripts, and meta information. It handles relative URL resolution, deduplication, and malformed HTML gracefully.

---

## Implementation Summary

### What was built:

**`crawler/parser.py`** — Full HTML parser module with:
- **`HTMLParser` class** providing:
  - URL resolution (relative to absolute)
  - Link extraction with deduplication
  - Form extraction with inputs, textareas, selects
  - Script extraction (external and inline)
  - Meta tag extraction

- **Data classes**:
  - `Form` — Represents an HTML form with action, method, inputs
  - `FormInput` — Represents form input fields
  - `ScriptReference` — Represents script references (external or inline)

### Key Features:

| Feature | Details |
|---------|---------|
| **Fast Parsing** | Uses selectolax for 5-10x faster parsing than BeautifulSoup |
| **URL Resolution** | Converts relative URLs to absolute (handles .., /, etc.) |
| **Link Deduplication** | Optional deduplication within page |
| **Form Extraction** | Extracts forms with all input types (text, password, textarea, select) |
| **Script Detection** | Finds external scripts and inline JavaScript |
| **Meta Extraction** | Extracts meta tags and Open Graph properties |
| **Malformed HTML** | Handles broken HTML gracefully |
| **All-in-One** | `extract_all()` extracts links, forms, scripts, meta in one call |

### Test Coverage:

- **42 comprehensive tests** covering:
  - URL resolution (absolute, relative, parent dirs, fragments, queries)
  - Link extraction (simple, duplicates, relative, malformed HTML)
  - Form extraction (GET/POST, inputs, textareas, selects, relative actions)
  - Script extraction (external, inline, content)
  - Meta tag extraction (standard, Open Graph)
  - Real-world HTML examples
  - Data class creation and validation

### Dependencies:

- `selectolax==0.3.21` — Fast HTML parser
- Python stdlib only otherwise

---

## Usage Guide

### Basic Usage

#### Initialize HTMLParser

```python
from dash_penetration.crawler import HTMLParser

# Create parser for a base URL
parser = HTMLParser("https://example.com")
```

#### Extract Links

```python
html = """
<html>
    <a href="https://example.com/page1">Link 1</a>
    <a href="/page2">Link 2</a>
    <a href="page3">Link 3</a>
</html>
"""

parser = HTMLParser("https://example.com")
links = parser.extract_links(html)
# Returns: ['https://example.com/page1', 'https://example.com/page2', 'https://example.com/page3']
```

#### Extract Forms

```python
html = """
<form action="/login" method="POST">
    <input type="text" name="username" required>
    <input type="password" name="password" required>
    <input type="submit" value="Login">
</form>
"""

parser = HTMLParser("https://example.com")
forms = parser.extract_forms(html)

form = forms[0]
print(f"Action: {form.action}")  # https://example.com/login
print(f"Method: {form.method}")  # POST
print(f"Inputs: {[i.name for i in form.inputs]}")  # ['username', 'password', 'submit']
```

#### Extract Scripts

```python
html = """
<head>
    <script src="https://example.com/lib.js"></script>
    <script src="/local.js"></script>
</head>
<body>
    <script>console.log("inline");</script>
</body>
"""

parser = HTMLParser("https://example.com")
scripts = parser.extract_scripts(html)

# External scripts
for script in scripts:
    if not script.is_inline:
        print(f"External: {script.src}")
    else:
        print(f"Inline: {script.content}")
```

#### Extract Meta Tags

```python
html = """
<head>
    <meta name="description" content="Test page">
    <meta name="robots" content="noindex, nofollow">
    <meta property="og:title" content="Page Title">
</head>
"""

parser = HTMLParser("https://example.com")
meta = parser.extract_meta(html)

print(meta["description"])  # Test page
print(meta["robots"])  # noindex, nofollow
print(meta["og:title"])  # Page Title
```

#### Extract Everything

```python
result = parser.extract_all(html)

# Returns dict with:
# {
#     "links": [...],
#     "forms": [...],
#     "scripts": [...],
#     "meta": {...}
# }
```

### URL Resolution

#### Absolute URLs (unchanged)

```python
parser = HTMLParser("https://example.com/page1")
url = parser.resolve_url("https://other.com/page2")
# Returns: https://other.com/page2
```

#### Relative Paths

```python
parser = HTMLParser("https://example.com/dir/page1")
url = parser.resolve_url("page2")
# Returns: https://example.com/dir/page2
```

#### Absolute Paths (from root)

```python
parser = HTMLParser("https://example.com/dir/page1")
url = parser.resolve_url("/page2")
# Returns: https://example.com/page2
```

#### Parent Directory

```python
parser = HTMLParser("https://example.com/dir/subdir/page1")
url = parser.resolve_url("../page2")
# Returns: https://example.com/dir/page2
```

#### Fragments and Query Strings

```python
parser = HTMLParser("https://example.com/page1")

# Fragment only (returns base URL)
url = parser.resolve_url("#section")
# Returns: https://example.com/page1

# Query string
url = parser.resolve_url("?id=123")
# Returns: https://example.com/page1?id=123
```

### Link Deduplication

#### With Deduplication (default)

```python
html = """
<a href="/page1">Link 1</a>
<a href="/page1">Link 2</a>
<a href="/page2">Link 3</a>
"""

parser = HTMLParser("https://example.com")
links = parser.extract_links(html, dedup=True)
# Returns: ['https://example.com/page1', 'https://example.com/page2']
# Duplicates removed
```

#### Without Deduplication

```python
links = parser.extract_links(html, dedup=False)
# Returns: ['https://example.com/page1', 'https://example.com/page1', 'https://example.com/page2']
# Duplicates preserved
```

### Real-World Examples

#### Extract All Data from a Page

```python
from dash_penetration.crawler import HTMLParser

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Product Page</title>
    <meta name="description" content="Buy products">
    <script src="https://cdn.example.com/jquery.js"></script>
</head>
<body>
    <form action="/search" method="GET">
        <input type="text" name="q" placeholder="Search...">
        <input type="submit" value="Search">
    </form>
    <a href="/product/1">Product 1</a>
    <a href="/product/2">Product 2</a>
    <script>console.log('loaded');</script>
</body>
</html>
"""

parser = HTMLParser("https://example.com/products")
result = parser.extract_all(html)

print(f"Found {len(result['links'])} links")
print(f"Found {len(result['forms'])} forms")
print(f"Found {len(result['scripts'])} scripts")
print(f"Meta: {result['meta']}")
```

#### Crawl a Page and Extract Endpoints

```python
async def crawl_page(url: str):
    from dash_penetration.crawler import HTTPClient, HTMLParser
    
    async with HTTPClient() as client:
        response = await client.get(url)
        
        if response.is_html():
            parser = HTMLParser(response.url)
            result = parser.extract_all(response.text())
            
            return {
                "url": response.url,
                "links": result["links"],
                "forms": result["forms"],
                "status": response.status_code,
            }

# Use it
import asyncio
result = asyncio.run(crawl_page("https://example.com"))
```

---

## API Reference

### `HTMLParser` Class

#### Constructor

```python
HTMLParser(base_url: str)
```

**Parameters:**
- `base_url` (required): Base URL for resolving relative URLs

#### Methods

##### `parse(html: str) -> SelectolaxParser`

Parse HTML content and return parsed document.

```python
doc = parser.parse("<html><body>Test</body></html>")
```

**Raises:** `ValueError` if HTML is empty or invalid

##### `resolve_url(url: str) -> str`

Resolve a relative or absolute URL to absolute URL.

```python
resolved = parser.resolve_url("/page")
# Returns: https://example.com/page
```

**Raises:** `ValueError` if URL is invalid or cannot be resolved

##### `extract_links(html: str, dedup: bool = True) -> list[str]`

Extract all links from HTML.

```python
links = parser.extract_links(html)
links = parser.extract_links(html, dedup=False)
```

**Returns:** List of absolute URLs

**Raises:** `ValueError` if HTML cannot be parsed

##### `extract_forms(html: str) -> list[Form]`

Extract all forms from HTML.

```python
forms = parser.extract_forms(html)
for form in forms:
    print(f"{form.method} {form.action}")
    for input_field in form.inputs:
        print(f"  - {input_field.name}")
```

**Returns:** List of `Form` objects

**Raises:** `ValueError` if HTML cannot be parsed

##### `extract_scripts(html: str) -> list[ScriptReference]`

Extract all script references from HTML.

```python
scripts = parser.extract_scripts(html)
for script in scripts:
    if script.is_inline:
        print(f"Inline: {script.content}")
    else:
        print(f"External: {script.src}")
```

**Returns:** List of `ScriptReference` objects

**Raises:** `ValueError` if HTML cannot be parsed

##### `extract_meta(html: str) -> dict[str, str]`

Extract meta tags from HTML.

```python
meta = parser.extract_meta(html)
print(meta["description"])
print(meta["og:title"])
```

**Returns:** Dictionary mapping tag names to content values

**Raises:** `ValueError` if HTML cannot be parsed

##### `extract_all(html: str) -> dict`

Extract all data (links, forms, scripts, meta) from HTML.

```python
result = parser.extract_all(html)
links = result["links"]
forms = result["forms"]
scripts = result["scripts"]
meta = result["meta"]
```

**Returns:** Dictionary with 'links', 'forms', 'scripts', 'meta' keys

### `Form` Dataclass

```python
@dataclass
class Form:
    action: str                  # Form action URL
    method: str = "GET"          # HTTP method (GET, POST, etc.)
    inputs: list[FormInput] = [] # Form input fields
```

**Properties:**
- `action` — Form action URL (absolute)
- `method` — HTTP method, normalized to uppercase
- `inputs` — List of `FormInput` objects

### `FormInput` Dataclass

```python
@dataclass
class FormInput:
    name: str              # Input field name
    input_type: str = "text"  # Input type (text, password, textarea, select, etc.)
    value: Optional[str] = None  # Input default value
    required: bool = False # Whether field is required
```

### `ScriptReference` Dataclass

```python
@dataclass
class ScriptReference:
    src: Optional[str] = None  # Script URL (for external scripts)
    is_inline: bool = False    # Whether script is inline
    content: Optional[str] = None  # Script content (for inline scripts)
```

---

## Testing

Run parser tests:

```bash
uv run pytest tests/test_parser.py -v
```

**Test Coverage:**
- ✅ 42 comprehensive tests
- ✅ URL resolution (absolute, relative, parent dirs, fragments)
- ✅ Link extraction (simple, duplicates, malformed HTML)
- ✅ Form extraction (GET/POST, various input types)
- ✅ Script extraction (external and inline)
- ✅ Meta tag extraction (standard and Open Graph)
- ✅ Real-world HTML examples

---

## Performance

HTMLParser uses `selectolax` for fast HTML parsing:

- **5-10x faster** than BeautifulSoup
- **Minimal memory** footprint
- **Handles malformed** HTML gracefully
- **Zero external** JS/browser requirements

---

## Next Steps

The HTML Parser is complete and ready for integration with the crawler engine. The next phase is:

**Step 7: Discovery Plugins** (`discovery/` module)
- Extract and categorize links (internal vs external)
- API endpoint detection
- JavaScript resource discovery
- Form parameter analysis

---

## Integration Notes

The HTML Parser integrates with:
- **HTTP Client (Step 5)** — Parse response content
- **URL Normalization (Step 3)** — Resolve discovered URLs
- **Scope Validation (Step 4)** — Validate discovered URLs within scope
- **Crawler Engine (Step 9)** — Extract new URLs to crawl

Example integration:

```python
from dash_penetration.crawler import HTTPClient, HTMLParser, Scope

async def crawl_and_extract(url: str):
    scope = Scope(allowed_domains=["example.com"])
    
    async with HTTPClient() as client:
        response = await client.get(url)
        
        if not response.is_html():
            return None
        
        parser = HTMLParser(response.url)
        result = parser.extract_all(response.text())
        
        # Filter links by scope
        in_scope_links = [
            link for link in result["links"]
            if scope.is_in_scope(link)
        ]
        
        return {
            "links": in_scope_links,
            "forms": result["forms"],
            "scripts": result["scripts"],
        }
```

---

## Architecture Progress

```
crawler/
├── urls.py (Step 3) ─→ normalize URLs ✅
├── scope.py (Step 4) ─→ validate scope ✅
├── http.py (Step 5) ─→ fetch URLs ✅
├── parser.py (Step 6) ─→ parse HTML ✅
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
  ├─→ Step 4: Scope Validation ✅
  ├─→ Step 5: HTTP Client ✅
  ├─→ Step 6: HTML Parser ✅ ← YOU ARE HERE
  │   ↓
  │  Step 9: Engine (depends on 3, 4, 5, 6, 7)
  │   ↓
  ├─→ Step 7: Discovery (pending)
  └─→ Step 8: Output (pending)
      ↓
   Step 10: CLI & Integration
      ↓
   Step 11: Polish
```

---

## Summary

✅ **Phase 6: HTML Parser** is complete with:
- Fast HTML parsing using selectolax
- URL resolution (absolute, relative, parent dirs)
- Link extraction with deduplication
- Comprehensive form extraction
- Script detection (external and inline)
- Meta tag extraction
- 42 comprehensive tests
- Production-ready code

Ready for Step 7: Discovery Plugins implementation.
