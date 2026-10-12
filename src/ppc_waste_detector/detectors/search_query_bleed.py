"""Detect zero-conversion search query spend and negative keyword opportunities."""

from __future__ import annotations

import re
from typing import List

from ppc_waste_detector.models import LeakCategory, SearchQueryRow, Severity, WasteFinding

LOW_INTENT_PATTERNS = [
    r"\bfree\b",
    r"\bcheap\b",
    r"\bcracked\b",
    r"\btorrent\b",
    r"\blogin\b",
    r"\bportal\b",
    r"\bsupport\b",
    r"\bcustomer service\b",
    r"\bjobs\b",
    r"\bcareers\b",
    r"\bsalary\b",
    r"\binternship\b",
    r"\bpdf\b",
    r"\bdownload\b",
    r"\bdiy\b",
]


def detect_search_query_bleed(
    queries: List[SearchQueryRow],
    min_cost_threshold: float = 30.0,
) -> List[WasteFinding]:
    """Scan search query report for non-converting spend and negative keyword gaps."""
    findings: List[WasteFinding] = []

    for q in queries:
        if q.conversions > 0:
            continue

        query_lower = q.query.lower().strip()
        has_low_intent_match = any(re.search(pat, query_lower) for pat in LOW_INTENT_PATTERNS)

        # 1. Negative Intent Trigger Match (High urgency)
        if has_low_intent_match and q.cost > 10.0:
            sev = (
                Severity.CRITICAL
                if q.cost >= 75.0
                else (Severity.HIGH if q.cost >= 25.0 else Severity.MEDIUM)
            )
            findings.append(
                WasteFinding(
                    category=LeakCategory.SEARCH_QUERY_BLEED,
                    severity=sev,
                    entity=q.query,
                    campaign=q.campaign,
                    wasted_spend=round(q.cost, 2),
                    clicks=q.clicks,
                    impressions=q.impressions,
                    conversions=q.conversions,
                    cpc=round(q.cost / max(1, q.clicks), 2),
                    evidence=(
                        f"Search term '{q.query}' contains low-intent terms with ${q.cost:.2f} spend "
                        f"and 0 conversions ({q.clicks} clicks)."
                    ),
                    proposed_action=f"Add exact match negative keyword for '{q.query}' to campaign '{q.campaign}'.",
                    negative_candidate=q.query,
                )
            )
        # 2. High-Spend Zero-Conversion Bleed
        elif q.cost >= min_cost_threshold:
            sev = Severity.CRITICAL if q.cost >= 150.0 else Severity.HIGH
            findings.append(
                WasteFinding(
                    category=LeakCategory.SEARCH_QUERY_BLEED,
                    severity=sev,
                    entity=q.query,
                    campaign=q.campaign,
                    wasted_spend=round(q.cost, 2),
                    clicks=q.clicks,
                    impressions=q.impressions,
                    conversions=q.conversions,
                    cpc=round(q.cost / max(1, q.clicks), 2),
                    evidence=(
                        f"High-spend non-converting search term: consumed ${q.cost:.2f} over "
                        f"{q.clicks} clicks with 0 conversions."
                    ),
                    proposed_action=f"Add exact match negative keyword for '{q.query}' or refine ad group match types.",
                    negative_candidate=q.query,
                )
            )

    return findings
