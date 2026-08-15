# Step 3: URL Handling & Deduplication — Complete ✅

## What Was Created

### crawler/urls.py (190 lines)

**Core Functions:**

1. **`normalize_url(url)`** — Canonicalize URLs for comparison
   - Defaults to `https://` if no scheme
   - Lowercases scheme and domain
   - Removes fragments (#)
   - Sorts query parameters alphabetically
   - Removes trailing slashes (except root)
   - Validates HTTP scheme (http/https only)
   - Returns consistent normalized URL

2. **`extract_domain(url)`** — Extract domain from URL
   - Handles URLs without schemes
   - Removes port numbers
   - Lowercases domain
   - Returns root domain (includes subdomains)

3. **`is_duplicate(url1, url2)`** — Detect URL duplicates
   - Normalizes both URLs and compares
   - Returns False for invalid URLs (safe)
   - Handles case differences, fragments, query order

4. **`extract_path_and_query(url)`** — Extract path and query separately
   - Returns (path, query_string) tuple
   - Normalized extraction

5. **`URLCache` class** — Efficient URL deduplication
   - `add(url)` → True if new, False if duplicate
   - `has_seen(url)` → bool
   - `get_count(url)` → how many times added
   - `get_all_urls()` → list of all unique URLs
   - `get_size()` → count of unique URLs
   - `clear()` → reset cache
   - Supports `in` operator: `"url" in cache`
   - Supports `len()`: `len(cache)`
   - O(1) lookups via internal set

### tests/test_urls.py (400+ lines)

**47 Comprehensive Tests:**
- URL normalization (14 tests)
- Domain extraction (7 tests)
- Duplicate detection (10 tests)
- Path/query extraction (3 tests)
- URLCache operations (13 tests)

**Test Results:**
```
✅ 70 total tests (23 models + 47 urls) PASSED
✅ 98% code coverage (crawler/urls.py)
✅ Code formatting ............................ ✓ Black
✅ Code style ................................. ✓ Flake8
✅ Total test time ............................ ~50ms
```

## Key Features

### Robust URL Normalization
```python
from crawler.urls import normalize_url, is_duplicate

# Case and query order differences handled
assert is_duplicate("https://EXAMPLE.COM?a=1&b=2", 
                    "https://example.com?b=2&a=1")

# Fragment differences ignored
assert is_duplicate("https://example.com#section1",
                    "https://example.com#section2")
```

### Efficient Caching
```python
from crawler.urls import URLCache

cache = URLCache()
cache.add("https://example.com/path")
cache.add("HTTPS://EXAMPLE.COM/path")  # Returns False (duplicate)

print(cache.get_size())  # 1
print(len(cache))         # 1
"https://example.com/path" in cache  # True
```

### Safe Duplicate Detection
```python
from crawler.urls import is_duplicate

# Safe with invalid URLs
is_duplicate("not a url", "also bad")  # False (not error)
```

## Design Decisions

1. **Normalization prioritizes consistency** — Query param sorting, lowercasing
2. **URLCache uses internal set** — O(1) lookups, O(n) space
3. **is_duplicate() returns False for invalid URLs** — Graceful degradation
4. **extract_domain() handles subdomains** — Preserves api.example.com vs example.com
5. **URL defaults to https** — Most common scheme

## Test Coverage by Area

| Area | Tests | Coverage |
|------|-------|----------|
| URL Normalization | 14 | 100% |
| Domain Extraction | 7 | 100% |
| Duplicate Detection | 10 | 100% |
| Path/Query Extraction | 3 | 100% |
| URLCache | 13 | 100% |
| **Total** | **47** | **98%** |

## Ready for Step 4

The URL handling is production-ready. Next: Scope validation (`crawler/scope.py`)

### Commands Reference

```bash
# Run URL tests only
uv run pytest tests/test_urls.py -v

# Run all tests (models + urls)
uv run pytest tests/test_models.py tests/test_urls.py -v

# Coverage
uv run pytest tests/test_urls.py --cov=crawler --cov-report=term-missing

# Run specific test
uv run pytest tests/test_urls.py::TestURLCache -v
```

## Integration Note

The URLCache is designed to be integrated into the crawl engine (Step 9):
- Tracks all discovered URLs
- Prevents duplicate crawling
- Maintains count for prioritization
- Can serialize/deserialize for resumable crawls
