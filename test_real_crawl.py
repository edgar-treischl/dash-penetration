#!/usr/bin/env python3
"""
Test script for the web crawler using a real website.

This demonstrates the CrawlEngine in action with your website.
"""

import asyncio
import logging
from datetime import datetime
from dash_penetration.crawler import CrawlEngine, Scope
from dash_penetration.output.console import ConsoleFormatter
from dash_penetration.output.json import JSONFormatter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def crawl_website():
    """
    Crawl edgar-treischl.de and display results.

    This is a real-world test of the crawler engine.
    """
    # Configuration
    target_url = "https://edgar-treischl.de"
    
    # Define scope - extract domain from target URL
    scope = Scope(allowed_domains=["edgar-treischl.de"])
    
    print("\n" + "=" * 70)
    print("WEB CRAWLER TEST - Real Website Crawl")
    print("=" * 70)
    print(f"\n📍 Target: {target_url}")
    print(f"🔒 Scope: {scope.allowed_domains}")
    print(f"⏱️  Starting crawl at {datetime.now().strftime('%H:%M:%S')}")
    print("\n" + "-" * 70 + "\n")
    
    try:
        # Create engine with moderate settings for real-world crawling
        async with CrawlEngine(
            target_url=target_url,
            scope=scope,
            rate_limit=5.0,        # Conservative: 5 requests/second
            max_concurrency=3,     # Sequential-ish: 3 parallel
            timeout=15.0,          # Generous timeout
            verify_ssl=True        # Verify SSL in production
        ) as engine:
            # Run the crawl
            result = await engine.crawl()
            
            # Display results
            print("\n" + "=" * 70)
            print("CRAWL RESULTS")
            print("=" * 70)
            
            # Show summary
            summary = ConsoleFormatter.format_crawl_summary(result)
            print(summary)
            
            # Show endpoints table
            endpoints_table = ConsoleFormatter.format_endpoints(result.endpoints)
            print(endpoints_table)
            
            # Show errors if any
            if result.errors:
                print("\n" + "=" * 70)
                print("ERRORS ENCOUNTERED")
                print("=" * 70)
                for error in result.errors:
                    print(f"  ⚠️  {error}")
            
            # JSON export option
            print("\n" + "=" * 70)
            print("EXPORT OPTIONS")
            print("=" * 70)
            
            json_str = JSONFormatter.format_endpoints(result)
            print(f"✅ JSON export: {len(json_str)} characters")
            
            # Save to file
            output_file = f"crawl_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            JSONFormatter.save_to_file(result, output_file)
            print(f"💾 Results saved to: {output_file}")
            
            # Summary statistics
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"✅ Pages crawled: {result.pages_crawled}")
            print(f"✅ Unique endpoints: {len(result.endpoints)}")
            print(f"✅ Errors: {len(result.errors)}")
            
            if result.start_time and result.end_time:
                duration = (result.end_time - result.start_time).total_seconds()
                print(f"⏱️  Duration: {duration:.2f} seconds")
                print(f"📊 Rate: {result.pages_crawled / duration:.2f} pages/sec")
            
            return result
            
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Crawl error: {e}")
        logger.exception("Crawl failed")
        return None


async def test_with_custom_scope():
    """
    Example: Crawl with custom path restrictions.
    """
    target_url = "https://edgar-treischl.de"
    
    # More restrictive scope - only specific paths
    scope = Scope(
        allowed_domains=["edgar-treischl.de"],
        # allowed_paths=["/blog", "/projects"],  # Uncomment to restrict
        disallowed_paths=["/admin", "/api"]  # Exclude these
    )
    
    print("\n" + "=" * 70)
    print("TEST 2: Custom Scope Configuration")
    print("=" * 70)
    print(f"Domain: {scope.allowed_domains}")
    print(f"Disallowed paths: {scope.disallowed_paths}")
    
    async with CrawlEngine(
        target_url=target_url,
        scope=scope,
        rate_limit=3.0,
        max_concurrency=2
    ) as engine:
        result = await engine.crawl()
        print(f"\n✅ Crawled {result.pages_crawled} pages")
        print(f"✅ Found {len(result.endpoints)} unique endpoints")
        return result


async def test_stealth_mode():
    """
    Example: Slow, discrete crawling.
    """
    target_url = "https://edgar-treischl.de"
    scope = Scope(allowed_domains=["edgar-treischl.de"])
    
    print("\n" + "=" * 70)
    print("TEST 3: Stealth Mode (Slow Crawling)")
    print("=" * 70)
    print("Settings: 1 req/sec, sequential requests")
    
    async with CrawlEngine(
        target_url=target_url,
        scope=scope,
        rate_limit=1.0,         # 1 request per second
        max_concurrency=1       # Sequential
    ) as engine:
        result = await engine.crawl()
        print(f"\n✅ Crawled {result.pages_crawled} pages")
        print(f"✅ Found {len(result.endpoints)} unique endpoints")
        return result


async def main():
    """Run all tests."""
    print("\n" + "🔍 " * 20)
    print("\nWEB CRAWLER - REAL-WORLD TEST SUITE")
    print("\nTesting against: https://edgar-treischl.de")
    print("This will demonstrate the crawler engine capabilities")
    print("\n" + "🔍 " * 20)
    
    # Test 1: Standard crawl
    result1 = await crawl_website()
    
    # Optionally run additional tests
    # Uncomment to run:
    # result2 = await test_with_custom_scope()
    # result3 = await test_stealth_mode()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
    print("\n✨ Crawler engine is working correctly!")
    print("\nNext steps:")
    print("  1. Review the JSON output file for detailed results")
    print("  2. Implement CLI wrapper (Step 10)")
    print("  3. Add more analysis plugins (Step 11)")


if __name__ == "__main__":
    asyncio.run(main())
