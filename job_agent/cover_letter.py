"""Builds a cover letter from a template, the job posting and your CV.

The template uses {placeholders}. The default lives in templates/cover_letter.md;
put your own version in private/cover_letter.md (gitignored) to override it.
"""
from __future__ import annotations

import re
from datetime import date
from typing import List

from .config import ROOT, Settings
from .matcher import MatchResult, _skill_regex, find_skills
from .search import Job
from .skills import SKILLS

SPOKEN_LANGUAGES = {"english", "german", "french", "spanish", "arabic", "urdu"}
PLACEHOLDER = re.compile(r"\{(\w+)\}")

DEFAULT_TEMPLATE = ROOT / "templates" / "cover_letter.md"
CUSTOM_TEMPLATE = ROOT / "private" / "cover_letter.md"


def _join(items: List[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _cv_highlights(cv_text: str, skills: List[str], limit: int = 3) -> List[str]:
    """CV lines (bullets/sentences) that mention the most matched skills."""
    lines = [
        re.sub(r"^[\s\-•*·▪●]+", "", line).strip()
        for line in re.split(r"[\n\r]+|(?<=[.!?])\s+(?=[A-Z])", cv_text)
    ]
    lines = [l for l in lines if 30 <= len(l) <= 300]
    scored = [
        (sum(1 for sk in skills if _skill_regex(sk).search(l.lower())), i, l)
        for i, l in enumerate(lines)
    ]
    best = sorted([t for t in scored if t[0] > 0], key=lambda t: (-t[0], t[1]))[:limit]
    return [l.rstrip(".") + "." for _, _, l in sorted(best, key=lambda t: t[1])]


def _display_name(skill: str, cv_text: str) -> str:
    """The skill as you wrote it in your CV (e.g. "TypeScript"), else as listed."""
    m = _skill_regex(skill).search(cv_text.lower())
    return cv_text[m.start():m.end()] if m else skill


def _render(template: str, values: dict) -> str:
    """Fill placeholders, dropping lines whose placeholders are all empty."""
    lines = []
    for line in template.splitlines():
        keys = PLACEHOLDER.findall(line)
        if keys and not any(values.get(k) for k in keys):
            continue
        lines.append(line.format_map(values))
    return "\n".join(lines)


def write_cover_letter(s: Settings, job: Job, match: MatchResult) -> str:
    template_path = CUSTOM_TEMPLATE if CUSTOM_TEMPLATE.exists() else DEFAULT_TEMPLATE
    template = template_path.read_text(encoding="utf-8")
    p = s.profile

    technical = [sk for sk in match.matched_skills if sk not in SPOKEN_LANGUAGES]
    skills = [_display_name(sk, s.cv_text) for sk in technical[:5]]
    highlights = _cv_highlights(s.cv_text, technical)
    if len(highlights) < 2:  # few direct matches: fall back to your strongest CV lines
        cv_skills = [sk for sk in find_skills(s.cv_text, SKILLS + s.extra_skills)
                     if sk not in SPOKEN_LANGUAGES]
        highlights = _cv_highlights(s.cv_text, cv_skills) or highlights
    values = {
        "date": date.today().strftime("%d %B %Y"),
        "full_name": p.full_name,
        "email": p.email,
        "phone": p.phone,
        "location": p.location,
        "linkedin_url": p.linkedin_url,
        "github_url": p.github_url,
        "portfolio_url": p.portfolio_url,
        "job_title": job.title,
        "company": job.company or "your company",
        "job_source": job.source,
        "matched_skills": _join(skills) or "the skills listed in the posting",
        "highlights": "\n".join(f"- {h}" for h in highlights)
        or "- My CV (attached) details my relevant experience.",
    }
    return _render(template, values).strip() + "\n"
