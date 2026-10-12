"""Unit tests for PPC Waste Detector CLI application."""

from pathlib import Path

from typer.testing import CliRunner

from ppc_waste_detector.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "PPC Waste Detector" in result.stdout


def test_cli_audit_with_sample_data(tmp_path: Path):
    out_dir = tmp_path / "reports"
    result = runner.invoke(app, ["audit", "--output-dir", str(out_dir), "--no-save-db"])

    assert result.exit_code == 0
    assert "PPC Budget Waste Summary" in result.stdout
    assert "Total Ad Spend Audited" in result.stdout
    assert "Identified Ad Spend Waste" in result.stdout
    assert "Reports & Exclusions Generated Successfully" in result.stdout

    # Verify report files were created
    html_files = list(out_dir.glob("*.html"))
    csv_files = list(out_dir.glob("*.csv"))
    assert len(html_files) >= 1
    assert len(csv_files) >= 1
