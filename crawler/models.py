"""
Data models for crawling results and endpoint discovery.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class DiscoverySource(str, Enum):
    """Source of URL discovery."""

    INITIAL = "initial"
    LINK = "link"
    FORM = "form"
    SCRIPT = "script"
    REDIRECT = "redirect"
    API = "api"


@dataclass
class Page:
    """Represents a crawled page."""

    url: str
    method: HTTPMethod
    status_code: int
    content_type: str
    headers: Dict[str, str]
    timestamp: datetime
    discovered_by: DiscoverySource
    content_length: Optional[int] = None
    redirected_to: Optional[str] = None

    def __post_init__(self):
        """Validate Page after initialization."""
        if not isinstance(self.method, HTTPMethod):
            self.method = HTTPMethod(self.method.upper())

        if not isinstance(self.discovered_by, DiscoverySource):
            self.discovered_by = DiscoverySource(self.discovered_by.lower())

        if not (100 <= self.status_code < 600):
            raise ValueError(f"Invalid HTTP status code: {self.status_code}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["method"] = self.method.value
        data["discovered_by"] = self.discovered_by.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Page":
        """Create Page from dictionary."""
        data = data.copy()
        data["method"] = HTTPMethod(data["method"])
        data["discovered_by"] = DiscoverySource(data["discovered_by"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class FormField:
    """Represents a form field."""

    name: str
    field_type: str
    value: Optional[str] = None
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormField":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Form:
    """Represents an HTML form."""

    action: str
    method: HTTPMethod
    fields: List[FormField]
    name: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self):
        """Validate Form after initialization."""
        if not isinstance(self.method, HTTPMethod):
            self.method = HTTPMethod(self.method.upper())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action,
            "method": self.method.value,
            "name": self.name,
            "id": self.id,
            "fields": [f.to_dict() for f in self.fields],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Form":
        """Create from dictionary."""
        data = data.copy()
        data["method"] = HTTPMethod(data["method"])
        data["fields"] = [FormField.from_dict(f) for f in data.get("fields", [])]
        return cls(**data)


@dataclass
class Endpoint:
    """Represents a discovered endpoint."""

    method: HTTPMethod
    path: str
    status_code: int
    content_type: str
    forms: List[Form] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    is_api: bool = False
    discovered_count: int = 1

    def __post_init__(self):
        """Validate Endpoint after initialization."""
        if not isinstance(self.method, HTTPMethod):
            self.method = HTTPMethod(self.method.upper())

        if not (100 <= self.status_code < 600):
            raise ValueError(f"Invalid HTTP status code: {self.status_code}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "method": self.method.value,
            "path": self.path,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "forms": [f.to_dict() for f in self.forms],
            "links": self.links,
            "scripts": self.scripts,
            "is_api": self.is_api,
            "discovered_count": self.discovered_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Endpoint":
        """Create Endpoint from dictionary."""
        data = data.copy()
        data["method"] = HTTPMethod(data["method"])
        data["forms"] = [Form.from_dict(f) for f in data.get("forms", [])]
        return cls(**data)


@dataclass
class CrawlResult:
    """Represents the complete results of a crawl."""

    target_url: str
    scope_domains: List[str]
    endpoints: Dict[str, Endpoint] = field(default_factory=dict)
    pages_crawled: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    def add_endpoint(self, endpoint: Endpoint) -> None:
        """Add or update an endpoint."""
        key = f"{endpoint.method.value}:{endpoint.path}"
        if key in self.endpoints:
            # Merge with existing endpoint
            existing = self.endpoints[key]
            existing.discovered_count += 1
            existing.forms.extend(endpoint.forms)
            existing.links = list(set(existing.links + endpoint.links))
            existing.scripts = list(set(existing.scripts + endpoint.scripts))
        else:
            self.endpoints[key] = endpoint

    def get_endpoint_summary(self) -> List[Dict[str, Any]]:
        """Get a list of all endpoints for display/export."""
        summary = []
        for key, endpoint in sorted(self.endpoints.items()):
            summary.append(
                {
                    "method": endpoint.method.value,
                    "path": endpoint.path,
                    "status": endpoint.status_code,
                    "content_type": endpoint.content_type,
                    "forms_count": len(endpoint.forms),
                    "links_count": len(endpoint.links),
                    "scripts_count": len(endpoint.scripts),
                    "is_api": endpoint.is_api,
                }
            )
        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "target_url": self.target_url,
            "scope_domains": self.scope_domains,
            "endpoints": {k: v.to_dict() for k, v in self.endpoints.items()},
            "pages_crawled": self.pages_crawled,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrawlResult":
        """Create CrawlResult from dictionary."""
        data = data.copy()
        data["endpoints"] = {
            k: Endpoint.from_dict(v) for k, v in data.get("endpoints", {}).items()
        }
        if data.get("start_time"):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        return cls(**data)
