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
    return {row["url"] for row in load_rows()}


def add_row(**fields: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    is_new = not REPORT_PATH.exists()
    row = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), **fields}
    with REPORT_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        if is_new:
            writer.writeheader()
        writer.writerow({c: row.get(c, "") for c in COLUMNS})


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
