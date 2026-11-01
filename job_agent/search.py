"""Job search across public job board APIs."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Callable, Dict, List

import requests

from .config import Settings

HEADERS = {"User-Agent": "job-search-agent/0.1 (+personal use)"}
TIMEOUT = 20


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    description: str
    source: str
    remote: bool = False


def _fix_text(text: str) -> str:
    """Repair double-encoded UTF-8 such as "Sothebyâ\x80\x99s" -> "Sotheby's"."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def _matches(job: Job, keywords: List[str]) -> bool:
    """True if the job title contains every word of at least one keyword."""
    if not keywords:
        return True
    title = re.sub(r"[-/]", " ", job.title.lower())
    compact = title.replace(" ", "")  # so "Full stack" also matches "Fullstack"
    return any(
        all(w in title for w in kw.lower().split()) or kw.lower().replace(" ", "") in compact
        for kw in keywords
    )


REMOTE_PATTERN = re.compile(r"remote|anywhere|worldwide|work from home|wfh|distributed", re.I)
# Remote jobs limited to a region you're not in, e.g. "Remote - US only", "LATAM"
REGION_LOCKED_PATTERN = re.compile(r"\bonly\b|latam|latin america|americas|north america", re.I)


def is_remote(job: Job) -> bool:
    return job.remote or bool(REMOTE_PATTERN.search(f"{job.title} {job.location}"))


def in_home_location(job: Job, s: Settings) -> bool:
    location = job.location.lower()
    return any(place.lower() in location for place in s.home_locations)


def location_allowed(job: Job, s: Settings) -> bool:
    """Jobs in your home country are always allowed; anywhere else must be remote."""
    if in_home_location(job, s):
        return not s.remote_only or is_remote(job)
    if s.home_locations or s.remote_only:
        # A remote job that names a specific place (e.g. "Berlin", "Brazil") is
        # usually only open to people living there.
        tied_to_place = job.location.strip() and not REMOTE_PATTERN.search(job.location)
        region_locked = REGION_LOCKED_PATTERN.search(f"{job.title} {job.location}")
        return is_remote(job) and not tied_to_place and not region_locked
    return True


def search_remoteok(s: Settings) -> List[Job]:
    resp = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=TIMEOUT)
    resp.encoding = "utf-8"
    data = resp.json()
    jobs = [
        Job(
            title=_fix_text(item.get("position", "")),
            company=_fix_text(item.get("company", "")),
            location=_fix_text(item.get("location") or "Remote"),
            url=item.get("apply_url") or item.get("url", ""),
            description=_strip_html(_fix_text(item.get("description", ""))),
            source="RemoteOK",
            remote=True,
        )
        for item in data
        if isinstance(item, dict) and item.get("position")
    ]
    return [j for j in jobs if _matches(j, s.keywords)][: s.max_results_per_source]


def search_arbeitnow(s: Settings) -> List[Job]:
    data = requests.get(
        "https://www.arbeitnow.com/api/job-board-api", headers=HEADERS, timeout=TIMEOUT
    ).json()
    jobs = [
        Job(
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=item.get("location", ""),
            url=item.get("url", ""),
            description=_strip_html(item.get("description", "")),
            source="Arbeitnow",
            remote=bool(item.get("remote")),
        )
        for item in data.get("data", [])
    ]
    return [j for j in jobs if _matches(j, s.keywords)][: s.max_results_per_source]


def search_adzuna(s: Settings) -> List[Job]:
    if not (s.adzuna_app_id and s.adzuna_app_key):
        return []
    jobs: List[Job] = []
    for kw in s.keywords or [""]:
        resp = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{s.adzuna_country}/search/1",
            params={
                "app_id": s.adzuna_app_id,
                "app_key": s.adzuna_app_key,
                "what": kw,
                "where": s.location,
                "results_per_page": s.max_results_per_source,
            },
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        for item in resp.json().get("results", []):
            jobs.append(
                Job(
                    title=_strip_html(item.get("title", "")),
                    company=(item.get("company") or {}).get("display_name", ""),
                    location=(item.get("location") or {}).get("display_name", ""),
                    url=item.get("redirect_url", ""),
                    description=_strip_html(item.get("description", "")),
                    source="Adzuna",
                )
            )
    return jobs


SOURCES: Dict[str, Callable[[Settings], List[Job]]] = {
    "remoteok": search_remoteok,
    "arbeitnow": search_arbeitnow,
    "adzuna": search_adzuna,
}


def search_jobs(s: Settings) -> List[Job]:
    """Query every source, skipping ones that fail, and de-duplicate by URL."""
    seen, results, filtered = set(), [], 0
    for name, fn in SOURCES.items():
        try:
            found = fn(s)
        except Exception as exc:  # one broken board shouldn't stop the run
            print(f"  ! {name} failed: {exc}")
            continue
        print(f"  {name}: {len(found)} jobs")
        for job in found:
            if not location_allowed(job, s):
                filtered += 1
                continue
            if job.url and job.url not in seen:
                seen.add(job.url)
                results.append(job)
    if filtered:
        print(f"  ({filtered} skipped: outside {', '.join(s.home_locations[:1]) or 'your area'} and not remote)")
    return results
