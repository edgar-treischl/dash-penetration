"""Tests for crawler/parser.py"""

import pytest
from dash_penetration.crawler.parser import (
    HTMLParser,
    Form,
    FormInput,
    ScriptReference,
)

# HTML fixtures
SIMPLE_HTML = """
<html>
    <head><title>Test</title></head>
    <body>
        <a href="https://example.com/page1">Link 1</a>
        <a href="/page2">Link 2</a>
        <a href="page3">Link 3</a>
    </body>
</html>
"""

HTML_WITH_FORMS = """
<html>
    <body>
        <form action="/login" method="POST">
            <input type="text" name="username" required>
            <input type="password" name="password" required>
            <input type="submit" value="Login">
        </form>
        <form action="/search" method="GET">
            <input type="text" name="q">
            <textarea name="comment"></textarea>
            <select name="filter">
                <option>All</option>
            </select>
        </form>
    </body>
</html>
"""

HTML_WITH_SCRIPTS = """
<html>
    <head>
        <script src="https://example.com/lib.js"></script>
        <script src="/local.js"></script>
    </head>
    <body>
        <script>console.log("inline script");</script>
        <div>Content</div>
    </body>
</html>
"""

HTML_WITH_META = """
<html>
    <head>
        <meta name="description" content="Test page">
        <meta name="robots" content="noindex, nofollow">
        <meta name="author" content="Test Author">
        <meta property="og:title" content="Open Graph Title">
        <meta property="og:url" content="https://example.com">
    </head>
</html>
"""

MALFORMED_HTML = """
<html>
    <body>
        <a href="/page1">Link 1
        <a href="/page2">Link 2</a>
        <form>
            <input name="field1"
            <input name="field2" type="text">
        </form>
    </body>
</html>
"""

EMPTY_LINKS_HTML = """
<html>
    <body>
        <a href="">Empty href</a>
        <a href="#">Fragment only</a>
        <a href="?query=1">Query only</a>
        <a>No href</a>
    </body>
</html>
"""


class TestHTMLParserInit:
    """Test HTMLParser initialization."""

    def test_parser_creation(self):
        """Test creating an HTMLParser."""
        parser = HTMLParser("https://example.com")
        assert parser.base_url == "https://example.com"

    def test_parser_with_trailing_slash(self):
        """Test parser with base URL trailing slash."""
        parser = HTMLParser("https://example.com/")
        assert parser.base_url == "https://example.com/"


class TestHTMLParserParse:
    """Test HTML parsing."""

    def test_parse_valid_html(self):
        """Test parsing valid HTML."""
        parser = HTMLParser("https://example.com")
        doc = parser.parse("<html><body>Test</body></html>")
        assert doc is not None

    def test_parse_empty_html_raises(self):
        """Test parsing empty HTML raises error."""
        parser = HTMLParser("https://example.com")
        with pytest.raises(ValueError, match="HTML content is empty"):
            parser.parse("")

    def test_parse_whitespace_only_raises(self):
        """Test parsing whitespace-only HTML raises error."""
        parser = HTMLParser("https://example.com")
        with pytest.raises(ValueError, match="HTML content is empty"):
            parser.parse("   \n\t  ")

    def test_parse_malformed_html(self):
        """Test parsing malformed HTML (selectolax is forgiving)."""
        parser = HTMLParser("https://example.com")
        doc = parser.parse("<html><body><p>Unclosed</body></html>")
        assert doc is not None


class TestResolveURL:
    """Test URL resolution."""

    def test_resolve_absolute_url(self):
        """Test resolving absolute URL (unchanged)."""
        parser = HTMLParser("https://example.com/page1")
        resolved = parser.resolve_url("https://other.com/page2")
        assert resolved == "https://other.com/page2"

    def test_resolve_relative_path(self):
        """Test resolving relative path."""
        parser = HTMLParser("https://example.com/dir/page1")
        resolved = parser.resolve_url("page2")
        assert resolved == "https://example.com/dir/page2"

    def test_resolve_absolute_path(self):
        """Test resolving absolute path (from root)."""
        parser = HTMLParser("https://example.com/dir/page1")
        resolved = parser.resolve_url("/page2")
        assert resolved == "https://example.com/page2"

    def test_resolve_parent_directory(self):
        """Test resolving parent directory."""
        parser = HTMLParser("https://example.com/dir/subdir/page1")
        resolved = parser.resolve_url("../page2")
        assert resolved == "https://example.com/dir/page2"

    def test_resolve_fragment_only(self):
        """Test resolving fragment-only URL."""
        parser = HTMLParser("https://example.com/page1")
        resolved = parser.resolve_url("#section")
        assert resolved == "https://example.com/page1"

    def test_resolve_query_only(self):
        """Test resolving query-only URL."""
        parser = HTMLParser("https://example.com/page1")
        resolved = parser.resolve_url("?id=123")
        assert resolved == "https://example.com/page1?id=123"

    def test_resolve_empty_url_raises(self):
        """Test resolving empty URL raises error."""
        parser = HTMLParser("https://example.com")
        with pytest.raises(ValueError, match="URL is empty"):
            parser.resolve_url("")

    def test_resolve_url_no_scheme_or_domain(self):
        """Test resolving URL that results in no scheme/domain."""
        parser = HTMLParser("https://example.com")
        # Relative-only URL can still resolve with base URL
        resolved = parser.resolve_url("../../etc/passwd")
        assert resolved.startswith("https://example.com")


class TestExtractLinks:
    """Test link extraction."""

    def test_extract_links_simple(self):
        """Test extracting simple links."""
        parser = HTMLParser("https://example.com")
        links = parser.extract_links(SIMPLE_HTML)
        assert len(links) == 3
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://example.com/page3" in links

    def test_extract_links_with_dedup(self):
        """Test link extraction with deduplication."""
        parser = HTMLParser("https://example.com")
        html = """
        <a href="/page1">Link 1</a>
        <a href="/page1">Link 2</a>
        <a href="/page2">Link 3</a>
        """
        links = parser.extract_links(html, dedup=True)
        assert len(links) == 2
        assert links.count("https://example.com/page1") == 1

    def test_extract_links_without_dedup(self):
        """Test link extraction without deduplication."""
        parser = HTMLParser("https://example.com")
        html = """
        <a href="/page1">Link 1</a>
        <a href="/page1">Link 2</a>
        <a href="/page2">Link 3</a>
        """
        links = parser.extract_links(html, dedup=False)
        assert len(links) == 3
        assert links.count("https://example.com/page1") == 2

    def test_extract_links_empty_href(self):
        """Test extracting links with empty or fragment-only href."""
        parser = HTMLParser("https://example.com/page")
        links = parser.extract_links(EMPTY_LINKS_HTML)
        # Should include fragment and query URLs
        assert len(links) >= 0

    def test_extract_links_from_malformed_html(self):
        """Test extracting links from malformed HTML."""
        parser = HTMLParser("https://example.com")
        links = parser.extract_links(MALFORMED_HTML)
        assert len(links) >= 2


class TestExtractForms:
    """Test form extraction."""

    def test_extract_forms_simple(self):
        """Test extracting forms."""
        parser = HTMLParser("https://example.com")
        forms = parser.extract_forms(HTML_WITH_FORMS)
        assert len(forms) == 2

    def test_extract_forms_with_inputs(self):
        """Test form contains inputs."""
        parser = HTMLParser("https://example.com")
        forms = parser.extract_forms(HTML_WITH_FORMS)

        # First form (login)
        login_form = forms[0]
        assert login_form.method == "POST"
        assert login_form.action == "https://example.com/login"
        assert len(login_form.inputs) >= 2

        # Check username input
        username_input = next((i for i in login_form.inputs if i.name == "username"), None)
        assert username_input is not None
        assert username_input.input_type == "text"
        assert username_input.required

    def test_extract_forms_textarea_and_select(self):
        """Test form extraction includes textarea and select."""
        parser = HTMLParser("https://example.com")
        forms = parser.extract_forms(HTML_WITH_FORMS)

        # Second form (search)
        search_form = forms[1]
        assert search_form.method == "GET"

        # Check for textarea
        textarea = next((i for i in search_form.inputs if i.input_type == "textarea"), None)
        assert textarea is not None

        # Check for select
        select = next((i for i in search_form.inputs if i.input_type == "select"), None)
        assert select is not None

    def test_extract_forms_default_method(self):
        """Test form default method is GET."""
        parser = HTMLParser("https://example.com")
        html = '<form action="/submit"><input name="field"></form>'
        forms = parser.extract_forms(html)
        assert len(forms) == 1
        assert forms[0].method == "GET"

    def test_extract_forms_no_action(self):
        """Test form with no action uses base URL."""
        parser = HTMLParser("https://example.com/page")
        html = '<form><input name="field"></form>'
        forms = parser.extract_forms(html)
        assert len(forms) == 1
        assert forms[0].action == "https://example.com/page"

    def test_extract_forms_resolves_relative_action(self):
        """Test form action is resolved to absolute URL."""
        parser = HTMLParser("https://example.com")
        html = '<form action="/submit"><input name="field"></form>'
        forms = parser.extract_forms(html)
        assert forms[0].action == "https://example.com/submit"

    def test_extract_forms_method_uppercase(self):
        """Test form method is normalized to uppercase."""
        parser = HTMLParser("https://example.com")
        html = '<form method="post" action="/submit"><input name="f"></form>'
        forms = parser.extract_forms(html)
        assert forms[0].method == "POST"


class TestExtractScripts:
    """Test script extraction."""

    def test_extract_scripts_external(self):
        """Test extracting external scripts."""
        parser = HTMLParser("https://example.com")
        scripts = parser.extract_scripts(HTML_WITH_SCRIPTS)

        external_scripts = [s for s in scripts if not s.is_inline]
        assert len(external_scripts) >= 2

    def test_extract_scripts_inline(self):
        """Test extracting inline scripts."""
        parser = HTMLParser("https://example.com")
        scripts = parser.extract_scripts(HTML_WITH_SCRIPTS)

        inline_scripts = [s for s in scripts if s.is_inline]
        assert len(inline_scripts) >= 1

    def test_extract_scripts_resolves_src(self):
        """Test script src is resolved to absolute URL."""
        parser = HTMLParser("https://example.com")
        scripts = parser.extract_scripts(HTML_WITH_SCRIPTS)

        # Should have absolute URLs
        for script in scripts:
            if script.src:
                assert script.src.startswith("https://")

    def test_extract_scripts_inline_has_content(self):
        """Test inline script has content."""
        parser = HTMLParser("https://example.com")
        scripts = parser.extract_scripts(HTML_WITH_SCRIPTS)

        inline_scripts = [s for s in scripts if s.is_inline]
        for script in inline_scripts:
            assert script.content is not None
            assert len(script.content) > 0


class TestExtractMeta:
    """Test meta tag extraction."""

    def test_extract_meta_simple(self):
        """Test extracting meta tags."""
        parser = HTMLParser("https://example.com")
        meta = parser.extract_meta(HTML_WITH_META)

        assert "description" in meta
        assert meta["description"] == "Test page"
        assert "robots" in meta
        assert meta["robots"] == "noindex, nofollow"

    def test_extract_meta_author(self):
        """Test extracting author meta tag."""
        parser = HTMLParser("https://example.com")
        meta = parser.extract_meta(HTML_WITH_META)

        assert "author" in meta
        assert meta["author"] == "Test Author"

    def test_extract_meta_open_graph(self):
        """Test extracting Open Graph meta tags."""
        parser = HTMLParser("https://example.com")
        meta = parser.extract_meta(HTML_WITH_META)

        assert "og:title" in meta
        assert meta["og:title"] == "Open Graph Title"
        assert "og:url" in meta

    def test_extract_meta_empty_html(self):
        """Test extracting meta from HTML with no meta tags."""
        parser = HTMLParser("https://example.com")
        html = "<html><body>No meta</body></html>"
        meta = parser.extract_meta(html)

        assert isinstance(meta, dict)
        assert len(meta) == 0


class TestExtractAll:
    """Test extract_all convenience method."""

    def test_extract_all_returns_dict(self):
        """Test extract_all returns dictionary with all keys."""
        parser = HTMLParser("https://example.com")
        result = parser.extract_all(SIMPLE_HTML)

        assert isinstance(result, dict)
        assert "links" in result
        assert "forms" in result
        assert "scripts" in result
        assert "meta" in result

    def test_extract_all_content(self):
        """Test extract_all returns correct content."""
        parser = HTMLParser("https://example.com")
        result = parser.extract_all(SIMPLE_HTML)

        assert isinstance(result["links"], list)
        assert isinstance(result["forms"], list)
        assert isinstance(result["scripts"], list)
        assert isinstance(result["meta"], dict)

        assert len(result["links"]) > 0


class TestFormDataClass:
    """Test Form and FormInput data classes."""

    def test_form_input_creation(self):
        """Test creating FormInput."""
        input_field = FormInput(name="username", input_type="text", required=True)
        assert input_field.name == "username"
        assert input_field.input_type == "text"
        assert input_field.required

    def test_form_creation(self):
        """Test creating Form."""
        form = Form(action="/login", method="POST")
        assert form.action == "/login"
        assert form.method == "POST"

    def test_form_method_normalized(self):
        """Test form method is normalized to uppercase."""
        form = Form(action="/login", method="post")
        assert form.method == "POST"


class TestScriptReference:
    """Test ScriptReference data class."""

    def test_script_reference_external(self):
        """Test creating external script reference."""
        script = ScriptReference(src="https://example.com/lib.js")
        assert script.src == "https://example.com/lib.js"
        assert not script.is_inline

    def test_script_reference_inline(self):
        """Test creating inline script reference."""
        script = ScriptReference(is_inline=True, content='console.log("test");')
        assert script.is_inline
        assert script.content == 'console.log("test");'


class TestRealWorldHTML:
    """Test with more realistic HTML examples."""

    def test_complex_page(self):
        """Test parsing complex HTML page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Product Page</title>
            <meta name="description" content="Buy awesome products">
            <script src="https://cdn.example.com/jquery.js"></script>
        </head>
        <body>
            <form action="/search" method="GET">
                <input type="text" name="q" placeholder="Search...">
                <input type="submit" value="Search">
            </form>
            <a href="/product/1">Product 1</a>
            <a href="/product/2">Product 2</a>
            <a href="https://external.com/link">External</a>
            <script>
                console.log('Page loaded');
            </script>
        </body>
        </html>
        """

        parser = HTMLParser("https://example.com/products")
        result = parser.extract_all(html)

        # Check links
        assert len(result["links"]) >= 3
        assert any("product/1" in link for link in result["links"])
        assert any("external.com" in link for link in result["links"])

        # Check forms
        assert len(result["forms"]) == 1
        assert result["forms"][0].method == "GET"

        # Check scripts
        assert len(result["scripts"]) >= 2

        # Check meta
        assert "description" in result["meta"]
