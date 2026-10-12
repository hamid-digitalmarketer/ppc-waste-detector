"""Report generation in HTML, CSV, and JSON formats for PPC waste audits."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader

from ppc_waste_detector.models import PPCAccountAudit


def get_template_env() -> Environment:
    template_dir = Path(__file__).parent / "templates"
    return Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)


def export_json(audit: PPCAccountAudit, output_path: Path) -> Path:
    """Export complete audit report as structured JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(audit.model_dump_json(indent=2))
    return output_path


def export_csv(audit: PPCAccountAudit, output_path: Path) -> Path:
    """Export findings table to CSV format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "category",
        "severity",
        "entity",
        "campaign",
        "wasted_spend",
        "clicks",
        "impressions",
        "conversions",
        "cpc",
        "evidence",
        "proposed_action",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for finding in audit.findings:
            writer.writerow(
                {
                    "id": finding.id,
                    "category": finding.category.value,
                    "severity": finding.severity.value,
                    "entity": finding.entity,
                    "campaign": finding.campaign,
                    "wasted_spend": finding.wasted_spend,
                    "clicks": finding.clicks,
                    "impressions": finding.impressions,
                    "conversions": finding.conversions,
                    "cpc": finding.cpc,
                    "evidence": finding.evidence,
                    "proposed_action": finding.proposed_action,
                }
            )
    return output_path


def export_html(audit: PPCAccountAudit, output_path: Path) -> Path:
    """Render and export interactive HTML audit dashboard."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = get_template_env()
    template = env.get_template("report.html")

    html_content = template.render(audit=audit)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return output_path


def generate_all_reports(audit: PPCAccountAudit, output_dir: Path) -> Dict[str, Path]:
    """Generate HTML, CSV, and JSON audit files in the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = audit.summary.audit_id

    json_path = output_dir / f"{base_name}.json"
    csv_path = output_dir / f"{base_name}.csv"
    html_path = output_dir / f"{base_name}.html"

    export_json(audit, json_path)
    export_csv(audit, csv_path)
    export_html(audit, html_path)

    return {
        "json": json_path,
        "csv": csv_path,
        "html": html_path,
    }
