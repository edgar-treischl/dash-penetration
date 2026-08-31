# Step 8: Output Formatters

## Overview

Output formatters convert crawl results into human-readable and structured formats for analysis and persistence. The dash-penetration crawler provides two primary formatters:

- **ConsoleFormatter**: Colored terminal output with tables and summaries
- **JSONFormatter**: JSON serialization for saving/loading crawl results

## ConsoleFormatter

Displays crawl results beautifully in the terminal with colored output.

### Usage

```python
from dash_penetration.output.console import ConsoleFormatter
from dash_penetration.crawler.models import CrawlResult

# Format complete report (summary + endpoints table)
report = ConsoleFormatter.format_full_report(result)
print(report)

# Format just the endpoints table
table = ConsoleFormatter.format_endpoints(result.endpoints)
print(table)

# Format just the summary statistics
summary = ConsoleFormatter.format_crawl_summary(result)
print(summary)
```

### Features

- **Colored Status Codes**: 
  - 🟢 Green (2xx – Success)
  - 🔵 Blue (HTTP Methods)
  - 🟡 Yellow (4xx – Client Errors)
  - 🔴 Red (5xx – Server Errors)

- **Summary Statistics**:
  - Pages crawled
  - Unique endpoints discovered
  - HTTP status distribution
  - HTTP method breakdown
  - API endpoint count
  - Forms and scripts found
  - Crawl duration
  - Errors encountered

- **Endpoint Table**:
  - Method, Path, Status, Content-Type
  - Form/Link/Script counts
  - API detection flag

## JSONFormatter

Serializes crawl results to JSON for persistence and later analysis.

### Usage

```python
from dash_penetration.output.json import JSONFormatter

# Save to file
JSONFormatter.save_to_file(result, "crawl_result.json")

# Load from file
loaded_result = JSONFormatter.load_from_file("crawl_result.json")

# Format as JSON string
json_str = JSONFormatter.format_crawl_result(result, indent=2)
print(json_str)

# Get quick file summary without loading everything
summary = JSONFormatter.get_file_summary("crawl_result.json")
print(summary)  # {'target_url': ..., 'endpoint_count': ..., ...}

# Validate file
is_valid = JSONFormatter.validate_json_file("crawl_result.json")
```

### Features

- **Save/Load**: Persist results to disk, reload for caching
- **Auto Directories**: Creates parent directories as needed
- **Validation**: Verify file integrity before loading
- **Summary Peek**: Quick stats without full deserialization
- **Serialization**: Complete `CrawlResult` → JSON → `CrawlResult` roundtrip

## JSON Structure

Saved crawl results follow this structure:

```json
{
  "target_url": "https://example.com",
  "scope_domains": ["example.com"],
  "endpoints": {
    "GET:/": {
      "method": "GET",
      "path": "/",
      "status_code": 200,
      "content_type": "text/html",
      "forms": [],
      "links": ["https://example.com/about"],
      "scripts": [],
      "is_api": false,
      "discovered_count": 1
    }
  },
  "pages_crawled": 42,
  "start_time": "2024-01-01T12:00:00",
  "end_time": "2024-01-01T12:01:30",
  "errors": []
}
```

## Typical Workflow

```python
from dash_penetration.crawler.engine import CrawlEngine
from dash_penetration.output.console import ConsoleFormatter
from dash_penetration.output.json import JSONFormatter

# 1. Run crawl
engine = CrawlEngine(target_url, scope, rate_limit=10, max_concurrency=5)
result = asyncio.run(engine.crawl())

# 2. Display results in terminal
print(ConsoleFormatter.format_full_report(result))

# 3. Save for later
JSONFormatter.save_to_file(result, "results/example.com.json")

# 4. Later: reload and inspect
loaded = JSONFormatter.load_from_file("results/example.com.json")
print(ConsoleFormatter.format_endpoints(loaded.endpoints))
```

## Testing

Run the output formatter tests:

```bash
uv run pytest tests/test_output.py -v
```

All 34 tests verify:
- Console formatting (colors, tables, summaries)
- JSON serialization and deserialization
- File I/O (save, load, validation)
- Roundtrip consistency (save → load → save identical)
- Error handling

## Next Steps

Once output formatters are working:
- **Step 9**: Implement the `CrawlEngine` to orchestrate crawling with these formatters
- **Step 10**: Build the CLI to tie everything together
