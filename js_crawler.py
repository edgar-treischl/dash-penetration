#!/usr/bin/env python3
"""
JavaScript-enabled crawler using Playwright
Discovers content rendered client-side by frameworks like React, Vue, Dash
"""

import asyncio
from playwright.async_api import async_playwright
from dash_penetration.crawler.parser import HTMLParser
from dash_penetration.discovery.links import LinkDiscovery
from dash_penetration.discovery.forms import FormDiscovery
from dash_penetration.crawler.scope import Scope


async def crawl_with_js(url: str, wait_time: int = 3000):
    """
    Crawl a URL with JavaScript rendering enabled

    Args:
        url: Target URL
        wait_time: Time to wait for JS to render (milliseconds)
    """
    print("=" * 80)
    print(f"🔧 JAVASCRIPT-ENABLED CRAWL")
    print("=" * 80)
    print(f"Target: {url}")
    print(f"Wait time: {wait_time}ms")
    print()

    async with async_playwright() as p:
        # Launch browser
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Track network requests
        requests = []

        def handle_request(request):
            requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                }
            )

        page.on("request", handle_request)

        # Navigate and wait for network to be idle
        print(f"📡 Fetching {url}...")
        await page.goto(url, wait_until="networkidle")

        # Wait additional time for dynamic content
        await page.wait_for_timeout(wait_time)

        # Get the rendered HTML
        html_content = await page.content()

        print(f"✅ Page loaded! ({len(html_content)} bytes)")
        print()

        # Parse with our existing parser
        print("🔍 ANALYZING RENDERED CONTENT")
        print("=" * 80)

        parser = HTMLParser(url)

        # Extract all content
        links = parser.extract_links(html_content)
        forms = parser.extract_forms(html_content)
        scripts = parser.extract_scripts(html_content)

        print(f"\n📊 DISCOVERY RESULTS:")
        print(f"  Links found: {len(links)}")
        print(f"  Forms found: {len(forms)}")
        print(f"  Scripts found: {len(scripts)}")

        # Show links
        if links:
            print(f"\n🔗 LINKS ({len(links)}):")
            scope = Scope(allowed_domains=[url.split("/")[2]])
            link_discovery = LinkDiscovery(url, scope)
            link_result = link_discovery.analyze(links)

            print(f"  Internal: {len(link_result.internal_links)}")
            for link in sorted(link_result.internal_links)[:20]:
                print(f"    → {link}")
            if len(link_result.internal_links) > 20:
                print(f"    ... and {len(link_result.internal_links) - 20} more")

            if link_result.external_links:
                print(f"  External: {len(link_result.external_links)}")
                for link in sorted(link_result.external_links)[:5]:
                    print(f"    → {link}")

        # Show forms
        if forms:
            print(f"\n📝 FORMS ({len(forms)}):")
            form_discovery = FormDiscovery()
            form_result = form_discovery.analyze(forms)

            for i, form_ep in enumerate(form_result.forms, 1):
                print(f"\n  Form #{i}:")
                print(f"    Action: {form_ep.action}")
                print(f"    Method: {form_ep.method}")
                print(f"    Fields: {len(form_ep.fields)}")

                for field in form_ep.fields:
                    req = " (required)" if field.required else ""
                    print(f"      • {field.name} [{field.field_type}]{req}")

        # Show network requests (potential API endpoints)
        print(f"\n🌐 NETWORK REQUESTS ({len(requests)}):")

        # Group by type
        api_requests = [r for r in requests if r["resource_type"] in ["xhr", "fetch"]]
        if api_requests:
            print(f"\n  ⚠️  XHR/Fetch requests (potential API endpoints):")
            seen = set()
            for req in api_requests:
                if req["url"] not in seen:
                    print(f"    {req['method']} {req['url']}")
                    seen.add(req["url"])

        # Show HTML structure
        print(f"\n📄 PAGE STRUCTURE:")

        # Count interactive elements
        buttons = await page.query_selector_all("button")
        inputs = await page.query_selector_all("input")
        textareas = await page.query_selector_all("textarea")
        selects = await page.query_selector_all("select")

        print(f"  Buttons: {len(buttons)}")
        print(f"  Input fields: {len(inputs)}")
        print(f"  Text areas: {len(textareas)}")
        print(f"  Select boxes: {len(selects)}")

        # Get page title
        title = await page.title()
        print(f"  Page title: {title}")

        # Check for specific elements
        print(f"\n🎯 INTERACTIVE ELEMENTS:")

        # Get button texts
        if buttons:
            print(f"  Buttons found:")
            for btn in buttons[:10]:
                text = await btn.inner_text()
                if text.strip():
                    print(f"    → {text.strip()}")

        # Get input names
        if inputs:
            print(f"  Input fields:")
            for inp in inputs[:10]:
                name = await inp.get_attribute("name")
                type_attr = await inp.get_attribute("type")
                placeholder = await inp.get_attribute("placeholder")
                if name or placeholder:
                    print(
                        f"    → {name or 'unnamed'} [{type_attr}] {f'({placeholder})' if placeholder else ''}"
                    )

        await browser.close()

        print(f"\n{'='*80}")
        print("✅ JavaScript crawl complete!")
        print("=" * 80)


if __name__ == "__main__":
    import sys

    url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://edgar-treischl.pages.gitlab.lrz.de/dash-demo/"
    )
    asyncio.run(crawl_with_js(url))
