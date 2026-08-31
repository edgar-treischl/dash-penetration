import asyncio
from dash_penetration.crawler.engine import CrawlEngine
from dash_penetration.crawler.scope import Scope

async def test_docs_site():
    """Test crawler against a link-heavy site"""
    scope = Scope(allowed_domains=["httpbin.org"])
    
    async with CrawlEngine(
        target_url="https://httpbin.org/",
        scope=scope,
        max_concurrency=3,
        rate_limit=2.0,
        timeout=10
    ) as engine:
        result = await engine.crawl()
    
    print("=" * 60)
    print("VALIDATION TEST: httpbin.org")
    print("=" * 60)
    print(f"Pages crawled: {result['pages_crawled']}")
    print(f"Endpoints found: {len(result['endpoints'])}")
    print()
    
    if result['endpoints']:
        print("Discovered Endpoints:")
        for endpoint_key, endpoint_data in list(result['endpoints'].items())[:10]:
            status = endpoint_data.get('status_code', '?')
            content_type = endpoint_data.get('content_type', '?')
            print(f"  {endpoint_key:40} | {status:3} | {content_type}")
            
            if endpoint_data.get('links'):
                print(f"    └─ Found {len(endpoint_data['links'])} links")
            if endpoint_data.get('forms'):
                print(f"    └─ Found {len(endpoint_data['forms'])} forms")
    
    if result.get('errors'):
        print(f"\nErrors encountered: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(test_docs_site())
