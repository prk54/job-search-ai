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
Filter results using values from `config.yml`:
- Title must contain at least one of `target.role_levels` (e.g. Senior, Staff) AND one of `target.role_keywords` (e.g. Software Engineer)
- Title must NOT contain any of `target.exclude_keywords`
- Location must match `target.city` OR contain "Remote"

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
 JOB SCAN — <city from config> <role_levels> Roles — <today's date>
 TC Target: <tc_target from config>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 TIER 1 — Apply First
┌────────────┬─────────────────────────────────┬──────────────┬───────────────┬──────┐
│ Company    │ Role                            │ TC Est       │ Meets Target  │ Fit  │
├────────────┼─────────────────────────────────┼──────────────┼───────────────┼──────┤
│ Stripe     │ Staff SWE – Search Platform     │ $220–280K    │ ✅            │ High │
│ Airbnb     │ Senior SWE – Payments           │ $180–240K    │ ✅            │ High │
└────────────┴─────────────────────────────────┴──────────────┴───────────────┴──────┘

 TIER 2 — Apply with Competing Offers
┌────────────┬─────────────────────────────────┬──────────────┬───────────────┬──────┐
│ Databricks │ Staff SWE – Fullstack           │ $200–300K    │ Likely        │ High │
│ Uber       │ Senior SWE – Data Solutions     │ $160–250K    │ Likely        │ High │
└────────────┴─────────────────────────────────┴──────────────┴───────────────┴──────┘

 PRACTICE — Interview Reps
 <company names> — roles found, details omitted

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
      "company": "<company name>",
      "tier": 1,
      "tc_range": "<range from companies.yml or freshly fetched>",
      "meets_target": true,
      "roles": [
        {
          "title": "<role title>",
          "url": "<direct JD URL>",
          "location": "<city>",
          "fit": "High"
        }
      ]
    }
  ]
}
```

## Notes

- Only surface roles matching the user's configured `role_levels` and `role_keywords` — never show internships, junior, or management roles unless they explicitly appear in those lists.
- For companies without a clean API (Workday, Taleo, iCIMS), use Puppeteer to browse the careers portal — filter by the user's configured city and role keywords.
- TC data from `companies.yml` is the baseline. Only do a fresh levels.fyi search if the user runs `--tc-only` or the cached data is clearly stale (>60 days old).
- If a company has no open matching roles, include it in the output with "No open roles found" — do not silently omit it.
- The "Meets Target" column compares each role's TC estimate against `target.tc_target` from `config.yml`.
