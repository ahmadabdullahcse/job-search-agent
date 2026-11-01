"""CLI: python -m job_agent {search,run,report}"""
from __future__ import annotations

import argparse

from . import report
from .config import load_settings
from .search import search_jobs


def main() -> None:
    parser = argparse.ArgumentParser(prog="job_agent", description="Job search & apply agent")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("search", help="List matching jobs without applying")

    run_p = sub.add_parser("run", help="Search, score, write cover letters and apply")
    run_p.add_argument("--dry-run", action="store_true",
                       help="Score and write cover letters, but don't open any application")
    run_p.add_argument("--auto-submit", action="store_true",
                       help="Click submit without asking you to review (use with care)")
    run_p.add_argument("--always-cover-letter", action="store_true",
                       help="Write a cover letter even when the posting doesn't ask for one")

    sub.add_parser("report", help="Show the applications report")

    args = parser.parse_args()
    if args.command == "report":
        report.print_report()
        return

    settings = load_settings()
    if args.command == "search":
        for job in search_jobs(settings):
            print(f"{job.source:<10} {job.title} @ {job.company} | {job.location}\n           {job.url}")
    else:
        from .agent import run
        run(settings, args.dry_run, args.auto_submit, args.always_cover_letter)


if __name__ == "__main__":
    main()
