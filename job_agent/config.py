"""Loads personal details, CV and search preferences from .env."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
COVER_LETTERS_DIR = ROOT / "output" / "cover_letters"


def _bool(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Optional[str], default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


@dataclass
class Profile:
    full_name: str
    email: str
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    work_authorization: str = ""
    notice_period: str = ""
    expected_salary: str = ""

    @property
    def first_name(self) -> str:
        return self.full_name.split()[0] if self.full_name else ""

    @property
    def last_name(self) -> str:
        parts = self.full_name.split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""


@dataclass
class Settings:
    profile: Profile
    cv_path: Optional[Path]
    cv_text: str
    extra_skills: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    location: str = ""
    remote_only: bool = False
    max_results_per_source: int = 25
    min_match_score: int = 70
    max_applications_per_run: int = 10
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "de"


def _read_cv(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8")


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    env = os.environ.get

    cv_path = None
    if env("CV_PATH"):
        cv_path = Path(env("CV_PATH"))
        if not cv_path.is_absolute():
            cv_path = ROOT / cv_path
        if not cv_path.exists():
            cv_path = None

    cv_text = (env("CV_TEXT") or "").strip()
    if not cv_text and cv_path:
        cv_text = _read_cv(cv_path)

    if not cv_text:
        raise SystemExit("No CV found: set CV_PATH (existing file) or CV_TEXT in .env")
    if not env("FULL_NAME") or not env("EMAIL"):
        raise SystemExit("FULL_NAME and EMAIL must be set in .env")

    return Settings(
        profile=Profile(
            full_name=env("FULL_NAME", ""),
            email=env("EMAIL", ""),
            phone=env("PHONE", ""),
            location=env("LOCATION", ""),
            linkedin_url=env("LINKEDIN_URL", ""),
            github_url=env("GITHUB_URL", ""),
            portfolio_url=env("PORTFOLIO_URL", ""),
            work_authorization=env("WORK_AUTHORIZATION", ""),
            notice_period=env("NOTICE_PERIOD", ""),
            expected_salary=env("EXPECTED_SALARY", ""),
        ),
        cv_path=cv_path,
        cv_text=cv_text,
        extra_skills=[k.strip().lower() for k in (env("EXTRA_SKILLS") or "").split(",") if k.strip()],
        keywords=[k.strip() for k in (env("JOB_KEYWORDS") or "").split(",") if k.strip()],
        location=env("JOB_LOCATION", ""),
        remote_only=_bool(env("REMOTE_ONLY")),
        max_results_per_source=_int(env("MAX_RESULTS_PER_SOURCE"), 25),
        min_match_score=_int(env("MIN_MATCH_SCORE"), 70),
        max_applications_per_run=_int(env("MAX_APPLICATIONS_PER_RUN"), 10),
        adzuna_app_id=env("ADZUNA_APP_ID", ""),
        adzuna_app_key=env("ADZUNA_APP_KEY", ""),
        adzuna_country=env("ADZUNA_COUNTRY") or "de",
    )
