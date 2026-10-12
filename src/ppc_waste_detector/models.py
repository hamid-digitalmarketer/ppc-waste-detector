"""Core data models for PPC Waste Detector."""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    """Urgency level for ad spend reclamation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LeakCategory(str, Enum):
    """Taxonomy of PPC budget waste channels."""
    SEARCH_QUERY_BLEED = "search_query_bleed"
    KEYWORD_CANNIBALIZATION = "keyword_cannibalization"
    JUNK_PLACEMENT_LEAK = "junk_placement_leak"
    GEO_BLEED = "geo_bleed"
    DAYPARTING_WASTE = "dayparting_waste"
    SMART_BIDDING_RUNAWAY = "smart_bidding_runaway"


class WasteFinding(BaseModel):
    """An identified area of ad spend leakage with actionable mitigation."""
    id: str = ""
    category: LeakCategory
    severity: Severity
    entity: str
    campaign: str
    wasted_spend: float
    clicks: int = 0
    impressions: int = 0
    conversions: float = 0.0
    cpc: float = 0.0
    evidence: str
    proposed_action: str
    negative_candidate: Optional[str] = None
    exclusion_candidate: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            raw_key = f"{self.category.value}|{self.campaign}|{self.entity}|{self.wasted_spend}"
            self.id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12]


class SearchQueryRow(BaseModel):
    """Search term performance record."""
    model_config = ConfigDict(extra="ignore")

    query: str
    campaign: str
    ad_group: str
    clicks: int = 0
    impressions: int = 0
    cost: float = 0.0
    conversions: float = 0.0
    conversion_value: float = 0.0


class PlacementRow(BaseModel):
    """Display/PMax placement performance record."""
    model_config = ConfigDict(extra="ignore")

    placement: str
    placement_type: str = "Website"
    campaign: str
    cost: float = 0.0
    clicks: int = 0
    impressions: int = 0
    conversions: float = 0.0


class GeoHourlyRow(BaseModel):
    """Geographic and hourly dayparting spend record."""
    model_config = ConfigDict(extra="ignore")

    location: str
    hour_of_day: int
    cost: float = 0.0
    clicks: int = 0
    conversions: float = 0.0


class WasteSummary(BaseModel):
    """Aggregate financial and efficiency metrics of the PPC account audit."""
    audit_id: str
    timestamp: str
    total_spend_analyzed: float
    total_wasted_spend: float
    waste_percentage: float
    total_findings_count: int
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    efficiency_score: int = 100
    top_waste_category: LeakCategory = LeakCategory.SEARCH_QUERY_BLEED


class PPCAccountAudit(BaseModel):
    """Full account audit report containing findings, exclusions, and financial summaries."""
    summary: WasteSummary
    findings: List[WasteFinding] = Field(default_factory=list)
    negative_keyword_candidates: List[str] = Field(default_factory=list)
    placement_exclusion_candidates: List[str] = Field(default_factory=list)
