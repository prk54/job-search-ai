# job-search-ai

> AI-powered job search skill suite for [Claude Code](https://claude.ai/code). Parse any resume, find matching roles at target companies with real-time TC data, generate tailored LaTeX PDF resumes, and get deep salary + interview intelligence from Levels.fyi, Glassdoor, Blind, Leetcode Discuss, AmbitionBox, Reddit and more — all using your existing Claude Code subscription.

**No API keys. No servers. No extra cost.**

```
/job-build                               → build base resume (interview or paste)
/job-profile ~/Downloads/resume.pdf      → extracts your profile from existing resume
/job-scan stripe airbnb databricks       → finds open roles + TC data
/job-resume https://careers.airbnb.com/… → tailored 1-page PDF in 60s
/job-intel stripe "senior software engineer" → salary + interview intel from 7 portals
/job-audit                               → audits your resume against a JD
```

---

## What it does

| Skill | Description |
|---|---|
| `/job-build` | Build your base profile via an interactive interview or pasting free text |
| `/job-profile` | Upload any resume (PDF, LinkedIn export) → structured profile stored locally |
| `/job-scan` | Scans target company career pages (via public APIs) → open roles + TC benchmarks |
| `/job-resume` | Takes a JD URL or text + your profile → generates a keyword-tailored LaTeX PDF |
| `/job-intel` | Aggregates salary data + interview process from 7+ portals → structured report |
| `/job-audit` | Audits your resume for ATS parsability, keyword coverage, and bullet quality |

### Why Claude Code skills vs a web app?

- **Zero cost** — uses your existing Claude Code subscription, no Anthropic API key needed
- **Full power** — Claude reasons about your profile vs JD, not just keyword matching
- **MCP-native** — integrates with Puppeteer, Google Drive, Gmail out of the box
- **Hackable** — skills are markdown files you can read, edit, and extend in minutes

---

## Prerequisites

| Tool | Install | Why |
|---|---|---|
| [Claude Code](https://claude.ai/code) | Any subscription tier | Runs the AI skills |
| [tectonic](https://tectonic-typesetting.github.io) | `brew install tectonic` | Compiles LaTeX → PDF locally |

That's it. No Node.js, no Python, no Docker.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/prk54/job-search-ai.git
cd job-search-ai

# 2. Run the installer
chmod +x install.sh && ./install.sh

# 3. Customise your target companies and preferences
nano ~/.job-search/companies.yml   # add/remove companies
nano ~/.job-search/config.yml      # set your city, TC target, role level

# 4. Open Claude Code in any project and start using the skills
claude
```

Then inside Claude Code:

```
/job-profile ~/Downloads/resume.pdf
```

---

## Usage

### `/job-build` — Build base resume

```
/job-build                                ← starts interactive interview wizard
/job-build --text                         ← paste raw text directly
/job-build --pdf-only                     ← compile base PDF from existing profile.json
```

Builds your first base profile via dynamic questions or free text, refines your work bullets into impact metrics, and compiles it to a base LaTeX PDF.

---

### `/job-profile` — Parse your resume

```
/job-profile ~/Downloads/resume.pdf
/job-profile ~/Downloads/Profile.pdf      ← LinkedIn PDF export also works
/job-profile                              ← paste resume text directly
```

Extracts and saves your profile to `~/.job-search/profile.json`. Run this once (or when your resume changes).

---

### `/job-scan` — Find open roles + TC data

```
/job-scan                                 ← scan all companies in companies.yml
/job-scan stripe airbnb databricks        ← scan specific companies
/job-scan --tc-only                       ← refresh TC data only (no role scan)
```

Hits Greenhouse, Ashby, and Lever APIs directly (zero tokens, no auth) + Puppeteer for others. Outputs a prioritised table:

```
 TIER 1 — Apply First
┌────────────┬──────────────────────────────┬──────────────┬─────┐
│ Company    │ Role                         │ TC Est       │ Fit │
├────────────┼──────────────────────────────┼──────────────┼─────┤
│ Stripe     │ Staff SWE – Search Platform  │ $220–280K    │ High│
│ Airbnb     │ Senior SWE – Payments        │ $180–240K    │ High│
└────────────┴──────────────────────────────┴──────────────┴─────┘
```

TC data sourced from levels.fyi via WebSearch.

---

### `/job-resume` — Generate tailored resume PDF

```
/job-resume https://careers.airbnb.com/positions/7581839/
/job-resume                               ← paste JD text directly
/job-resume <URL> --template jake         ← Jake's Resume style (default)
/job-resume <URL> --template classic      ← classic single-column style
/job-resume <URL> --save-drive            ← auto-save PDF to Google Drive
```

What happens:
1. Fetches the JD (Puppeteer or WebFetch)
2. Analyses required skills and keywords
3. Rewrites your bullets to lead with most relevant experience
4. Injects JD keywords naturally into bullet text
5. Compiles to a 1-page PDF via `tectonic`
6. Opens the PDF

Output: `~/.job-search/output/<company>-<role>-<date>.pdf`

---

### `/job-intel` — Salary + interview intelligence

Searches **Levels.fyi, Glassdoor, Blind, Leetcode Discuss, AmbitionBox, Reddit, Naukri** simultaneously and synthesises the results into one report.

```
/job-intel stripe                              ← full report, all levels
/job-intel airbnb "senior software engineer"   ← role-specific
/job-intel uber bangalore                      ← location-specific
/job-intel databricks --salary-only            ← TC data only
/job-intel google --interview-only             ← interview process only
```

Output includes:
- **Salary table** — base, equity, bonus, total comp by level with real offer examples
- **Negotiation signals** — where companies move, what levers to pull
- **Interview rounds breakdown** — number of rounds, type (DSA / system design / behavioural), duration
- **Topics seen** — DSA patterns, system design questions from recent candidates
- **Difficulty rating** — aggregated from Glassdoor + community reports
- **Tips from recent candidates** — what worked, what didn't

Report saved to `~/.job-search/intel/<company>-<date>.md`.

---

### `/job-cover` — Tailored cover letter PDF

```
/job-cover https://careers.airbnb.com/positions/7581839/
/job-cover                                ← paste JD text directly
/job-cover <URL> --template career-ops    ← use specific template
```

Generates a tailored single-page cover letter matching the template formatting and contact header of your resume.

---

### `/job-apply` — Auto-fill application forms

```
/job-apply https://boards.greenhouse.io/stripe/jobs/123456
/job-apply <JD-url> /path/to/specific/resume.pdf
```

Automatically opens a non-headless Chrome browser via Playwright, fills out all standard input fields (Name, Email, Phone, Location, Social Profiles), attaches the latest tailored resume PDF for that company, and leaves the browser open for final review and manual submit.

---

### `/job-audit` — Resume Quality Audit

```
/job-audit                                ← audits the last generated resume PDF
/job-audit /path/to/specific/resume.pdf
/job-audit <pdf-path> <JD-url>            ← checks keyword coverage vs a JD
```

Audits PDF resumes for selectable text (ATS parsability), page counts, keyword coverage, verb strength, and overused buzzwords, and offers to auto-fix and recompile the PDF.

---


## Configuration

### `~/.job-search/config.yml`

```yaml
target:
  city: "San Francisco"        # your preferred job location
  tc_target: "$200K USD"       # your TC goal (shown in scan output)
  currency: "USD"              # USD, INR, EUR, GBP, etc.
  role_levels:
    - Senior
    - Staff
    - Principal
  role_keywords:
    - Software Engineer
    - SWE
    - Full Stack Engineer
```

### `~/.job-search/companies.yml`

Copy from `templates/companies.example.yml` and customise:

```yaml
companies:
  - name: Stripe
    careers_url: https://stripe.com/jobs
    api: greenhouse
    api_slug: stripe
    tc_range: "$180–280K"
    tier: 1            # 1 = apply first, 2 = with negotiation, 3 = monitor, practice = reps only
    notes: "Strong match for payments + search infra roles"
```

See `templates/companies.example.yml` for 30+ pre-configured companies.

---

## LaTeX Templates

Two templates included, both single-page, ATS-optimised:

| Template | Flag | Style |
|---|---|---|
| Jake's Resume | `--template jake` (default) | Clean, minimal, widely used |
| Classic | `--template classic` | Slightly more compact, different section spacing |

To use a custom template: place your `.tex` file in `~/.job-search/templates/` and reference it with `--template <filename-without-extension>`.

---

## File Structure (after install)

```
~/.job-search/
├── config.yml            ← your preferences (city, TC target, role level)
├── profile.json          ← extracted from your resume (/job-profile writes this)
├── companies.yml         ← your target companies
├── scan-results.json     ← latest scan output
├── templates/
│   ├── jake.tex          ← Jake's Resume LaTeX template
│   └── classic.tex       ← classic LaTeX template
├── scripts/
│   └── apply.py          ← browser auto-fill automation script
└── output/               ← generated PDFs and .tex files

~/.claude/skills/
├── job.md                ← orchestrator skill
├── job-build.md          ← /job-build skill
├── job-profile.md        ← /job-profile skill
├── job-scan.md           ← /job-scan skill
├── job-resume.md         ← /job-resume skill
├── job-intel.md          ← /job-intel skill
└── job-audit.md          ← /job-audit skill
```

---

## Uninstall

```bash
./uninstall.sh
```

Removes `~/.job-search/` and the seven skill files. Does not touch your Claude Code installation.

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

Ideas for extensions:
- `/job-prep` — generate STAR interview stories and roleplay mock interviews per company
- `/job-track` — Kanban tracker for application pipeline
- `/job-negotiate` — evaluate offer letters and draft counter-offer email scripts
- Additional LaTeX templates
- Support for more ATS systems (SmartRecruiters, iCIMS, Workday)

---

## License

MIT — use it, fork it, build on it.

---

*Built with [Claude Code](https://claude.ai/code). Skills are plain markdown — read them, edit them, make them yours.*
