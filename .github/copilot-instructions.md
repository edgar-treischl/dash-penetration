# Copilot Instructions for dash-penetration

## Project Overview

This is a **vulnerability scanner test repository** for penetration testing of the author's own Dash web application. The goal is to identify security weak spots and vulnerabilities in a controlled, authorized environment.

**Primary target:** https://edgar-treischl.pages.gitlab.lrz.de/dash-demo/ (React/Dash SPA)

**Current focus:** Automated vulnerability scanning with JavaScript rendering capabilities to find:
- Cross-Site Scripting (XSS) vulnerabilities
- SQL Injection vulnerabilities
- Missing security headers
- CSRF weaknesses
- Authentication issues
- Information disclosure
- Exposed APIs and sensitive endpoints

## Build, Test, and Lint Commands

**Quick start commands:**

- **Scan your app:** `make scan URL=https://your-app.com`
- **Demo scan:** `make demo` (scans the test Dash app)
- **Run tests:** `make test` or `uv run pytest tests/ -v --tb=short`
- **Generate report:** `make report` (creates HTML from latest scan)
- **Format code:** `make format` or `uv run black .`
- **Check formatting:** `uv run black --check .`

**Test commands:**
- `uv run pytest` — Run all tests
- `uv run pytest tests/test_<module>.py` — Run specific test file
- `uv run pytest -v --tb=short` — Verbose with short tracebacks

## High-Level Architecture

### Core Components

The scanner is designed as a modular vulnerability detection system:

**Main Entry Point:**
- **`pentest_scanner.py`** — Orchestrates 3-phase scanning: (1) JavaScript rendering & discovery, (2) Vulnerability scanning, (3) Report generation

**Crawler Foundation:**
- **`dash_penetration/crawler/http.py`** — Async HTTP client with error handling, rate limiting, retries
- **`dash_penetration/crawler/parser.py`** — Fast HTML parsing using `selectolax`
- **`dash_penetration/crawler/scope.py`** — Scope validation for authorized targets only

**Discovery Modules:**
- **`dash_penetration/discovery/links.py`** — Extract links from HTML
- **`dash_penetration/discovery/forms.py`** — Extract forms and identify input parameters

**Vulnerability Scanners:**
- **`dash_penetration/scanner/sql_injection.py`** — SQL injection detection (error-based, boolean-based, time-based)
- **`dash_penetration/scanner/xss.py`** — XSS detection (reflected, encoded, DOM-based)
- **`dash_penetration/scanner/csrf.py`** — CSRF token validation and unsafe method detection
- **`dash_penetration/scanner/headers.py`** — Security headers scanning (CSP, X-Frame-Options, HSTS, etc.)
- **`dash_penetration/scanner/auth.py`** — Authentication weaknesses (weak credentials, username enumeration)
- **`dash_penetration/scanner/info_disclosure.py`** — Information disclosure (exposed files, APIs, sensitive patterns)

**JavaScript Rendering:**
- **`js_crawler.py`** — Playwright-based crawler for React/Vue/Angular SPAs
- Clicks interactive elements to reveal hidden forms
- Monitors network requests to discover API endpoints

**Reporting:**
- **`generate_report.py`** — Converts JSON scan results to self-contained Quarto HTML reports
- Includes XSS-safe HTML escaping for payloads
- Embeds all CSS/JS for portable single-file reports

### Key Dependencies

- **`httpx`** — Async HTTP client for concurrent vulnerability testing
- **`selectolax`** — Fast HTML parsing (faster than BeautifulSoup)
- **`playwright`** — Browser automation for JavaScript-rendered SPAs
- **`asyncio`** — Built-in Python concurrency
- **`uv`** — Fast Python package manager
- **`quarto`** — Document rendering for HTML reports
- **`pytest`** — Testing framework

### Vulnerability Detection Approach

Unlike traditional automated scanners that just run predefined checks, this scanner:

1. **JavaScript rendering first** — Uses Playwright to discover hidden content in React/Vue/Angular apps
2. **Form parameter extraction** — Identifies all input fields, including those revealed by clicking buttons
3. **Targeted testing** — Tests each parameter with specific payloads for each vulnerability type
4. **Evidence-based reporting** — Only flags vulnerabilities with clear evidence (not just guesses)
5. **Confidence scoring** — Each finding includes a confidence score (0-100)

## Key Conventions and Patterns

### Vulnerability Scanning

- **Always test on authorized targets only** — This scanner is for testing YOUR OWN applications
- **SPA detection** — Automatically detects React/Vue/Angular apps and uses JavaScript rendering
- **Rate limiting** — Implements delays between requests to avoid DoS
- **Scope validation** — Every URL is validated against allowed domains before testing
- **Evidence collection** — Each vulnerability includes the payload, parameter, and response evidence

### Scanner Architecture

- **Independent scanners** — Each vulnerability type has its own scanner class
- **Async-compatible** — All scanners support `async`/`await` for concurrent testing
- **Context managers** — Scanners use `async with` for proper resource cleanup
- **Standardized results** — All scanners return `ScanResult` objects with:
  - `vulnerability_type` — Human-readable name
  - `severity` — CRITICAL, HIGH, MEDIUM, LOW, INFO
  - `url` — Where the vulnerability was found
  - `description` — What the issue is
  - `evidence` — Proof of the vulnerability
  - `remediation` — How to fix it
  - `cwe_id` — CWE database reference
  - `confidence` — 0-100 score

### False Positive Prevention

The scanners implement several strategies to avoid false positives:

1. **SPA detection** — Skip testing authentication on React/Vue/Angular apps (auth happens client-side)
2. **Positive indicators** — Look for success indicators (e.g., "welcome", "dashboard") not just absence of errors
3. **Response comparison** — Compare responses to detect actual differences vs. false positives
4. **Pattern matching** — Use specific error patterns (e.g., SQL error messages) not generic keywords
5. **Confidence scoring** — Lower confidence for ambiguous findings

## Code Organization

- **Modular design** — Each scanner has a single responsibility
- **Async-first** — All I/O-bound code uses `async/await`
- **Type hints** — Use Python type hints for clarity
- **Dataclasses** — Use dataclasses for `ScanResult` and form structures
- **Context managers** — Scanners implement `async with` for resource management

## Testing Strategy

- **Unit tests** for HTTP client, HTML parser, and scope validation (115 tests passing)
- **Mock HTTP responses** — Never test against real servers in unit tests
- **Real-world testing** — Use the demo target (dash-demo app) for integration testing
- **Evidence validation** — Verify that reported vulnerabilities are real (manual verification)

## Typical Workflow

1. **Scan an app:** `make scan URL=https://your-app.com`
2. **Review JSON results:** `cat pentest_report_*.json`
3. **Generate HTML report:** `make report`
4. **Open report in browser:** `open pentest_report_*.html`
5. **Fix vulnerabilities** in your app
6. **Re-scan** to verify fixes

## Important Security Notes

- ⚠️ **Authorization required** — Only scan applications you own or have permission to test
- ⚠️ **Not for production use** — This is a learning/testing tool, not a production security scanner
- ⚠️ **Rate limiting** — The scanner implements delays to avoid DoS, but still be careful
- ⚠️ **Scope control** — Always validate that scopes are correctly configured before scanning

## Known Limitations

1. **SPA authentication** — Cannot test authentication on React/Vue/Angular apps where auth happens entirely client-side
2. **Time-based SQL injection** — Currently placeholder implementation (no real delay testing)
3. **CAPTCHA/bot protection** — Scanner will be blocked by CAPTCHA or bot detection
4. **Complex workflows** — Cannot handle multi-step workflows requiring specific sequences
5. **Rate limiting detection** — May get rate-limited on heavily protected sites

## Future Enhancements

Planned improvements documented in `plan.md`:

- **Phase 4:** SSRF vulnerability detection
- **Phase 5:** File upload vulnerabilities
- **Phase 6:** XXE (XML External Entity) detection
- **Phase 7:** Advanced time-based blind injection testing
- **Phase 8:** Directory traversal detection
- **Phase 9:** CI/CD integration for continuous security testing
