"""
Tests for output formatters (console and JSON).
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from dash_penetration.output.console import ConsoleFormatter
from dash_penetration.output.json import JSONFormatter
from dash_penetration.crawler.models import (
    CrawlResult,
    Endpoint,
    HTTPMethod,
    Form,
    FormField,
)


@pytest.fixture
def sample_crawl_result():
    """Create a sample CrawlResult for testing."""
    result = CrawlResult(
        target_url="https://example.com",
        scope_domains=["example.com", "api.example.com"],
        pages_crawled=42,
        start_time=datetime(2024, 1, 1, 12, 0, 0),
        end_time=datetime(2024, 1, 1, 12, 1, 30),
    )

    # Add some endpoints
    endpoint1 = Endpoint(
        method=HTTPMethod.GET,
        path="/",
        status_code=200,
        content_type="text/html",
        links=["https://example.com/about", "https://example.com/contact"],
    )
    result.add_endpoint(endpoint1)

    endpoint2 = Endpoint(
        method=HTTPMethod.GET,
        path="/login",
        status_code=200,
        content_type="text/html",
        forms=[
            Form(
                action="/authenticate",
                method=HTTPMethod.POST,
                fields=[
                    FormField(name="username", field_type="text", required=True),
                    FormField(name="password", field_type="password", required=True),
                ],
            )
        ],
    )
    result.add_endpoint(endpoint2)

    endpoint3 = Endpoint(
        method=HTTPMethod.POST,
        path="/api/users",
        status_code=201,
        content_type="application/json",
        is_api=True,
    )
    result.add_endpoint(endpoint3)

    endpoint4 = Endpoint(
        method=HTTPMethod.GET,
        path="/admin",
        status_code=403,
        content_type="text/html",
    )
    result.add_endpoint(endpoint4)

    endpoint5 = Endpoint(
        method=HTTPMethod.GET,
        path="/notfound",
        status_code=404,
        content_type="text/html",
    )
    result.add_endpoint(endpoint5)

    return result


class TestConsoleFormatter:
    """Tests for ConsoleFormatter."""

    def test_format_endpoints_with_data(self, sample_crawl_result):
        """Test formatting endpoints with data."""
        output = ConsoleFormatter.format_endpoints(sample_crawl_result.endpoints)

        assert "METHOD" in output
        assert "PATH" in output
        assert "STATUS" in output
        assert "CONTENT-TYPE" in output
        assert "/" in output
        assert "/login" in output
        assert "/api/users" in output
        assert "200" in output
        assert "201" in output
        assert "403" in output
        assert "404" in output

    def test_format_endpoints_empty(self):
        """Test formatting with no endpoints."""
        output = ConsoleFormatter.format_endpoints({})
        assert "No endpoints discovered" in output

    def test_format_endpoints_colors(self, sample_crawl_result):
        """Test that color codes are present in output."""
        output = ConsoleFormatter.format_endpoints(sample_crawl_result.endpoints)

        # Check for ANSI color codes
        assert "\033[" in output  # ANSI escape sequence
        assert "92m" in output or "91m" in output or "93m" in output  # Color codes

    def test_get_status_color_success(self):
        """Test status color for 2xx responses."""
        color = ConsoleFormatter._get_status_color(200)
        assert color == ConsoleFormatter.GREEN

    def test_get_status_color_redirect(self):
        """Test status color for 3xx responses."""
        color = ConsoleFormatter._get_status_color(302)
        assert color == ConsoleFormatter.CYAN

    def test_get_status_color_client_error(self):
        """Test status color for 4xx responses."""
        color = ConsoleFormatter._get_status_color(404)
        assert color == ConsoleFormatter.YELLOW

    def test_get_status_color_server_error(self):
        """Test status color for 5xx responses."""
        color = ConsoleFormatter._get_status_color(500)
        assert color == ConsoleFormatter.RED

    def test_format_crawl_summary(self, sample_crawl_result):
        """Test formatting crawl summary."""
        output = ConsoleFormatter.format_crawl_summary(sample_crawl_result)

        assert "Crawl Summary" in output
        assert "https://example.com" in output
        assert "example.com" in output
        assert "Pages Crawled:" in output
        assert "42" in output
        assert "Unique Endpoints:" in output
        assert "5" in output  # 5 endpoints added

    def test_format_crawl_summary_status_distribution(self, sample_crawl_result):
        """Test that status distribution is shown."""
        output = ConsoleFormatter.format_crawl_summary(sample_crawl_result)

        assert "Status Code Distribution:" in output
        # Status codes have color codes, so check without colon
        assert "200" in output
        assert "201" in output
        assert "403" in output
        assert "404" in output

    def test_format_crawl_summary_http_methods(self, sample_crawl_result):
        """Test that HTTP methods are shown."""
        output = ConsoleFormatter.format_crawl_summary(sample_crawl_result)

        assert "HTTP Methods:" in output
        assert "GET:" in output
        assert "POST:" in output

    def test_format_crawl_summary_api_endpoints(self, sample_crawl_result):
        """Test that API endpoint count is shown."""
        output = ConsoleFormatter.format_crawl_summary(sample_crawl_result)

        assert "API Endpoints:" in output
        assert "1" in output

    def test_format_crawl_summary_forms(self, sample_crawl_result):
        """Test that form count is shown."""
        output = ConsoleFormatter.format_crawl_summary(sample_crawl_result)

        assert "Forms Found:" in output
        assert "1" in output

    def test_format_crawl_summary_timing(self, sample_crawl_result):
        """Test that crawl duration is shown."""
        output = ConsoleFormatter.format_crawl_summary(sample_crawl_result)

        assert "Crawl Duration:" in output
        assert "90" in output  # 1.5 minutes

    def test_format_crawl_summary_with_errors(self, sample_crawl_result):
        """Test that errors are shown."""
        sample_crawl_result.errors = ["Connection timeout", "SSL certificate error", "Invalid response"]
        output = ConsoleFormatter.format_crawl_summary(sample_crawl_result)

        assert "Errors (3):" in output
        assert "Connection timeout" in output

    def test_format_full_report(self, sample_crawl_result):
        """Test formatting complete report."""
        output = ConsoleFormatter.format_full_report(sample_crawl_result)

        assert "Crawl Summary" in output
        assert "Discovered Endpoints" in output
        assert "METHOD" in output
        assert "https://example.com" in output


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_endpoints_valid_json(self, sample_crawl_result):
        """Test that formatted endpoints is valid JSON."""
        output = JSONFormatter.format_endpoints(sample_crawl_result)

        data = json.loads(output)
        assert isinstance(data, dict)
        assert "GET:/" in data
        assert data["GET:/"]["status_code"] == 200

    def test_format_endpoints_structure(self, sample_crawl_result):
        """Test that formatted endpoints has correct structure."""
        output = JSONFormatter.format_endpoints(sample_crawl_result)

        data = json.loads(output)
        endpoint = data["GET:/"]

        assert "method" in endpoint
        assert "path" in endpoint
        assert "status_code" in endpoint
        assert "content_type" in endpoint
        assert "forms" in endpoint
        assert "links" in endpoint
        assert "scripts" in endpoint
        assert "is_api" in endpoint

    def test_format_crawl_result_valid_json(self, sample_crawl_result):
        """Test that formatted crawl result is valid JSON."""
        output = JSONFormatter.format_crawl_result(sample_crawl_result)

        data = json.loads(output)
        assert isinstance(data, dict)

    def test_format_crawl_result_structure(self, sample_crawl_result):
        """Test that formatted crawl result has correct structure."""
        output = JSONFormatter.format_crawl_result(sample_crawl_result)

        data = json.loads(output)

        assert "target_url" in data
        assert "scope_domains" in data
        assert "endpoints" in data
        assert "pages_crawled" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "errors" in data

    def test_save_to_file(self, sample_crawl_result):
        """Test saving crawl result to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "crawl_result.json"

            JSONFormatter.save_to_file(sample_crawl_result, str(filepath))

            assert filepath.exists()

            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["target_url"] == "https://example.com"
            assert data["pages_crawled"] == 42

    def test_save_to_file_creates_directories(self, sample_crawl_result):
        """Test that save_to_file creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nested" / "path" / "crawl_result.json"

            JSONFormatter.save_to_file(sample_crawl_result, str(filepath))

            assert filepath.exists()

    def test_save_to_file_invalid_filename(self, sample_crawl_result):
        """Test save_to_file with invalid filename."""
        with pytest.raises(ValueError):
            JSONFormatter.save_to_file(sample_crawl_result, "")

    def test_load_from_file(self, sample_crawl_result):
        """Test loading crawl result from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "crawl_result.json"

            JSONFormatter.save_to_file(sample_crawl_result, str(filepath))
            loaded = JSONFormatter.load_from_file(str(filepath))

            assert loaded.target_url == sample_crawl_result.target_url
            assert loaded.pages_crawled == sample_crawl_result.pages_crawled
            assert len(loaded.endpoints) == len(sample_crawl_result.endpoints)

    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            JSONFormatter.load_from_file("/nonexistent/file.json")

    def test_load_from_file_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "invalid.json"

            with open(filepath, "w") as f:
                f.write("invalid json content {")

            with pytest.raises(json.JSONDecodeError):
                JSONFormatter.load_from_file(str(filepath))

    def test_roundtrip_save_load(self, sample_crawl_result):
        """Test saving and loading produces equivalent result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "crawl_result.json"

            JSONFormatter.save_to_file(sample_crawl_result, str(filepath))
            loaded = JSONFormatter.load_from_file(str(filepath))

            # Compare key attributes
            assert loaded.target_url == sample_crawl_result.target_url
            assert loaded.scope_domains == sample_crawl_result.scope_domains
            assert loaded.pages_crawled == sample_crawl_result.pages_crawled
            assert len(loaded.endpoints) == len(sample_crawl_result.endpoints)

    def test_validate_json_file_valid(self, sample_crawl_result):
        """Test validating a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "crawl_result.json"

            JSONFormatter.save_to_file(sample_crawl_result, str(filepath))
            is_valid = JSONFormatter.validate_json_file(str(filepath))

            assert is_valid is True

    def test_validate_json_file_invalid(self):
        """Test validating an invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "invalid.json"

            with open(filepath, "w") as f:
                f.write("invalid json")

            is_valid = JSONFormatter.validate_json_file(str(filepath))
            assert is_valid is False

    def test_validate_json_file_not_found(self):
        """Test validating a non-existent file."""
        is_valid = JSONFormatter.validate_json_file("/nonexistent/file.json")
        assert is_valid is False

    def test_get_file_summary(self, sample_crawl_result):
        """Test getting summary from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "crawl_result.json"

            JSONFormatter.save_to_file(sample_crawl_result, str(filepath))
            summary = JSONFormatter.get_file_summary(str(filepath))

            assert summary["target_url"] == "https://example.com"
            assert summary["endpoint_count"] == 5
            assert summary["pages_crawled"] == 42
            assert "example.com" in summary["scope_domains"]

    def test_get_file_summary_not_found(self):
        """Test get_file_summary with non-existent file."""
        with pytest.raises(FileNotFoundError):
            JSONFormatter.get_file_summary("/nonexistent/file.json")

    def test_format_endpoints_compact_json(self, sample_crawl_result):
        """Test formatting endpoints with compact JSON (no indent)."""
        output = JSONFormatter.format_endpoints(sample_crawl_result, indent=None)

        # Should be valid JSON
        data = json.loads(output)
        assert isinstance(data, dict)

        # Should be more compact (no newlines between properties)
        assert output.count("\n") < 5


class TestIntegration:
    """Integration tests combining console and JSON formatters."""

    def test_json_and_console_consistency(self, sample_crawl_result):
        """Test that JSON and console formatters handle same data."""
        json_output = JSONFormatter.format_crawl_result(sample_crawl_result)
        console_output = ConsoleFormatter.format_full_report(sample_crawl_result)

        # Both should contain the target URL
        json_data = json.loads(json_output)
        assert json_data["target_url"] in console_output

        # Both should reflect the same endpoint count
        assert len(json_data["endpoints"]) == len(sample_crawl_result.endpoints)

    def test_save_and_display(self, sample_crawl_result):
        """Test saving to file and then displaying via console."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "crawl_result.json"

            JSONFormatter.save_to_file(sample_crawl_result, str(filepath))
            loaded = JSONFormatter.load_from_file(str(filepath))

            console_output = ConsoleFormatter.format_full_report(loaded)

            assert "Crawl Summary" in console_output
            assert "https://example.com" in console_output
            assert "Discovered Endpoints" in console_output
