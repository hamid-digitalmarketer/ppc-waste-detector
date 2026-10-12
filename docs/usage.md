# CLI & Python API Usage Guide

`ppc-waste-detector` provides both an ergonomic command-line interface (CLI) powered by Typer and Rich, as well as a pure Python programmatic API for pipeline integration.

---

## Command Line Interface (CLI)

### Installation
```bash
pip install ppc-waste-detector
# Or install in editable mode for development
pip install -e ".[dev]"
```

### Running an Audit
Execute a comprehensive PPC budget leak audit against your export CSV files:

```bash
ppc-waste audit \
  --search-queries path/to/google_search_queries.csv \
  --placements path/to/display_placement_performance.csv \
  --geo-hourly path/to/geo_hourly_performance.csv \
  --out-dir ./reports \
  --cost-threshold 50.0 \
  --clicks-threshold 10
```

#### CLI Parameters
| Parameter | Option | Default | Description |
|---|---|---|---|
| `--search-queries` | `-s` | `None` | Path to Google Search Query Report CSV |
| `--placements` | `-p` | `None` | Path to Display/PMax Placement Report CSV |
| `--geo-hourly` | `-g` | `None` | Path to Geographic / Hourly Performance CSV |
| `--out-dir` | `-o` | `./reports` | Directory where HTML, CSV, JSON reports and negative keyword lists are saved |
| `--cost-threshold` | `-c` | `50.0` | Minimum zero-conversion spend ($) to trigger a waste finding |
| `--clicks-threshold` | `-k` | `10` | Minimum zero-conversion clicks to trigger a waste finding |
| `--open-browser` | | `False` | Automatically launch browser to view the generated HTML report |

If no input files are specified, `ppc-waste audit` automatically loads the built-in sample datasets:
```bash
ppc-waste audit --open-browser
```

### Launching the Web Viewer
You can view past audit reports or explore findings interactively through the built-in local web server:

```bash
ppc-waste serve --port 8000 --host 127.0.0.1
```

---

## Python Programmatic API

You can embed `ppc-waste-detector` into custom data pipelines, Airflow DAGs, or ETL workflows:

```python
from pathlib import Path
from ppc_waste_detector.data.loader import (
    load_search_queries,
    load_placements,
    load_geo_hourly,
)
from ppc_waste_detector.detectors import (
    SearchQueryBleedDetector,
    KeywordCannibalizationDetector,
    JunkPlacementLeakDetector,
    GeoBleedDetector,
    DaypartingWasteDetector,
    SmartBiddingRunawayDetector,
)
from ppc_waste_detector.report import ReportGenerator
from ppc_waste_detector.storage import SQLiteStorage

# 1. Load CSV data
search_rows = load_search_queries(Path("data/sample_data/google_search_queries.csv"))
placement_rows = load_placements(Path("data/sample_data/display_placement_performance.csv"))
geo_rows = load_geo_hourly(Path("data/sample_data/geo_hourly_performance.csv"))

# 2. Run detection engines
all_findings = []
all_findings.extend(SearchQueryBleedDetector(cost_threshold=50.0, clicks_threshold=10).run(search_rows))
all_findings.extend(KeywordCannibalizationDetector().run(search_rows))
all_findings.extend(JunkPlacementLeakDetector().run(placement_rows))
all_findings.extend(GeoBleedDetector().run(geo_rows))
all_findings.extend(DaypartingWasteDetector().run(geo_rows))
all_findings.extend(SmartBiddingRunawayDetector().run(search_rows))

# 3. Save findings to SQLite and export reports
storage = SQLiteStorage("reports/ppc_waste.sqlite")
storage.save_findings(all_findings)

reporter = ReportGenerator(output_dir=Path("./reports"))
paths = reporter.generate_all(all_findings)
print(f"Generated HTML report at: {paths['html']}")
```

---

## Generated Export Formats

1. **`reports/audit-<timestamp>-<hash>.html`**: Self-contained Tailwind CSS dashboard with responsive data tables, leak breakdowns, and copy-to-clipboard functionality.
2. **`reports/audit-<timestamp>-<hash>.json`**: Machine-readable JSON summary for CI/CD assertions and alerting integrations.
3. **`reports/audit-<timestamp>-<hash>.csv`**: Flat CSV export of all findings for Google Sheets or Excel analysis.
4. **`reports/negative_keywords_editor.csv`**: Formatted for direct upload to **Google Ads Editor** (`Campaign`, `Ad Group`, `Criterion Type`, `Keyword`).
5. **`reports/negative_keywords_raw.txt`**: Plaintext list of exact and broad match negative keywords.
6. **`reports/placement_exclusions_editor.csv`**: Formatted placement exclusion CSV for Google Ads Editor.
7. **`reports/placement_exclusions_raw.txt`**: One exclusion domain/app-ID per line for pasting into Google Ads Web UI.
