"""Detect out-of-target geographic spend bleed and non-converting location waste."""

from __future__ import annotations

from typing import List, Optional, Set

from ppc_waste_detector.models import GeoHourlyRow, LeakCategory, Severity, WasteFinding


def detect_geo_bleed(
    geo_rows: List[GeoHourlyRow],
    target_locations: Optional[Set[str]] = None,
    min_spend_threshold: float = 30.0,
) -> List[WasteFinding]:
    """Scan geographic performance for spend leaking into unintended or non-converting territories."""
    findings: List[WasteFinding] = []
    targets = {t.lower() for t in target_locations} if target_locations else None

    # Aggregate by location
    loc_stats: dict[str, dict[str, float]] = {}
    for r in geo_rows:
        loc = r.location.strip()
        if loc not in loc_stats:
            loc_stats[loc] = {"cost": 0.0, "clicks": 0.0, "conversions": 0.0}
        loc_stats[loc]["cost"] += r.cost
        loc_stats[loc]["clicks"] += r.clicks
        loc_stats[loc]["conversions"] += r.conversions

    for loc, stats in loc_stats.items():
        is_outside_target = targets is not None and loc.lower() not in targets
        has_zero_conv = stats["conversions"] == 0

        if (is_outside_target or has_zero_conv) and stats["cost"] >= min_spend_threshold:
            sev = Severity.CRITICAL if stats["cost"] >= 120.0 else Severity.HIGH
            reason = (
                "Location is outside explicit target geography and has 0 conversions"
                if is_outside_target
                else "Location generated significant ad spend with 0 conversions"
            )

            findings.append(
                WasteFinding(
                    category=LeakCategory.GEO_BLEED,
                    severity=sev,
                    entity=loc,
                    campaign="Account/Campaign Geo Targeting",
                    wasted_spend=round(stats["cost"], 2),
                    clicks=int(stats["clicks"]),
                    conversions=stats["conversions"],
                    cpc=round(stats["cost"] / max(1, stats["clicks"]), 2),
                    evidence=f"{reason}: ${stats['cost']:.2f} spent over {int(stats['clicks'])} clicks.",
                    proposed_action=f"Exclude location '{loc}' in campaign location targeting settings.",
                )
            )

    return findings
