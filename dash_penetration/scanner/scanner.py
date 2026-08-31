"""
Core vulnerability scanner orchestrator.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class Severity(Enum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"  # Immediate exploitation possible
    HIGH = "high"  # Serious security issue
    MEDIUM = "medium"  # Moderate risk
    LOW = "low"  # Minor issue
    INFO = "info"  # Informational only


@dataclass
class ScanResult:
    """Result of a vulnerability scan."""

    vulnerability_type: str
    """Type of vulnerability (e.g., 'SQL Injection', 'XSS')"""

    severity: Severity
    """Severity level of the vulnerability"""

    url: str
    """URL where vulnerability was found"""

    description: str
    """Human-readable description of the vulnerability"""

    evidence: str
    """Evidence/proof of the vulnerability"""

    remediation: str
    """Suggested fix for the vulnerability"""

    cwe_id: Optional[str] = None
    """Common Weakness Enumeration ID"""

    confidence: int = 100
    """Confidence level (0-100) that this is a real vulnerability"""

    timestamp: datetime = field(default_factory=datetime.now)
    """When the vulnerability was discovered"""

    payload: Optional[str] = None
    """Payload used to discover the vulnerability"""

    parameter: Optional[str] = None
    """Parameter that was vulnerable"""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "vulnerability_type": self.vulnerability_type,
            "severity": self.severity.value,
            "url": self.url,
            "description": self.description,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "cwe_id": self.cwe_id,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "parameter": self.parameter,
        }


class VulnerabilityScanner:
    """
    Main vulnerability scanner that orchestrates all scan modules.
    """

    def __init__(self):
        """Initialize the scanner."""
        self.results: list[ScanResult] = []

    def add_result(self, result: ScanResult):
        """Add a scan result."""
        self.results.append(result)

    def get_results_by_severity(self, severity: Severity) -> list[ScanResult]:
        """Get all results with a specific severity."""
        return [r for r in self.results if r.severity == severity]

    def get_critical_count(self) -> int:
        """Get count of critical vulnerabilities."""
        return len(self.get_results_by_severity(Severity.CRITICAL))

    def get_high_count(self) -> int:
        """Get count of high severity vulnerabilities."""
        return len(self.get_results_by_severity(Severity.HIGH))

    def generate_report(self) -> dict:
        """Generate a vulnerability report."""
        return {
            "total_vulnerabilities": len(self.results),
            "critical": self.get_critical_count(),
            "high": self.get_high_count(),
            "medium": len(self.get_results_by_severity(Severity.MEDIUM)),
            "low": len(self.get_results_by_severity(Severity.LOW)),
            "info": len(self.get_results_by_severity(Severity.INFO)),
            "vulnerabilities": [r.to_dict() for r in self.results],
        }
