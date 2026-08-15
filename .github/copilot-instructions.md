# Copilot Instructions for dash-penetration

## Project Overview

This is a **web penetration testing learning project** focused on understanding attack surfaces step-by-step rather than relying on automated scanners. The project is structured as a learning progression with multiple phases, starting with a Python-based web crawler.

**Phase 1 (current focus):** Build a Python crawler for authorized website scanning.

## Build, Test, and Lint Commands

When Phase 1 development begins:

- **Install dependencies:** `uv pip install -r requirements.txt` (using UV as the package manager)
- **Run the crawler:** `python main.py --url <target_url> [--save] [--output format]`
- **Run tests:** `uv run pytest` or `uv run pytest tests/test_<module>.py` for individual test files
- **Lint:** `uv run black --check .` and `uv run flake8 .` (to be integrated)
- **Format code:** `uv run black .`

## High-Level Architecture

### Phase 1: Python Crawler (Active Development)

The crawler is designed as a modular system with clear separation of concerns:

- **`crawler/engine.py`** — Main crawl loop managing the queue, concurrency, and orchestration of discovery
- **`crawler/http.py`** — HTTP client handling redirects, timeouts, and response validation
- **`crawler/parser.py`** — HTML parsing using `selectolax` for fast extraction
- **`crawler/urls.py`** — URL normalization and deduplication (critical for preventing duplicates and scope creep)
- **`crawler/scope.py`** — Scope validation ensuring crawls stay within authorized targets
- **`crawler/models.py`** — Data structures for `Page` and `Endpoint` (for structured results)

- **`discovery/`** — Discovery plugins that run during/after crawling:
  - `links.py` — Extract HTML links
  - `forms.py` — Extract forms and identify parameters
  - `scripts.py` — Discover JavaScript resources
  - `api.py` — Identify API endpoints

- **`output/`** — Output formatters:
  - `console.py` — Human-readable terminal output
  - `json.py` — Structured JSON export

### Key Dependencies

- **`httpx`** — Async HTTP client for concurrent requests
- **`selectolax`** — Fast HTML parsing (faster than BeautifulSoup)
- **`asyncio`** — Built-in Python concurrency
- **`uv`** — Fast Python package manager and lock file manager

### Future Phases

Phases 2–4 (Burp Suite learning, ffuf content discovery, OWASP ZAP automation) are documented but not yet implemented. Each phase builds on the `Endpoint` inventory produced by Phase 1.

## Key Conventions and Patterns

### URL Handling

- **Normalize all URLs** before deduplication (scheme, domain case-folding, parameter ordering)
- **Track URL state** in the `Page` model (crawled, queued, failed)
- **Validate scope** for every discovered URL before adding to the queue

### HTTP Crawling

- Implement **rate limiting** to avoid overloading the target
- **Follow redirects** (up to a configurable limit, typically 5)
- **Respect timeouts** (default 10s, increase for slow targets)
- **Record HTTP status and content type** on all requests
- **Handle errors gracefully** — log failures, don't crash

### Output Structure

The crawler produces a structured **endpoint inventory** with:

```
METHOD  PATH                STATUS  CONTENT_TYPE
GET     /                   200     text/html
GET     /login              200     text/html
POST    /login              200     application/json
GET     /api/products       200     application/json
```

This inventory is the foundation for later analysis phases.

### Code Organization

- **Modular design** — Each module has a single responsibility (HTTP, parsing, scope, URLs, etc.)
- **Async-first** — All I/O-bound code uses `async/await`
- **Type hints** — Use Python type hints for clarity
- **Models** — Use dataclasses or Pydantic for `Page` and `Endpoint` structures
- **Configuration** — CLI arguments or `.env` file for target URL, scope rules, rate limits

### Testing Strategy

- **Unit tests** for URL normalization, scope validation, and parsing logic
- **Integration tests** for the crawl loop with mock HTTP responses
- **Avoid testing against real servers** — use fixtures or mocked responses

## First Steps

When starting Phase 1 implementation:

1. Set up the project structure as outlined in the README
2. Implement `crawler/urls.py` first (URL normalization and deduplication)
3. Implement `crawler/scope.py` (scope validation)
4. Build `crawler/http.py` (HTTP client with httpx)
5. Add `crawler/parser.py` (link extraction with selectolax)
6. Implement `discovery/` plugins (forms, scripts, API detection)
7. Build `crawler/engine.py` (main crawl orchestration)
8. Add output formatters and CLI in `main.py`
9. Write tests as you go

This order ensures the most critical and reusable components are solid before orchestration logic.

## Important Notes

- **Security** — This is an educational project for authorized testing only. Always get permission before crawling any target.
- **Scope control** — The scope validation logic is critical; incorrect scope can lead to crawling unintended targets.
- **Rate limiting** — Respect server resources and crawl at a reasonable rate (configurable).
- **Caching crawl results** — The README mentions saving and reusing crawl results; implement a simple JSON or SQLite cache.

## Integration with Future Phases

- Phase 2 (Burp Suite) builds on understanding endpoints from Phase 1
- Phase 3 (ffuf) uses the endpoint inventory to discover additional hidden routes
- Phase 4 (ZAP) validates and extends the inventory with automated security tests

Each phase should reference the `Endpoint` structure from Phase 1.
