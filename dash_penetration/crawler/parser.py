"""
HTML parser for web crawler.

Extracts links, forms, scripts, and meta information from HTML using selectolax.
"""

from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import logging

from selectolax.parser import HTMLParser as SelectolaxParser

logger = logging.getLogger(__name__)


@dataclass
class FormInput:
    """Represents a form input field."""

    name: str
    input_type: str = "text"
    value: Optional[str] = None
    required: bool = False


@dataclass
class Form:
    """Represents an HTML form."""

    action: str
    method: str = "GET"
    inputs: list[FormInput] = field(default_factory=list)

    def __post_init__(self):
        """Normalize method to uppercase."""
        self.method = self.method.upper()


@dataclass
class ScriptReference:
    """Represents a script reference (external or inline)."""

    src: Optional[str] = None
    is_inline: bool = False
    content: Optional[str] = None


class HTMLParser:
    """
    HTML parser for extracting links, forms, scripts, and meta information.

    Uses selectolax for fast HTML parsing and extraction.
    """

    def __init__(self, base_url: str):
        """
        Initialize HTMLParser.

        Args:
            base_url: Base URL for resolving relative URLs
        """
        self.base_url = base_url

    def parse(self, html: str) -> SelectolaxParser:
        """
        Parse HTML content.

        Args:
            html: HTML content to parse

        Returns:
            Parsed HTML document (selectolax HTMLParser)

        Raises:
            ValueError: If HTML is empty or invalid
        """
        if not html or not html.strip():
            raise ValueError("HTML content is empty")

        try:
            return SelectolaxParser(html)
        except Exception as e:
            raise ValueError(f"Failed to parse HTML: {e}") from e

    def resolve_url(self, url: str) -> str:
        """
        Resolve a relative or absolute URL to absolute URL.

        Args:
            url: URL to resolve (relative or absolute)

        Returns:
            Absolute URL

        Raises:
            ValueError: If URL is invalid or cannot be resolved
        """
        if not url or not url.strip():
            raise ValueError("URL is empty")

        url = url.strip()

        # Handle URLs with only fragments or query params
        if url.startswith("#"):
            return self.base_url
        if url.startswith("?"):
            return self.base_url + url

        try:
            # Resolve relative to absolute
            resolved = urljoin(self.base_url, url)

            # Validate the resolved URL
            parsed = urlparse(resolved)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL after resolution: {resolved}")

            return resolved
        except Exception as e:
            raise ValueError(f"Failed to resolve URL '{url}': {e}") from e

    def extract_links(self, html: str, dedup: bool = True) -> list[str]:
        """
        Extract all links from HTML.

        Args:
            html: HTML content to parse
            dedup: Remove duplicate URLs (default True)

        Returns:
            List of absolute URLs

        Raises:
            ValueError: If HTML cannot be parsed
        """
        doc = self.parse(html)
        urls = []

        # Extract href from <a> tags
        for link in doc.css("a"):
            href = link.attributes.get("href")
            if href:
                try:
                    resolved = self.resolve_url(href)
                    urls.append(resolved)
                except ValueError:
                    # Skip invalid URLs
                    pass

        # Deduplicate if requested
        if dedup:
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            return unique_urls

        return urls

    def extract_forms(self, html: str) -> list[Form]:
        """
        Extract all forms from HTML.

        Args:
            html: HTML content to parse

        Returns:
            List of Form objects with action, method, and inputs

        Raises:
            ValueError: If HTML cannot be parsed
        """
        doc = self.parse(html)
        forms = []

        for form_elem in doc.css("form"):
            action = form_elem.attributes.get("action", "")
            method = form_elem.attributes.get("method", "GET")

            # Resolve form action to absolute URL
            try:
                if action:
                    action = self.resolve_url(action)
                else:
                    action = self.base_url
            except ValueError:
                # If action cannot be resolved, use base URL
                action = self.base_url

            # Extract form inputs
            inputs = []
            for input_elem in form_elem.css("input"):
                name = input_elem.attributes.get("name", "")
                if name:
                    input_type = input_elem.attributes.get("type", "text")
                    value = input_elem.attributes.get("value")
                    required = "required" in input_elem.attributes

                    inputs.append(
                        FormInput(
                            name=name,
                            input_type=input_type,
                            value=value,
                            required=required,
                        )
                    )

            # Extract textarea
            for textarea_elem in form_elem.css("textarea"):
                name = textarea_elem.attributes.get("name", "")
                if name:
                    required = "required" in textarea_elem.attributes
                    inputs.append(
                        FormInput(
                            name=name,
                            input_type="textarea",
                            required=required,
                        )
                    )

            # Extract select
            for select_elem in form_elem.css("select"):
                name = select_elem.attributes.get("name", "")
                if name:
                    required = "required" in select_elem.attributes
                    inputs.append(
                        FormInput(
                            name=name,
                            input_type="select",
                            required=required,
                        )
                    )

            if action:
                forms.append(Form(action=action, method=method, inputs=inputs))

        return forms

    def extract_scripts(self, html: str) -> list[ScriptReference]:
        """
        Extract all script references from HTML.

        Args:
            html: HTML content to parse

        Returns:
            List of ScriptReference objects (external or inline)

        Raises:
            ValueError: If HTML cannot be parsed
        """
        doc = self.parse(html)
        scripts = []

        for script_elem in doc.css("script"):
            src = script_elem.attributes.get("src")

            if src:
                # External script
                try:
                    resolved_src = self.resolve_url(src)
                    scripts.append(ScriptReference(src=resolved_src, is_inline=False))
                except ValueError:
                    # Skip invalid script URLs
                    pass
            else:
                # Inline script
                content = script_elem.text()
                if content and content.strip():
                    scripts.append(ScriptReference(is_inline=True, content=content.strip()))

        return scripts

    def extract_meta(self, html: str) -> dict[str, str]:
        """
        Extract meta tags from HTML.

        Args:
            html: HTML content to parse

        Returns:
            Dictionary mapping meta tag names to content values

        Raises:
            ValueError: If HTML cannot be parsed
        """
        doc = self.parse(html)
        meta_tags = {}

        for meta_elem in doc.css("meta"):
            name = meta_elem.attributes.get("name", "").lower()
            content = meta_elem.attributes.get("content", "")

            if name and content:
                meta_tags[name] = content

            # Also handle property attribute (Open Graph, etc.)
            prop = meta_elem.attributes.get("property", "").lower()
            if prop and content:
                meta_tags[prop] = content

        return meta_tags

    def extract_all(self, html: str) -> dict:
        """
        Extract all data from HTML (links, forms, scripts, meta).

        Args:
            html: HTML content to parse

        Returns:
            Dictionary with 'links', 'forms', 'scripts', 'meta' keys

        Raises:
            ValueError: If HTML cannot be parsed
        """
        return {
            "links": self.extract_links(html),
            "forms": self.extract_forms(html),
            "scripts": self.extract_scripts(html),
            "meta": self.extract_meta(html),
        }
