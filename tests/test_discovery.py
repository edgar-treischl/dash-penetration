"""
Comprehensive tests for discovery plugins.

Tests cover:
- LinkDiscovery: link categorization, scope validation
- FormDiscovery: form extraction, field analysis
- ScriptDiscovery: script categorization, framework detection
- APIDiscovery: API pattern detection, versioning
"""

import pytest

from dash_penetration.crawler import Scope
from dash_penetration.crawler.parser import Form, FormInput
from dash_penetration.discovery import (
    LinkDiscovery,
    FormDiscovery,
    ScriptDiscovery,
    APIDiscovery,
)


class TestLinkDiscovery:
    """Test LinkDiscovery plugin."""

    def test_init_empty_url(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            LinkDiscovery("")

    def test_init_valid_url(self):
        """Test initialization with valid URL."""
        ld = LinkDiscovery("https://example.com")
        assert ld.base_url == "https://example.com"
        assert ld.base_domain == "example.com"

    def test_analyze_empty_list(self):
        """Test analyze with empty link list."""
        ld = LinkDiscovery("https://example.com")
        result = ld.analyze([])
        assert result.total_links() == 0
        assert result.internal_count() == 0

    def test_analyze_internal_links(self):
        """Test internal link detection."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/about",
        ]
        result = ld.analyze(links)
        assert result.internal_count() == 3
        assert result.external_count() == 0

    def test_analyze_external_links(self):
        """Test external link detection."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://google.com",
            "https://github.com",
            "https://stackoverflow.com",
        ]
        result = ld.analyze(links)
        assert result.internal_count() == 0
        assert result.external_count() == 3

    def test_analyze_dynamic_links(self):
        """Test dynamic link detection."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/search?q=test",
            "https://example.com/page#section",
            "https://example.com/post?id=123&sort=date",
        ]
        result = ld.analyze(links)
        assert result.dynamic_count() == 3

    def test_analyze_mixed_links(self):
        """Test analysis of mixed link types."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/page1",
            "https://example.com/search?q=test",
            "https://google.com",
            "https://google.com/search?q=test",
            "https://example.com/about#team",
        ]
        result = ld.analyze(links)
        assert result.internal_count() == 1  # Only /page1
        assert result.dynamic_count() == 3
        assert result.external_count() == 1  # google.com (non-dynamic)

    def test_analyze_domain_case_insensitive(self):
        """Test that domain comparison is case-insensitive."""
        ld = LinkDiscovery("https://Example.Com")
        links = [
            "https://EXAMPLE.COM/page1",
            "https://example.com/page2",
        ]
        result = ld.analyze(links)
        assert result.internal_count() == 2

    def test_analyze_scope_validation(self):
        """Test scope validation during analysis."""
        scope = Scope(allowed_domains=["example.com"])
        ld = LinkDiscovery("https://example.com", scope=scope)
        links = [
            "https://example.com/page1",
            "https://notallowed.com/page",
        ]
        result = ld.analyze(links)
        assert result.violation_count() == 1
        assert "https://notallowed.com/page" in result.scope_violations

    def test_analyze_by_domain(self):
        """Test grouping links by domain."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://google.com",
            "https://github.com",
            "https://github.com/user/repo",
        ]
        grouped = ld.analyze_by_domain(links)
        assert len(grouped) == 3
        assert len(grouped["example.com"]) == 2
        assert len(grouped["google.com"]) == 1
        assert len(grouped["github.com"]) == 2

    def test_filter_internal(self):
        """Test filtering internal links."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/page1",
            "https://google.com",
            "https://example.com/page2",
        ]
        internal = ld.filter_internal(links)
        assert len(internal) == 2
        assert "https://google.com" not in internal

    def test_filter_external(self):
        """Test filtering external links."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/page1",
            "https://google.com",
            "https://github.com",
        ]
        external = ld.filter_external(links)
        assert len(external) == 2
        assert "https://example.com/page1" not in external

    def test_filter_dynamic(self):
        """Test filtering dynamic links."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/page1",
            "https://example.com/search?q=test",
            "https://example.com/page#section",
        ]
        dynamic = ld.filter_dynamic(links)
        assert len(dynamic) == 2
        assert "https://example.com/page1" not in dynamic

    def test_result_to_dict(self):
        """Test LinkDiscoveryResult.to_dict()."""
        ld = LinkDiscovery("https://example.com")
        links = [
            "https://example.com/page1",
            "https://google.com",
        ]
        result = ld.analyze(links)
        data = result.to_dict()
        assert data["summary"]["total_links"] == 2
        assert data["summary"]["internal"] == 1
        assert data["summary"]["external"] == 1


class TestFormDiscovery:
    """Test FormDiscovery plugin."""

    def test_init(self):
        """Test FormDiscovery initialization."""
        fd = FormDiscovery()
        assert fd is not None

    def test_analyze_empty_forms(self):
        """Test analyze with empty form list."""
        fd = FormDiscovery()
        result = fd.analyze([])
        assert result.total_forms == 0

    def test_analyze_single_form(self):
        """Test analyzing a single form."""
        fd = FormDiscovery()
        forms = [
            Form(
                action="https://example.com/login",
                method="POST",
                inputs=[
                    FormInput(name="username", input_type="text"),
                    FormInput(name="password", input_type="password", required=True),
                ],
            )
        ]
        result = fd.analyze(forms)
        assert result.total_forms == 1
        assert result.post_forms == 1
        assert result.required_fields == 1
        assert result.optional_fields == 1

    def test_analyze_multiple_forms(self):
        """Test analyzing multiple forms."""
        fd = FormDiscovery()
        forms = [
            Form(
                action="https://example.com/login",
                method="POST",
                inputs=[FormInput(name="username", input_type="text")],
            ),
            Form(
                action="https://example.com/search",
                method="GET",
                inputs=[FormInput(name="q", input_type="text", required=True)],
            ),
        ]
        result = fd.analyze(forms)
        assert result.total_forms == 2
        assert result.post_forms == 1
        assert result.get_forms == 1

    def test_analyze_form_methods(self):
        """Test form method tracking."""
        fd = FormDiscovery()
        forms = [
            Form(action="https://example.com/1", method="GET"),
            Form(action="https://example.com/2", method="POST"),
            Form(action="https://example.com/3", method="POST"),
            Form(action="https://example.com/4", method="GET"),
        ]
        result = fd.analyze(forms)
        assert result.get_forms == 2
        assert result.post_forms == 2

    def test_find_by_method(self):
        """Test finding forms by HTTP method."""
        fd = FormDiscovery()
        forms = [
            Form(action="https://example.com/1", method="GET"),
            Form(action="https://example.com/2", method="POST"),
        ]
        post_forms = fd.find_by_method(forms, "POST")
        assert len(post_forms) == 1
        assert post_forms[0].method == "POST"

    def test_get_all_endpoints(self):
        """Test extracting all form action endpoints."""
        fd = FormDiscovery()
        forms = [
            Form(action="https://example.com/login"),
            Form(action="https://example.com/register"),
            Form(action="https://example.com/login"),  # Duplicate
        ]
        endpoints = fd.get_all_endpoints(forms)
        assert len(endpoints) == 2
        assert "https://example.com/login" in endpoints

    def test_get_all_parameters(self):
        """Test extracting all form parameter names."""
        fd = FormDiscovery()
        forms = [
            Form(
                action="https://example.com/1",
                inputs=[
                    FormInput(name="username", input_type="text"),
                    FormInput(name="email", input_type="text"),
                ],
            ),
            Form(
                action="https://example.com/2",
                inputs=[
                    FormInput(name="username", input_type="text"),
                    FormInput(name="password", input_type="password"),
                ],
            ),
        ]
        params = fd.get_all_parameters(forms)
        assert params["username"] == 2
        assert params["email"] == 1
        assert params["password"] == 1

    def test_result_to_dict(self):
        """Test FormDiscoveryResult.to_dict()."""
        fd = FormDiscovery()
        forms = [
            Form(
                action="https://example.com/login",
                method="POST",
                inputs=[FormInput(name="username", input_type="text")],
            )
        ]
        result = fd.analyze(forms)
        data = result.to_dict()
        assert data["total_forms"] == 1
        assert data["post_forms"] == 1
        assert "endpoints" in data


class TestScriptDiscovery:
    """Test ScriptDiscovery plugin."""

    def test_init_empty_url(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            ScriptDiscovery("")

    def test_init_valid_url(self):
        """Test initialization with valid URL."""
        sd = ScriptDiscovery("https://example.com")
        assert sd.base_url == "https://example.com"

    def test_analyze_empty_scripts(self):
        """Test analyze with empty script lists."""
        sd = ScriptDiscovery("https://example.com")
        result = sd.analyze([], [])
        assert result.total_scripts() == 0

    def test_analyze_external_scripts(self):
        """Test analyzing external scripts."""
        sd = ScriptDiscovery("https://example.com")
        scripts = [
            "https://cdn.example.com/jquery.js",
            "https://cdn.example.com/app.js",
        ]
        result = sd.analyze(scripts, [])
        assert result.external_count() == 2

    def test_analyze_inline_scripts(self):
        """Test analyzing inline scripts."""
        sd = ScriptDiscovery("https://example.com")
        inline = ['console.log("hello");', "var x = 1;"]
        result = sd.analyze([], inline)
        assert result.inline_count() == 2
        assert result.total_scripts() == 2

    def test_analyze_third_party_scripts(self):
        """Test third-party script detection."""
        sd = ScriptDiscovery("https://example.com")
        scripts = [
            "https://example.com/app.js",  # Same domain
            "https://cdn.example.com/jquery.js",  # Different subdomain (third-party)
            "https://google.com/analytics.js",  # Third-party
            "https://cloudflare.com/script.js",  # Third-party
        ]
        result = sd.analyze(scripts, [])
        assert result.external_count() == 4
        assert result.third_party_count() == 3  # cdn, google, cloudflare

    def test_framework_detection(self):
        """Test framework detection in script URLs."""
        sd = ScriptDiscovery("https://example.com")
        scripts = [
            "https://cdn.example.com/jquery-3.6.0.js",
            "https://cdn.example.com/react.js",
            "https://cdn.example.com/angular.js",
        ]
        result = sd.analyze(scripts, [])
        assert "jQuery" in result.detected_frameworks
        assert "React" in result.detected_frameworks
        assert "Angular" in result.detected_frameworks

    def test_framework_detection_inline(self):
        """Test framework detection in inline scripts."""
        sd = ScriptDiscovery("https://example.com")
        inline = [
            "import React from 'react';",
            "const app = new Vue();",
        ]
        result = sd.analyze([], inline)
        assert "React" in result.detected_frameworks
        assert "Vue" in result.detected_frameworks

    def test_get_external_urls(self):
        """Test getting external script URLs."""
        sd = ScriptDiscovery("https://example.com")
        scripts = [
            "https://cdn.example.com/jquery.js",
            "https://cdn.example.com/app.js",
        ]
        urls = sd.get_all_external_urls(scripts, [])
        assert len(urls) == 2

    def test_get_third_party_domains(self):
        """Test getting third-party domains."""
        sd = ScriptDiscovery("https://example.com")
        scripts = [
            "https://example.com/app.js",
            "https://cdn.example.com/jquery.js",
            "https://google.com/analytics.js",
            "https://cloudflare.com/script.js",
        ]
        domains = sd.get_third_party_domains(scripts, [])
        assert "google.com" in domains
        assert "cloudflare.com" in domains
        assert "cdn.example.com" in domains
        assert len(domains) == 3

    def test_filter_by_domain(self):
        """Test filtering scripts by domain."""
        sd = ScriptDiscovery("https://example.com")
        scripts = [
            "https://cdn.example.com/jquery.js",
            "https://google.com/analytics.js",
            "https://cdn.example.com/app.js",
        ]
        cdn_scripts = sd.filter_by_domain(scripts, "cdn.example.com")
        assert len(cdn_scripts) == 2

    def test_filter_by_framework(self):
        """Test filtering scripts by framework."""
        sd = ScriptDiscovery("https://example.com")
        scripts = [
            "https://cdn.example.com/jquery.js",
            "https://cdn.example.com/react.js",
            "https://cdn.example.com/app.js",
        ]
        jquery_scripts = sd.filter_by_framework(scripts, "jquery")
        assert len(jquery_scripts) == 1

    def test_result_to_dict(self):
        """Test ScriptDiscoveryResult.to_dict()."""
        sd = ScriptDiscovery("https://example.com")
        scripts = ["https://cdn.example.com/jquery.js"]
        result = sd.analyze(scripts, ["console.log()"])
        data = result.to_dict()
        assert data["total_scripts"] == 2
        assert data["external_scripts"] == 1


class TestAPIDiscovery:
    """Test APIDiscovery plugin."""

    def test_init_empty_url(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            APIDiscovery("")

    def test_init_valid_url(self):
        """Test initialization with valid URL."""
        ad = APIDiscovery("https://example.com")
        assert ad.base_url == "https://example.com"

    def test_analyze_empty_links(self):
        """Test analyze with empty link list."""
        ad = APIDiscovery("https://example.com")
        result = ad.analyze([])
        assert result.total_endpoints() == 0

    def test_detect_rest_api_paths(self):
        """Test REST API path detection."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/api/users",
            "https://example.com/api/products",
            "https://example.com/rest/v1/users",
        ]
        result = ad.analyze(links)
        assert result.total_endpoints() == 3

    def test_detect_api_versions(self):
        """Test API version detection."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/v1/users",
            "https://example.com/v2/users",
            "https://example.com/api/v3/products",
        ]
        result = ad.analyze(links)
        assert "v1" in result.versions_detected
        assert "v2" in result.versions_detected
        assert "v3" in result.versions_detected

    def test_detect_graphql(self):
        """Test GraphQL endpoint detection."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/graphql",
            "https://example.com/api/graphql",
        ]
        result = ad.analyze(links)
        assert result.graphql_count() == 2

    def test_detect_json_response(self):
        """Test JSON content-type detection."""
        ad = APIDiscovery("https://example.com")
        links = ["https://example.com/data"]
        content_types = {"https://example.com/data": "application/json"}
        result = ad.analyze(links, content_types=content_types)
        assert result.total_endpoints() == 1

    def test_api_domain_patterns(self):
        """Test API domain pattern detection."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://api.example.com/users",
            "https://apis.example.com/data",
            "https://rest.example.com/endpoint",
            "https://gateway.example.com/service",
        ]
        result = ad.analyze(links)
        assert result.total_endpoints() == 4

    def test_get_by_version(self):
        """Test filtering by API version."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/v1/users",
            "https://example.com/v2/users",
            "https://example.com/v1/products",
        ]
        v1_apis = ad.get_by_version(links, "v1")
        assert len(v1_apis) == 2

    def test_get_by_type(self):
        """Test filtering by API type."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/graphql",
            "https://example.com/api/users",
        ]
        graphql_apis = ad.get_by_type(links, "graphql")
        assert len(graphql_apis) == 1

    def test_filter_json_likely(self):
        """Test filtering JSON-likely endpoints."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/page",
            "https://example.com/api/users",
            "https://example.com/data.json",
        ]
        api_links = ad.filter_json_likely(links)
        assert len(api_links) >= 1

    def test_authentication_detection(self):
        """Test authentication endpoint detection."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/api/auth/login",
            "https://example.com/api/auth/token",
            "https://example.com/api/users",
        ]
        result = ad.analyze(links)
        auth_endpoints = [e for e in result.endpoints if e.is_authenticated]
        assert len(auth_endpoints) >= 1

    def test_result_to_dict(self):
        """Test APIDiscoveryResult.to_dict()."""
        ad = APIDiscovery("https://example.com")
        links = [
            "https://example.com/v1/users",
            "https://example.com/graphql",
        ]
        result = ad.analyze(links)
        data = result.to_dict()
        assert data["total_endpoints"] == 2
        assert "v1" in data["versions"]
