"""The pipeline: search -> match -> cover letter -> apply -> report."""
from __future__ import annotations

import re

from . import report
from .apply import apply_to_job
from .config import COVER_LETTERS_DIR, Settings
from .cover_letter import write_cover_letter
from .matcher import evaluate_match
from .search import Job, search_jobs


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _save_cover_letter(job: Job, text: str) -> str:
    COVER_LETTERS_DIR.mkdir(parents=True, exist_ok=True)
    path = COVER_LETTERS_DIR / f"{_slug(job.company)}_{_slug(job.title)}.md"
    path.write_text(text, encoding="utf-8")
    return str(path.relative_to(COVER_LETTERS_DIR.parent.parent))


def run(s: Settings, dry_run: bool, auto_submit: bool, always_cover_letter: bool) -> None:
    print(f"Searching for: {', '.join(s.keywords) or '(any)'} in {s.location or 'anywhere'}")
    jobs = search_jobs(s)
    done = report.processed_urls()
    jobs = [j for j in jobs if j.url not in done]
    print(f"{len(jobs)} new jobs to evaluate\n")

    applied = 0
    for job in jobs:
        if applied >= s.max_applications_per_run:
            print(f"Reached MAX_APPLICATIONS_PER_RUN ({s.max_applications_per_run}).")
            break

        print(f"- {job.title} @ {job.company} ({job.source})")
        try:
            match = evaluate_match(s, job)
        except Exception as exc:
            print(f"    ! match failed: {exc}")
            continue
        print(f"    score {match.score}: {match.reasons[:140]}")

        row = dict(
            title=job.title, company=job.company, location=job.location,
            source=job.source, url=job.url, match_score=str(match.score),
        )
        if match.score < s.min_match_score:
            report.add_row(**row, status="low_match", notes=match.reasons[:300])
            continue

        cover_letter, cl_path = None, ""
        if match.cover_letter_required or always_cover_letter:
            cover_letter = write_cover_letter(s, job, match)
            cl_path = _save_cover_letter(job, cover_letter)
            print(f"    cover letter -> {cl_path}")

        if dry_run:
            report.add_row(**row, cover_letter=cl_path, status="shortlisted",
                           notes="Dry run - not applied")
            applied += 1
            continue

        status, notes = apply_to_job(s, job.url, cover_letter, auto_submit)
        print(f"    {status}: {notes}")
        report.add_row(**row, cover_letter=cl_path, status=status, notes=notes)
        if status == "applied":
            applied += 1

    print()
    report.print_report()
