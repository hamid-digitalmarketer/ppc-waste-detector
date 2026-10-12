"""Export placement exclusion candidates for Display Network and Performance Max."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from ppc_waste_detector.models import WasteFinding


def export_placement_exclusions(
    findings: List[WasteFinding],
    output_csv_path: Path,
    output_txt_path: Path,
) -> tuple[Path, Path]:
    """Generate ready-to-upload placement exclusion lists for Google Ads and DSP platforms."""
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_txt_path.parent.mkdir(parents=True, exist_ok=True)

    candidates: List[tuple[str, str]] = []
    seen = set()

    for f in findings:
        if f.exclusion_candidate:
            clean_placement = f.exclusion_candidate.strip()
            key = (f.campaign, clean_placement.lower())
            if key not in seen:
                seen.add(key)
                candidates.append((f.campaign, clean_placement))

    # 1. Google Ads Editor Placement Exclusion CSV
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Campaign", "Placement", "Criterion Type"])
        for camp, placement in candidates:
            writer.writerow([camp, placement, "Negative Placement"])

    # 2. Raw Text List
    with open(output_txt_path, "w", encoding="utf-8") as txtfile:
        for _, placement in candidates:
            txtfile.write(f"{placement}\n")

    return output_csv_path, output_txt_path
