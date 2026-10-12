"""Detectors registry for identifying ad spend waste across PPC channels."""

from ppc_waste_detector.detectors.dayparting_waste import detect_dayparting_waste
from ppc_waste_detector.detectors.geo_bleed import detect_geo_bleed
from ppc_waste_detector.detectors.junk_placement_leak import detect_junk_placements
from ppc_waste_detector.detectors.keyword_cannibalization import detect_keyword_cannibalization
from ppc_waste_detector.detectors.search_query_bleed import detect_search_query_bleed
from ppc_waste_detector.detectors.smart_bidding_runaway import detect_smart_bidding_runaway

__all__ = [
    "detect_search_query_bleed",
    "detect_keyword_cannibalization",
    "detect_junk_placements",
    "detect_geo_bleed",
    "detect_dayparting_waste",
    "detect_smart_bidding_runaway",
]
