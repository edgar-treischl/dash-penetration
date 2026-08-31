"""
Form discovery plugin for analyzing web forms.

Extracts form metadata and parameters:
- Form endpoints (action URLs)
- HTTP methods (GET/POST)
- Input field types and names
- Required vs optional fields
- Form validation rules

Useful for identifying data input surfaces during reconnaissance.
"""

from dataclasses import dataclass, field
from typing import Sequence

from dash_penetration.crawler.parser import Form


@dataclass
class FormField:
    """Metadata about a form input field."""

    name: str
    """Field name attribute."""

    field_type: str = "text"
    """HTML input type (text, password, email, etc.)."""

    required: bool = False
    """Whether field is marked as required."""

    value: str = ""
    """Default or preset value."""


@dataclass
class FormDiscoveryResult:
    """Result of form discovery analysis."""

    forms: list["FormEndpoint"] = field(default_factory=list)
    """List of discovered forms."""

    total_forms: int = 0
    """Count of total forms discovered."""

    get_forms: int = 0
    """Count of GET method forms."""

    post_forms: int = 0
    """Count of POST method forms."""

    required_fields: int = 0
    """Total count of required fields across all forms."""

    optional_fields: int = 0
    """Total count of optional fields across all forms."""

    def get_endpoints(self) -> list[str]:
        """Return list of unique form action endpoints."""
        return sorted({f.action for f in self.forms if f.action})

    def get_by_method(self, method: str) -> list["FormEndpoint"]:
        """Get forms filtered by HTTP method."""
        return [f for f in self.forms if f.method.upper() == method.upper()]

    def to_dict(self) -> dict:
        """Export result as dictionary."""
        return {
            "total_forms": self.total_forms,
            "get_forms": self.get_forms,
            "post_forms": self.post_forms,
            "endpoints": self.get_endpoints(),
            "field_summary": {
                "required": self.required_fields,
                "optional": self.optional_fields,
            },
            "forms": [f.to_dict() for f in self.forms],
        }


@dataclass
class FormEndpoint:
    """Metadata about a discovered form."""

    action: str
    """Form action URL (target endpoint)."""

    method: str = "GET"
    """HTTP method (GET, POST, etc.)."""

    fields: list[FormField] = field(default_factory=list)
    """List of form input fields."""

    def field_count(self) -> int:
        """Return total count of fields."""
        return len(self.fields)

    def required_count(self) -> int:
        """Return count of required fields."""
        return sum(1 for f in self.fields if f.required)

    def optional_count(self) -> int:
        """Return count of optional fields."""
        return len(self.fields) - self.required_count()

    def get_field_names(self) -> list[str]:
        """Return list of field names."""
        return [f.name for f in self.fields if f.name]

    def to_dict(self) -> dict:
        """Export form as dictionary."""
        return {
            "action": self.action,
            "method": self.method,
            "field_count": self.field_count(),
            "required_fields": self.required_count(),
            "optional_fields": self.optional_count(),
            "fields": [
                {
                    "name": f.name,
                    "type": f.field_type,
                    "required": f.required,
                }
                for f in self.fields
            ],
        }


class FormDiscovery:
    """
    Analyzes forms discovered during crawling.

    Extracts form actions, methods, fields, and metadata to identify
    potential data entry points for security testing.
    """

    def __init__(self):
        """Initialize FormDiscovery."""
        pass

    def analyze(self, forms: Sequence[Form]) -> FormDiscoveryResult:
        """
        Analyze a list of Form objects from parser.

        Args:
            forms: Sequence of Form objects from HTMLParser

        Returns:
            FormDiscoveryResult with form metadata and statistics
        """
        if not forms:
            return FormDiscoveryResult()

        result = FormDiscoveryResult()
        result.total_forms = len(forms)

        for form in forms:
            endpoint = self._form_to_endpoint(form)
            result.forms.append(endpoint)

            # Update method counts
            if endpoint.method.upper() == "GET":
                result.get_forms += 1
            elif endpoint.method.upper() == "POST":
                result.post_forms += 1

            # Update field counts
            result.required_fields += endpoint.required_count()
            result.optional_fields += endpoint.optional_count()

        return result

    def _form_to_endpoint(self, form: Form) -> FormEndpoint:
        """Convert Form object to FormEndpoint."""
        endpoint = FormEndpoint(
            action=form.action or "",
            method=form.method or "GET",
        )

        # Convert form inputs to fields
        for input_obj in form.inputs:
            field = FormField(
                name=input_obj.name or "",
                field_type=input_obj.input_type or "text",
                required=input_obj.required,
                value=input_obj.value or "",
            )
            endpoint.fields.append(field)

        return endpoint

    def find_by_method(self, forms: Sequence[Form], method: str) -> list[FormEndpoint]:
        """
        Find forms using a specific HTTP method.

        Args:
            forms: Sequence of Form objects
            method: HTTP method to filter by (GET, POST, etc.)

        Returns:
            List of matching FormEndpoint objects
        """
        result = self.analyze(forms)
        return result.get_by_method(method)

    def get_all_endpoints(self, forms: Sequence[Form]) -> list[str]:
        """
        Get all unique form action endpoints.

        Args:
            forms: Sequence of Form objects

        Returns:
            Sorted list of unique action URLs
        """
        result = self.analyze(forms)
        return result.get_endpoints()

    def get_all_parameters(self, forms: Sequence[Form]) -> dict[str, int]:
        """
        Get all parameter names and their frequency.

        Args:
            forms: Sequence of Form objects

        Returns:
            Dictionary mapping parameter name to count
        """
        result = self.analyze(forms)
        params = {}

        for form in result.forms:
            for form_field in form.fields:
                if form_field.name:
                    params[form_field.name] = params.get(form_field.name, 0) + 1

        return dict(sorted(params.items()))
