"""Command-Line Interface (CLI) for PPC Waste Detector."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ppc_waste_detector import __version__
from ppc_waste_detector.data.loader import load_geo_hourly, load_placements, load_search_queries
from ppc_waste_detector.detectors import (
    detect_dayparting_waste,
    detect_geo_bleed,
    detect_junk_placements,
    detect_keyword_cannibalization,
    detect_search_query_bleed,
    detect_smart_bidding_runaway,
)
from ppc_waste_detector.exporters import (
    export_negative_keywords,
    export_placement_exclusions,
)
from ppc_waste_detector.models import (
    LeakCategory,
    PPCAccountAudit,
    Severity,
    WasteFinding,
    WasteSummary,
)
from ppc_waste_detector.report import generate_all_reports
from ppc_waste_detector.storage import get_default_db_path, list_audits, save_audit

app = typer.Typer(
    name="ppc-waste",
    help="Free open-source PPC budget leak detector for Google Ads and Meta Ads.",
    add_completion=False,
)
console = Console()


@app.command()
def audit(
    search_queries: Optional[Path] = typer.Option(
        None, "--search-queries", "-q", help="Path to Google Ads Search Terms CSV export"
    ),
    placements: Optional[Path] = typer.Option(
        None, "--placements", "-p", help="Path to Display/PMax Placements CSV export"
    ),
    geo_hourly: Optional[Path] = typer.Option(
        None, "--geo-hourly", "-g", help="Path to Geographic & Hourly Dayparting CSV export"
    ),
    output_dir: Path = typer.Option(
        Path("./reports"), "--output-dir", "--out-dir", "-o", help="Target directory for generated audit reports"
    ),
    save_to_db: bool = typer.Option(
        True, "--save-db/--no-save-db", help="Persist audit results to local SQLite database"
    ),
) -> None:
    """Run full PPC budget waste audit across search queries, display placements, and dayparting."""
    package_data_dir = Path(__file__).parent / "data" / "sample_data"
    root_data_dir = Path(__file__).parent.parent.parent / "data" / "sample_data"
    default_dir = package_data_dir if package_data_dir.exists() else root_data_dir
    sq_file = search_queries or (default_dir / "google_search_queries.csv")
    pl_file = placements or (default_dir / "display_placement_performance.csv")
    gh_file = geo_hourly or (default_dir / "geo_hourly_performance.csv")

    console.print(
        Panel.fit(
            f"[bold green][+] PPC Waste Detector[/bold green] v{__version__}\n"
            f"[dim]Search Queries:[/dim] {sq_file.name if sq_file.exists() else 'None'}\n"
            f"[dim]Placements:[/dim]     {pl_file.name if pl_file.exists() else 'None'}\n"
            f"[dim]Geo & Hourly:[/dim]   {gh_file.name if gh_file.exists() else 'None'}",
            border_style="green",
        )
    )

    all_findings: List[WasteFinding] = []
    total_spend_analyzed = 0.0

    # 1. Audit Search Queries
    if sq_file.exists():
        queries = load_search_queries(sq_file)
        total_spend_analyzed += sum(q.cost for q in queries)
        all_findings.extend(detect_search_query_bleed(queries))
        all_findings.extend(detect_keyword_cannibalization(queries))
        all_findings.extend(detect_smart_bidding_runaway(queries))

    # 2. Audit Placements
    if pl_file.exists():
        plac_rows = load_placements(pl_file)
        total_spend_analyzed += sum(p.cost for p in plac_rows)
        all_findings.extend(detect_junk_placements(plac_rows))

    # 3. Audit Geo & Hourly Dayparting
    if gh_file.exists():
        geo_rows = load_geo_hourly(gh_file)
        # Avoid double-counting spend if geo rows overlap
        if not sq_file.exists() and not pl_file.exists():
            total_spend_analyzed += sum(r.cost for r in geo_rows)
        all_findings.extend(detect_geo_bleed(geo_rows, target_locations={"United States"}))
        all_findings.extend(detect_dayparting_waste(geo_rows))

    # Deduplicate findings
    unique_findings: List[WasteFinding] = []
    seen_ids = set()
    for f in all_findings:
        if f.id not in seen_ids:
            seen_ids.add(f.id)
            unique_findings.append(f)

    # Sort by wasted spend descending
    unique_findings.sort(key=lambda x: x.wasted_spend, reverse=True)

    total_waste = sum(f.wasted_spend for f in unique_findings)
    waste_pct = round((total_waste / max(1.0, total_spend_analyzed)) * 100.0, 1)
    efficiency_score = max(0, min(100, int(100 - waste_pct)))

    crit_c = sum(1 for f in unique_findings if f.severity == Severity.CRITICAL)
    high_c = sum(1 for f in unique_findings if f.severity == Severity.HIGH)
    med_c = sum(1 for f in unique_findings if f.severity == Severity.MEDIUM)
    low_c = sum(1 for f in unique_findings if f.severity == Severity.LOW)

    top_cat = unique_findings[0].category if unique_findings else LeakCategory.SEARCH_QUERY_BLEED

    summary = WasteSummary(
        audit_id=f"audit-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}",
        timestamp=datetime.utcnow().isoformat() + "Z",
        total_spend_analyzed=round(total_spend_analyzed, 2),
        total_wasted_spend=round(total_waste, 2),
        waste_percentage=waste_pct,
        total_findings_count=len(unique_findings),
        critical_findings=crit_c,
        high_findings=high_c,
        medium_findings=med_c,
        low_findings=low_c,
        efficiency_score=efficiency_score,
        top_waste_category=top_cat,
    )

    # Extract negative keywords and placement exclusions
    neg_candidates = list(
        dict.fromkeys([f.negative_candidate for f in unique_findings if f.negative_candidate])
    )
    excl_candidates = list(
        dict.fromkeys([f.exclusion_candidate for f in unique_findings if f.exclusion_candidate])
    )

    audit_report = PPCAccountAudit(
        summary=summary,
        findings=unique_findings,
        negative_keyword_candidates=neg_candidates,
        placement_exclusion_candidates=excl_candidates,
    )

    # Persist and Export
    paths = generate_all_reports(audit_report, output_dir)
    neg_csv, neg_txt = export_negative_keywords(
        unique_findings,
        output_dir / "negative_keywords_editor.csv",
        output_dir / "negative_keywords_raw.txt",
    )
    excl_csv, excl_txt = export_placement_exclusions(
        unique_findings,
        output_dir / "placement_exclusions_editor.csv",
        output_dir / "placement_exclusions_raw.txt",
    )

    if save_to_db:
        save_audit(audit_report)

    # Terminal Dashboard Output
    table = Table(title="PPC Budget Waste Summary", border_style="dim")
    table.add_column("Financial Metric", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Total Ad Spend Audited", f"${summary.total_spend_analyzed:,.2f}")
    table.add_row("Identified Ad Spend Waste", f"[red]${summary.total_wasted_spend:,.2f}[/red]")
    table.add_row("Waste Rate", f"[red]{summary.waste_percentage}%[/red]")
    table.add_row("PPC Capital Efficiency Score", f"[green]{summary.efficiency_score} / 100[/green]")
    table.add_row(
        "Annualized Reclaim Potential", f"[bold green]${summary.total_wasted_spend * 12:,.2f}[/bold green]"
    )
    table.add_row("Total Leak Findings", str(summary.total_findings_count))
    table.add_row("Critical Urgent Leaks", f"[red]{summary.critical_findings}[/red]")
    table.add_row("Negative Keywords Identified", f"[cyan]{len(neg_candidates)} terms[/cyan]")
    table.add_row("Placement Exclusions Identified", f"[cyan]{len(excl_candidates)} placements[/cyan]")

    console.print(table)

    if unique_findings:
        console.print("\n[bold][!] Top Budget Leaks to Fix Immediately:[/bold]")
        top_table = Table(border_style="dim")
        top_table.add_column("Severity", style="bold")
        top_table.add_column("Category")
        top_table.add_column("Entity / Query", max_width=35, overflow="fold")
        top_table.add_column("Wasted Spend", justify="right")
        top_table.add_column("Action Required", max_width=45, overflow="fold")

        for f in unique_findings[:5]:
            sev_color = "red" if f.severity == "critical" else "yellow"
            top_table.add_row(
                f"[{sev_color}]{f.severity.upper()}[/{sev_color}]",
                f.category.value.replace("_", " ").title(),
                f.entity,
                f"[red]${f.wasted_spend:,.2f}[/red]",
                f.proposed_action,
            )
        console.print(top_table)

    console.print("\n[bold green][OK] Reports & Exclusions Generated Successfully:[/bold green]")
    console.print(f"  * HTML Dashboard:              [cyan]{paths['html']}[/cyan]")
    console.print(f"  * CSV Findings Backlog:        [cyan]{paths['csv']}[/cyan]")
    console.print(f"  * JSON Machine Report:         [cyan]{paths['json']}[/cyan]")
    console.print(f"  * Negative Keywords Editor:    [cyan]{neg_csv}[/cyan]")
    console.print(f"  * Placement Exclusions Editor: [cyan]{excl_csv}[/cyan]\n")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host address to bind to"),
    port: int = typer.Option(8001, "--port", "-p", help="Port to listen on"),
    reports_dir: Path = typer.Option(Path("./reports"), "--reports-dir", help="Directory where reports are stored"),
) -> None:
    """Launch local web viewer to inspect PPC waste audit reports in your browser."""
    server_app = FastAPI(
        title="PPC Waste Detector Web Viewer",
        version=__version__,
    )

    @server_app.get("/", response_class=HTMLResponse)
    def index() -> str:
        audits = list_audits(get_default_db_path())
        html_files = sorted(reports_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)

        links_html = "".join(
            f'<li class="p-4 bg-slate-800 rounded-lg hover:bg-slate-700 transition flex justify-between items-center"><a class="text-rose-400 font-mono text-sm hover:underline" href="/report/{h.stem}">{h.name}</a><span class="text-xs text-slate-400 font-mono">{round(h.stat().st_size / 1024, 1)} KB</span></li>'
            for h in html_files
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>PPC Waste Detector Local Viewer</title>
          <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-slate-950 text-slate-100 min-h-screen p-8">
          <div class="max-w-4xl mx-auto space-y-6">
            <div class="flex items-center gap-3">
              <span class="text-3xl">💸</span>
              <div>
                <h1 class="text-2xl font-bold">PPC Waste Detector Local Dashboard</h1>
                <p class="text-xs text-slate-400">Reports in {reports_dir.resolve()}</p>
                <p class="text-xs text-slate-500 mt-1 font-mono">Stored Audits in SQLite: {len(audits)}</p>
              </div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">Saved HTML Reports ({len(html_files)})</h2>
              <ul class="space-y-2">
                {links_html or '<li class="text-sm text-slate-500">No reports generated yet. Run: ppc-waste audit</li>'}
              </ul>
            </div>
          </div>
        </body>
        </html>
        """

    @server_app.get("/report/{report_id}", response_class=HTMLResponse)
    def view_report(report_id: str) -> str:
        target_html = reports_dir / f"{report_id}.html"
        if not target_html.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        return target_html.read_text(encoding="utf-8")

    console.print(f"[bold green][*] PPC Waste Detector launching at http://{host}:{port}[/bold green]")
    uvicorn.run(server_app, host=host, port=port)


@app.command()
def version() -> None:
    """Show PPC Waste Detector version."""
    console.print(f"PPC Waste Detector [bold green]v{__version__}[/bold green]")


if __name__ == "__main__":
    app()
