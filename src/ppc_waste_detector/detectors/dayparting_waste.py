"""Detect non-converting dayparting hours and off-peak ad spend drain."""

from __future__ import annotations

from typing import List

from ppc_waste_detector.models import GeoHourlyRow, LeakCategory, Severity, WasteFinding


def detect_dayparting_waste(
    hourly_rows: List[GeoHourlyRow],
    min_hourly_waste: float = 40.0,
) -> List[WasteFinding]:
    """Scan hourly performance distribution to identify non-converting schedule windows."""
    findings: List[WasteFinding] = []

    # Aggregate by hour
    hour_stats: dict[int, dict[str, float]] = {}
    for r in hourly_rows:
        h = r.hour_of_day
        if h not in hour_stats:
            hour_stats[h] = {"cost": 0.0, "clicks": 0.0, "conversions": 0.0}
        hour_stats[h]["cost"] += r.cost
        hour_stats[h]["clicks"] += r.clicks
        hour_stats[h]["conversions"] += r.conversions

    for h, stats in hour_stats.items():
        # High spend with zero conversions
        if stats["conversions"] == 0 and stats["cost"] >= min_hourly_waste:
            is_overnight = 0 <= h <= 5
            sev = (
                Severity.CRITICAL
                if stats["cost"] >= 150.0
                else (Severity.HIGH if is_overnight else Severity.MEDIUM)
            )

            hour_str = f"{h:02d}:00 - {h+1:02d}:00"
            findings.append(
                WasteFinding(
                    category=LeakCategory.DAYPARTING_WASTE,
                    severity=sev,
                    entity=hour_str,
                    campaign="Account Ad Schedule",
                    wasted_spend=round(stats["cost"], 2),
                    clicks=int(stats["clicks"]),
                    conversions=stats["conversions"],
                    cpc=round(stats["cost"] / max(1, stats["clicks"]), 2),
                    evidence=(
                        f"Hour window {hour_str} accumulated ${stats['cost']:.2f} across "
                        f"{int(stats['clicks'])} clicks with zero conversions."
                    ),
                    proposed_action=(
                        f"Implement a -100% ad schedule bid modifier or pause campaign during {hour_str}."
                    ),
                )
            )

    return findings
