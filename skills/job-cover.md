---
name: job-cover
description: Draft a highly personalized cover letter for a target role.
---

# /job-cover — Generate Tailored LaTeX Cover Letter PDF

Generate a professional, keyword-tailored cover letter in LaTeX, compiled to a single-page PDF that visually matches the aesthetic of your resume template.

## Usage

- `/job-cover https://careers.airbnb.com/positions/7581839/` — generate cover letter from JD URL
- `/job-cover` — paste JD text directly in chat
- `/job-cover <URL> --template jake` — use Jake's aesthetic (default)
- `/job-cover <URL> --template career-ops` — use career-ops aesthetic

---

## Steps

### 1. Load Profile
Read `~/.job-search/profile.json`. If it doesn't exist, stop and prompt the user to run `/job build` first.

### 2. Fetch & Analyze JD
- Fetch the job description text using Puppeteer or WebFetch (fallback: ask user to paste).
- Extract:
  - `company` — company name
  - `role_title` — job title
  - `required_skills` — top 3 required skills
  - `responsibilities` — core challenges

### 3. Generate Tailored Letter Content
Draft a professional, compelling 4-paragraph cover letter using these guidelines:
- **Salutation**: "Dear Hiring Team at <Company>," (or hiring manager name if found).
- **Paragraph 1: The Hook**: State that you are applying for the `<Role Title>` position. Immediately establish credibility by summarizing your years of experience, core archetype, and why this specific role matches your skills.
- **Paragraph 2: The Core Accomplishment (The Evidence)**: Select the single most relevant project from your work history in `profile.json` that directly maps to the JD's biggest need. Frame this accomplishment using the **X-Y-Z formula** (*"At <Company>, I accomplished X, measured by Y, by implementing Z"*). Inject 2-3 key keywords from the JD naturally.
- **Paragraph 3: Company Alignment (The "Why <Company>")**: State why you are excited to join `<Company>`. Use a specific company detail (e.g. Stripe's developer focus, Airbnb's host community, or Notion's clean design docs) to show you've done your research and aren't sending a generic letter.
- **Paragraph 4: Closing**: Reiterate your enthusiasm, mention that your resume is attached, state your availability for an interview, and thank them for their consideration.
- **Sign-off**: "Sincerely,\n\n<Your Name>"

### 4. Format LaTeX Document
Format the content into a single-page LaTeX document using the structure of the selected template (`~/.job-search/templates/jake.tex` or `career-ops.tex`):
- **Header**: Use the exact contact header code block from the template to ensure your name, email, phone, location, and social links are visually identical to your resume.
- **Letter Body**:
  - Add date: `\hfill \today \\`
  - Add recipient block:
    ```latex
    \vspace{10pt}
    \begin{flushleft}
    \textbf{Hiring Team} \\
    \textit{<Company>}
    \end{flushleft}
    \vspace{10pt}
    ```
  - Output paragraphs with appropriate line spacing (`\vspace{8pt}` or similar).
  - Escape all LaTeX special characters (`&` $\rightarrow$ `\&`, `%` $\rightarrow$ `\%`, `$` $\rightarrow$ `\$`, etc.).

### 5. Write and Compile
1. Save the LaTeX code to: `~/.job-search/output/<company-slug>-cover-<YYYY-MM-DD>.tex`.
2. Compile with tectonic:
   ```bash
   cd ~/.job-search/output && tectonic <filename>.tex 2>&1
   ```
   - If compile fails: read the error log, fix LaTeX escaping or syntax, and retry (up to 2 times).
3. Verify that the output is exactly 1 page:
   ```bash
   pdfinfo <filename>.pdf 2>/dev/null | grep "Pages:" || echo "Pages: unknown"
   ```
   If it spills over to page 2, trim the body paragraphs or adjust the layout spacing until it fits perfectly on a single page.
4. Open the PDF:
   ```bash
   open ~/.job-search/output/<filename>.pdf
   ```

### 6. Print Summary

Print a confirmation summary:
```
✅ Cover letter generated: <company-slug>-cover-<date>.pdf

  Company:   <company name>
  Role:      <role title>
  Template:  <template name>
  Pages:     1 page
  File:      ~/.job-search/output/<filename>.pdf

The PDF has been opened in your system viewer.
```

---

## Notes
- **Tone**: Professional, confident, and direct. Avoid overly formal or archaic phrasing (like *"I write to you today to express my interest..."*). Use modern, active verbs.
- **Aesthetic Unity**: The cover letter and resume MUST use the exact same template and margins. It looks highly premium when both documents match.
