# /job-discover — Discover Target Companies Dynamically

Automatically scans a seed database of 50+ tier-1 tech companies and searches live job board directories (Greenhouse, Lever) for active job postings in your target city. It aggregates their metadata, creates their API slugs, and compiles them directly into your `~/.job-search/companies.yml` file for scanning.

## Usage

- `/job-discover` — runs the discoverer and updates `companies.yml`

---

## Steps

### 1. Verify Config
Ensure `~/.job-search/config.yml` exists:
```bash
test -f ~/.job-search/config.yml && echo "exists" || echo "missing"
```
If missing, stop and prompt the user to configure their target city and role levels first.

### 2. Run the Discoverer Script
Run the python discovery compiler:
```bash
python3 ~/.job-search/scripts/discover.py
```

### 3. Review Discovered Companies
Print a structured summary of the newly populated `companies.yml`:
```
✓ Companies discovered and saved to ~/.job-search/companies.yml

Discovered Companies Summary:
  Location Target: <target.city from config.yml>
  Total Companies: <count from companies.yml>
  
Top Targets populated:
  <list the top 5 companies added, e.g. Stripe, Airbnb, Notion, Vercel, Linear>

Next steps:
  1. Open ~/.job-search/companies.yml to verify or manually adjust tiers/notes.
  2. Run /job scan to search these companies for matching open roles.
```

---

## Notes
- **Locations Evaluated**: The discoverer checks if a company has a matching office location in your target city OR if it offers remote postings.
- **Deduplication**: Companies are deduplicated by their unique API boards (slug + API host name) so you never scan the same board twice.
- **Tier Assignment**: 
  - Seed-matching companies are assigned to **Tier 2** (Apply with competing offers).
  - Newly harvested live-search companies are assigned to **Tier 3** (Monitor and scan).
