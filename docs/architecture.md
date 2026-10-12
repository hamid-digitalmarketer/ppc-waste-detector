# PPC Waste Detector Architecture & Technical Design

## 1. System Overview

**PPC Waste Detector** is designed as a modular, high-throughput pipeline that ingests Google Ads and Meta Ads performance exports, executes specialized rule-based and statistical anomaly detectors, and exports prioritized remediation lists:

```
[ Search Query Report CSV ]  \
[ Placement Report CSV    ]  --> [ Data Loaders & Standardizer ]
[ Geo & Hourly Report CSV ]  /
                                        |
                                        v
                       [ 6 Specialized Waste Detectors ]
                       • Search Query Bleed
                       • Keyword Cannibalization
                       • Junk Placement Leak
                       • Geo Bleed
                       • Dayparting Waste
                       • Smart Bidding Runaway
                                        |
                                        v
                       [ Deduplication & Impact Ranking ]
                                        |
                                        +---> [ SQLite Audit History ]
                                        |
                                        +---> [ HTML Dashboard / CSV / JSON ]
                                        |
                                        +---> [ Google Ads Editor Negatives CSV ]
                                        +---> [ Placement Exclusions CSV/TXT ]
```

---

## 2. Ingestion & Data Standardization Layer (`data/loader.py`)

Ad platforms export data in disparate schemas. The loader standardizes columns across variations:
- Queries: `Search Term`, `Search Query`, `Query`, `Keyword` $\to$ `query`
- Spend: `Cost`, `Spend`, `Amount Spent` $\to$ `cost`
- Results: `Conversions`, `Results`, `Actions` $\to$ `conversions`

---

## 3. The 6 Specialized Waste Detectors (`detectors/`)

1. **Search Query Bleed (`detectors/search_query_bleed.py`)**:
   - Compares search terms against high-risk non-commercial keyword dictionaries (e.g. `free`, `login`, `jobs`, `pdf`, `cracked`).
   - Flags zero-conversion queries exceeding customizable cost thresholds.
2. **Keyword Cannibalization (`detectors/keyword_cannibalization.py`)**:
   - Detects queries triggering ads across multiple active ad groups/campaigns.
   - Calculates internal auction friction penalties ($20\%$ estimated waste).
3. **Junk Placement Leak (`detectors/junk_placement_leak.py`)**:
   - Identifies mobile game package names (`com.`, `app::`, `puzzle`, `arcade`).
   - Isolates zero-conversion display placements.
4. **Geo Bleed (`detectors/geo_bleed.py`)**:
   - Validates geographical spend against target market whitelists.
5. **Dayparting Waste (`detectors/dayparting_waste.py`)**:
   - Identifies non-converting midnight/early-morning schedule windows (1 AM - 5 AM).
6. **Smart Bidding Runaway (`detectors/smart_bidding_runaway.py`)**:
   - Detects outlier CPC spikes where automated bidding placed bids $\ge 3\times$ the account average.

---

## 4. Multi-Format Exporters & Action Plans (`exporters/`, `report.py`)

- **Negative Keywords Editor CSV**: Pre-formatted for one-click upload into Google Ads Editor (`Campaign`, `Keyword`, `Match Type = Exact`, `Criterion Type = Negative`).
- **Placement Exclusions Editor CSV**: Pre-formatted for one-click placement negation across Display and Performance Max.
- **HTML Visual Dashboard**: Interactive client-ready audit report.
