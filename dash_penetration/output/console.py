"""
Console output formatter for human-readable crawl results display.
"""

from typing import List, Dict, Any
from dash_penetration.crawler.models import CrawlResult, Endpoint


class ConsoleFormatter:
    """Formats crawl results for console display with colored output."""

    # Color codes for terminal output
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @staticmethod
    def _get_status_color(status_code: int) -> str:
        """Get color for HTTP status code."""
        if 200 <= status_code < 300:
            return ConsoleFormatter.GREEN
        elif 300 <= status_code < 400:
            return ConsoleFormatter.CYAN
        elif 400 <= status_code < 500:
            return ConsoleFormatter.YELLOW
        else:
            return ConsoleFormatter.RED

    @staticmethod
    def format_endpoints(endpoints: Dict[str, Endpoint]) -> str:
        """
        Format endpoints as a human-readable table.

        Args:
            endpoints: Dictionary of endpoints from CrawlResult

        Returns:
            Formatted table string
        """
        if not endpoints:
            return "No endpoints discovered."

        lines = []
        lines.append("")
        lines.append(f"{ConsoleFormatter.BOLD}Discovered Endpoints:{ConsoleFormatter.RESET}")
        lines.append("-" * 120)

        # Header
        header = f"{'METHOD':<8} {'PATH':<50} {'STATUS':<8} {'CONTENT-TYPE':<25} {'FORMS':<6} {'LINKS':<6} {'API':<5}"
        lines.append(ConsoleFormatter.BOLD + header + ConsoleFormatter.RESET)
        lines.append("-" * 120)

        # Rows
        for key, endpoint in sorted(endpoints.items()):
            method = endpoint.method.value
            path = endpoint.path[:49]  # Truncate long paths
            status = endpoint.status_code
            content_type = endpoint.content_type[:24]
            forms = len(endpoint.forms)
            links = len(endpoint.links)
            api_flag = "YES" if endpoint.is_api else "NO"

            # Color the status code
            status_color = ConsoleFormatter._get_status_color(status)
            status_str = f"{status_color}{status}{ConsoleFormatter.RESET}"

            # Color the method
            method_color = ConsoleFormatter.BLUE
            method_str = f"{method_color}{method:<8}{ConsoleFormatter.RESET}"

            row = f"{method_str} {path:<50} {status_str:<20} {content_type:<25} {forms:<6} {links:<6} {api_flag:<5}"
            lines.append(row)

        lines.append("-" * 120)
        return "\n".join(lines)

    @staticmethod
    def format_crawl_summary(result: CrawlResult) -> str:
        """
        Format crawl summary statistics.

        Args:
            result: CrawlResult object

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("")
        lines.append(f"{ConsoleFormatter.BOLD}Crawl Summary:{ConsoleFormatter.RESET}")
        lines.append("-" * 60)

        lines.append(f"Target URL:       {ConsoleFormatter.CYAN}{result.target_url}{ConsoleFormatter.RESET}")
        lines.append(f"Scope Domains:    {', '.join(result.scope_domains)}")
        lines.append(f"Pages Crawled:    {ConsoleFormatter.GREEN}{result.pages_crawled}{ConsoleFormatter.RESET}")
        lines.append(f"Unique Endpoints: {ConsoleFormatter.GREEN}{len(result.endpoints)}{ConsoleFormatter.RESET}")

        # Count by status
        status_counts: Dict[int, int] = {}
        for endpoint in result.endpoints.values():
            status = endpoint.status_code
            status_counts[status] = status_counts.get(status, 0) + 1

        if status_counts:
            lines.append("")
            lines.append("Status Code Distribution:")
            for status in sorted(status_counts.keys()):
                count = status_counts[status]
                color = ConsoleFormatter._get_status_color(status)
                lines.append(f"  {color}{status}{ConsoleFormatter.RESET}: {count}")

        # Count by method
        method_counts: Dict[str, int] = {}
        for endpoint in result.endpoints.values():
            method = endpoint.method.value
            method_counts[method] = method_counts.get(method, 0) + 1

        if method_counts:
            lines.append("")
            lines.append("HTTP Methods:")
            for method in sorted(method_counts.keys()):
                count = method_counts[method]
                lines.append(f"  {method}: {count}")

        # API Detection
        api_count = sum(1 for e in result.endpoints.values() if e.is_api)
        if api_count > 0:
            lines.append("")
            lines.append(f"API Endpoints:    {ConsoleFormatter.YELLOW}{api_count}{ConsoleFormatter.RESET}")

        # Forms & Scripts
        forms_count = sum(len(e.forms) for e in result.endpoints.values())
        scripts_count = sum(len(e.scripts) for e in result.endpoints.values())
        if forms_count > 0 or scripts_count > 0:
            lines.append("")
            if forms_count > 0:
                lines.append(f"Forms Found:      {ConsoleFormatter.YELLOW}{forms_count}{ConsoleFormatter.RESET}")
            if scripts_count > 0:
                lines.append(f"Scripts Found:    {ConsoleFormatter.YELLOW}{scripts_count}{ConsoleFormatter.RESET}")

        # Timing
        if result.start_time and result.end_time:
            duration = (result.end_time - result.start_time).total_seconds()
            lines.append("")
            lines.append(f"Crawl Duration:   {duration:.2f} seconds")

        if result.errors:
            lines.append("")
            lines.append(f"{ConsoleFormatter.RED}Errors ({len(result.errors)}):{ConsoleFormatter.RESET}")
            for error in result.errors[:5]:  # Show first 5 errors
                lines.append(f"  • {error}")
            if len(result.errors) > 5:
                lines.append(f"  ... and {len(result.errors) - 5} more")

        lines.append("-" * 60)
        return "\n".join(lines)

    @staticmethod
    def format_full_report(result: CrawlResult) -> str:
        """
        Format complete crawl report with summary and endpoints.

        Args:
            result: CrawlResult object

        Returns:
            Formatted full report string
        """
        output = []
        output.append(ConsoleFormatter.format_crawl_summary(result))
        output.append(ConsoleFormatter.format_endpoints(result.endpoints))
        return "\n".join(output)
