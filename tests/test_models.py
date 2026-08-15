"""
Tests for crawler data models.
"""

import pytest
from datetime import datetime
from crawler.models import (
    HTTPMethod,
    DiscoverySource,
    Page,
    FormField,
    Form,
    Endpoint,
    CrawlResult,
)


class TestHTTPMethod:
    """Test HTTPMethod enum."""

    def test_http_method_values(self):
        """Test valid HTTP methods."""
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
        assert HTTPMethod.PUT.value == "PUT"

    def test_http_method_from_string(self):
        """Test creating HTTPMethod from string."""
        assert HTTPMethod("GET") == HTTPMethod.GET
        assert HTTPMethod("POST") == HTTPMethod.POST
        with pytest.raises(ValueError):
            HTTPMethod("post")  # Strict case - lowercase fails


class TestDiscoverySource:
    """Test DiscoverySource enum."""

    def test_discovery_source_values(self):
        """Test valid discovery sources."""
        assert DiscoverySource.LINK.value == "link"
        assert DiscoverySource.FORM.value == "form"
        assert DiscoverySource.INITIAL.value == "initial"


class TestPage:
    """Test Page model."""

    def test_page_creation(self):
        """Test creating a basic page."""
        now = datetime.now()
        page = Page(
            url="https://example.com/",
            method="GET",
            status_code=200,
            content_type="text/html",
            headers={"Content-Length": "1234"},
            timestamp=now,
            discovered_by="initial",
            content_length=1234,
        )
        assert page.url == "https://example.com/"
        assert page.status_code == 200
        assert isinstance(page.method, HTTPMethod)
        assert page.method == HTTPMethod.GET

    def test_page_method_normalization(self):
        """Test HTTP method is normalized."""
        now = datetime.now()
        page = Page(
            url="https://example.com/",
            method="post",
            status_code=200,
            content_type="application/json",
            headers={},
            timestamp=now,
            discovered_by="form",
        )
        assert page.method == HTTPMethod.POST

    def test_page_discovery_source_normalization(self):
        """Test discovery source is normalized."""
        now = datetime.now()
        page = Page(
            url="https://example.com/",
            method="GET",
            status_code=200,
            content_type="text/html",
            headers={},
            timestamp=now,
            discovered_by="LINK",
        )
        assert page.discovered_by == DiscoverySource.LINK

    def test_page_invalid_status_code(self):
        """Test that invalid status codes raise error."""
        now = datetime.now()
        with pytest.raises(ValueError, match="Invalid HTTP status code"):
            Page(
                url="https://example.com/",
                method="GET",
                status_code=999,
                content_type="text/html",
                headers={},
                timestamp=now,
                discovered_by="initial",
            )

    def test_page_serialization(self):
        """Test Page to_dict and from_dict."""
        now = datetime.now()
        page = Page(
            url="https://example.com/",
            method="GET",
            status_code=200,
            content_type="text/html",
            headers={"Server": "nginx"},
            timestamp=now,
            discovered_by="initial",
            content_length=1000,
        )

        data = page.to_dict()
        assert data["url"] == "https://example.com/"
        assert data["method"] == "GET"
        assert data["status_code"] == 200
        assert data["discovered_by"] == "initial"

        # Verify round-trip
        page2 = Page.from_dict(data)
        assert page2.url == page.url
        assert page2.method == page.method
        assert page2.status_code == page.status_code


class TestFormField:
    """Test FormField model."""

    def test_form_field_creation(self):
        """Test creating a form field."""
        field = FormField(
            name="username",
            field_type="text",
            value="john",
            required=True,
        )
        assert field.name == "username"
        assert field.field_type == "text"
        assert field.value == "john"
        assert field.required is True

    def test_form_field_serialization(self):
        """Test FormField to_dict and from_dict."""
        field = FormField(name="email", field_type="email", required=True)
        data = field.to_dict()
        field2 = FormField.from_dict(data)
        assert field2.name == field.name
        assert field2.field_type == field.field_type


class TestForm:
    """Test Form model."""

    def test_form_creation(self):
        """Test creating a form."""
        fields = [
            FormField(name="username", field_type="text", required=True),
            FormField(name="password", field_type="password", required=True),
        ]
        form = Form(
            action="/login",
            method="POST",
            fields=fields,
            name="login_form",
        )
        assert form.action == "/login"
        assert form.method == HTTPMethod.POST
        assert len(form.fields) == 2

    def test_form_method_normalization(self):
        """Test form method is normalized."""
        form = Form(
            action="/submit",
            method="post",
            fields=[],
        )
        assert form.method == HTTPMethod.POST

    def test_form_serialization(self):
        """Test Form to_dict and from_dict."""
        form = Form(
            action="/api/submit",
            method="POST",
            fields=[
                FormField(name="email", field_type="email", required=True),
            ],
            name="contact_form",
        )
        data = form.to_dict()
        form2 = Form.from_dict(data)
        assert form2.action == form.action
        assert form2.method == form.method
        assert len(form2.fields) == 1


class TestEndpoint:
    """Test Endpoint model."""

    def test_endpoint_creation(self):
        """Test creating an endpoint."""
        endpoint = Endpoint(
            method="GET",
            path="/api/users",
            status_code=200,
            content_type="application/json",
        )
        assert endpoint.method == HTTPMethod.GET
        assert endpoint.path == "/api/users"
        assert endpoint.status_code == 200
        assert endpoint.is_api is False
        assert endpoint.discovered_count == 1

    def test_endpoint_with_forms_and_links(self):
        """Test endpoint with forms and links."""
        form = Form(
            action="/login",
            method="POST",
            fields=[FormField(name="user", field_type="text")],
        )
        endpoint = Endpoint(
            method="POST",
            path="/login",
            status_code=200,
            content_type="text/html",
            forms=[form],
            links=["https://example.com/", "https://example.com/register"],
            scripts=["app.js"],
        )
        assert len(endpoint.forms) == 1
        assert len(endpoint.links) == 2
        assert len(endpoint.scripts) == 1

    def test_endpoint_invalid_status_code(self):
        """Test that invalid status codes raise error."""
        with pytest.raises(ValueError, match="Invalid HTTP status code"):
            Endpoint(
                method="GET",
                path="/",
                status_code=999,
                content_type="text/html",
            )

    def test_endpoint_serialization(self):
        """Test Endpoint to_dict and from_dict."""
        endpoint = Endpoint(
            method="POST",
            path="/api/data",
            status_code=201,
            content_type="application/json",
            is_api=True,
        )
        data = endpoint.to_dict()
        endpoint2 = Endpoint.from_dict(data)
        assert endpoint2.method == endpoint.method
        assert endpoint2.path == endpoint.path
        assert endpoint2.status_code == endpoint.status_code
        assert endpoint2.is_api == endpoint.is_api


class TestCrawlResult:
    """Test CrawlResult model."""

    def test_crawl_result_creation(self):
        """Test creating a crawl result."""
        result = CrawlResult(
            target_url="https://example.com",
            scope_domains=["example.com"],
            pages_crawled=0,
        )
        assert result.target_url == "https://example.com"
        assert result.scope_domains == ["example.com"]
        assert len(result.endpoints) == 0

    def test_add_endpoint_new(self):
        """Test adding a new endpoint."""
        result = CrawlResult(
            target_url="https://example.com",
            scope_domains=["example.com"],
        )
        endpoint = Endpoint(
            method="GET",
            path="/api/users",
            status_code=200,
            content_type="application/json",
            is_api=True,
        )
        result.add_endpoint(endpoint)
        assert len(result.endpoints) == 1
        assert "GET:/api/users" in result.endpoints

    def test_add_endpoint_merge_existing(self):
        """Test merging duplicate endpoints."""
        result = CrawlResult(
            target_url="https://example.com",
            scope_domains=["example.com"],
        )
        endpoint1 = Endpoint(
            method="GET",
            path="/users",
            status_code=200,
            content_type="application/json",
            links=["https://example.com/users/1"],
            discovered_count=1,
        )
        endpoint2 = Endpoint(
            method="GET",
            path="/users",
            status_code=200,
            content_type="application/json",
            links=["https://example.com/users/2"],
            discovered_count=1,
        )
        result.add_endpoint(endpoint1)
        result.add_endpoint(endpoint2)

        assert len(result.endpoints) == 1
        merged = result.endpoints["GET:/users"]
        assert merged.discovered_count == 2
        assert len(merged.links) == 2

    def test_get_endpoint_summary(self):
        """Test getting endpoint summary."""
        result = CrawlResult(
            target_url="https://example.com",
            scope_domains=["example.com"],
        )
        result.add_endpoint(
            Endpoint(
                method="GET",
                path="/",
                status_code=200,
                content_type="text/html",
            )
        )
        result.add_endpoint(
            Endpoint(
                method="GET",
                path="/api/users",
                status_code=200,
                content_type="application/json",
                is_api=True,
            )
        )

        summary = result.get_endpoint_summary()
        assert len(summary) == 2
        assert summary[0]["path"] == "/"
        assert summary[1]["path"] == "/api/users"
        assert summary[1]["is_api"] is True

    def test_crawl_result_serialization(self):
        """Test CrawlResult to_dict and from_dict."""
        now = datetime.now()
        result = CrawlResult(
            target_url="https://example.com",
            scope_domains=["example.com"],
            start_time=now,
            end_time=now,
            pages_crawled=5,
        )
        result.add_endpoint(
            Endpoint(
                method="GET",
                path="/",
                status_code=200,
                content_type="text/html",
            )
        )

        data = result.to_dict()
        result2 = CrawlResult.from_dict(data)
        assert result2.target_url == result.target_url
        assert result2.pages_crawled == result.pages_crawled
        assert len(result2.endpoints) == 1
        assert result2.start_time is not None
        assert result2.end_time is not None

    def test_crawl_result_with_errors(self):
        """Test crawl result tracking errors."""
        result = CrawlResult(
            target_url="https://example.com",
            scope_domains=["example.com"],
            errors=["Timeout on /admin", "SSL error on /secure"],
        )
        assert len(result.errors) == 2
        assert "Timeout" in result.errors[0]
