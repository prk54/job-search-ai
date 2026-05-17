# /job-resume — Generate Tailored LaTeX Resume PDF

Given a JD (URL or pasted text) and the stored profile, generate a keyword-injected, ATS-optimised LaTeX resume compiled to a single-page PDF.

## Usage

- `/job-resume https://careers.airbnb.com/positions/7581839/` — from URL
- `/job-resume` — paste JD text directly in chat
- `/job-resume <URL> --template jake` — use Jake's Resume template (default)
- `/job-resume <URL> --template career-ops` — use career-ops template
- `/job-resume <URL> --save-drive` — auto-save PDF to Google Drive after generation

## Templates

| Flag | File | Style |
|------|------|-------|
| `--template jake` (default) | `~/.job-search/templates/jake.tex` | Single column, 10pt, tight margins, Summary → Experience → Skills → Certs → Education |
| `--template career-ops` | `~/.job-search/templates/career-ops.tex` | sb2nov base, slightly different section spacing |

Both compile with tectonic (XeLaTeX). Neither uses `\pdfgentounicode` or `\input{glyphtounicode}` (incompatible with XeLaTeX).

## Steps

### 1. Load profile
Read `~/.job-search/profile.json`. If it doesn't exist, tell the user to run `/job-profile` first.

### 2. Fetch JD content
- If a URL is provided:
  - Use Puppeteer to navigate to the URL and extract full page text
  - If Puppeteer fails, use WebFetch as fallback
- If no URL, ask user to paste the JD text

### 3. Analyse the JD
Extract the following from the JD text:
```json
{
  "company": "",
  "role_title": "",
  "team": "",
  "seniority": "Senior | Staff | Principal",
  "location": "",
  "required_skills": [],
  "preferred_skills": [],
  "key_keywords": [],
  "responsibilities": [],
  "archetype": "fullstack | backend | data-platform | search-infra | ai-platform | devtools"
}
```

### 4. Score profile fit per JD
For each experience entry in the profile, score relevance to this JD (High / Medium / Low) based on:
- Skill keyword overlap
- Domain match (payments, data platform, search, AI, etc.)
- Recency (more recent = higher weight)

### 5. Generate tailored LaTeX content

**Rules for tailoring:**

- **Summary**: Rewrite to lead with the JD's archetype and top 2–3 required skills. Max 3 sentences.
- **Experience bullets**:
  - Lead each company section with the bullet most relevant to the JD
  - Inject JD keywords naturally (don't keyword-stuff — rewrite the bullet to include the term meaningfully)
  - Drop or deprioritise bullets with no relevance to the JD
  - LinkedIn (current role): max 4 bullets
  - Salesforce: max 3 bullets
  - Nutanix: max 1–2 bullets (combine if needed)
  - JPMorgan: max 3 bullets (always one company block, "Software Engineer, promoted to Software Engineer II")
- **Skills section**: Lead with the skills most relevant to the JD
- **Certifications**: Only include if relevant to the JD domain (e.g. AWS cert for cloud roles, MLOps for AI roles)
- **One page rule**: The final PDF MUST be one page. Trim bullets ruthlessly if it overflows.

**LaTeX generation rules (to avoid tectonic compile errors):**
- Do NOT use `\pdfgentounicode=1` or `\input{glyphtounicode}` — XeLaTeX incompatible
- Use `\&` for ampersands inside tabular cells
- Use `--` for en-dashes in date ranges
- Escape `%` as `\%` in bullet text
- Use `\textbf{}` for bold, `\textit{}` for italic
- Arrow between two job titles: use text `promoted to` — do NOT use `$\to$` (ATS unfriendly)

### 6. Read the template
Read the selected template file (`~/.job-search/templates/jake.tex` or `career-ops.tex`).
Use it as the structural base — replace preamble, commands, and section structure exactly as-is.
Fill in only the content sections: header, summary, experience, skills, certifications, education.

### 7. Write .tex file
Save to: `~/.job-search/output/<company-slug>-<role-slug>-<YYYY-MM-DD>.tex`

Example: `~/.job-search/output/airbnb-senior-swe-payments-2026-05-17.tex`

### 8. Compile with tectonic
```bash
cd ~/.job-search/output && tectonic <filename>.tex 2>&1
```
- If compilation fails, read the error, fix the .tex file, and retry (max 2 retries).
- Common fixes: escape special chars, remove incompatible packages, fix unclosed environments.

### 9. Verify PDF is 1 page
```bash
python3 -c "
import subprocess
result = subprocess.run(['pdfinfo', '<filename>.pdf'], capture_output=True, text=True)
print(result.stdout)
" 2>/dev/null || echo "pdfinfo not available — check manually"
```
If 2+ pages, tighten spacing: reduce `\vspace`, increase `\vspace` negative values, trim 1–2 bullets from least-relevant role, reduce font to 9.5pt.

### 10. Open PDF
```bash
open ~/.job-search/output/<filename>.pdf
```

### 11. If --save-drive
Use the Google Drive MCP tool to upload the PDF:
- Target folder: "Job Search / Resumes" (create if it doesn't exist)
- File name: `<Company> - <Role Title> - <Date>.pdf`

### 12. Print confirmation
```
✅ Resume generated: airbnb-senior-swe-payments-2026-05-17.pdf

  Company:   Airbnb
  Role:      Senior Software Engineer – Payments
  Template:  Jake's Resume
  Pages:     1
  File:      ~/.job-search/output/airbnb-senior-swe-payments-2026-05-17.pdf

  Key tailoring applied:
  → Summary rewritten for Payments / FinTech archetype
  → JPMorgan Fraud Detection Engine bullet moved to #1 (10K TPS, payments domain)
  → Kafka + Elasticsearch keywords injected into LinkedIn bullets
  → AWS cert included (cloud infra role)

PDF is open in your viewer. Run /job-resume <next JD URL> for another role.
```

## Notes

- Always generate fresh from `profile.json` — never use hardcoded profile data.
- The one-page rule is non-negotiable. Recruiters at these companies expect 1 page for senior ICs.
- After generation, briefly list what tailoring was applied so the user can verify it makes sense.
- If the JD URL is a LinkedIn job URL, Puppeteer should still be able to fetch it if the user is logged in. If not, ask the user to paste the JD text instead.
- For Broadcom/Nvidia roles on Workday (iframe-heavy), fetch the page and look for the main job description div — it may require scrolling/waiting.
