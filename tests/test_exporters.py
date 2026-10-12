"""Unit tests for negative keyword and placement exclusion exporters."""

from pathlib import Path

from ppc_waste_detector.exporters import (
    export_negative_keywords,
    export_placement_exclusions,
)
from ppc_waste_detector.models import LeakCategory, Severity, WasteFinding


def test_export_negative_keywords(tmp_path: Path):
    f1 = WasteFinding(
        category=LeakCategory.SEARCH_QUERY_BLEED,
        severity=Severity.HIGH,
        entity="free download",
        campaign="Search - Beans",
        wasted_spend=50.0,
        evidence="Non-converting query",
        proposed_action="Add negative",
        negative_candidate="free download",
    )
    csv_out = tmp_path / "negatives.csv"
    txt_out = tmp_path / "negatives.txt"

    export_negative_keywords([f1], csv_out, txt_out)

    assert csv_out.exists()
    assert txt_out.exists()

    csv_text = csv_out.read_text(encoding="utf-8")
    assert "Search - Beans" in csv_text
    assert "free download" in csv_text
    assert "Negative" in csv_text

    txt_text = txt_out.read_text(encoding="utf-8")
    assert "[free download]" in txt_text


def test_export_placement_exclusions(tmp_path: Path):
    f1 = WasteFinding(
        category=LeakCategory.JUNK_PLACEMENT_LEAK,
        severity=Severity.CRITICAL,
        entity="com.game.puzzle",
        campaign="Display - Retargeting",
        wasted_spend=80.0,
        evidence="Mobile app fat finger clicks",
        proposed_action="Exclude placement",
        exclusion_candidate="com.game.puzzle",
    )
    csv_out = tmp_path / "exclusions.csv"
    txt_out = tmp_path / "exclusions.txt"

    export_placement_exclusions([f1], csv_out, txt_out)

    assert csv_out.exists()
    assert txt_out.exists()

    csv_text = csv_out.read_text(encoding="utf-8")
    assert "Display - Retargeting" in csv_text
    assert "com.game.puzzle" in csv_text

    txt_text = txt_out.read_text(encoding="utf-8")
    assert "com.game.puzzle" in txt_text
