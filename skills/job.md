# /job — Umbrella Orchestrator

Single entry point for the entire job search workflow. Understands natural language, checks current state, and chains the right sub-skills automatically. You never need to remember which individual skill to call.

## Usage

```
/job                                    → status dashboard + guided next step
/job airbnb                             → intel report for Airbnb + suggest resume
/job resume airbnb payments             → generate tailored resume for Airbnb Payments
/job resume https://careers.airbnb.com/…→ generate resume from JD URL
/job scan                               → scan all target companies for open roles
/job scan stripe databricks             → scan specific companies only
/job intel stripe                       → salary + interview intel for Stripe
/job intel stripe --salary-only         → TC data only
/job full airbnb stripe                 → intel + resume for multiple companies in sequence
/job profile                            → re-parse resume and update profile
/job profile ~/Downloads/resume.pdf     → parse a specific file
/job status                             → show what's been done, what's pending
```

---

## Step 1 — Detect intent from arguments

Parse the user's input after `/job`:

| Input pattern | Intent | Action |
|---|---|---|
| No args / `status` | Dashboard | Show step 2 status check |
| `profile [file?]` | Parse resume | Follow job-profile.md |
| `scan [companies?]` | Find roles | Follow job-scan.md |
| `intel <company> [role?] [--flags]` | Research | Follow job-intel.md |
| `resume <company/URL> [--flags]` | Generate PDF | Follow job-resume.md |
| `full <company> [company…]` | Full pipeline | Intel → resume for each company |
| `<company name only>` | Smart mode | Auto-detect best next action (see Step 3) |

---

## Step 2 — Always check current state first

Before doing anything, silently check:

```bash
# Profile exists and is recent?
ls -la ~/.job-search/profile.json 2>/dev/null

# Last scan results?
ls -la ~/.job-search/scan-results.json 2>/dev/null

# Recent intel reports?
ls ~/.job-search/intel/ 2>/dev/null

# Recent generated resumes?
ls ~/.job-search/output/*.pdf 2>/dev/null | tail -5
```

Use this state to:
- Warn if profile is missing (always run job-profile first)
- Show how stale the last scan is
- Avoid re-running intel if a recent report (<7 days) exists for the same company

---

## Step 3 — Smart mode (company name only)

When user types `/job <company>` with no other instruction, use this decision tree:

```
Does profile.json exist?
  NO  → "Profile not found. Let me parse your resume first." → run job-profile
  YES ↓

Does intel report exist for this company (<7 days old)?
  NO  → Run job-intel for this company first
  YES → "Intel report found (date). Skipping fresh search."

Are there recent scan results for this company (<14 days)?
  NO  → Run job-scan for this company
  YES → Show top roles from cached scan-results.json

Ask: "Which role do you want a resume for?" → show role list from scan/intel
User picks role → run job-resume
```

---

## Step 4 — Status dashboard (no args or `status`)

Print a clear status overview:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 JOB SEARCH STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Profile      ✅  <name> | <current role> | last updated <date>
 Last scan    ⚠️  <date> — <N> roles found across <M> companies (14 days ago)
 Intel        ✅  Airbnb (3 days ago)  Stripe (—)  Databricks (—)
 Resumes      ✅  airbnb-senior-swe-payments-2026-05-17.pdf

 SUGGESTED NEXT STEPS:
  1. /job intel stripe          → get TC + interview data for Stripe
  2. /job resume stripe         → generate Stripe resume (scan found 3 open roles)
  3. /job scan                  → refresh job listings (last scan was 14 days ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Populate all fields dynamically from actual files in `~/.job-search/`.

---

## Step 5 — Full pipeline mode (`/job full <companies>`)

For each company in the list, run in sequence:
1. Check if intel report is fresh → if not, run job-intel
2. Show top matching roles from intel/scan
3. Ask user to confirm which role to target (or proceed with best match)
4. Run job-resume for that role
5. Confirm PDF generated, print path

Example output for `/job full stripe airbnb`:
```
[1/2] STRIPE
  → Running intel... ✅ TC: $220–280K | Interview: 5 rounds
  → Best matching role: Staff SWE – Search Platform
  → Generating resume... ✅ ~/.job-search/output/stripe-staff-search-2026-05-17.pdf

[2/2] AIRBNB
  → Intel report found (3 days ago) ✅
  → Best matching role: Senior SWE – Payments (G9 target)
  → Generating resume... ✅ ~/.job-search/output/airbnb-senior-swe-payments-2026-05-17.pdf

Done. 2 resumes generated. Run /job status to see full pipeline.
```

---

## Skill delegation rules

When this skill delegates to a sub-skill, follow that skill's instructions exactly as written in:
- `~/.claude/skills/job-profile.md` — for profile parsing
- `~/.claude/skills/job-scan.md` — for company scanning
- `~/.claude/skills/job-intel.md` — for salary + interview intel
- `~/.claude/skills/job-resume.md` — for resume generation

Do not duplicate the logic here — read and follow those files at delegation time.

---

## Notes

- Always check profile.json exists before running scan, intel, or resume. If missing, prompt the user to run `/job profile` first.
- Never re-generate a resume that already exists for the same company+role+date without asking.
- In full pipeline mode, ask for confirmation before generating resumes if more than 2 companies are in the list.
- Keep responses concise — the user wants to move fast. Show results, not explanations.
