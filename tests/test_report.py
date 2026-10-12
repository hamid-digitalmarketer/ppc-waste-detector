"""Unit tests for PPC waste audit report generation in HTML, CSV, and JSON."""

import json
from pathlib import Path

from ppc_waste_detector.models import (
    LeakCategory,
    PPCAccountAudit,
    Severity,
    WasteFinding,
    WasteSummary,
)
from ppc_waste_detector.report import (
    export_csv,
    export_html,
    export_json,
    generate_all_reports,
)


def _create_mock_audit() -> PPCAccountAudit:
    summary = WasteSummary(
        audit_id="test-audit-999",
        timestamp="2026-01-01T12:00:00Z",
        total_spend_analyzed=5000.0,
        total_wasted_spend=1200.0,
        waste_percentage=24.0,
        total_findings_count=1,
        critical_findings=1,
        efficiency_score=76,
    )
    findings = [
        WasteFinding(
            category=LeakCategory.SEARCH_QUERY_BLEED,
            severity=Severity.CRITICAL,
            entity="free download",
            campaign="Search - Beans",
            wasted_spend=450.0,
            evidence="Zero conversion trigger",
            proposed_action="Add negative keyword",
            negative_candidate="free download",
        )
    ]
    return PPCAccountAudit(
        summary=summary,
        findings=findings,
        negative_keyword_candidates=["free download"],
    )


def test_export_json(tmp_path: Path):
    audit = _create_mock_audit()
    p = tmp_path / "audit.json"
    export_json(audit, p)
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["summary"]["audit_id"] == "test-audit-999"


def test_export_csv(tmp_path: Path):
    audit = _create_mock_audit()
    p = tmp_path / "audit.csv"
    export_csv(audit, p)
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "search_query_bleed" in content
    assert "450.0" in content


def test_export_html(tmp_path: Path):
    audit = _create_mock_audit()
    p = tmp_path / "audit.html"
    export_html(audit, p)
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "PPC Waste Detector" in content
    assert "test-audit-999" in content
    assert "76%" in content


def test_generate_all_reports(tmp_path: Path):
    audit = _create_mock_audit()
    paths = generate_all_reports(audit, tmp_path)
    assert paths["json"].exists()
    assert paths["csv"].exists()
    assert paths["html"].exists()
