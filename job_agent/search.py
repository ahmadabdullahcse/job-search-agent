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


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def _matches(job: Job, keywords: List[str]) -> bool:
    if not keywords:
        return True
    haystack = f"{job.title} {job.description}".lower()
    return any(all(w in haystack for w in kw.lower().split()) for kw in keywords)


def search_remoteok(s: Settings) -> List[Job]:
    data = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=TIMEOUT).json()
    jobs = [
        Job(
            title=item.get("position", ""),
            company=item.get("company", ""),
            location=item.get("location") or "Remote",
            url=item.get("apply_url") or item.get("url", ""),
            description=_strip_html(item.get("description", "")),
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
    seen, results = set(), []
    for name, fn in SOURCES.items():
        try:
            found = fn(s)
        except Exception as exc:  # one broken board shouldn't stop the run
            print(f"  ! {name} failed: {exc}")
            continue
        print(f"  {name}: {len(found)} jobs")
        for job in found:
            if s.remote_only and not job.remote:
                continue
            if job.url and job.url not in seen:
                seen.add(job.url)
                results.append(job)
    return results
