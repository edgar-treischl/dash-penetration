"""
JSON output formatter for crawl results serialization and deserialization.
"""

import json
from typing import Dict, Any
from pathlib import Path
from dash_penetration.crawler.models import CrawlResult


class JSONFormatter:
    """Handles JSON serialization and deserialization of crawl results."""

    @staticmethod
    def format_endpoints(result: CrawlResult, indent: int = 2) -> str:
        """
        Format endpoints as JSON string.

        Args:
            result: CrawlResult object
            indent: JSON indentation level (None for compact)

        Returns:
            JSON formatted string of endpoints
        """
        endpoints_data = {}
        for key, endpoint in result.endpoints.items():
            endpoints_data[key] = endpoint.to_dict()

        return json.dumps(endpoints_data, indent=indent)

    @staticmethod
    def format_crawl_result(result: CrawlResult, indent: int = 2) -> str:
        """
        Format complete crawl result as JSON string.

        Args:
            result: CrawlResult object
            indent: JSON indentation level (None for compact)

        Returns:
            JSON formatted string
        """
        return json.dumps(result.to_dict(), indent=indent)

    @staticmethod
    def save_to_file(result: CrawlResult, filename: str) -> None:
        """
        Save crawl result to a JSON file.

        Args:
            result: CrawlResult object to save
            filename: Path to output JSON file

        Raises:
            IOError: If file cannot be written
            ValueError: If filename is invalid
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        filepath = Path(filename)

        # Create parent directories if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

    @staticmethod
    def load_from_file(filename: str) -> CrawlResult:
        """
        Load crawl result from a JSON file.

        Args:
            filename: Path to JSON file

        Returns:
            CrawlResult object

        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If file is not valid JSON
            ValueError: If JSON data is invalid for CrawlResult
        """
        filepath = Path(filename)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return CrawlResult.from_dict(data)

    @staticmethod
    def validate_json_file(filename: str) -> bool:
        """
        Validate that a file contains valid JSON and can be loaded as CrawlResult.

        Args:
            filename: Path to JSON file

        Returns:
            True if valid, False otherwise
        """
        try:
            JSONFormatter.load_from_file(filename)
            return True
        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
            return False

    @staticmethod
    def get_file_summary(filename: str) -> Dict[str, Any]:
        """
        Get a quick summary of a crawl result file without loading everything.

        Args:
            filename: Path to JSON file

        Returns:
            Dictionary with file summary (target_url, endpoint_count, etc.)

        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If file is not valid JSON
        """
        filepath = Path(filename)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "target_url": data.get("target_url", "unknown"),
            "scope_domains": data.get("scope_domains", []),
            "endpoint_count": len(data.get("endpoints", {})),
            "pages_crawled": data.get("pages_crawled", 0),
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
            "error_count": len(data.get("errors", [])),
        }
