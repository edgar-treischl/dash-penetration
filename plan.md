# Web Crawler Development Plan

## Overview

This plan breaks down the Python crawler development into logical, incrementally testable steps. Each step builds on previous work and can be validated independently before moving forward.

**Total estimated phases: 10 major steps**

---

## Phase 1: Project Setup & Foundational Infrastructure

### Step 1: Initialize project structure and dependencies
**Goal:** Set up the project, install core dependencies, and create the directory structure.

**Tasks:**
- Create `requirements.txt` with core dependencies:
  - `httpx` (async HTTP client)
  - `selectolax` (HTML parsing)
  - `pytest` (testing)
  - `black` (code formatting)
  - `flake8` (linting)
  - `python-dotenv` (environment config)
  - `click` (CLI framework)
- Create project directories: `crawler/`, `discovery/`, `output/`, `tests/`
- Create `__init__.py` files in each package
- Create `.gitignore`, `.env.example`
- Initialize `uv` lock file: `uv pip compile requirements.txt`
- Create empty `main.py` entry point

**Output:**
- Full project structure ready
- All dependencies installed and locked
- Verified imports work

**Validation:**
```bash
uv run python -c "import httpx, selectolax, pytest; print('All imports OK')"
```

---

## Phase 2: Data Models (Foundation Layer)

### Step 2: Define data structures
**Goal:** Create reusable models for Pages, Endpoints, and crawl results.

**Tasks:**
- Create `crawler/models.py` with:
  - `Page` dataclass: url, method, status_code, content_type, content, headers, timestamp, discovered_by
  - `Endpoint` dataclass: method, path, status_code, content_type, forms, links, scripts
  - `CrawlResult` dataclass: target_url, scope, endpoints (list), pages_crawled, start_time, end_time
- Add validation methods (e.g., validate status_code, validate method)
- Add serialization methods (to_dict, from_dict)
- Create `tests/test_models.py` with basic instantiation tests

**Output:**
- Type-safe models for the entire crawler
- Tests validating model creation and serialization

**Validation:**
```bash
uv run pytest tests/test_models.py -v
```

---

## Phase 3: URL Handling (Critical Foundation)

### Step 3: Implement URL normalization and deduplication
**Goal:** Ensure URLs are consistently normalized and duplicates are detected.

**Tasks:**
- Create `crawler/urls.py` with:
  - `normalize_url(url)` → canonicalized URL
    - Handle scheme (default to https)
    - Lowercase domain
    - Remove fragments
    - Sort query parameters
    - Decode/re-encode paths consistently
  - `extract_domain(url)` → root domain
  - `is_duplicate(url1, url2)` → bool
  - `URLCache` class to track seen URLs with deduplication set
- Write comprehensive unit tests in `tests/test_urls.py`:
  - Test various URL formats (query params, fragments, case variations)
  - Test duplicate detection
  - Test edge cases (encoded characters, paths with dots)

**Output:**
- Robust URL normalization preventing duplicates
- Fast lookups via set/cache
- Full test coverage

**Validation:**
```bash
uv run pytest tests/test_urls.py -v
```

---

## Phase 4: Scope Validation (Critical Foundation)

### Step 4: Implement scope checking
**Goal:** Ensure crawling stays within authorized targets.

**Tasks:**
- Create `crawler/scope.py` with:
  - `Scope` class to define target domains/paths
    - `allowed_domains` (list of base domains)
    - `allowed_paths` (optional path prefix whitelist)
    - `disallowed_paths` (exclude paths like /admin, /private)
  - `is_in_scope(url, scope)` → bool
  - `parse_scope_config(dict)` → Scope object
- Write tests in `tests/test_scope.py`:
  - Test domain validation
  - Test path inclusion/exclusion
  - Test subdomain handling
  - Test edge cases

**Output:**
- Scope validator preventing out-of-scope crawling
- Flexible configuration format
- Full test coverage

**Validation:**
```bash
uv run pytest tests/test_scope.py -v
```

---

## Phase 5: HTTP Client (Core I/O)

### Step 5: Build HTTP client wrapper
**Goal:** Wrap httpx for consistent error handling, timeouts, and redirects.

**Tasks:**
- Create `crawler/http.py` with:
  - `HTTPClient` class wrapping httpx.AsyncClient
  - Methods:
    - `fetch(url, method='GET', follow_redirects=True)` → response or error
    - `get_with_timeout(url, timeout=10)` → response
    - `close()` → cleanup
  - Error handling for:
    - Connection errors
    - Timeouts
    - Invalid SSL (for learning purposes)
    - Rate limiting (429 responses)
  - Response validation (status, content-type, content-length)
- Write tests in `tests/test_http.py` using mocked responses:
  - Test successful requests
  - Test redirect following
  - Test timeout handling
  - Test error responses

**Output:**
- Reliable, retry-aware HTTP client
- Consistent error handling
- Mocked tests (no real network calls)

**Validation:**
```bash
uv run pytest tests/test_http.py -v
```

---

## Phase 6: HTML Parsing (Discovery Foundation)

### Step 6: Implement HTML parser
**Goal:** Extract links, forms, and other relevant elements from HTML.

**Tasks:**
- Create `crawler/parser.py` with:
  - `HTMLParser` class using selectolax
  - Methods:
    - `extract_links(html)` → list of URLs
    - `extract_forms(html)` → list of form data (action, method, inputs)
    - `extract_scripts(html)` → list of script URLs/inline content
    - `extract_meta(html)` → meta tags (robots, etc.)
  - Handling:
    - Relative URL resolution to absolute URLs
    - Deduplication within page
    - Filtering invalid links
- Write tests in `tests/test_parser.py`:
  - Test with sample HTML fixtures
  - Test relative URL resolution
  - Test form extraction
  - Test edge cases (malformed HTML)

**Output:**
- Fast HTML parsing with selectolax
- Consistent extraction methods
- Full test coverage with fixtures

**Validation:**
```bash
uv run pytest tests/test_parser.py -v
```

---

## Phase 7: Discovery Plugins (Modular Discovery)

### Step 7: Implement discovery modules
**Goal:** Extract specific insights from crawled pages.

**Tasks:**
- Create `discovery/links.py`:
  - Extract and categorize internal vs external links
  - Return structured `LinkDiscovery` result
- Create `discovery/forms.py`:
  - Extract forms with fields, types, validation
  - Return structured `FormDiscovery` result
- Create `discovery/scripts.py`:
  - Extract .js resources and inline scripts
  - Return structured `ScriptDiscovery` result
- Create `discovery/api.py`:
  - Identify API endpoints (JSON responses, API paths like /api/*)
  - Return structured `APIDiscovery` result
- Create `discovery/__init__.py` exporting all discoverers
- Write tests in `tests/test_discovery.py` with HTML fixtures

**Output:**
- Modular discovery plugins
- Reusable on any parsed page
- Full test coverage

**Validation:**
```bash
uv run pytest tests/test_discovery.py -v
```

---

## Phase 8: Output Formatters (Export)

### Step 8: Implement output modules
**Goal:** Provide human-readable and structured outputs.

**Tasks:**
- Create `output/console.py`:
  - `ConsoleFormatter` class
  - Method: `format_endpoints(endpoints)` → formatted table
  - Method: `format_crawl_summary(result)` → summary stats
  - Uses colored output for readability (e.g., status codes: 200=green, 404=yellow, 500=red)
- Create `output/json.py`:
  - `JSONFormatter` class
  - Method: `format_endpoints(endpoints)` → JSON string
  - Method: `save_to_file(result, filename)` → write JSON
  - Method: `load_from_file(filename)` → read previous crawl
- Create tests in `tests/test_output.py`:
  - Test JSON serialization/deserialization
  - Test console formatting doesn't crash

**Output:**
- Multiple output formats
- Save/load crawl results for caching
- Full test coverage

**Validation:**
```bash
uv run pytest tests/test_output.py -v
```

---

## Phase 9: Main Crawler Engine (Orchestration)

### Step 9: Implement crawl engine
**Goal:** Orchestrate the entire crawl workflow with queue, concurrency, and discovery.

**Tasks:**
- Create `crawler/engine.py` with:
  - `CrawlEngine` class
  - Constructor: `__init__(target_url, scope, rate_limit=10/sec, max_concurrency=5)`
  - Methods:
    - `async crawl()` → CrawlResult
    - `async _process_queue()` → async queue worker
    - `async _handle_page(url)` → fetch + parse + discover
    - `_add_discovered_urls(urls)` → add to queue respecting scope
  - Rate limiter (token bucket or delay-based)
  - Concurrency control (semaphore or worker pool)
  - Comprehensive logging
- Write integration tests in `tests/test_engine.py` with mocked HTTP:
  - Test crawl start to finish
  - Test rate limiting (verify timing)
  - Test concurrency (verify parallel requests)
  - Test scope enforcement (verify out-of-scope URLs rejected)

**Output:**
- Complete, working crawler engine
- Configurable concurrency and rate limiting
- Integration tests with mocked responses

**Validation:**
```bash
uv run pytest tests/test_engine.py -v
```

---

## Phase 10: CLI & End-to-End Integration

### Step 10: Build CLI and main entry point
**Goal:** Create user-facing CLI with all options integrated.

**Tasks:**
- Create/update `main.py` with Click CLI:
  - Command: `crawl --url <target> --scope <domains> --output [console|json] --save [filename]`
  - Options:
    - `--url` (required): target URL
    - `--scope` (optional): comma-separated allowed domains
    - `--max-concurrency` (optional, default 5)
    - `--rate-limit` (optional, default 10 requests/sec)
    - `--timeout` (optional, default 10s)
    - `--output` (optional, default console)
    - `--save` (optional): save to JSON file for caching
    - `--load` (optional): load previous crawl results
    - `--verbose` (optional): debug logging
  - Error handling and user-friendly messages
- Create `tests/test_cli.py`:
  - Test CLI parsing
  - Test with mocked crawl engine
  - Test output options
- Create `README_USAGE.md`:
  - Example: `python main.py --url https://example.com --scope example.com`
  - Example: `python main.py --load previous_crawl.json --output console`

**Output:**
- Fully functional CLI
- End-to-end crawl capability
- Complete usage documentation

**Validation:**
```bash
uv run pytest tests/test_cli.py -v
uv run python main.py --help
uv run python main.py --url https://httpbin.org --scope httpbin.org --output console
```

---

## Phase 11: Documentation & Refinement (Optional)

### Step 11: Polish and document
**Goal:** Ensure code quality and comprehensive documentation.

**Tasks:**
- Add docstrings to all public methods
- Add type hints to all functions
- Run linting and formatting:
  - `uv run black .`
  - `uv run flake8 . --max-line-length=100`
- Add inline comments for complex logic
- Create `DEVELOPMENT.md` with:
  - Architecture overview
  - How to add new discovery plugins
  - How to extend output formatters
- Update main `README.md` with Phase 1 completion notes

**Validation:**
```bash
uv run black . --check
uv run flake8 . --max-line-length=100
uv run pytest (full suite)
```

---

## Summary: Development Order & Dependencies

```
Step 1: Setup
    ↓
Step 2: Models
    ↓
├─→ Step 3: URL Handling (independent)
├─→ Step 4: Scope Validation (independent)
│   ↓
│  Step 9: Engine (depends on 3, 4)
│   ↓
├─→ Step 5: HTTP Client (independent)
├─→ Step 6: Parser (independent)
├─→ Step 7: Discovery (independent)
└─→ Step 8: Output (independent)
    ↓
Step 10: CLI & Integration
    ↓
Step 11: Polish (optional)
```

**Parallel opportunities:**
- Steps 3–8 can be developed in parallel after Step 2
- Step 9 depends on 3, 4, 5, 6, 7 being complete
- Step 10 depends on 9 being complete

---

## Testing Strategy

**Throughout all steps:**
- Write tests first or alongside implementation
- Use pytest for all unit and integration tests
- Mock external HTTP calls (no real network requests in CI)
- Aim for >80% code coverage
- Run: `uv run pytest tests/ -v --cov=crawler --cov=discovery --cov=output`

---

## Checkpoint: Minimum Viable Crawler

After Step 9 (Engine), you have a **working crawler** that:
- ✅ Discovers URLs from a target
- ✅ Respects scope
- ✅ Rate-limits requests
- ✅ Extracts links, forms, scripts
- ✅ Produces structured endpoint inventory

This is the foundation for Phases 2–4 (Burp, ffuf, ZAP).

Step 10 adds the CLI polish; Step 11 is quality refinement.
