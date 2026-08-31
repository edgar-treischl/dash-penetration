"""Tests for crawler/scope.py"""

import pytest
from dash_penetration.crawler.scope import Scope


class TestScopeInit:
    """Test Scope initialization."""

    def test_scope_creation_with_single_domain(self):
        """Test creating a scope with a single domain."""
        scope = Scope(allowed_domains=["example.com"])
        assert scope.allowed_domains == ["example.com"]
        assert scope.allowed_paths == []
        assert scope.disallowed_paths == []

    def test_scope_creation_with_multiple_domains(self):
        """Test creating a scope with multiple domains."""
        scope = Scope(allowed_domains=["example.com", "api.example.com"])
        assert len(scope.allowed_domains) == 2

    def test_scope_creation_with_paths(self):
        """Test creating a scope with allowed and disallowed paths."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api", "/public"],
            disallowed_paths=["/admin", "/private"],
        )
        assert scope.allowed_paths == ["/api", "/public"]
        assert scope.disallowed_paths == ["/admin", "/private"]

    def test_scope_requires_allowed_domains(self):
        """Test that Scope requires at least one allowed domain."""
        with pytest.raises(ValueError, match="At least one allowed domain"):
            Scope(allowed_domains=[])

    def test_domain_lowercased(self):
        """Test that domains are lowercased."""
        scope = Scope(allowed_domains=["EXAMPLE.COM", "API.EXAMPLE.COM"])
        assert scope.allowed_domains == ["example.com", "api.example.com"]

    def test_paths_lowercased(self):
        """Test that paths are lowercased."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/API", "/PUBLIC"],
            disallowed_paths=["/ADMIN"],
        )
        assert scope.allowed_paths == ["/api", "/public"]
        assert scope.disallowed_paths == ["/admin"]


class TestIsDomainAllowed:
    """Test domain validation."""

    def test_exact_domain_match(self):
        """Test exact domain match."""
        scope = Scope(allowed_domains=["example.com"])
        assert scope.is_domain_allowed("https://example.com/path")
        assert scope.is_domain_allowed("http://example.com/")

    def test_subdomain_allowed(self):
        """Test subdomain is allowed when parent domain is in scope."""
        scope = Scope(allowed_domains=["example.com"])
        assert scope.is_domain_allowed("https://api.example.com/path")
        assert scope.is_domain_allowed("https://v2.api.example.com/path")

    def test_case_insensitive_domain(self):
        """Test domain matching is case-insensitive."""
        scope = Scope(allowed_domains=["example.com"])
        assert scope.is_domain_allowed("https://EXAMPLE.COM/path")
        assert scope.is_domain_allowed("https://Api.Example.Com/path")

    def test_domain_with_port(self):
        """Test domain with port."""
        scope = Scope(allowed_domains=["example.com:8080"])
        assert scope.is_domain_allowed("https://example.com:8080/path")

    def test_domain_with_port_subdomain(self):
        """Test subdomain with port."""
        scope = Scope(allowed_domains=["example.com:8080"])
        assert scope.is_domain_allowed("https://api.example.com:8080/path")

    def test_different_domain_rejected(self):
        """Test different domain is rejected."""
        scope = Scope(allowed_domains=["example.com"])
        assert not scope.is_domain_allowed("https://other.com/path")
        assert not scope.is_domain_allowed("https://examplecom.org/path")

    def test_multiple_allowed_domains(self):
        """Test with multiple allowed domains."""
        scope = Scope(allowed_domains=["example.com", "other.com"])
        assert scope.is_domain_allowed("https://example.com/path")
        assert scope.is_domain_allowed("https://other.com/path")
        assert not scope.is_domain_allowed("https://third.com/path")

    def test_invalid_url_rejected(self):
        """Test invalid URL is rejected."""
        scope = Scope(allowed_domains=["example.com"])
        assert not scope.is_domain_allowed("not-a-url")
        assert not scope.is_domain_allowed("")


class TestIsPathAllowed:
    """Test path validation."""

    def test_no_path_restrictions_allows_all(self):
        """Test that all paths are allowed when no restrictions set."""
        scope = Scope(allowed_domains=["example.com"])
        assert scope.is_path_allowed("https://example.com/any/path")
        assert scope.is_path_allowed("https://example.com/api/users")
        assert scope.is_path_allowed("https://example.com/admin/dashboard")

    def test_allowed_paths_whitelist(self):
        """Test allowed_paths acts as a whitelist."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api", "/public"],
        )
        assert scope.is_path_allowed("https://example.com/api/users")
        assert scope.is_path_allowed("https://example.com/api/v2/products")
        assert scope.is_path_allowed("https://example.com/public/docs")
        assert not scope.is_path_allowed("https://example.com/admin/dashboard")
        assert not scope.is_path_allowed("https://example.com/other")

    def test_disallowed_paths_blacklist(self):
        """Test disallowed_paths acts as a blacklist."""
        scope = Scope(
            allowed_domains=["example.com"],
            disallowed_paths=["/admin", "/private"],
        )
        assert scope.is_path_allowed("https://example.com/api/users")
        assert scope.is_path_allowed("https://example.com/public")
        assert not scope.is_path_allowed("https://example.com/admin/dashboard")
        assert not scope.is_path_allowed("https://example.com/private/data")

    def test_disallowed_takes_priority_over_allowed(self):
        """Test that disallowed_paths takes priority."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api", "/admin"],
            disallowed_paths=["/admin/sensitive"],
        )
        assert scope.is_path_allowed("https://example.com/api/users")
        assert scope.is_path_allowed("https://example.com/admin/general")
        assert not scope.is_path_allowed("https://example.com/admin/sensitive/data")

    def test_root_path_allowed(self):
        """Test root path is allowed."""
        scope = Scope(allowed_domains=["example.com"])
        assert scope.is_path_allowed("https://example.com/")
        assert scope.is_path_allowed("https://example.com")

    def test_case_insensitive_paths(self):
        """Test path matching is case-insensitive."""
        scope = Scope(
            allowed_domains=["example.com"],
            disallowed_paths=["/admin"],
        )
        assert not scope.is_path_allowed("https://example.com/ADMIN")
        assert not scope.is_path_allowed("https://example.com/Admin")

    def test_path_with_query_params_ignored(self):
        """Test that query parameters don't affect path matching."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api"],
        )
        assert scope.is_path_allowed("https://example.com/api/users?id=123")
        assert scope.is_path_allowed("https://example.com/api?filter=active")

    def test_invalid_url_with_no_path_restrictions(self):
        """Test that URLs with no path restrictions allow any parsed path."""
        scope = Scope(allowed_domains=["example.com"])
        # urlparse treats "not-a-url" as a path-only URL, so it's allowed
        assert scope.is_path_allowed("not-a-url")


class TestIsInScope:
    """Test combined scope validation."""

    def test_url_in_scope(self):
        """Test URL that is fully in scope."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api"],
        )
        assert scope.is_in_scope("https://example.com/api/users")

    def test_subdomain_in_scope(self):
        """Test subdomain URL is in scope."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api"],
        )
        assert scope.is_in_scope("https://api.example.com/api/users")

    def test_domain_out_of_scope(self):
        """Test domain out of scope fails."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api"],
        )
        assert not scope.is_in_scope("https://other.com/api/users")

    def test_path_out_of_scope(self):
        """Test path out of scope fails."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api"],
        )
        assert not scope.is_in_scope("https://example.com/admin/users")

    def test_domain_and_path_both_must_match(self):
        """Test both domain and path must be in scope."""
        scope = Scope(
            allowed_domains=["example.com"],
            disallowed_paths=["/admin"],
        )
        assert scope.is_in_scope("https://example.com/api/users")
        assert not scope.is_in_scope("https://other.com/api/users")
        assert not scope.is_in_scope("https://example.com/admin/users")
        assert not scope.is_in_scope("https://other.com/admin/users")

    def test_complex_scope(self):
        """Test complex scope with multiple domains and paths."""
        scope = Scope(
            allowed_domains=["example.com", "api.example.com"],
            allowed_paths=["/api", "/public"],
            disallowed_paths=["/admin"],
        )
        assert scope.is_in_scope("https://example.com/api/users")
        assert scope.is_in_scope("https://api.example.com/api/products")
        assert scope.is_in_scope("https://app.example.com/public/docs")
        assert not scope.is_in_scope("https://example.com/admin")
        assert not scope.is_in_scope("https://other.com/api/users")
        assert not scope.is_in_scope("https://example.com/login")


class TestParseDomain:
    """Test domain extraction."""

    def test_parse_domain_from_url(self):
        """Test parsing domain from URL."""
        assert Scope.parse_domain_from_url("https://example.com/path") == "example.com"

    def test_parse_domain_with_port(self):
        """Test parsing domain with port."""
        assert (
            Scope.parse_domain_from_url("https://example.com:8080/path")
            == "example.com:8080"
        )

    def test_parse_domain_with_subdomain(self):
        """Test parsing domain with subdomain."""
        assert (
            Scope.parse_domain_from_url("https://api.example.com/path")
            == "api.example.com"
        )

    def test_parse_domain_case_insensitive(self):
        """Test domain is lowercased."""
        assert (
            Scope.parse_domain_from_url("https://EXAMPLE.COM/path") == "example.com"
        )

    def test_parse_domain_invalid_url(self):
        """Test invalid URL raises error."""
        with pytest.raises(ValueError):
            Scope.parse_domain_from_url("not-a-url")

    def test_parse_domain_no_domain(self):
        """Test URL with no domain raises error."""
        with pytest.raises(ValueError):
            Scope.parse_domain_from_url("/path/only")


class TestScopeFromDict:
    """Test Scope.from_dict() factory method."""

    def test_from_dict_minimal(self):
        """Test creating Scope from minimal dict."""
        config = {"allowed_domains": ["example.com"]}
        scope = Scope.from_dict(config)
        assert scope.allowed_domains == ["example.com"]
        assert scope.allowed_paths == []
        assert scope.disallowed_paths == []

    def test_from_dict_full(self):
        """Test creating Scope from full dict."""
        config = {
            "allowed_domains": ["example.com"],
            "allowed_paths": ["/api"],
            "disallowed_paths": ["/admin"],
        }
        scope = Scope.from_dict(config)
        assert scope.allowed_domains == ["example.com"]
        assert scope.allowed_paths == ["/api"]
        assert scope.disallowed_paths == ["/admin"]

    def test_from_dict_invalid_config_not_dict(self):
        """Test from_dict rejects non-dict config."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            Scope.from_dict("not-a-dict")

    def test_from_dict_missing_allowed_domains(self):
        """Test from_dict requires allowed_domains."""
        with pytest.raises(ValueError, match="'allowed_domains' is required"):
            Scope.from_dict({})

    def test_from_dict_allowed_domains_not_list(self):
        """Test from_dict requires allowed_domains to be a list."""
        with pytest.raises(ValueError, match="'allowed_domains' must be a list"):
            Scope.from_dict({"allowed_domains": "example.com"})


class TestScopeToDict:
    """Test Scope.to_dict() serialization."""

    def test_to_dict_full(self):
        """Test converting Scope to dict."""
        scope = Scope(
            allowed_domains=["example.com"],
            allowed_paths=["/api"],
            disallowed_paths=["/admin"],
        )
        result = scope.to_dict()
        assert result["allowed_domains"] == ["example.com"]
        assert result["allowed_paths"] == ["/api"]
        assert result["disallowed_paths"] == ["/admin"]

    def test_to_dict_round_trip(self):
        """Test serialization and deserialization."""
        original = Scope(
            allowed_domains=["example.com", "api.example.com"],
            allowed_paths=["/api", "/public"],
            disallowed_paths=["/admin"],
        )
        serialized = original.to_dict()
        restored = Scope.from_dict(serialized)
        assert restored.allowed_domains == original.allowed_domains
        assert restored.allowed_paths == original.allowed_paths
        assert restored.disallowed_paths == original.disallowed_paths


class TestScopeRepr:
    """Test Scope string representation."""

    def test_repr(self):
        """Test __repr__ returns useful string."""
        scope = Scope(allowed_domains=["example.com"])
        repr_str = repr(scope)
        assert "Scope" in repr_str
        assert "example.com" in repr_str
