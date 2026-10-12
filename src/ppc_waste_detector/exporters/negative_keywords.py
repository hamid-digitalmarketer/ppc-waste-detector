"""Export negative keyword candidates for Google Ads and Meta Ads."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from ppc_waste_detector.models import WasteFinding


def export_negative_keywords(
    findings: List[WasteFinding],
    output_csv_path: Path,
    output_txt_path: Path,
) -> tuple[Path, Path]:
    """Generate ready-to-upload Google Ads Editor CSV and plain TXT negative keyword lists."""
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_txt_path.parent.mkdir(parents=True, exist_ok=True)

    candidates: List[tuple[str, str]] = []
    seen = set()

    for f in findings:
        if f.negative_candidate:
            clean_term = f.negative_candidate.strip("[]\"'")
            key = (f.campaign, clean_term.lower())
            if key not in seen:
                seen.add(key)
                candidates.append((f.campaign, clean_term))

    # 1. Google Ads Editor CSV Format
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Campaign", "Keyword", "Criterion Type", "Match Type"])
        for camp, term in candidates:
            writer.writerow([camp, term, "Negative", "Exact"])

    # 2. Plain Text Format (bracketed exact match)
    with open(output_txt_path, "w", encoding="utf-8") as txtfile:
        for _, term in candidates:
            txtfile.write(f"[{term}]\n")

    return output_csv_path, output_txt_path
