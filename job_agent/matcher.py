"""Scores how well a job fits the CV — locally, no external AI service.

Score (0-100) = 70% skill coverage + 30% title relevance.
- Skill coverage: of the known skills the job mentions, how many appear in the CV.
- Title relevance: how many words of your JOB_KEYWORDS appear in the job title.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from .config import Settings
from .search import Job
from .skills import ALIASES, SKILLS

COVER_LETTER_PATTERN = re.compile(
    r"cover letter|covering letter|motivation(al)? letter|letter of motivation|"
    r"anschreiben|motivationsschreiben",
    re.I,
)


@dataclass
class MatchResult:
    score: int
    reasons: str
    key_requirements: List[str] = field(default_factory=list)
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    cover_letter_required: bool = False
    cover_letter_instructions: str = ""


def _skill_regex(skill: str) -> re.Pattern:
    # word boundaries that still work for skills like "c++", "c#", ".net", "node.js"
    return re.compile(r"(?<![\w+#.])" + re.escape(skill.lower()) + r"(?![\w+#])")


def find_skills(text: str, vocabulary: List[str]) -> List[str]:
    lowered = text.lower()
    return [
        s for s in vocabulary
        if any(_skill_regex(v).search(lowered) for v in [s] + ALIASES.get(s, []))
    ]


def _vocabulary(s: Settings) -> List[str]:
    return list(dict.fromkeys(SKILLS + s.extra_skills))


def evaluate_match(s: Settings, job: Job) -> MatchResult:
    vocab = _vocabulary(s)
    job_skills = find_skills(f"{job.title} {job.description}", vocab)
    cv_skills = set(find_skills(s.cv_text, vocab))
    matched = [sk for sk in job_skills if sk in cv_skills]
    missing = [sk for sk in job_skills if sk not in cv_skills]

    skill_score = len(matched) / len(job_skills) if job_skills else 0.5
    title = re.sub(r"[-/]", " ", job.title.lower())
    # best-fitting keyword: share of its words found in the title
    title_score = max(
        (sum(w in title for w in kw.lower().split()) / len(kw.split()) for kw in s.keywords),
        default=0.5,
    )
    score = round(100 * (0.7 * skill_score + 0.3 * title_score))

    instructions = ""
    m = COVER_LETTER_PATTERN.search(job.description)
    if m:
        # the sentence around the mention, e.g. "Please include a cover letter in English."
        start = job.description.rfind(".", 0, m.start()) + 1
        end = job.description.find(".", m.end())
        instructions = job.description[start:end if end != -1 else None].strip()[:300]

    reasons = (
        f"{len(matched)}/{len(job_skills)} skills matched"
        + (f" ({', '.join(matched[:6])})" if matched else "")
        + (f"; missing: {', '.join(missing[:6])}" if missing else "")
    )
    return MatchResult(
        score=score,
        reasons=reasons,
        key_requirements=job_skills,
        matched_skills=matched,
        missing_skills=missing,
        cover_letter_required=bool(m),
        cover_letter_instructions=instructions,
    )
