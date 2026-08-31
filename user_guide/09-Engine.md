---
title: "Step 9: Main Crawler Engine"
guide-section: "Getting Started"
---

**Status:** ✅ Complete  
**Module:** `dash_penetration.crawler.engine`  
**Tests:** 14 comprehensive integration tests  

## Overview

The Crawler Engine orchestrates the complete web crawling workflow, managing URL discovery, concurrency, rate limiting, page fetching, parsing, and discovery plugin execution. It's the central component that ties together all the foundational modules (URL handling, scope validation, HTTP client, parsing, and discovery).

---

## Implementation Summary

### What was built:

**`crawler/engine.py`** — Complete crawler engine with:

- **`CrawlEngine` class** — Main orchestrator with:
  - URL queue management with deduplication
  - Concurrent request handling
  - Rate limiting using token bucket algorithm
  - Page fetching and HTML parsing
  - Discovery plugin integration
  - Result aggregation and tracking

- **`RateLimiter` class** — Token bucket rate limiter with:
  - Smooth rate limiting without blocking
  - Configurable requests per second
  - Async-aware design

### Key Features:

| Feature | Details |
|---------|---------|
| **URL Queue Management** | Deque-based queue with scope validation and deduplication |
| **Concurrency Control** | Configurable max concurrent requests (default: 5) with semaphore |
| **Rate Limiting** | Token bucket algorithm (default: 10 req/s) |
| **Page Processing** | Fetch, parse, and process HTML with discovery plugins |
| **Discovery Integration** | Links, forms, scripts, and API endpoint extraction |
| **Result Tracking** | Comprehensive results with pages crawled, endpoints, and errors |
| **Progress Monitoring** | Real-time progress information |
| **Error Handling** | Graceful error handling with logging |

### Test Coverage:

- **14 comprehensive integration tests** covering:
  - Engine initialization
  - Rate limiter token bucket
  - URL queue validation (duplicates, scope, invalid URLs)
  - Single page crawl
  - Concurrency limits enforced
  - Rate limiting enforced
  - Scope enforcement during discovery
  - Progress tracking
  - Error handling and edge cases

### Dependencies:

- `httpx` — Async HTTP client
- `selectolax` — HTML parsing
- Previously completed modules:
  - `crawler.urls` — URL normalization and deduplication
  - `crawler.scope` — Scope validation
  - `crawler.http` — HTTP client wrapper
  - `crawler.parser` — HTML parser
  - `discovery.*` — Discovery plugins

---

## Architecture

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                    CrawlEngine                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  URL Queue Management                              │   │
│  │  - Initial target URL                              │   │
│  │  - Discovered URLs from links, forms, scripts      │   │
│  │  - Scope validation on add                         │   │
│  │  - Deduplication via URLCache                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Concurrency Control (Semaphore)                   │   │
│  │  - Max concurrent workers (default: 5)             │   │
│  │  - Async processing                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Rate Limiter (Token Bucket)                       │   │
│  │  - Requests per second (default: 10)               │   │
│  │  - Smooth rate limiting                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Page Fetching (HTTPClient)                        │   │
│  │  - HTTP request execution                          │   │
│  │  - Response validation                             │   │
│  │  - Error handling                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HTML Parsing (HTMLParser)                         │   │
│  │  - Extract links, forms, scripts, meta             │   │
│  │  - Relative URL resolution                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Discovery Plugins                                 │   │
│  │  - LinkDiscovery: categorize internal/external     │   │
│  │  - FormDiscovery: extract form endpoints           │   │
│  │  - ScriptDiscovery: track script resources         │   │
│  │  - APIDiscovery: detect API endpoints              │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Result Aggregation (CrawlResult)                  │   │
│  │  - Endpoint inventory                              │   │
│  │  - Page count and timing                           │   │
│  │  - Error tracking                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Processing Flow

```
START
  ↓
[Initialize CrawlEngine]
  - Create URL queue
  - Set concurrency/rate limits
  - Initialize discovery plugins
  ↓
[Add target URL to queue]
  - Validate scope
  - Add as INITIAL source
  ↓
[Main crawl loop]
  ├─→ [Dequeue URL]
  │    ↓
  │   [Acquire semaphore] (concurrency control)
  │    ↓
  │   [Acquire rate limiter token]
  │    ↓
  │   [Fetch page with HTTPClient]
  │    ↓
  │   [Parse HTML]
  │    ↓
  │   [Run discovery plugins]
  │    │
  │    ├─→ LinkDiscovery → Extract links → Add internal to queue
  │    ├─→ FormDiscovery → Extract forms → Add actions to queue
  │    ├─→ ScriptDiscovery → Track scripts
  │    └─→ APIDiscovery → Detect APIs
  │    ↓
  │   [Create/update Endpoint]
  │    ↓
  │   [Release semaphore]
  │    ↓
  └─→ [Repeat until queue empty]
  ↓
[Set end time]
  ↓
[Return CrawlResult]
  ↓
END
```

---

## Usage Guide

### Basic Usage

#### Simple Single-Domain Crawl

```python
import asyncio
from dash_penetration.crawler import CrawlEngine, Scope

async def main():
    # Define scope
    scope = Scope(allowed_domains=["example.com"])
    
    # Create and run engine
    async with CrawlEngine(
        target_url="https://example.com",
        scope=scope
    ) as engine:
        result = await engine.crawl()
    
    # Access results
    print(f"Pages crawled: {result.pages_crawled}")
    print(f"Endpoints found: {len(result.endpoints)}")
    
    # Print endpoint summary
    for endpoint in result.get_endpoint_summary():
        print(f"  {endpoint['method']} {endpoint['path']} → {endpoint['status']}")

# Run async crawl
asyncio.run(main())
```

#### Multi-Domain with Path Restrictions

```python
scope = Scope(
    allowed_domains=["example.com", "api.example.com"],
    allowed_paths=["/api", "/v2"],
    disallowed_paths=["/admin", "/private"]
)

async with CrawlEngine(
    target_url="https://example.com",
    scope=scope,
    rate_limit=5.0,  # 5 requests per second
    max_concurrency=3  # Max 3 parallel requests
) as engine:
    result = await engine.crawl()
```

### Configuration Options

#### CrawlEngine Constructor

```python
CrawlEngine(
    target_url: str,
    scope: Scope,
    rate_limit: float = 10.0,        # Requests per second
    max_concurrency: int = 5,         # Max parallel requests
    timeout: float = 10.0,            # HTTP timeout in seconds
    verify_ssl: bool = True           # SSL verification
)
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_url` | Required | Initial URL to start crawling |
| `scope` | Required | Scope object defining allowed domains/paths |
| `rate_limit` | 10.0 | Requests per second (10 = 1 request every 100ms) |
| `max_concurrency` | 5 | Maximum parallel requests |
| `timeout` | 10.0 | HTTP request timeout in seconds |
| `verify_ssl` | True | Whether to verify SSL certificates |

### Working with Results

#### CrawlResult Object

```python
result = await engine.crawl()

# Access basic metrics
print(f"Pages crawled: {result.pages_crawled}")
print(f"Unique endpoints: {len(result.endpoints)}")
print(f"Errors: {len(result.errors)}")

# Access timing
print(f"Duration: {(result.end_time - result.start_time).total_seconds()}s")

# Access target and scope info
print(f"Target: {result.target_url}")
print(f"Scope: {result.scope_domains}")
```

#### Endpoint Summary

```python
# Get formatted endpoint list
summary = result.get_endpoint_summary()

for endpoint in summary:
    print(f"{endpoint['method']:6} {endpoint['path']:40} {endpoint['status']:3} "
          f"Forms: {endpoint['forms_count']} Links: {endpoint['links_count']}")

# Example output:
# GET    /                                        200 Forms: 1 Links: 5
# GET    /login                                   200 Forms: 1 Links: 2
# POST   /login                                   200 Forms: 0 Links: 0
# GET    /api/products                            200 Forms: 0 Links: 0
```

#### Individual Endpoints

```python
# Access specific endpoints
for key, endpoint in result.endpoints.items():
    print(f"\nEndpoint: {key}")
    print(f"  Status: {endpoint.status_code}")
    print(f"  Content-Type: {endpoint.content_type}")
    print(f"  Forms: {len(endpoint.forms)}")
    print(f"  Links: {len(endpoint.links)}")
    print(f"  Scripts: {len(endpoint.scripts)}")
    print(f"  Is API: {endpoint.is_api}")
    
    # Access form details
    for form in endpoint.forms:
        print(f"    Form: {form.action} ({form.method})")
        for field in form.fields:
            print(f"      - {field.name} ({field.field_type}) "
                  f"{'[required]' if field.required else ''}")
```

#### Serialization

```python
import json

# Convert to JSON for storage
json_data = json.dumps(result.to_dict(), indent=2)

# Save to file
with open("crawl_results.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2)

# Load from file
with open("crawl_results.json") as f:
    data = json.load(f)

from dash_penetration.crawler import CrawlResult
restored_result = CrawlResult.from_dict(data)
```

### Progress Monitoring

#### Real-time Progress

```python
async with CrawlEngine(target_url, scope) as engine:
    # Get progress at any time
    progress = engine.get_progress()
    
    print(f"Pages crawled: {progress['pages_crawled']}")
    print(f"Unique endpoints: {progress['unique_endpoints']}")
    print(f"Queue size: {progress['queue_size']}")
    print(f"Currently processing: {progress['processing']}")
    print(f"Errors: {progress['errors']}")
```

#### Progress During Crawl

```python
import asyncio

async def monitor_progress(engine):
    """Monitor crawl progress in background."""
    while True:
        progress = engine.get_progress()
        if progress['queue_size'] == 0 and progress['processing'] == 0:
            break
        
        print(f"Progress: {progress['pages_crawled']} pages, "
              f"{progress['unique_endpoints']} endpoints, "
              f"Q:{progress['queue_size']} W:{progress['processing']}")
        
        await asyncio.sleep(1)

async def crawl_with_monitoring(target_url, scope):
    async with CrawlEngine(target_url, scope) as engine:
        # Run monitor and crawl concurrently
        crawl_task = asyncio.create_task(engine.crawl())
        monitor_task = asyncio.create_task(monitor_progress(engine))
        
        result = await crawl_task
        await monitor_task
        
        return result
```

### Error Handling

#### Handling Crawl Errors

```python
async with CrawlEngine(target_url, scope) as engine:
    try:
        result = await engine.crawl()
    except ValueError as e:
        # Target URL out of scope
        print(f"Scope error: {e}")
    except Exception as e:
        # Network or unexpected errors
        print(f"Crawl error: {e}")

# Check errors after crawl
print(f"Crawl errors ({len(result.errors)}):")
for error in result.errors:
    print(f"  - {error}")
```

#### Timeout and Network Issues

```python
# Increase timeout for slow targets
async with CrawlEngine(
    target_url="https://slow-api.example.com",
    scope=scope,
    timeout=30.0  # 30 second timeout
) as engine:
    result = await engine.crawl()
```

---

## Advanced Features

### Rate Limiting Strategies

#### Conservative Rate Limiting

For stealth or to avoid overloading a server:

```python
# 1 request per second
async with CrawlEngine(
    target_url, scope,
    rate_limit=1.0,
    max_concurrency=1
) as engine:
    result = await engine.crawl()
```

#### Aggressive Rate Limiting

For fast crawling of well-provisioned APIs:

```python
# 50 requests per second, 10 parallel
async with CrawlEngine(
    target_url, scope,
    rate_limit=50.0,
    max_concurrency=10
) as engine:
    result = await engine.crawl()
```

#### Balanced Configuration

Default recommended settings:

```python
# 10 requests per second, 5 parallel
async with CrawlEngine(
    target_url, scope,
    rate_limit=10.0,
    max_concurrency=5
) as engine:
    result = await engine.crawl()
```

### Discovery Plugin Integration

The engine automatically runs all discovery plugins:

#### Links Discovery

```python
# Internal links are automatically added to queue
# External links are tracked but not crawled

endpoint = result.endpoints[key]
print(f"Links found: {endpoint.links}")  # List of discovered links
```

#### Form Discovery

```python
# Form actions are automatically added to queue

endpoint = result.endpoints[key]
for form in endpoint.forms:
    print(f"Form: {form.action}")
    print(f"Method: {form.method}")
    for field in form.fields:
        print(f"  {field.name}: {field.field_type}")
```

#### Script Discovery

```python
# Scripts are tracked but not crawled as pages

endpoint = result.endpoints[key]
print(f"Scripts: {endpoint.scripts}")  # List of script URLs
```

#### API Detection

```python
# API endpoints are automatically marked

endpoint = result.endpoints[key]
if endpoint.is_api:
    print(f"API endpoint detected: {endpoint.path}")
```

---

## API Reference

### `CrawlEngine` Class

#### Constructor

```python
CrawlEngine(
    target_url: str,
    scope: Scope,
    rate_limit: float = 10.0,
    max_concurrency: int = 5,
    timeout: float = 10.0,
    verify_ssl: bool = True
)
```

#### Async Methods

##### `async crawl() -> CrawlResult`

Execute the complete crawl workflow.

```python
async with CrawlEngine(target_url, scope) as engine:
    result = await engine.crawl()
```

**Returns:** CrawlResult with all discovered endpoints

**Raises:**
- `ValueError`: If target_url is out of scope
- `RuntimeError`: If not used as async context manager
- `HTTPError`: On network errors

##### `get_progress() -> dict`

Get current crawl progress.

```python
progress = engine.get_progress()
# Returns:
# {
#     "pages_crawled": 42,
#     "unique_endpoints": 38,
#     "queue_size": 15,
#     "processing": 3,
#     "errors": 0
# }
```

#### Context Manager

```python
async with CrawlEngine(target_url, scope) as engine:
    result = await engine.crawl()
# Automatically closes HTTP client
```

### `RateLimiter` Class

#### Constructor

```python
RateLimiter(rate: float)
```

**Parameters:**
- `rate`: Requests per second

#### Async Methods

##### `async acquire()`

Acquire a token (waits if necessary).

```python
rate_limiter = RateLimiter(rate=10.0)
await rate_limiter.acquire()  # Wait until rate allows
# Proceed with request
```

---

## Real-World Examples

### Example 1: Basic E-commerce Site Crawl

```python
import asyncio
from dash_penetration.crawler import CrawlEngine, Scope

async def crawl_ecommerce():
    scope = Scope(allowed_domains=["shop.example.com"])
    
    async with CrawlEngine(
        target_url="https://shop.example.com",
        scope=scope
    ) as engine:
        result = await engine.crawl()
    
    print(f"\nCrawl Results for {result.target_url}")
    print(f"Pages crawled: {result.pages_crawled}")
    print(f"Endpoints discovered: {len(result.endpoints)}")
    
    # Analyze results
    for endpoint in result.get_endpoint_summary():
        if endpoint['forms_count'] > 0:
            print(f"  {endpoint['method']} {endpoint['path']} → "
                  f"Forms: {endpoint['forms_count']}")

asyncio.run(crawl_ecommerce())
```

### Example 2: Multi-API System

```python
async def crawl_api_system():
    scope = Scope(
        allowed_domains=[
            "api.example.com",
            "v2.api.example.com",
            "auth.example.com"
        ],
        allowed_paths=["/api", "/v2", "/auth"],
        disallowed_paths=["/admin", "/internal", "/debug"]
    )
    
    async with CrawlEngine(
        target_url="https://api.example.com",
        scope=scope,
        rate_limit=20.0,      # Higher rate for API
        max_concurrency=8,
        timeout=15.0
    ) as engine:
        result = await engine.crawl()
    
    # Filter API endpoints
    api_endpoints = [
        ep for ep in result.get_endpoint_summary()
        if ep.get('is_api')
    ]
    
    print(f"API Endpoints discovered: {len(api_endpoints)}")
    for ep in api_endpoints:
        print(f"  {ep['method']} {ep['path']}")

asyncio.run(crawl_api_system())
```

### Example 3: Stealth Crawling

```python
async def stealth_crawl():
    """Slow, discrete crawling to avoid detection."""
    scope = Scope(allowed_domains=["example.com"])
    
    async with CrawlEngine(
        target_url="https://example.com",
        scope=scope,
        rate_limit=0.5,       # 1 request every 2 seconds
        max_concurrency=1,    # Sequential requests
        timeout=20.0          # Allow slow responses
    ) as engine:
        result = await engine.crawl()
    
    return result

asyncio.run(stealth_crawl())
```

### Example 4: Progressive Results Display

```python
import asyncio
from dash_penetration.crawler import CrawlEngine, Scope

async def crawl_with_progress(target_url, scope):
    async with CrawlEngine(target_url, scope) as engine:
        # Start crawl
        crawl_task = asyncio.create_task(engine.crawl())
        
        # Monitor progress
        while not crawl_task.done():
            progress = engine.get_progress()
            print(f"\r Pages: {progress['pages_crawled']:3d} | "
                  f"Endpoints: {progress['unique_endpoints']:3d} | "
                  f"Queue: {progress['queue_size']:3d} | "
                  f"Working: {progress['processing']:2d}",
                  end="", flush=True)
            
            await asyncio.sleep(0.5)
        
        result = await crawl_task
        print()  # Newline after progress
        
        return result

# Run with progress display
result = asyncio.run(crawl_with_progress(
    "https://example.com",
    Scope(allowed_domains=["example.com"])
))

print(f"\nFinal: {result.pages_crawled} pages, {len(result.endpoints)} endpoints")
```

### Example 5: Resilient Crawling with Retries

```python
import asyncio
from dash_penetration.crawler import CrawlEngine, Scope

async def resilient_crawl(target_url, scope, max_retries=3):
    """Crawl with retry logic."""
    for attempt in range(max_retries):
        try:
            async with CrawlEngine(target_url, scope) as engine:
                result = await engine.crawl()
                print(f"Crawl succeeded on attempt {attempt + 1}")
                return result
        
        except Exception as e:
            print(f"Crawl attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                print("All retries exhausted")
                raise

result = asyncio.run(resilient_crawl(
    "https://example.com",
    Scope(allowed_domains=["example.com"]),
    max_retries=3
))
```

---

## Testing

Run engine integration tests:

```bash
uv run pytest tests/test_engine.py -v
```

**Test Summary:**
- ✅ 14 comprehensive integration tests
- ✅ Engine initialization
- ✅ Rate limiter functionality
- ✅ URL queue management
- ✅ Concurrency control
- ✅ Rate limiting enforcement
- ✅ Scope validation during discovery
- ✅ Progress tracking
- ✅ Error handling

Run full test suite:

```bash
uv run pytest tests/ -v
# All 282 tests pass
```

---

## Performance Considerations

### Tuning for Speed

```python
# Fast crawling: high concurrency, high rate limit
async with CrawlEngine(
    target_url, scope,
    rate_limit=100.0,      # 100 req/s
    max_concurrency=20     # 20 parallel
) as engine:
    result = await engine.crawl()
```

### Tuning for Stealth

```python
# Stealth crawling: low concurrency, low rate limit
async with CrawlEngine(
    target_url, scope,
    rate_limit=0.5,        # 1 req every 2 seconds
    max_concurrency=1      # Sequential
) as engine:
    result = await engine.crawl()
```

### Memory Efficiency

For very large sites, consider:
- Processing results incrementally (not all at once)
- Clearing intermediate caches periodically
- Using lower concurrency to reduce memory usage

---

## Troubleshooting

### Crawl Hangs or Times Out

```python
# Increase timeout for slow targets
async with CrawlEngine(
    target_url, scope,
    timeout=30.0  # 30 second timeout
) as engine:
    result = await engine.crawl()
```

### Too Many Requests / Rate Limited

```python
# Reduce rate limit
async with CrawlEngine(
    target_url, scope,
    rate_limit=5.0,        # 5 req/s instead of 10
    max_concurrency=3      # 3 parallel instead of 5
) as engine:
    result = await engine.crawl()
```

### SSL Certificate Errors

```python
# Disable SSL verification (for testing only!)
async with CrawlEngine(
    target_url, scope,
    verify_ssl=False
) as engine:
    result = await engine.crawl()
```

### Out of Memory

```python
# Use lower concurrency and rate limit
async with CrawlEngine(
    target_url, scope,
    rate_limit=5.0,
    max_concurrency=2
) as engine:
    result = await engine.crawl()
```

---

## Next Steps

**Step 9: Main Crawler Engine** is complete with:
- ✅ Full crawl orchestration
- ✅ Concurrency and rate limiting
- ✅ Discovery plugin integration
- ✅ Result tracking and serialization
- ✅ 14 comprehensive integration tests
- ✅ Production-ready code

**Next phase:**

**Step 10: CLI & End-to-End Integration**
- Build Click CLI for user-facing crawling
- Add command options for concurrency, rate limit, scope
- Implement result output and caching
- Create user guide and examples

---

## Dependencies

Crawler Engine depends on:
- `httpx` — Async HTTP client
- `selectolax` — HTML parsing
- `asyncio` — Built-in Python concurrency
- Previously completed modules:
  - `crawler.urls` — URL normalization
  - `crawler.scope` — Scope validation
  - `crawler.http` — HTTP client
  - `crawler.parser` — HTML parser
  - `crawler.models` — Data structures
  - `discovery.*` — Discovery plugins

**No additional external dependencies required.**

---

## Architecture Overview

```
crawler/
├── urls.py (Step 3) ────────┐
│                             │
├── scope.py (Step 4) ────────┤
│                             │
├── http.py (Step 5) ─────────┤
│                             ├──→ engine.py (Step 9) ✅
├── parser.py (Step 6) ───────┤
│                             │
├── models.py (Step 2) ───────┤
│                             │
└── engine.py (Step 9) ◄──────┘

discovery/ (Step 7)
├── links.py
├── forms.py
├── scripts.py
└── api.py
         ↓
    Used by engine.py

output/ (Step 8)
├── console.py
└── json.py
         ↓
    Used in CLI (Step 10)

cli.py (Step 10)
     ↓
Wrapper around engine.py
```

---

## Summary

✅ **Step 9: Main Crawler Engine** is complete with:
- Complete crawl orchestration with queue management
- Configurable concurrency and rate limiting
- Full discovery plugin integration
- Comprehensive result tracking and serialization
- 14 integration tests (all passing)
- Production-ready error handling and logging
- Zero additional external dependencies

**Ready for Step 10: CLI & End-to-End Integration**
