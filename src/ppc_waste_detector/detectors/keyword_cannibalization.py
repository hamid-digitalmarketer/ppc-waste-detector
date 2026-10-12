"""Detect cross-campaign and cross-ad-group keyword cannibalization."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from ppc_waste_detector.models import LeakCategory, SearchQueryRow, Severity, WasteFinding


def detect_keyword_cannibalization(
    queries: List[SearchQueryRow],
    min_overlap_spend: float = 40.0,
) -> List[WasteFinding]:
    """Identify search terms competing in multiple internal auctions, inflating CPCs."""
    findings: List[WasteFinding] = []
    query_map: Dict[str, List[SearchQueryRow]] = defaultdict(list)

    for q in queries:
        query_map[q.query.lower().strip()].append(q)

    for query_text, rows in query_map.items():
        campaigns = list({r.campaign for r in rows})
        ad_groups = list({f"{r.campaign} > {r.ad_group}" for r in rows})

        # Cannibalization occurs if query triggers 2+ distinct ad groups or campaigns
        if len(ad_groups) > 1:
            total_cost = sum(r.cost for r in rows)
            total_clicks = sum(r.clicks for r in rows)
            total_conv = sum(r.conversions for r in rows)

            if total_cost >= min_overlap_spend:
                # Conservative estimate: internal auction friction inflates CPC by ~15-25%
                estimated_waste = round(total_cost * 0.20, 2)
                sev = Severity.CRITICAL if total_cost >= 250.0 else Severity.HIGH

                campaign_str = ", ".join(campaigns[:3])
                ad_group_str = ", ".join(ad_groups[:3])

                findings.append(
                    WasteFinding(
                        category=LeakCategory.KEYWORD_CANNIBALIZATION,
                        severity=sev,
                        entity=query_text,
                        campaign=campaign_str,
                        wasted_spend=estimated_waste,
                        clicks=total_clicks,
                        conversions=total_conv,
                        cpc=round(total_cost / max(1, total_clicks), 2),
                        evidence=(
                            f"Search term '{query_text}' triggers ads across {len(ad_groups)} internal ad groups "
                            f"({ad_group_str}) totaling ${total_cost:.2f} spend. Internal bidding competition "
                            f"is inflating CPCs."
                        ),
                        proposed_action=(
                            f"Add negative keyword for '{query_text}' to non-primary ad groups and route traffic "
                            f"exclusively to the dedicated high-relevance ad group."
                        ),
                        negative_candidate=f"[{query_text}]",
                    )
                )

    return findings
