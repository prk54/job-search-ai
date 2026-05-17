# Job Search Workspace

This directory is your job search workspace. Use `/job` as the single entry point — it orchestrates all skills automatically.

## Available skills

| Command | What it does |
|---|---|
| `/job` | Status dashboard + suggested next step |
| `/job <company>` | Smart mode — intel + resume for that company |
| `/job profile [file]` | Parse resume and update profile |
| `/job scan [companies]` | Find open roles at target companies |
| `/job intel <company>` | Salary + interview data from 7 portals |
| `/job resume <URL or company>` | Generate tailored 1-page LaTeX PDF |
| `/job audit [pdf] [jd-url]` | Audit resume for ATS, keywords, quality |
| `/job full co1 co2 co3` | Full pipeline for multiple companies |

## Your profile

<!-- This section is auto-populated when you run /job profile -->
<!-- Run: /job profile ~/Downloads/resume.pdf -->

Profile not yet generated. Run `/job profile ~/path/to/resume.pdf` to get started.

## Target companies

Read `~/.job-search/companies.yml` for the full list with TC ranges and API config.

Tiers:
- **Tier 1** — Apply first (highest TC + best fit)
- **Tier 2** — Apply with competing offers
- **Tier 3** — Monitor or target Staff level
- **Practice** — Interview reps only

## Key rules

- Always check profile.json exists before running scan, intel, or resume
- Reuse cached intel reports if < 7 days old
- Reuse cached scan results if < 14 days old
- All TC data is in the currency set in `~/.job-search/config.yml`
- Generated resumes are in `~/.job-search/output/`
- Intel reports are in `~/.job-search/intel/`
