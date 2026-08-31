#!/usr/bin/env python3
"""
Generate Quarto HTML report from pentest JSON results.

Usage:
    python generate_report.py pentest_report_20260831_172000.json
"""

import json
import sys
import html
from datetime import datetime
from pathlib import Path


SEVERITY_COLORS = {
    "critical": "#dc3545",  # Red
    "high": "#fd7e14",      # Orange
    "medium": "#ffc107",    # Yellow
    "low": "#28a745",       # Green
    "info": "#17a2b8",      # Blue
}

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "info": "ℹ️",
}


def escape_for_display(text: str) -> str:
    """Escape HTML entities for safe display."""
    if not text:
        return text
    # Escape HTML special characters
    return html.escape(text)


def generate_quarto_report(json_path: str) -> str:
    """Generate Quarto markdown from JSON report."""
    
    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract filename for title
    report_name = Path(json_path).stem
    
    # Start building Quarto document
    qmd = []
    qmd.append("---")
    qmd.append("title: \"Penetration Test Report\"")
    qmd.append(f"subtitle: \"{report_name}\"")
    qmd.append(f"date: \"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\"")
    qmd.append("format:")
    qmd.append("  html:")
    qmd.append("    toc: true")
    qmd.append("    toc-depth: 3")
    qmd.append("    code-fold: false")
    qmd.append("    theme: cosmo")
    qmd.append("---")
    qmd.append("")
    
    # Executive Summary
    qmd.append("## Executive Summary")
    qmd.append("")
    qmd.append(f"**Total Vulnerabilities:** {data['total_vulnerabilities']}")
    qmd.append("")
    qmd.append("| Severity | Count |")
    qmd.append("|----------|-------|")
    qmd.append(f"| 🔴 Critical | {data['critical']} |")
    qmd.append(f"| 🟠 High     | {data['high']} |")
    qmd.append(f"| 🟡 Medium   | {data['medium']} |")
    qmd.append(f"| 🟢 Low      | {data['low']} |")
    qmd.append(f"| ℹ️  Info     | {data['info']} |")
    qmd.append("")
    
    # Findings by Severity
    qmd.append("## Findings")
    qmd.append("")
    
    # Group vulnerabilities by severity
    by_severity = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
        "info": [],
    }
    
    for vuln in data.get('vulnerabilities', []):
        severity = vuln['severity'].lower()
        by_severity[severity].append(vuln)
    
    # Generate findings sections
    finding_number = 1
    for severity in ["critical", "high", "medium", "low", "info"]:
        vulns = by_severity[severity]
        if not vulns:
            continue
        
        emoji = SEVERITY_EMOJI[severity]
        qmd.append(f"### {emoji} {severity.upper()} Severity ({len(vulns)} findings)")
        qmd.append("")
        
        for vuln in vulns:
            qmd.append(f"#### Finding #{finding_number}: {escape_for_display(vuln['vulnerability_type'])}")
            qmd.append("")
            
            # Basic info
            qmd.append(f"**URL:** `{escape_for_display(vuln['url'])}`")
            qmd.append("")
            qmd.append(f"**Description:** {escape_for_display(vuln['description'])}")
            qmd.append("")
            
            # Parameter and payload
            if vuln.get('parameter'):
                qmd.append(f"**Parameter:** `{escape_for_display(vuln['parameter'])}`")
                qmd.append("")
            
            if vuln.get('payload'):
                qmd.append(f"**Payload:**")
                qmd.append("")
                qmd.append("```text")
                qmd.append(escape_for_display(vuln['payload']))
                qmd.append("```")
                qmd.append("")
            
            # Evidence
            qmd.append(f"**Evidence:** {escape_for_display(vuln['evidence'])}")
            qmd.append("")
            
            # Remediation
            qmd.append("**Remediation:**")
            qmd.append("")
            qmd.append(escape_for_display(vuln['remediation']))
            qmd.append("")
            
            # Technical details
            qmd.append("::: {.callout-note collapse=\"true\"}")
            qmd.append("## Technical Details")
            qmd.append("")
            cwe_num = vuln['cwe_id'].split('-')[1] if '-' in vuln['cwe_id'] else '0'
            qmd.append(f"- **CWE ID:** [{escape_for_display(vuln['cwe_id'])}](https://cwe.mitre.org/data/definitions/{cwe_num}.html)")
            qmd.append(f"- **Confidence:** {vuln['confidence']}%")
            qmd.append(f"- **Timestamp:** {escape_for_display(str(vuln['timestamp']))}")
            qmd.append("")
            qmd.append(":::")
            qmd.append("")
            qmd.append("---")
            qmd.append("")
            
            finding_number += 1
    
    # Appendix
    qmd.append("## Appendix")
    qmd.append("")
    qmd.append("### Severity Definitions")
    qmd.append("")
    qmd.append("| Severity | Definition |")
    qmd.append("|----------|------------|")
    qmd.append("| 🔴 Critical | Exploitable vulnerabilities that allow complete system compromise |")
    qmd.append("| 🟠 High | Serious vulnerabilities that expose sensitive data or functionality |")
    qmd.append("| 🟡 Medium | Moderate vulnerabilities that require additional conditions to exploit |")
    qmd.append("| 🟢 Low | Minor vulnerabilities with limited impact |")
    qmd.append("| ℹ️  Info | Informational findings that may not be directly exploitable |")
    qmd.append("")
    
    qmd.append("### Vulnerability Categories")
    qmd.append("")
    
    # Count by type
    type_counts = {}
    for vuln in data.get('vulnerabilities', []):
        vtype = vuln['vulnerability_type']
        type_counts[vtype] = type_counts.get(vtype, 0) + 1
    
    qmd.append("| Category | Count |")
    qmd.append("|----------|-------|")
    for vtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        qmd.append(f"| {escape_for_display(vtype)} | {count} |")
    qmd.append("")
    
    qmd.append("### References")
    qmd.append("")
    qmd.append("- [OWASP Top 10](https://owasp.org/www-project-top-ten/)")
    qmd.append("- [CWE Database](https://cwe.mitre.org/)")
    qmd.append("- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)")
    qmd.append("")
    
    return "\n".join(qmd)


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <pentest_report.json>")
        print("Example: python generate_report.py pentest_report_20260831_172000.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not Path(json_path).exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)
    
    # Generate Quarto markdown
    print(f"📄 Generating report from {json_path}...")
    qmd_content = generate_quarto_report(json_path)
    
    # Write to .qmd file
    output_path = Path(json_path).stem + ".qmd"
    with open(output_path, 'w') as f:
        f.write(qmd_content)
    
    print(f"✅ Quarto markdown generated: {output_path}")
    print(f"\nTo render HTML report:")
    print(f"  quarto render {output_path}")
    print(f"\nOr use make:")
    print(f"  make report FILE={json_path}")


if __name__ == "__main__":
    main()
