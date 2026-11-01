"""Application log: one CSV row per job the agent processed."""
from __future__ import annotations

import csv
from datetime import datetime
from typing import Dict, List, Set

from .config import REPORTS_DIR

REPORT_PATH = REPORTS_DIR / "applications.csv"
COLUMNS = [
    "date", "title", "company", "location", "source", "url",
    "match_score", "cover_letter", "status", "notes",
]


def load_rows() -> List[Dict[str, str]]:
    if not REPORT_PATH.exists():
        return []
    with REPORT_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def processed_urls() -> Set[str]:
    """Jobs to skip on later runs. Dry-run shortlists stay open so you can apply later."""
    return {row["url"] for row in load_rows() if row["status"] != "shortlisted"}


def add_row(**fields: str) -> None:
    """Append a row, or replace the existing row for the same job URL."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    new = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), **fields}
    new = {c: new.get(c, "") for c in COLUMNS}
    rows = [r for r in load_rows() if r["url"] != new["url"]] + [new]
    with REPORT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def print_report() -> None:
    rows = load_rows()
    if not rows:
        print("No applications yet.")
        return
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        print(f"{row['date']}  [{row['status']:<13}] {row['match_score']:>3}  "
              f"{row['title']} @ {row['company']}")
    print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    print(f"Full report: {REPORT_PATH}")
