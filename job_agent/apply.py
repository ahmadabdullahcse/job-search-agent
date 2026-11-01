"""Fills application forms in a real browser with Playwright.

Job sites differ wildly, so this is best-effort: it fills the common fields
(name, email, phone, links, CV upload, cover letter), then hands control to you.
The agent never clicks submit: you review every application and submit it
yourself. Pages behind a login or CAPTCHA are logged as "needs_manual".
"""
from __future__ import annotations

import re
from typing import Optional

from .config import Settings

# field key -> patterns matched against an input's name/id/label/placeholder
FIELD_PATTERNS = {
    "first_name": r"first.?name|given.?name|vorname",
    "last_name": r"last.?name|surname|family.?name|nachname",
    "full_name": r"^name$|full.?name|your.?name",
    "email": r"e-?mail",
    "phone": r"phone|mobile|telefon",
    "location": r"location|city|address|wohnort",
    "linkedin_url": r"linkedin",
    "github_url": r"github",
    "portfolio_url": r"portfolio|website|personal.?site",
    "work_authorization": r"authori[sz]ation|visa|work.?permit",
    "notice_period": r"notice|start.?date|availability",
    "expected_salary": r"salary|compensation|gehalt",
}
BLOCKER_PATTERN = re.compile(r"captcha|sign in to apply|log in to apply|create an account", re.I)


def _field_values(s: Settings) -> dict:
    p = s.profile
    return {
        "first_name": p.first_name, "last_name": p.last_name, "full_name": p.full_name,
        "email": p.email, "phone": p.phone, "location": p.location,
        "linkedin_url": p.linkedin_url, "github_url": p.github_url,
        "portfolio_url": p.portfolio_url, "work_authorization": p.work_authorization,
        "notice_period": p.notice_period, "expected_salary": p.expected_salary,
    }


def _describe(el) -> str:
    """name/id/placeholder/aria-label plus the text of an associated <label>."""
    return el.evaluate(
        """e => [e.name, e.id, e.placeholder, e.getAttribute('aria-label'),
                 e.labels && e.labels[0] ? e.labels[0].innerText : '']
                .filter(Boolean).join(' ')"""
    )


def _fill_form(page, s: Settings, cover_letter: Optional[str]) -> int:
    values = _field_values(s)
    filled = 0
    for el in page.query_selector_all("input:visible, textarea:visible"):
        kind = (el.get_attribute("type") or "text").lower()
        desc = _describe(el)
        if kind == "file":
            if s.cv_path and re.search(r"cv|resume|lebenslauf|file|upload", desc, re.I):
                el.set_input_files(str(s.cv_path))
                filled += 1
            continue
        if kind in {"hidden", "submit", "button", "checkbox", "radio", "password"}:
            continue
        if el.input_value():
            continue
        if cover_letter and re.search(r"cover|motivation|anschreiben|message", desc, re.I):
            el.fill(cover_letter)
            filled += 1
            continue
        for key, pattern in FIELD_PATTERNS.items():
            if values[key] and re.search(pattern, desc, re.I):
                el.fill(values[key])
                filled += 1
                break
    return filled


def apply_to_job(s: Settings, url: str, cover_letter: Optional[str]) -> tuple:
    """Returns (status, notes). Status: applied | needs_review | needs_manual | skipped."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)

            # Many job pages show the form only after clicking "Apply".
            apply_btn = page.get_by_role("link", name=re.compile(r"^apply", re.I)).or_(
                page.get_by_role("button", name=re.compile(r"^apply", re.I))
            )
            if apply_btn.count():
                apply_btn.first.click()
                page.wait_for_timeout(2500)

            if BLOCKER_PATTERN.search(page.content()):
                return "needs_manual", "Login or CAPTCHA required"

            filled = _fill_form(page, s, cover_letter)
            if filled == 0:
                return "needs_manual", "No application form detected"

            answer = input(
                f"    Filled {filled} fields. Review the browser, finish any extra questions "
                "and submit.\n    Did you submit? [y]es / [n]o / [s]kip: "
            ).strip().lower()
            if answer.startswith("y"):
                return "applied", f"Submitted after review ({filled} fields auto-filled)"
            if answer.startswith("s"):
                return "skipped", "Skipped by user"
            return "needs_review", f"Filled {filled} fields; not submitted"
        except Exception as exc:
            return "needs_manual", f"Browser error: {exc}"[:300]
        finally:
            browser.close()
