---
name: job-audit
description: Evaluate your tailored resume against target requirements and score its ATS parseability.
---

# /job-audit — Resume Audit

Audit a generated resume PDF for ATS parsability, keyword coverage, bullet quality, and common mistakes. Outputs a scored report with specific fixes.

## Usage

```
/job-audit                                          ← audit the last generated resume
/job-audit ~/.job-search/output/stripe-swe-2026.pdf ← audit a specific PDF
/job-audit stripe-swe-2026.pdf https://stripe.com/jobs/... ← audit + check keyword coverage vs JD
/job audit                                          ← same via umbrella skill
```

## Steps

### 1. Find the resume to audit

- If a PDF path is provided → use it
- If no path → find the most recently modified PDF in `~/.job-search/output/`:
  ```bash
  ls -t ~/.job-search/output/*.pdf 2>/dev/null | head -1
  ```
- If no PDFs exist → tell the user to run `/job resume` first

### 2. ATS Parsability Check

Test whether the PDF contains real selectable text (not an image/scan):

```bash
python3 -c "
import subprocess, sys
result = subprocess.run(['pdftotext', sys.argv[1], '-'], capture_output=True, text=True)
text = result.stdout.strip()
words = len(text.split())
print(f'words_extracted:{words}')
print(f'sample:{text[:200]}')
" <pdf_path> 2>/dev/null
```

If `pdftotext` is not installed, use:
```bash
python3 -c "
import subprocess, sys
result = subprocess.run(
    ['python3', '-c',
     f'import pdfminer.high_level; print(pdfminer.high_level.extract_text(\"{sys.argv[1]}\"))'],
    capture_output=True, text=True
)
print(result.stdout[:500] if result.stdout else 'extraction_failed')
" 2>/dev/null
```

**Score:**
- ✅ **Pass**: ≥ 100 words extracted — ATS can read this resume
- ⚠️ **Warn**: 10–99 words — partial extraction, likely has text but with formatting issues
- ❌ **Fail**: 0–9 words — resume is an image or unreadable by ATS

### 3. Page Count Check

```bash
python3 -c "
import subprocess, sys
r = subprocess.run(['pdfinfo', sys.argv[1]], capture_output=True, text=True)
for line in r.stdout.splitlines():
    if 'Pages:' in line:
        print(line.strip())
" <pdf_path> 2>/dev/null || echo "Pages: unknown (pdfinfo not installed)"
```

**Score:**
- ✅ **Pass**: 1 page
- ⚠️ **Warn**: 2 pages (acceptable for 10+ years experience)
- ❌ **Fail**: 3+ pages

### 4. Keyword Coverage (only if JD URL or text provided)

If a JD URL is provided:
- Fetch JD text using WebFetch (fallback: ask user to paste)
- Extract required skills from JD (look for "Required", "Must have", "Qualifications" sections)
- Extract PDF text (from Step 2)
- For each required skill: check if it appears in the PDF text (case-insensitive)

```
Score = matched_skills / total_required_skills × 100
```

**Rating:**
- ✅ **Excellent**: ≥ 80% keywords covered
- ⚠️ **Good**: 60–79%
- ❌ **Needs work**: < 60% — list the missing keywords explicitly

Show which keywords are **present** and which are **missing** so the user knows exactly what to add.

### 5. Bullet Quality Check

From the extracted PDF text, identify all bullet points (lines starting with •, -, *, or a dash equivalent).

Check each bullet for:

**A. Quantification** — does the bullet contain a number or percentage?
- Words/patterns that count: `%`, numbers (`10K`, `50M`, `100+`), time (`60%`, `3x`, `2 weeks`), scale (`millions`, `thousands`)
- Score: `quantified_bullets / total_bullets × 100`
- ✅ ≥ 70% quantified | ⚠️ 50–69% | ❌ < 50%

**B. Action verb start** — does each bullet begin with a strong action verb?
- Strong verbs: Built, Led, Designed, Engineered, Architected, Developed, Reduced, Improved, Launched, Drove, Owned, Scaled, Automated, Optimised, Shipped, Created, Established, Grew, Increased, Decreased, Implemented, Delivered
- Weak starts (flag these): "Was responsible for", "Helped with", "Worked on", "Assisted in", "Participated in", "Involved in"
- Score: `action_verb_bullets / total_bullets × 100`
- ✅ ≥ 85% strong | ⚠️ 70–84% | ❌ < 70%

**C. Buzzword check** — flag overused meaningless words:
- Flag if found: "passionate", "innovative", "synergy", "leverage" (as a verb), "dynamic", "proactive", "results-driven", "detail-oriented", "go-getter", "team player", "hardworking", "self-starter", "guru", "ninja", "rockstar", "wizard"
- For each flagged word, show which bullet contains it and suggest a replacement

### 6. Contact Info Check

From the extracted text, verify these fields appear:
- Name (should be first line or largest text)
- Email address (pattern: `@`)
- Phone number (pattern: digits with dashes/spaces)
- LinkedIn URL (pattern: `linkedin.com/in/`)

**Score:** 1 point per field present. ✅ 4/4 | ⚠️ 3/4 | ❌ ≤ 2/4

### 7. Date Consistency Check

From the extracted text, find all date ranges (e.g., "Jan 2022 – Oct 2022", "Sept 2024 – Present").

Check:
- Are all dates in the same format? (Month Year vs MM/YYYY vs just Year)
- Are there any overlapping date ranges? (flag as potential error)
- Is the most recent role listed first?

Flag any inconsistencies found.

### 8. Generate Audit Report

Print a structured report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 RESUME AUDIT — <filename> — <date>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 OVERALL SCORE: <X>/100

 ┌─────────────────────────────────┬────────┬───────┐
 │ Check                           │ Score  │ Pass? │
 ├─────────────────────────────────┼────────┼───────┤
 │ ATS Parsability                 │  25/25 │ ✅    │
 │ Page Count (1 page)             │  15/15 │ ✅    │
 │ Keyword Coverage (vs JD)        │  18/25 │ ⚠️    │
 │ Bullet Quantification           │  12/15 │ ⚠️    │
 │ Action Verb Usage               │  10/10 │ ✅    │
 │ Contact Info Complete           │   5/5  │ ✅    │
 │ Buzzword-free                   │   4/5  │ ⚠️    │
 └─────────────────────────────────┴────────┴───────┘

 ISSUES TO FIX:

 ⚠️  Keyword Coverage (72%) — missing from JD:
    - "idempotency" (appears in JD required skills, not in resume)
    - "distributed tracing" (appears 2x in JD, not in resume)
    → Add these to relevant bullets or skills section

 ⚠️  Bullet Quantification (60%) — bullets without metrics:
    - "Developed breaking change detection engine..."
    - "Built AI Prompt Builder..."
    → Add impact metrics: how many engineers use it? time saved? error rate reduced?

 ⚠️  Buzzword found: "passionate" in summary
    → Replace with: "Led by strong conviction in..." or remove entirely

 ✅  ATS: 847 words extracted — fully parseable
 ✅  1 page
 ✅  All contact fields present
 ✅  92% bullets start with strong action verbs
 ✅  No date inconsistencies

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Want me to fix the issues above? Say "fix audit issues" and I will
 update the .tex file and recompile the PDF.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 9. Offer to fix

After printing the report, ask: **"Want me to fix these issues and recompile?"**

If yes:
- Read the corresponding `.tex` file (same name as PDF, `.tex` extension)
- Apply the specific fixes listed (add missing keywords, strengthen weak bullets, remove buzzwords)
- Recompile with tectonic
- Re-run the audit to confirm score improved

## Scoring weights

| Check | Max points | Why |
|---|---|---|
| ATS Parsability | 25 | A resume ATS can't read is invisible |
| Page count | 15 | Recruiters skip page 2 |
| Keyword coverage (if JD provided) | 25 | ATS keyword matching is real |
| Bullet quantification | 15 | Numbers = credibility |
| Action verb usage | 10 | Weak verbs signal weak ownership |
| Contact info | 5 | Missing email/LinkedIn = missed contact |
| Buzzword-free | 5 | Buzzwords signal filler |

If no JD is provided, redistribute keyword coverage points equally across other checks.

## Notes

- If `pdftotext` is not installed, skip Step 2 extraction and note it in the report. Tell the user to `brew install poppler`.
- If the PDF has fewer than 50 words extracted, warn that it may have been generated with non-standard fonts that embed text as paths — this passes visual review but fails ATS. Suggest recompiling with tectonic using standard fonts.
- Do not penalise for technical terms that aren't in the buzzword list — only flag the specific words listed above.
- The audit is meant to be actionable, not demoralising. Lead with what's good, then show what to fix.
