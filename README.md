# Web Pentesting Learning Path

The goal is to learn the workflow step by step rather than relying
immediately on automated scanners.

## 1. Python crawler — start here

Build a crawler for my own/authorized website.

Recommended stack:

- `httpx` — HTTP requests and async crawling
- `selectolax` — fast HTML parsing
- `asyncio` — concurrency
- URL normalization + deduplication
- scope checking — stay within the target domain
- rate limiting — don't overload the server
- add a feature to crawl once, save results, only crawl again if asked 
- use UV as Python package manager

The crawler should initially:

- crawl pages starting from the target URL
- extract links from HTML
- follow redirects
- identify forms
- collect query parameters
- record HTTP status codes
- record content types
- discover referenced resources such as JavaScript files
- produce a structured endpoint inventory

Example output:

    GET  /                    200  text/html
    GET  /login               200  text/html
    GET  /products            200  text/html
    GET  /products/123        200  text/html
    POST /login               200  application/json
    GET  /api/products        200  application/json

Keep the first version simple. Get reliable crawling and URL
discovery working before adding JavaScript/browser automation.

Something like:

```
crawler/
│
├── main.py                  # Entry point / CLI
│
├── crawler/
│   ├── __init__.py
│   ├── engine.py            # Main crawl loop / queue
│   ├── http.py              # HTTP client, redirects, timeouts
│   ├── parser.py            # HTML parsing with selectolax
│   ├── urls.py              # URL normalization + deduplication
│   ├── scope.py             # Target/scope validation
│   └── models.py            # Page / endpoint data structures
│
├── discovery/
│   ├── __init__.py
│   ├── links.py             # Extract links from HTML
│   ├── forms.py             # Extract forms + parameters
│   ├── scripts.py           # Discover JavaScript resources
│   └── api.py               # Identify API endpoints
│
├── output/
│   ├── __init__.py
│   ├── console.py           # Human-readable output
│   └── json.py              # Save structured results
│
├── tests/
│   ├── test_urls.py
│   ├── test_scope.py
│   └── test_parser.py
│
├── requirements.txt
├── README.md
└── .gitignore
```


## Later

## 2. Burp Suite — later

Once the crawler works, learn HTTP traffic interactively with
Burp Suite.

Focus on:

- requests and responses
- headers
- cookies
- sessions
- authentication
- parameters
- redirects
- repeater/manual request modification
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
