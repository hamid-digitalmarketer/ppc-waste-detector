"""Unit tests covering all specialized PPC waste detectors."""

from ppc_waste_detector.detectors import (
    detect_dayparting_waste,
    detect_geo_bleed,
    detect_junk_placements,
    detect_keyword_cannibalization,
    detect_search_query_bleed,
    detect_smart_bidding_runaway,
)
from ppc_waste_detector.models import (
    GeoHourlyRow,
    LeakCategory,
    PlacementRow,
    SearchQueryRow,
    Severity,
)


def test_search_query_bleed():
    # Low-intent trigger query
    q1 = SearchQueryRow(
        query="free coffee beans download pdf",
        campaign="Search - Beans",
        ad_group="Single Origin",
        cost=85.0,
        clicks=40,
        conversions=0.0,
    )
    # High-spend non-converting query
    q2 = SearchQueryRow(
        query="commercial bulk roasting machine",
        campaign="Search - Equipment",
        ad_group="Commercial",
        cost=180.0,
        clicks=25,
        conversions=0.0,
    )
    # Good query (converting)
    q3 = SearchQueryRow(
        query="buy ethiopian yirgacheffe beans",
        campaign="Search - Beans",
        ad_group="Single Origin",
        cost=200.0,
        clicks=50,
        conversions=15.0,
    )

    findings = detect_search_query_bleed([q1, q2, q3])
    assert len(findings) == 2
    entities = [f.entity for f in findings]
    assert "free coffee beans download pdf" in entities
    assert "commercial bulk roasting machine" in entities

    f1 = next(f for f in findings if f.entity == "free coffee beans download pdf")
    assert f1.severity == Severity.CRITICAL
    assert f1.negative_candidate == "free coffee beans download pdf"


def test_keyword_cannibalization():
    q_camp_a = SearchQueryRow(
        query="artisanal coffee bean roastery",
        campaign="Campaign A",
        ad_group="AdGroup 1",
        cost=80.0,
        clicks=30,
        conversions=2.0,
    )
    q_camp_b = SearchQueryRow(
        query="artisanal coffee bean roastery",
        campaign="Campaign B",
        ad_group="AdGroup 2",
        cost=120.0,
        clicks=45,
        conversions=3.0,
    )

    findings = detect_keyword_cannibalization([q_camp_a, q_camp_b])
    assert len(findings) == 1
    f = findings[0]
    assert f.category == LeakCategory.KEYWORD_CANNIBALIZATION
    assert f.entity == "artisanal coffee bean roastery"
    assert f.wasted_spend == 40.0  # 20% of $200


def test_junk_placements():
    p_game = PlacementRow(
        placement="com.candycrush.mobile.app",
        placement_type="Mobile App",
        campaign="Display Retargeting",
        cost=120.0,
        clicks=300,
        conversions=0.0,
    )
    p_good = PlacementRow(
        placement="sprudge.com",
        placement_type="Website",
        campaign="Display Retargeting",
        cost=250.0,
        clicks=180,
        conversions=20.0,
    )

    findings = detect_junk_placements([p_game, p_good])
    assert len(findings) == 1
    f = findings[0]
    assert f.category == LeakCategory.JUNK_PLACEMENT_LEAK
    assert f.entity == "com.candycrush.mobile.app"
    assert f.severity == Severity.CRITICAL
    assert f.exclusion_candidate == "com.candycrush.mobile.app"


def test_geo_bleed():
    r_target = GeoHourlyRow(
        location="United States",
        hour_of_day=14,
        cost=500.0,
        clicks=200,
        conversions=30.0,
    )
    r_bleed = GeoHourlyRow(
        location="Antarctica",
        hour_of_day=14,
        cost=95.0,
        clicks=80,
        conversions=0.0,
    )

    findings = detect_geo_bleed([r_target, r_bleed], target_locations={"United States"})
    assert len(findings) == 1
    f = findings[0]
    assert f.category == LeakCategory.GEO_BLEED
    assert f.entity == "Antarctica"
    assert f.wasted_spend == 95.0


def test_dayparting_waste():
    r_day = GeoHourlyRow(
        location="United States",
        hour_of_day=14,
        cost=400.0,
        clicks=120,
        conversions=25.0,
    )
    r_night = GeoHourlyRow(
        location="United States",
        hour_of_day=3,
        cost=110.0,
        clicks=45,
        conversions=0.0,
    )

    findings = detect_dayparting_waste([r_day, r_night])
    assert len(findings) == 1
    f = findings[0]
    assert f.category == LeakCategory.DAYPARTING_WASTE
    assert "03:00 - 04:00" in f.entity
    assert f.wasted_spend == 110.0


def test_smart_bidding_runaway():
    # Avg CPC is ($100 / 100) = $1.00
    q_normal = SearchQueryRow(
        query="normal keyword",
        campaign="Search",
        ad_group="General",
        cost=100.0,
        clicks=100,
        conversions=5.0,
    )
    # Runaway query: $100 for 2 clicks ($50/click) and 0 conversions
    q_anomaly = SearchQueryRow(
        query="expensive anomalous term",
        campaign="Search",
        ad_group="General",
        cost=100.0,
        clicks=2,
        conversions=0.0,
    )

    findings = detect_smart_bidding_runaway([q_normal, q_anomaly], cpc_multiplier_threshold=3.0)
    assert len(findings) == 1
    f = findings[0]
    assert f.category == LeakCategory.SMART_BIDDING_RUNAWAY
    assert f.entity == "expensive anomalous term"
    assert f.cpc == 50.0
