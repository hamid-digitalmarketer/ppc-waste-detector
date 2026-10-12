"""Detect mobile app games, MFA sites, and click-fraud display placements."""

from __future__ import annotations

import re
from typing import List

from ppc_waste_detector.models import LeakCategory, PlacementRow, Severity, WasteFinding

MOBILE_APP_PATTERNS = [
    r"^mobileapp::",
    r"^com\.",
    r"^net\.",
    r"^org\.",
    r"\bgames?\b",
    r"\bpuzzle\b",
    r"\bcasual\b",
    r"\bquiz\b",
    r"\barcade\b",
]


def detect_junk_placements(
    placements: List[PlacementRow],
    min_waste_threshold: float = 20.0,
) -> List[WasteFinding]:
    """Scan Display, Demand Gen, and PMax placement reports for low-intent app and MFA leaks."""
    findings: List[WasteFinding] = []

    for p in placements:
        if p.conversions > 0:
            continue

        placement_lower = p.placement.lower().strip()
        is_mobile_app = (
            p.placement_type.lower() == "mobile app"
            or any(re.search(pat, placement_lower) for pat in MOBILE_APP_PATTERNS)
        )

        # 1. Mobile App Game Waste
        if is_mobile_app and p.cost >= 15.0:
            sev = Severity.CRITICAL if p.cost >= 100.0 else Severity.HIGH
            findings.append(
                WasteFinding(
                    category=LeakCategory.JUNK_PLACEMENT_LEAK,
                    severity=sev,
                    entity=p.placement,
                    campaign=p.campaign,
                    wasted_spend=round(p.cost, 2),
                    clicks=p.clicks,
                    impressions=p.impressions,
                    conversions=p.conversions,
                    cpc=round(p.cost / max(1, p.clicks), 2),
                    evidence=(
                        f"Mobile app placement '{p.placement}' consumed ${p.cost:.2f} across "
                        f"{p.clicks} clicks with 0 conversions. Typically caused by accidental 'fat-finger' gaming clicks."
                    ),
                    proposed_action=f"Exclude mobile placement '{p.placement}' or negate all app categories in campaign '{p.campaign}'.",
                    exclusion_candidate=p.placement,
                )
            )
        # 2. Non-converting website placement with high spend
        elif p.cost >= min_waste_threshold:
            sev = Severity.CRITICAL if p.cost >= 150.0 else Severity.HIGH
            findings.append(
                WasteFinding(
                    category=LeakCategory.JUNK_PLACEMENT_LEAK,
                    severity=sev,
                    entity=p.placement,
                    campaign=p.campaign,
                    wasted_spend=round(p.cost, 2),
                    clicks=p.clicks,
                    impressions=p.impressions,
                    conversions=p.conversions,
                    cpc=round(p.cost / max(1, p.clicks), 2),
                    evidence=(
                        f"Non-converting placement '{p.placement}' spent ${p.cost:.2f} with "
                        f"{p.clicks} clicks and 0 conversions."
                    ),
                    proposed_action=f"Add '{p.placement}' to account-level placement exclusion list.",
                    exclusion_candidate=p.placement,
                )
            )

    return findings
