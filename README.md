# Job Search Agent

An autonomous job-hunting agent that searches job boards, scores each posting
against your CV, writes a tailored cover letter when the posting asks for one,
fills in the application in a real browser for you to review, and logs every
job it handled as a row in `reports/applications.csv`.

**Human in the loop by design:** the agent searches, scores and fills forms, but
it never clicks submit. You review every application and submit it yourself.

Runs fully locally — no paid AI APIs. Matching uses a skill-extraction and
scoring engine, and cover letters are generated from a template plus the most
relevant lines of your CV.

## How it works

```
search job boards ─► location filter ─► score fit vs. CV ─► cover letter if required
   ─► fill application form (Playwright) ─► YOU review & submit ─► row in reports/applications.csv
```

| Step | Module |
|---|---|
| Load personal details, CV, preferences from `.env` | `job_agent/config.py` |
| Search RemoteOK, Arbeitnow, Adzuna (optional free key) | `job_agent/search.py` |
| Skill extraction + match scoring | `job_agent/matcher.py`, `job_agent/skills.py` |
| Cover letter generation | `job_agent/cover_letter.py`, `templates/cover_letter.md` |
| Browser form filling | `job_agent/apply.py` |
| CSV report | `job_agent/report.py` |
| Pipeline / CLI | `job_agent/agent.py`, `job_agent/__main__.py` |

### Location rule

Jobs located in `HOME_LOCATIONS` (default: Bangladesh and its major cities) are
allowed on-site or remote. Jobs anywhere else are kept only if they are remote
and not limited to another region (e.g. "Remote – US only", "Remote, Berlin").
Set `REMOTE_ONLY=true` to accept remote jobs only, even at home.

### Match score (0–100)

- **70% skill coverage** — of the skills the job mentions, how many are in your CV.
- **30% title relevance** — how well the job title matches your best-fitting `JOB_KEYWORDS` entry.

Only jobs whose title matches one of your `JOB_KEYWORDS` are considered.

Jobs below `MIN_MATCH_SCORE` are logged as `low_match` and skipped.

### Cover letters

Written only when the posting mentions a cover/motivation letter (or with
`--always-cover-letter`). The agent fills `templates/cover_letter.md` with the
company, role, your matched skills and the CV lines that best match the job.
To use your own wording, copy the template to `private/cover_letter.md` and edit it.
Letters are saved to `output/cover_letters/`.

## Setup

Requires Python 3.9+.

```bash
python3 -m venv job-agent-env
source job-agent-env/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env              # fill in your details
cp ~/path/to/your-cv.pdf private/cv.pdf
```

`.env`, `private/`, `reports/` and `output/` are gitignored — your personal
details, CV, cover letters and application log never get committed.

## Usage

```bash
python -m job_agent search                 # list matching jobs
python -m job_agent run --dry-run          # score + cover letters, no applying
python -m job_agent run                    # fill forms; you review and submit each one
python -m job_agent report                 # summary of the applications log
```

## The report

`reports/applications.csv` gets one row per job processed:

| date | title | company | location | source | url | match_score | cover_letter | status | notes |
|---|---|---|---|---|---|---|---|---|---|

Statuses: `applied`, `needs_review` (filled, not submitted), `needs_manual`
(login/CAPTCHA/no form), `skipped`, `low_match`, `shortlisted` (dry run).
Jobs already in the report are never processed twice, except `shortlisted`
ones, so a dry run never stops you from applying later.

## Notes

- For each application the browser stays open with the form filled in. Check it,
  answer any extra questions, submit it yourself, then tell the agent whether you did.
- Sites behind logins or CAPTCHAs are logged as `needs_manual` with the link.
- Check each job board's terms of use before automating applications.

## Author

Built by [Ahmad Abdullah](https://github.com/ahmadabdullahcse).
