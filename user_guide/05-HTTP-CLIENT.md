
---
title: "Step 5: HTTP Client"
guide-section: "Getting Started"
---

**Status:** ✅ Complete  
**Module:** `dash_penetration.crawler.http`  
**Tests:** 31 comprehensive tests  


## Overview

The HTTP Client module provides a robust, async-first wrapper around `httpx` for consistent error handling, timeout management, redirect handling, and response validation. It's designed for the web crawler to safely and reliably fetch URLs with automatic retries and detailed error reporting.

---

## Implementation Summary

### What was built:

**`crawler/http.py`** — Full HTTP client module with:
- **`HTTPResponse` dataclass** — Structured HTTP response with:
  - URL, status code, content, headers
  - Automatic content-type and content-length extraction
  - Helper methods: `text()`, `is_html()`, `is_json()`
  - UTF-8 decoding with fallback support

- **`HTTPClient` class** wrapping `httpx.AsyncClient` with:
  - Configurable timeout, redirects, SSL verification, retries
  - Async/await support with context manager
  - Automatic connection management (`connect()`, `close()`)
  - Retry logic with exponential backoff
  - Rate limit detection (HTTP 429)

- **Error handling** with custom exceptions:
  - `HTTPError` — Base exception
  - `HTTPConnectionError` — Network/connection failures
  - `HTTPTimeoutError` — Request timeouts
  - `HTTPSSLError` — SSL certificate errors
  - `HTTPTooManyRedirectsError` — Redirect loops
  - `HTTPStatusError` — HTTP error status codes

### Key Features:

| Feature | Details |
|---------|---------|
| **Async-First** | Full async/await support with context managers |
| **Retry Logic** | Exponential backoff on transient failures (configurable) |
| **Timeout Handling** | Configurable per-request timeouts |
| **Redirect Control** | Override follow_redirects per-request |
| **Rate Limit Detection** | Automatic detection of HTTP 429 responses |
| **Response Validation** | Automatic content-type and content-length extraction |
| **Error Messages** | Clear, actionable error messages with URLs |
| **SSL Control** | Configurable SSL verification (for learning purposes) |

### Test Coverage:

- **31 comprehensive tests** covering:
  - Response creation and content parsing
  - Client initialization and connection management
  - Successful GET, POST, HEAD requests
  - Redirect following and override
  - Timeout handling with retries
  - Connection errors with exponential backoff
  - SSL/certificate errors
  - Too many redirects detection
  - Rate limit detection (429 responses)
  - JSON parsing convenience method
  - Error message clarity

### Dependencies:

- `httpx==0.27.0` — Async HTTP client
- Python stdlib only otherwise

---

## Usage Guide

### Basic Usage

#### Simple GET Request

```python
from dash_penetration.crawler import HTTPClient

async def main():
    async with HTTPClient() as client:
        response = await client.get("https://example.com")
        print(f"Status: {response.status_code}")
        print(f"Content type: {response.content_type}")
        print(f"Content: {response.text()}")

asyncio.run(main())
```

#### With Custom Configuration

```python
async with HTTPClient(
    timeout=30.0,                 # 30 second timeout
    follow_redirects=False,        # Don't follow redirects
    verify_ssl=False,              # Disable SSL verification (for learning)
    max_retries=5,                 # Retry up to 5 times
) as client:
    response = await client.get("https://example.com")
```

#### Manual Connection Management

```python
client = HTTPClient(timeout=15.0)

try:
    await client.connect()
    response = await client.get("https://example.com")
    print(response.text())
finally:
    await client.close()
```

### HTTP Methods

```python
async with HTTPClient() as client:
    # GET request
    response = await client.get("https://api.example.com/users")
    
    # POST request with JSON data
    response = await client.post(
        "https://api.example.com/users",
        json={"name": "Alice", "email": "alice@example.com"}
    )
    
    # HEAD request (no response body)
    response = await client.head("https://api.example.com/users")
    
    # Generic fetch with method and custom headers
    response = await client.fetch(
        "https://api.example.com/users",
        method="PUT",
        headers={"Authorization": "Bearer token123"}
    )
```

### Working with Responses

#### Basic Response Information

```python
response = await client.get("https://example.com")

print(f"URL: {response.url}")
print(f"Status: {response.status_code}")
print(f"Content type: {response.content_type}")
print(f"Content length: {response.content_length}")
print(f"Elapsed time: {response.elapsed_ms}ms")
print(f"Timestamp: {response.timestamp}")
```

#### Response Content

```python
response = await client.get("https://example.com")

# Get text (UTF-8 with fallback)
text = response.text()

# Get raw bytes
raw_bytes = response.content

# Check content type
if response.is_html():
    print("Response is HTML")
    
if response.is_json():
    print("Response is JSON")
```

#### Response Headers

```python
response = await client.get("https://example.com")

# Access headers as dict
headers = response.headers
print(headers.get("content-type"))
print(headers.get("cache-control"))

# Check for specific headers
if "set-cookie" in response.headers:
    print("Response sets cookies")
```

### Error Handling

#### Catching Specific Errors

```python
from dash_penetration.crawler import (
    HTTPClient,
    HTTPConnectionError,
    HTTPTimeoutError,
    HTTPSSLError,
    HTTPError,
)

async with HTTPClient(timeout=5.0) as client:
    try:
        response = await client.get("https://example.com")
    except HTTPTimeoutError:
        print("Request timed out")
    except HTTPConnectionError as e:
        print(f"Connection failed: {e}")
    except HTTPSSLError as e:
        print(f"SSL certificate error: {e}")
    except HTTPError as e:
        print(f"Generic HTTP error: {e}")
```

#### Catching All HTTP Errors

```python
try:
    response = await client.get("https://example.com")
except HTTPError as e:
    print(f"HTTP error: {e}")
```

#### Rate Limit Handling

```python
response = await client.get("https://example.com")

if response.status_code == 429:
    print("Rate limited! Waiting...")
    await asyncio.sleep(60)
    response = await client.get("https://example.com")
```

### Convenience Methods

#### JSON Parsing

```python
async with HTTPClient() as client:
    # GET and parse JSON
    data = await client.get_json("https://api.example.com/users")
    print(data)  # {'id': 1, 'name': 'Alice', ...}
```

### Redirect Handling

#### Follow Redirects (Default)

```python
async with HTTPClient(follow_redirects=True) as client:
    response = await client.get("https://example.com/old")
    # If /old redirects to /new, response.url will be the final URL
    print(response.url)  # https://example.com/new
```

#### Don't Follow Redirects

```python
async with HTTPClient(follow_redirects=False) as client:
    response = await client.get("https://example.com/old")
    # Response will be the redirect (301, 302, etc.)
    print(response.status_code)  # 301 or 302
```

#### Override Per-Request

```python
async with HTTPClient(follow_redirects=True) as client:
    # Override to not follow redirects for this request
    response = await client.get(
        "https://example.com/old",
        follow_redirects=False
    )
    print(response.status_code)  # 301 or 302
```

### Retry Behavior

```python
# Retry up to 3 times (default is 2)
async with HTTPClient(max_retries=3) as client:
    try:
        response = await client.get("https://flaky-server.example.com")
    except HTTPConnectionError:
        print("Failed after 4 attempts")
```

**Retry logic:**
- Transient errors (connection, timeout) trigger retries
- Exponential backoff: 0.5s, 1s, 1.5s, ...
- SSL errors and redirects loops don't retry (permanent failures)
- Non-transient HTTP status codes don't retry (4xx, 5xx)

### SSL Certificate Verification

#### Verify Certificates (Recommended)

```python
async with HTTPClient(verify_ssl=True) as client:  # Default
    response = await client.get("https://example.com")
```

#### Disable Verification (Learning Only)

```python
async with HTTPClient(verify_ssl=False) as client:
    # For testing/learning, ignore certificate errors
    response = await client.get("https://self-signed.example.com")
```

### Real-World Examples

#### Web Crawling with Rate Limiting

```python
async def crawl_urls(urls: list[str]):
    async with HTTPClient(
        timeout=10.0,
        follow_redirects=True,
        max_retries=2,
    ) as client:
        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"✓ {url} ({response.content_type})")
                elif response.status_code == 429:
                    print(f"⏱  Rate limited, waiting...")
                    await asyncio.sleep(60)
                else:
                    print(f"✗ {url} ({response.status_code})")
            except HTTPTimeoutError:
                print(f"⏱  Timeout: {url}")
            except HTTPError as e:
                print(f"✗ Error: {url} - {e}")
            
            await asyncio.sleep(1)  # Respectful delay

asyncio.run(crawl_urls([
    "https://example.com",
    "https://example.com/about",
    "https://example.com/api",
]))
```

#### API Client with Error Recovery

```python
async def fetch_api_data(url: str, retries: int = 3):
    async with HTTPClient(
        timeout=15.0,
        max_retries=retries,
    ) as client:
        try:
            data = await client.get_json(url)
            return data
        except HTTPTimeoutError:
            print(f"API timeout after {retries} retries")
            return None
        except HTTPSSLError:
            print("SSL certificate error - using non-SSL connection")
            url = url.replace("https://", "http://")
            return await client.get_json(url)
        except HTTPError as e:
            print(f"API error: {e}")
            return None

data = asyncio.run(fetch_api_data("https://api.example.com/data"))
```

---

## API Reference

### `HTTPResponse` Dataclass

```python
@dataclass
class HTTPResponse:
    url: str                          # Final URL (after redirects)
    status_code: int                  # HTTP status code
    content: bytes                    # Response body (binary)
    headers: dict                     # Response headers
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    elapsed_ms: float = 0.0           # Request duration in milliseconds
    timestamp: Optional[datetime] = None
```

#### Methods

##### `text() -> str`

Get response content as text (UTF-8 with fallback to handle encoding errors).

```python
text = response.text()
```

##### `is_html() -> bool`

Check if response is HTML (content-type contains "text/html").

```python
if response.is_html():
    # Parse HTML
```

##### `is_json() -> bool`

Check if response is JSON (content-type contains "application/json").

```python
if response.is_json():
    # Parse JSON
```

### `HTTPClient` Class

#### Constructor

```python
HTTPClient(
    timeout: float = 10.0,
    follow_redirects: bool = True,
    max_redirects: int = 5,
    verify_ssl: bool = True,
    user_agent: Optional[str] = None,
    max_retries: int = 2,
)
```

**Parameters:**
- `timeout` — Request timeout in seconds (default 10s)
- `follow_redirects` — Follow HTTP redirects (default True)
- `max_redirects` — Maximum number of redirects (default 5)
- `verify_ssl` — Verify SSL certificates (default True)
- `user_agent` — Custom User-Agent header (default: Mozilla 5.0 compatible)
- `max_retries` — Retry count for transient errors (default 2)

#### Methods

##### Lifecycle

```python
async connect() -> None
```
Manually initialize the async HTTP client.

```python
async close() -> None
```
Close the async HTTP client and clean up resources.

##### HTTP Requests

```python
async fetch(url: str, method: str = "GET", follow_redirects: Optional[bool] = None, **kwargs) -> HTTPResponse
```
Perform a generic HTTP request with full customization.

```python
async get(url: str, **kwargs) -> HTTPResponse
```
Perform a GET request.

```python
async post(url: str, **kwargs) -> HTTPResponse
```
Perform a POST request.

```python
async head(url: str, **kwargs) -> HTTPResponse
```
Perform a HEAD request (no response body).

##### Convenience Methods

```python
async get_json(url: str, **kwargs) -> dict
```
GET and parse JSON response. Raises `ValueError` if JSON is invalid.

#### Context Manager

```python
async with HTTPClient() as client:
    response = await client.get("https://example.com")
```

### Exception Hierarchy

```
HTTPError (base)
├── HTTPConnectionError
├── HTTPTimeoutError
├── HTTPSSLError
├── HTTPTooManyRedirectsError
└── HTTPStatusError
```

#### `HTTPConnectionError`
Network/connection failure (DNS, connection refused, etc.).

#### `HTTPTimeoutError`
Request timed out after configured timeout.

#### `HTTPSSLError`
SSL certificate validation error.

#### `HTTPTooManyRedirectsError`
Too many redirects (redirect loop detected).

#### `HTTPStatusError`
HTTP error status (4xx, 5xx). Has `status_code` and `url` attributes.

---

## Testing

Run HTTP client tests:

```bash
uv run pytest tests/test_http.py -v
```

**Test Coverage:**
- ✅ 31 comprehensive tests
- ✅ Response parsing and content type detection
- ✅ Client initialization and connection management
- ✅ HTTP methods (GET, POST, HEAD)
- ✅ Successful requests and responses
- ✅ Error handling (connection, timeout, SSL, redirects)
- ✅ Retry logic with exponential backoff
- ✅ Rate limit detection
- ✅ JSON parsing
- ✅ Redirect following and override
- ✅ Error message clarity

---

## Next Steps

The HTTP Client is complete and ready for integration with other modules. The next phase is:

**Step 6: HTML Parser** (`crawler/parser.py`)
- Extract links from HTML
- Extract forms and inputs
- Extract script resources
- Resolve relative URLs to absolute

---

## Dependencies

HTTP Client uses:
- `httpx==0.27.0` — Async HTTP client
- Python stdlib: `asyncio`, `logging`, `dataclasses`, `datetime`

**No additional external dependencies.**

---

## Integration Notes

The HTTP Client integrates seamlessly with:
- **Crawler Engine (Step 9)** — Used to fetch discovered URLs
- **URL Normalization (Step 3)** — Normalized URLs passed to client
- **Scope Validation (Step 4)** — Scope check before HTTP request
- **HTML Parser (Step 6)** — Parse response content

Example integration:

```python
from dash_penetration.crawler import HTTPClient, Scope, normalize_url

scope = Scope(allowed_domains=["example.com"])

async def crawl_url(url: str):
    normalized_url = normalize_url(url)
    
    if not scope.is_in_scope(normalized_url):
        print(f"Out of scope: {url}")
        return None
    
    async with HTTPClient(timeout=10.0) as client:
        try:
            response = await client.get(normalized_url)
            
            if response.status_code == 200:
                # Process response (e.g., parse HTML)
                return response
            else:
                print(f"Non-200 status: {response.status_code}")
                return response
                
        except HTTPError as e:
            print(f"HTTP error: {e}")
            return None

result = asyncio.run(crawl_url("https://example.com/page"))
```

---

## Architecture Progress

```
crawler/
├── urls.py (Step 3) ─→ normalize URLs ✅
├── scope.py (Step 4) ─→ validate scope ✅
├── http.py (Step 5) ─→ fetch URLs ✅
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
  ├─→ Step 4: Scope Validation ✅
  ├─→ Step 5: HTTP Client ✅ ← YOU ARE HERE
  │   ↓
  │  Step 9: Engine (depends on 3, 4, 5, 6, 7)
  │   ↓
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

✅ **Phase 5: HTTP Client** is complete with:
- Robust async HTTP client with error handling
- Automatic retry logic with exponential backoff
- Comprehensive response parsing and validation
- Rate limit detection
- SSL verification control (for learning)
- 31 comprehensive tests
- Production-ready code

Ready for Step 6: HTML Parser implementation.
