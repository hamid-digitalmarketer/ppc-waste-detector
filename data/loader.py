"""Data ingestion connectors and parsers for Google Ads and Meta Ads export reports."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from ppc_waste_detector.models import GeoHourlyRow, PlacementRow, SearchQueryRow


def load_search_queries(csv_path: Path) -> List[SearchQueryRow]:
    """Load and normalize search query performance data from CSV."""
    df = pd.read_csv(csv_path)

    # Normalize column names to lowercase
    col_map = {c: c.lower().strip().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=col_map)

    # Standardize column naming
    query_col = next((c for c in ["query", "search_term", "search_query"] if c in df.columns), "query")
    campaign_col = next((c for c in ["campaign", "campaign_name"] if c in df.columns), "campaign")
    adgroup_col = next((c for c in ["ad_group", "adgroup", "ad_group_name"] if c in df.columns), "ad_group")
    cost_col = next((c for c in ["cost", "spend", "amount_spent"] if c in df.columns), "cost")
    clicks_col = next((c for c in ["clicks", "num_clicks"] if c in df.columns), "clicks")
    impr_col = next((c for c in ["impressions", "impr"] if c in df.columns), "impressions")
    conv_col = next((c for c in ["conversions", "conv", "results"] if c in df.columns), "conversions")
    conv_val_col = next((c for c in ["conversion_value", "conv_value", "revenue"] if c in df.columns), "conversion_value")

    rows: List[SearchQueryRow] = []
    for _, r in df.iterrows():
        rows.append(
            SearchQueryRow(
                query=str(r.get(query_col, "")),
                campaign=str(r.get(campaign_col, "Default Campaign")),
                ad_group=str(r.get(adgroup_col, "Default Ad Group")),
                cost=float(r.get(cost_col, 0.0) or 0.0),
                clicks=int(r.get(clicks_col, 0) or 0),
                impressions=int(r.get(impr_col, 0) or 0),
                conversions=float(r.get(conv_col, 0.0) or 0.0),
                conversion_value=float(r.get(conv_val_col, 0.0) or 0.0),
            )
        )
    return rows


def load_placements(csv_path: Path) -> List[PlacementRow]:
    """Load and normalize Display / PMax placement report from CSV."""
    df = pd.read_csv(csv_path)
    col_map = {c: c.lower().strip().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=col_map)

    plac_col = next((c for c in ["placement", "url", "domain", "app"] if c in df.columns), "placement")
    type_col = next((c for c in ["placement_type", "type"] if c in df.columns), "placement_type")
    campaign_col = next((c for c in ["campaign", "campaign_name"] if c in df.columns), "campaign")
    cost_col = next((c for c in ["cost", "spend", "amount_spent"] if c in df.columns), "cost")
    clicks_col = next((c for c in ["clicks"] if c in df.columns), "clicks")
    impr_col = next((c for c in ["impressions", "impr"] if c in df.columns), "impressions")
    conv_col = next((c for c in ["conversions", "conv"] if c in df.columns), "conversions")

    rows: List[PlacementRow] = []
    for _, r in df.iterrows():
        rows.append(
            PlacementRow(
                placement=str(r.get(plac_col, "")),
                placement_type=str(r.get(type_col, "Website")),
                campaign=str(r.get(campaign_col, "Display Campaign")),
                cost=float(r.get(cost_col, 0.0) or 0.0),
                clicks=int(r.get(clicks_col, 0) or 0),
                impressions=int(r.get(impr_col, 0) or 0),
                conversions=float(r.get(conv_col, 0.0) or 0.0),
            )
        )
    return rows


def load_geo_hourly(csv_path: Path) -> List[GeoHourlyRow]:
    """Load and normalize geographic and hourly dayparting reports from CSV."""
    df = pd.read_csv(csv_path)
    col_map = {c: c.lower().strip().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=col_map)

    loc_col = next((c for c in ["location", "country", "region", "geo"] if c in df.columns), "location")
    hour_col = next((c for c in ["hour_of_day", "hour", "time_of_day"] if c in df.columns), "hour_of_day")
    cost_col = next((c for c in ["cost", "spend"] if c in df.columns), "cost")
    clicks_col = next((c for c in ["clicks"] if c in df.columns), "clicks")
    conv_col = next((c for c in ["conversions", "conv"] if c in df.columns), "conversions")

    rows: List[GeoHourlyRow] = []
    for _, r in df.iterrows():
        rows.append(
            GeoHourlyRow(
                location=str(r.get(loc_col, "United States")),
                hour_of_day=int(r.get(hour_col, 12) or 12),
                cost=float(r.get(cost_col, 0.0) or 0.0),
                clicks=int(r.get(clicks_col, 0) or 0),
                conversions=float(r.get(conv_col, 0.0) or 0.0),
            )
        )
    return rows
