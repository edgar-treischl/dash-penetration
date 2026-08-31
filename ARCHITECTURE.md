# Architecture Overview

## Project Purpose

**dash-penetration** is an automated web application security scanner for authorized penetration testing. It combines JavaScript rendering with comprehensive vulnerability detection to test modern web applications.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    pentest_scanner.py                        │
│              Main Orchestrator & Entry Point                 │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌───────────────────┐              ┌──────────────────────┐
│  Phase 1: Discover│              │  Phase 2: Scan       │
│  (JavaScript)     │              │  (Vulnerabilities)   │
└───────────────────┘              └──────────────────────┘
        │                                     │
        ▼                                     ▼
┌───────────────────┐              ┌──────────────────────┐
│  Playwright       │              │  6 Scanners          │
│  Browser          │              │  - SQL Injection     │
│  - Click buttons  │              │  - XSS               │
│  - Wait for JS    │              │  - CSRF              │
│  - Extract forms  │              │  - Auth              │
└───────────────────┘              │  - Headers           │
        │                          │  - Info Disclosure   │
        ▼                          └──────────────────────┘
┌───────────────────┐                       │
│  Parser & Extractor│                      ▼
│  - Links          │              ┌──────────────────────┐
│  - Forms          │              │  Report Generator    │
│  - Scripts        │              │  - JSON export       │
└───────────────────┘              │  - Console output    │
                                   └──────────────────────┘
```

---

## Module Breakdown

### 1. **Main Scanner** (`pentest_scanner.py`)

**Purpose:** Orchestrate the entire penetration test workflow.

**Responsibilities:**
- Phase 1: JavaScript rendering and discovery
- Phase 2: Run all 6 vulnerability scanners
- Phase 3: Generate reports (console + JSON)

**Entry Point:**
```bash
uv run python pentest_scanner.py https://target.com
```

---

### 2. **JavaScript Discovery** (`js_crawler.py`)

**Purpose:** Discover attack surface in modern JavaScript-rendered apps.

**Key Features:**
- Uses Playwright to render React/Vue/Angular apps
- Clicks interactive elements (buttons, tabs) to reveal hidden content
- Extracts forms, links, scripts
- Monitors network requests to discover API endpoints

**Dependencies:**
- `playwright` — Browser automation
- `dash_penetration.crawler.parser` — HTML parsing
- `dash_penetration.discovery.forms` — Form extraction
- `dash_penetration.discovery.links` — Link extraction

---

### 3. **Vulnerability Scanner Module** (`dash_penetration/scanner/`)

**Purpose:** Detect exploitable vulnerabilities with high confidence.

#### Core Scanner (`scanner.py`)
- `ScanResult` dataclass: Stores vulnerability details
- `Severity` enum: CRITICAL > HIGH > MEDIUM > LOW > INFO
- `VulnerabilityScanner` class: Aggregates results and generates reports

#### SQL Injection Scanner (`sql_injection.py`)
- Error-based detection (database errors in responses)
- Boolean-based blind injection
- Time-based blind detection (placeholder)
- Tests all form parameters

#### XSS Scanner (`xss.py`)
- Reflected XSS (input mirrored in response)
- Encoded payload testing
- DOM-based XSS (static JavaScript analysis)
- Tests username, password, text fields

#### CSRF Scanner (`csrf.py`)
- Missing CSRF token detection
- Unsafe GET method detection
- Form submission security validation

#### Authentication Scanner (`auth.py`)
- Weak/default credentials testing
- Username enumeration detection
- Login form analysis

#### Security Headers Scanner (`headers.py`)
- Missing Content-Security-Policy
- Missing X-Frame-Options
- Missing HSTS
- Complete HTTP security header audit

#### Information Disclosure Scanner (`info_disclosure.py`)
- Exposed .git/.env files
- Swagger/OpenAPI exposure
- Sensitive patterns in responses
- Directory listing vulnerabilities

---

### 4. **HTTP Client Module** (`dash_penetration/crawler/http.py`)

**Purpose:** Consistent async HTTP client with error handling.

**Key Features:**
- Async HTTP requests with `httpx`
- Timeout handling
- Redirect following
- SSL error handling
- Custom error types for different failure modes

---

### 5. **HTML Parser Module** (`dash_penetration/crawler/parser.py`)

**Purpose:** Fast HTML parsing and content extraction.

**Key Features:**
- Uses `selectolax` (faster than BeautifulSoup)
- Extracts links (relative → absolute resolution)
- Extracts forms (action, method, inputs)
- Extracts scripts (external + inline)
- Robust handling of malformed HTML

---

### 6. **Discovery Plugins** (`dash_penetration/discovery/`)

**Purpose:** Modular content extraction from HTML.

#### Links Discovery (`links.py`)
- Categorize internal vs external links
- Scope validation
- URL normalization

#### Forms Discovery (`forms.py`)
- Extract form endpoints
- Extract form fields (name, type, value)
- Identify hidden fields
- Identify password fields

---

### 7. **Scope Validation Module** (`dash_penetration/crawler/scope.py`)

**Purpose:** Ensure testing stays within authorized targets.

**Key Features:**
- Domain whitelisting
- Path inclusion/exclusion rules
- Subdomain handling
- Case-insensitive matching

---

## Data Flow

### Phase 1: Discovery

```
Target URL
    │
    ▼
Playwright Browser
    │
    ├─→ Wait for JavaScript rendering
    ├─→ Click interactive elements
    └─→ Monitor network requests
    │
    ▼
HTML Content
    │
    ▼
Parser (selectolax)
    │
    ├─→ Links
    ├─→ Forms (action, method, inputs)
    └─→ Scripts
```

### Phase 2: Vulnerability Scanning

```
Discovered Forms
    │
    ├─→ SQL Injection Scanner
    │       └─→ Test each parameter with payloads
    │
    ├─→ XSS Scanner
    │       └─→ Test reflected/encoded/DOM-based
    │
    ├─→ CSRF Scanner
    │       └─→ Check for CSRF tokens
    │
    ├─→ Auth Scanner
    │       └─→ Test weak credentials
    │
    ├─→ Headers Scanner
    │       └─→ Check security headers
    │
    └─→ Info Disclosure Scanner
            └─→ Check sensitive files/patterns
    │
    ▼
ScanResult[] (all findings)
```

### Phase 3: Reporting

```
ScanResult[]
    │
    ▼
VulnerabilityScanner.generate_report()
    │
    ├─→ Console output (color-coded severity)
    └─→ JSON export (pentest_report_*.json)
```

---

## Key Design Decisions

### 1. **JavaScript Rendering First**
- Modern apps don't expose content in static HTML
- Playwright enables discovery of hidden forms/APIs
- Button clicking reveals interactive content

### 2. **Async Architecture**
- All I/O operations are async (httpx, Playwright)
- Concurrent scanning of multiple parameters
- Faster scan completion

### 3. **Modular Scanner Design**
- Each scanner is independent
- Easy to add new vulnerability types
- Can enable/disable scanners individually

### 4. **High-Confidence Detection**
- Focus on reducing false positives
- Evidence-based findings
- Confidence scores for each result

### 5. **Severity-Based Reporting**
- Industry-standard severity levels (CRITICAL → INFO)
- CWE IDs for each vulnerability type
- Remediation guidance included

---

## Testing Strategy

### Unit Tests
- HTTP client error handling
- HTML parser extraction logic
- Scope validation rules

### Integration Tests
- Full scan workflow (discovery → scanning → reporting)
- JavaScript rendering with mocked pages
- Vulnerability detection accuracy

### Current Coverage
- 115 tests passing
- Core modules (HTTP, Parser, Scope) fully tested
- Scanner modules manually validated

---

## Dependencies

### Core
- **httpx** — Async HTTP client
- **selectolax** — Fast HTML parsing
- **playwright** — Browser automation for JavaScript rendering

### Development
- **pytest** — Testing framework
- **pytest-asyncio** — Async test support
- **black** — Code formatting
- **flake8** — Linting
- **uv** — Package management

---

## Security & Ethics

⚠️ **IMPORTANT:** This tool is for **authorized security testing only**.

**Authorized Use:**
- Testing your own applications
- Testing with explicit written permission
- Educational/learning purposes on authorized targets

**Unauthorized Use:**
- Scanning websites without permission is **illegal**
- Can result in criminal charges under CFAA (US) and similar laws
- Always get written authorization before testing

---

## Future Enhancements

### Short Term
- [ ] Time-based SQL injection (real implementation)
- [ ] SSRF detection
- [ ] File upload vulnerabilities
- [ ] HTML reports

### Medium Term
- [ ] API security testing (GraphQL, REST)
- [ ] JWT security analysis
- [ ] OAuth/OIDC testing
- [ ] Rate limiting & stealth mode

### Long Term
- [ ] Exploit verification (safe PoC generation)
- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Comparison with OWASP ZAP/Burp Suite
- [ ] Machine learning for false positive reduction

---

## Performance Characteristics

### Typical Scan Times
- Small app (1-5 pages): 10-30 seconds
- Medium app (5-20 pages): 30-90 seconds
- Large app (20+ pages): 2-5 minutes

### Resource Usage
- Memory: ~200-500 MB (Playwright browser)
- CPU: Moderate during scanning phase
- Network: Configurable rate limiting (default: reasonable)

### Scalability
- Concurrent HTTP requests
- Async vulnerability testing
- Can scan multiple forms in parallel

---

## References

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CWE Database**: https://cwe.mitre.org/
- **Playwright Docs**: https://playwright.dev/python/
- **httpx Docs**: https://www.python-httpx.org/
