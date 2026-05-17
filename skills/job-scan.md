# /job-scan — Find Open Roles + TC Data at Target Companies

Scan target companies for open roles matching your configured seniority and location, fetch TC data from levels.fyi, and output a prioritised table with profile fit scores.

## Usage

- `/job-scan` — scan all companies in `~/.job-search/companies.yml`
- `/job-scan stripe airbnb databricks` — scan specific companies (space-separated, case-insensitive)
- `/job-scan --tc-only` — skip role scanning, just refresh TC data for all companies

## Steps

### 1. Load data
- Read `~/.job-search/companies.yml` — company list, API types, TC benchmarks
- Read `~/.job-search/profile.json` — user's skills for fit scoring
- If `profile.json` doesn't exist, tell the user to run `/job-profile` first.

### 2. For each company — find open roles

**Priority order for fetching jobs:**

**A. Greenhouse API** (if `api: greenhouse`):
```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/<api_slug>/jobs?content=true" | python3 -m json.tool
```
Filter results: keep jobs where title contains any of: `Senior`, `Staff`, `Principal` AND contains any of: `Software Engineer`, `SWE`, `Engineer` AND location contains `Bengaluru` OR `Bangalore` OR `India` OR `Remote`.

**B. Ashby API** (if `api: ashby`):
```bash
curl -s "https://api.ashbyhq.com/posting-api/job-board/<api_slug>?includeCompensation=true"
```
Same title/location filtering.

**C. Lever API** (if `api: lever`):
```bash
curl -s "https://api.lever.co/v0/postings/<api_slug>?mode=json"
```
Same filtering.

**D. No API / fallback** (if `api: null`):
Use WebSearch: `site:<careers_url_domain> senior software engineer bangalore 2026`
OR use Puppeteer to navigate to the careers URL and extract job titles + links.

### 3. Fetch TC data from levels.fyi

For each company, use WebSearch:
```
"<company name>" senior software engineer bangalore levels.fyi 2025 OR 2026
```

Extract: median TC range in INR Cr. If already stored in `companies.yml` and was updated within 30 days, use the cached value and skip the search.

### 4. Score profile fit

For each open role found:
- Fetch the JD text (WebFetch or Puppeteer on the job URL)
- Count keyword overlaps between JD required skills and `profile.json` skills
- Score: **High** (>70% overlap), **Medium** (40–70%), **Low** (<40%)

### 5. Output results table

Group by tier. Format:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 JOB SCAN RESULTS — Bangalore Senior/Staff SWE — May 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 TIER 1 — Apply First (TC ≥ 1.5 Cr reliable)
┌────────────┬─────────────────────────────────┬──────────────┬─────────────┬──────┐
│ Company    │ Role                            │ TC Est       │ Meets 1.5Cr │ Fit  │
├────────────┼─────────────────────────────────┼──────────────┼─────────────┼──────┤
│ Stripe     │ Staff SWE – Search Platform     │ 1.33–1.71 Cr │ ✅          │ High │
│ Airbnb     │ Senior SWE – Payments           │ 1.12–1.72 Cr │ ✅          │ High │
│ Broadcom   │ [No open Bangalore SWE roles]   │ 1.77–1.88 Cr │ ✅          │ —    │
└────────────┴─────────────────────────────────┴──────────────┴─────────────┴──────┘

 TIER 2 — Apply with Competing Offers
┌────────────┬─────────────────────────────────┬──────────────┬─────────────┬──────┐
│ Databricks │ Staff SWE – Fullstack           │ up to 1.7 Cr │ Likely      │ High │
│ Uber       │ Senior SWE – Data Solutions     │ 1.06–1.75 Cr │ Likely      │ High │
│ Atlassian  │ Senior Full Stack SWE           │ 1.05–1.77 Cr │ At P60      │ High │
└────────────┴─────────────────────────────────┴──────────────┴─────────────┴──────┘

 PRACTICE — Interview Reps (TC not the goal)
 Flipkart · Postman · Okta — roles found, details omitted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 8 roles found across 7 companies
 Run /job-resume <JD URL> to generate a tailored resume for any role.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Include the JD URL for each role so the user can pass it directly to `/job-resume`.

### 6. Save results
Write the full results to `~/.job-search/scan-results.json`:
```json
{
  "scanned_at": "2026-05-17T...",
  "results": [
    {
      "company": "Stripe",
      "tier": 1,
      "tc_range": "1.33–1.71 Cr",
      "meets_target": true,
      "roles": [
        {
          "title": "Staff Software Engineer – Search Platform",
          "url": "https://stripe.com/jobs/listing/...",
          "location": "Bengaluru",
          "fit": "High"
        }
      ]
    }
  ]
}
```

## Notes

- Be aggressive with filtering: only surface **Senior, Staff, or Principal** Software Engineer roles. Skip product managers, designers, sales, data analysts, ML researchers unless the title clearly says "Software Engineer".
- For Broadcom/Nvidia/Uber without a clean API, use Puppeteer to browse the careers portal — filter by location (Bangalore) and keyword (Software Engineer).
- TC data from `companies.yml` is the baseline. Only do a fresh levels.fyi search if the user runs `--tc-only` or the cached data is clearly stale (>60 days old).
- If a company has no open Bangalore roles, say so clearly — don't omit them silently.
