---
name: job-intel
description: Fetch interview questions and total compensation benchmarks for a company.
---

# /job-intel — Salary + Interview Intelligence from Multiple Portals

Aggregates real salary data and interview process intel for a company + role from Levels.fyi, Glassdoor, Blind, Leetcode Discuss, AmbitionBox, Reddit, and more. Outputs a structured report so you walk into every interview knowing exactly what to expect and what to negotiate.

## Usage

- `/job-intel stripe` — full salary + interview report for Stripe (all SWE levels)
- `/job-intel airbnb "senior software engineer"` — specific role
- `/job-intel uber bangalore` — location-specific data
- `/job-intel databricks --salary-only` — TC data only, skip interview process
- `/job-intel google --interview-only` — interview process only, skip salary
- `/job-intel meta staff` — staff-level specific data

## Steps

### 1. Parse arguments

Extract from the user's input:
- `company` — required (e.g. "stripe", "airbnb")
- `role` — optional (e.g. "senior software engineer", "staff swe")
- `location` — optional, defaults to `target.city` from `~/.job-search/config.yml`
- `--salary-only` / `--interview-only` flags

Read `~/.job-search/config.yml` for defaults (city, currency, role_levels).

### 2. Run salary research (skip if --interview-only)

Run each search in sequence. Print a one-line progress indicator before each search so the user knows it's working (e.g. `→ Searching Levels.fyi...`). This takes 3–6 minutes for all portals — set expectations upfront.

**A. Levels.fyi**
```
site:levels.fyi "<company>" software engineer <role> <location> salary 2025 OR 2026
```
Look for: base salary, equity (RSU/4yr), bonus, total comp. Note the level (L3/L4/L5/Staff etc.)

**B. Glassdoor**
```
site:glassdoor.com "<company>" software engineer salary <location> 2025 OR 2026
```
Look for: salary range, base + bonus breakdown, reported year.

**C. Blind (TeamBlind)**
```
site:teamblind.com "<company>" salary offer <role> <location> 2025 OR 2026
```
Look for: real offer breakdowns (base + RSU + bonus), level at offer.

**D. Leetcode Discuss**
```
site:leetcode.com/discuss "<company>" offer compensation <role> <location> 2025 OR 2026
```
Look for: verified offer posts with full TC breakdown.

**E. AmbitionBox** (especially useful for India)
```
site:ambitionbox.com "<company>" software engineer salary <location>
```
Look for: India-specific salary ranges, fresher vs experienced breakdown.

**F. LinkedIn Salary**
```
site:linkedin.com/salary "<company>" software engineer <location>
```

**G. Reddit**
```
site:reddit.com "<company>" salary offer compensation software engineer 2025 OR 2026
```
Focus on: r/cscareerquestions, r/leetcode, r/developersIndia, r/india

After all searches, synthesise into a clean salary table:

```
── SALARY DATA ─────────────────────────────────────────────────────────
 Company: Stripe  |  Role: Senior Software Engineer  |  Location: Bangalore
 Currency: INR    |  Data freshness: 2025–2026

 Level        Base          Equity (4yr)   Bonus    Total Comp    Source
 ─────────────────────────────────────────────────────────────────────────
 L3 (Senior)  ₹65–75L       $120–160K RSU  15–20%   ₹1.3–1.7 Cr  levels.fyi
 L4 (Staff)   ₹85–100L      $200–250K RSU  20–25%   ₹2.0–2.5 Cr  levels.fyi, Blind
 ─────────────────────────────────────────────────────────────────────────

 Real offer examples (from Leetcode Discuss / Blind, 2025–2026):
  • L3 Bangalore, Nov 2025: ₹72L base + $140K RSU/4yr + 18% bonus ≈ ₹1.53 Cr TC
  • L3 Bangalore, Mar 2026: ₹68L base + $120K RSU/4yr + 15% bonus ≈ ₹1.35 Cr TC

 Negotiation signals:
  • Typical band width at this level: ~20–25%
  • RSU is the primary lever — equity is where Stripe moves most
  • Competing offer from Databricks / Airbnb consistently unlocks 10–15% uplift
────────────────────────────────────────────────────────────────────────
```

### 3. Run interview process research (skip if --salary-only)

Search all portals **in parallel**:

**A. Leetcode Discuss**
```
site:leetcode.com/discuss "<company>" interview experience <role> 2025 OR 2026
```
Look for: number of rounds, round types (DSA/system design/behavioural/take-home), difficulty, question topics, rejection/offer ratio.

**B. Glassdoor Interview Reviews**
```
site:glassdoor.com "<company>" interview questions software engineer 2025 OR 2026
```
Look for: interview difficulty rating, specific questions asked, process timeline.

**C. Blind**
```
site:teamblind.com "<company>" interview process <role> 2025 OR 2026
```
Look for: interview structure, bar-raiser details, common rejections.

**D. Reddit**
```
site:reddit.com "<company>" interview experience software engineer 2025 OR 2026
```
Focus on r/cscareerquestions, r/leetcode, r/developersIndia

**E. Naukri / AmbitionBox** (India-specific)
```
site:naukri.com "<company>" interview questions software engineer
site:ambitionbox.com "<company>" interview
```

**F. Company engineering blog / Tech blog**
```
"<company>" engineering blog interview process hiring bar 2025 OR 2026
```
Sometimes companies publish their own hiring bar publicly.

After all searches, synthesise into:

```
── INTERVIEW PROCESS ────────────────────────────────────────────────────
 Company: Stripe  |  Role: Senior Software Engineer
 Data: Glassdoor, Leetcode Discuss, Blind, Reddit (2025–2026 reports)

 TIMELINE
  Recruiter screen (30 min) → Technical phone screen (60 min) →
  Virtual onsite (4–5 rounds, ~1 day) → Offer

 ROUND BREAKDOWN
 ┌──────────────────────────────┬────────────┬──────────────────────────────┐
 │ Round                        │ Duration   │ What to expect               │
 ├──────────────────────────────┼────────────┼──────────────────────────────┤
 │ Recruiter screen             │ 30 min     │ Background, motivation, comp │
 │ Technical phone screen       │ 60 min     │ 1–2 DSA problems (Medium)    │
 │ Onsite 1 — Coding            │ 60 min     │ 2 DSA problems (Med/Hard)    │
 │ Onsite 2 — System Design     │ 60 min     │ Design a payment/API system  │
 │ Onsite 3 — Coding            │ 60 min     │ 2 DSA problems (Med/Hard)    │
 │ Onsite 4 — Behavioural       │ 45 min     │ Leadership principles, STAR  │
 │ Onsite 5 — Hiring manager    │ 30 min     │ Career goals, team fit       │
 └──────────────────────────────┴────────────┴──────────────────────────────┘

 CODING TOPICS SEEN (from recent reports)
  ✦ Most common: Arrays/strings, Trees/graphs, Dynamic programming
  ✦ Difficulty: Mostly Leetcode Medium, some Hard in final rounds
  ✦ Language: Any — Python and Java are most common at this company

 SYSTEM DESIGN TOPICS SEEN
  ✦ Design a payment processing system
  ✦ Design a rate limiter / API gateway
  ✦ Design a distributed job queue
  ✦ Design a fraud detection system

 BEHAVIOURAL SIGNALS (from Glassdoor + Blind)
  ✦ Strong emphasis on "why Stripe" and knowledge of Stripe's products
  ✦ Conflict resolution and cross-functional collaboration stories
  ✦ Examples of ownership and impact at scale

 DIFFICULTY RATING
  ✦ Glassdoor: 3.8/5 (Hard)
  ✦ Offer rate from onsite (community estimate): ~15–20%

 TIPS FROM RECENT CANDIDATES
  • Practice Medium/Hard graph and DP problems — they come up consistently
  • System design: know distributed payment flows and idempotency
  • Research Stripe's products deeply — interviewers test genuine interest
  • Timeline from application to offer: typically 3–5 weeks

────────────────────────────────────────────────────────────────────────
```

### 4. Save report

Write to `~/.job-search/intel/<company-slug>-<YYYY-MM-DD>.md`

Create the directory if it doesn't exist:
```bash
mkdir -p ~/.job-search/intel
```

### 5. Print summary and file location

```
✅ Intel report ready: ~/.job-search/intel/<company>-<date>.md

  Salary range (Senior): <range>
  Total Comp (estimated): <TC>
  Interview rounds: <N>
  Difficulty: <rating>

Full report saved. Pass any JD URL to /job-resume to generate your tailored resume.
```

## Notes

- Always cite the source and approximate date for every data point — compensation data goes stale fast.
- If a portal returns no results for a specific role/location, note it ("No recent Blind posts found for Stripe India 2025–2026") rather than omitting it silently.
- Prioritise 2025–2026 data. Flag any data older than 12 months as potentially stale.
- For India-specific searches, always include AmbitionBox and Naukri — they often have data that Western portals miss.
- Do not fabricate salary numbers or interview experiences. Only report what was found. If data is sparse, say so.
- Real offer examples from Leetcode Discuss and Blind are more reliable than aggregated ranges — always surface them when found.
- If the user doesn't specify a role, default to Senior Software Engineer / equivalent based on their profile level.
