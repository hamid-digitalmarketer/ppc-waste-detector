"""SQLite storage layer for saving and loading PPC waste audits."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from ppc_waste_detector.models import PPCAccountAudit


def get_default_db_path() -> Path:
    return Path("./reports/ppc_waste.sqlite")


def init_db(db_path: Path) -> None:
    """Initialize database tables if they do not exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ppc_audits (
                audit_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                total_spend REAL NOT NULL,
                wasted_spend REAL NOT NULL,
                waste_pct REAL NOT NULL,
                total_findings INTEGER NOT NULL,
                critical_findings INTEGER NOT NULL,
                high_findings INTEGER NOT NULL,
                efficiency_score INTEGER NOT NULL,
                audit_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_audit(audit: PPCAccountAudit, db_path: Optional[Path] = None) -> None:
    """Persist a PPC account audit into SQLite."""
    target_db = db_path or get_default_db_path()
    init_db(target_db)

    audit_json_str = audit.model_dump_json()
    s = audit.summary

    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO ppc_audits (
                audit_id, timestamp, total_spend, wasted_spend, waste_pct,
                total_findings, critical_findings, high_findings, efficiency_score, audit_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                s.audit_id,
                s.timestamp,
                s.total_spend_analyzed,
                s.total_wasted_spend,
                s.waste_percentage,
                s.total_findings_count,
                s.critical_findings,
                s.high_findings,
                s.efficiency_score,
                audit_json_str,
            ),
        )
        conn.commit()


def get_audit(audit_id: str, db_path: Optional[Path] = None) -> Optional[PPCAccountAudit]:
    """Retrieve an audit report by ID."""
    target_db = db_path or get_default_db_path()
    if not target_db.exists():
        return None

    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audit_json FROM ppc_audits WHERE audit_id = ?", (audit_id,))
        row = cursor.fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return PPCAccountAudit.model_validate(data)


def list_audits(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """List summary records of previous PPC waste audits."""
    target_db = db_path or get_default_db_path()
    if not target_db.exists():
        return []

    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT audit_id, timestamp, total_spend, wasted_spend, waste_pct, efficiency_score
            FROM ppc_audits
            ORDER BY timestamp DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "audit_id": r[0],
                "timestamp": r[1],
                "total_spend": r[2],
                "wasted_spend": r[3],
                "waste_pct": r[4],
                "efficiency_score": r[5],
            }
            for r in rows
        ]
