# dash-penetration 🔐

**Automated web application security scanner for authorized penetration testing**

A Python-based vulnerability scanner that combines JavaScript rendering with comprehensive security testing. Built for security learning and authorized testing of your own web applications.

Next to do:
1. API Endpoint Fuzzing (40 mins) - Discover more endpoints, find unauth access
2. Rate Limiting Detection (30 mins) - Protect against brute force

## 🎯 What It Does

This tool performs **automated penetration testing** by:

1. **JavaScript Rendering** — Uses Playwright to discover content in modern web apps (React, Vue, Angular)
2. **Interactive Discovery** — Clicks buttons and triggers interactions to find hidden forms/APIs
3. **Vulnerability Scanning** — Tests for 6 categories of security vulnerabilities
4. **Professional Reporting** — Generates detailed JSON reports with CWE IDs, severity ratings, and remediation guidance

## 🚀 Quick Start

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run penetration test
uv run python pentest_scanner.py https://your-app.com

# Output: Console report + JSON file
```

## 📊 Vulnerability Detection

The scanner tests for:

### 1. **SQL Injection**
- Error-based detection (database errors in responses)
- Boolean-based blind injection
- Time-based blind injection
- Tests all form parameters

### 2. **Cross-Site Scripting (XSS)**
- Reflected XSS (input mirrored in response)
- Encoded payload bypass attempts
- DOM-based XSS (static JavaScript analysis)
- Tests username, password, and text fields

### 3. **CSRF (Cross-Site Request Forgery)**
- Missing CSRF tokens in forms
- Unsafe GET methods for state-changing operations
- Form submission security validation

### 4. **Authentication Vulnerabilities**
- Weak/default credentials testing (admin/admin, etc.)
- Username enumeration detection
- Login form security analysis

### 5. **Security Headers**
- Missing Content-Security-Policy (XSS protection)
- Missing X-Frame-Options (clickjacking protection)
- Missing HSTS (Strict-Transport-Security)
- Missing X-Content-Type-Options
- Missing Referrer-Policy
- Missing Permissions-Policy

### 6. **Information Disclosure**
- Exposed sensitive files (.git, .env, config files)
- Exposed API documentation (Swagger/OpenAPI)
- Sensitive patterns in responses (API keys, passwords)
- Directory listing vulnerabilities

## 🏗️ Architecture

```
dash-penetration/
│
├── pentest_scanner.py           # Main integrated scanner (entry point)
├── js_crawler.py                # JavaScript-enabled discovery with Playwright
│
├── dash_penetration/
│   ├── scanner/                 # Vulnerability scanner modules
│   │   ├── scanner.py           # Core scanner orchestration
│   │   ├── sql_injection.py     # SQL injection detection
│   │   ├── xss.py               # XSS detection
│   │   ├── csrf.py              # CSRF detection
│   │   ├── auth.py              # Authentication testing
│   │   ├── headers.py           # Security headers analysis
│   │   └── info_disclosure.py   # Information disclosure detection
│   │
│   ├── crawler/                 # HTTP utilities
│   │   ├── http.py              # Async HTTP client
│   │   ├── parser.py            # HTML parsing with selectolax
│   │   └── scope.py             # Scope validation
│   │
│   └── discovery/               # Content discovery
│       ├── links.py             # Link extraction
│       └── forms.py             # Form extraction
│
└── tests/                       # Test suite
```

## 📋 Example Output

```
🔐 AUTOMATED PENETRATION TEST
Target: https://example.com

🌐 Phase 1: JavaScript Rendering & Discovery
✓ Found 2 forms (login + contact)
✓ Found 15 links
✓ Discovered backend API endpoint

🔍 Phase 2: Vulnerability Scanning
[1/6] Security headers... 6 issues
[2/6] Information disclosure... 1 issue
[3/6] SQL injection... 0 issues
[4/6] XSS... 4 issues
[5/6] CSRF... 0 issues
[6/6] Authentication... 1 issue

📊 SCAN COMPLETE
Total Vulnerabilities: 12
  🔴 Critical: 1
  🟠 High:     5
  🟡 Medium:   2
  🟢 Low:      3
  ℹ️  Info:     1

📄 Full report saved to: pentest_report_20260831_172000.json
```

## 🔧 Tech Stack

- **Python 3.12+** with UV package manager
- **httpx** — Async HTTP client
- **selectolax** — Fast HTML parsing
- **playwright** — JavaScript rendering and browser automation
- **asyncio** — Concurrent vulnerability testing

## ⚠️ Security & Ethics

**IMPORTANT:** This tool is for **authorized security testing only**.

✅ **Authorized Use:**
- Testing your own applications
- Testing with explicit written permission
- Educational/learning purposes on authorized targets

❌ **Unauthorized Use:**
- Scanning websites without permission is **illegal**
- Unauthorized penetration testing can result in criminal charges
- Always get written authorization before testing

## 📝 License

MIT License - For educational and authorized security testing only.

## 🤝 Contributing

This is a learning project. Contributions welcome for:
- New vulnerability detection modules
- Improved detection accuracy
- False positive reduction
- Performance optimizations
- understanding how the application behaves

The goal is to understand what the crawler is seeing at the HTTP
level and learn how to investigate individual endpoints.

## 3. ffuf — content discovery

After understanding normal crawling, learn the distinction between:

    Crawling:
    "What can I discover by following what the application exposes?"

    Content discovery:
    "What potentially exists even though the application doesn't
     link to it?"

Use ffuf against your authorized target to investigate things such
as undocumented routes, directories, and application artifacts.

Keep discovery scoped and rate-limited.

## 4. OWASP ZAP — automation

Finally, learn OWASP ZAP as an automated web-security testing tool.

Compare its results with your own inventory:

    Python crawler
          ↓
    known attack surface
          ↓
    Burp Suite
          ↓
    understand/test individual requests
          ↓
    ffuf
          ↓
    discover potentially hidden content
          ↓
    ZAP
          ↓
    automated security analysis

## Overall learning progression

    1. Python crawler
           ↓
    2. Understand HTTP with Burp Suite
           ↓
    3. Discover unknown content with ffuf
           ↓
    4. Automate/validate with OWASP ZAP

The important principle:

    First understand the application.
    Then map its attack surface.
    Then investigate individual endpoints.
    Then automate.

Start with the Python crawler; everything else can build on the
endpoint inventory it produces.
