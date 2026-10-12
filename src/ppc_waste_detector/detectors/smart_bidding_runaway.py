"""Detect runaway automated smart bidding CPC spikes and broad-match anomalies."""

from __future__ import annotations

from typing import List

from ppc_waste_detector.models import LeakCategory, SearchQueryRow, Severity, WasteFinding


def detect_smart_bidding_runaway(
    queries: List[SearchQueryRow],
    cpc_multiplier_threshold: float = 3.0,
    min_spend: float = 35.0,
) -> List[WasteFinding]:
    """Identify queries where automated bidding placed outlier bids exceeding normal benchmarks."""
    findings: List[WasteFinding] = []

    # Calculate global average CPC
    total_spend = sum(q.cost for q in queries)
    total_clicks = sum(q.clicks for q in queries)
    if total_clicks == 0:
        return findings

    avg_cpc = total_spend / total_clicks

    for q in queries:
        if q.clicks > 0 and q.conversions == 0 and q.cost >= min_spend:
            query_cpc = q.cost / q.clicks
            if query_cpc >= (avg_cpc * cpc_multiplier_threshold):
                sev = Severity.CRITICAL if q.cost >= 150.0 or query_cpc >= 25.0 else Severity.HIGH

                findings.append(
                    WasteFinding(
                        category=LeakCategory.SMART_BIDDING_RUNAWAY,
                        severity=sev,
                        entity=q.query,
                        campaign=q.campaign,
                        wasted_spend=round(q.cost, 2),
                        clicks=q.clicks,
                        impressions=q.impressions,
                        conversions=q.conversions,
                        cpc=round(query_cpc, 2),
                        evidence=(
                            f"Runaway CPC anomaly: query was billed at ${query_cpc:.2f} per click "
                            f"({query_cpc / avg_cpc:.1f}x higher than the account average ${avg_cpc:.2f}) "
                            f"totaling ${q.cost:.2f} with zero conversions."
                        ),
                        proposed_action=(
                            f"Apply a Portfolio Bid Strategy with a maximum CPC bid cap on campaign '{q.campaign}', "
                            f"or add exact negative for '{q.query}'."
                        ),
                        negative_candidate=q.query,
                    )
                )

    return findings
