---
name: job-profile
description: Parse a resume PDF or LinkedIn export PDF and extract a structured profile.
---

# /job-profile — Parse Resume & Build Profile

Parse a resume PDF or LinkedIn export PDF and extract a structured profile saved to `~/.job-search/profile.json`. This is the foundation for all other job-search skills.

## Usage

- `/job-profile ~/Downloads/resume.pdf` — parse a resume PDF
- `/job-profile ~/Downloads/Profile.pdf` — parse a LinkedIn PDF export
- `/job-profile` (no args) — user will paste raw resume text in the chat

## Steps

1. **Get the resume text**
   - If a file path is provided as an argument, read the PDF:
     ```bash
     pdftotext "<path>" - 2>/dev/null || echo "pdftotext not available"
     ```
   - If pdftotext fails, use the Read tool directly on the PDF path — Claude can read PDFs natively.
   - If no path provided, ask the user to paste their resume text.

2. **Extract structured profile** from the resume text. Output strict JSON matching this schema:
```json
{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "summary": "",
  "experience": [
    {
      "company": "",
      "title": "",
      "start": "",
      "end": "",
      "location": "",
      "bullets": []
    }
  ],
  "skills": {
    "languages": [],
    "frontend": [],
    "backend": [],
    "databases": [],
    "infra": [],
    "streaming": [],
    "testing": [],
    "other": []
  },
  "education": [
    {
      "institution": "",
      "degree": "",
      "field": "",
      "start": "",
      "end": "",
      "location": ""
    }
  ],
  "certifications": [],
  "awards": [],
  "publications": []
}
```

2.5 **Refine bullets with missing metrics (Interactive Verification)**
   - Analyze the extracted experience bullets. If the bullets are vague or lack numerical metrics (e.g., "improved database query performance", "worked on backend systems", "wrote dashboard APIs"):
     - Show the user the list of vague bullet points that can be improved.
     - Present 2-3 specific, polite questions asking for metrics (e.g., "By how much did database performance improve?", "How many users or daily requests did the APIs support?").
     - Wait for the user's answers.
     - Once the user answers, rewrite these bullets to integrate the metrics using Google's X-Y-Z formula (Accomplished [X] as measured by [Y], by doing [Z]).
     - Proceed to validation and save the final refined profile to `~/.job-search/profile.json`.

3. **Validate the extracted JSON** before saving:
   - `name` must be a non-empty string
   - `experience` must be a non-empty array with at least 1 entry
   - Each experience entry must have `company`, `title`, `start`
   - `skills` must have at least one non-empty array
   - If validation fails: show the user what's missing and ask them to clarify or paste the missing section. Do NOT save a corrupt profile.

   Validate with:
   ```bash
   python3 -c "
   import json, sys
   p = json.load(open(sys.argv[1]))
   assert p.get('name'), 'name is missing'
   assert p.get('experience'), 'experience is empty'
   assert any(p.get('skills', {}).values()), 'skills are empty'
   print('valid')
   " ~/.job-search/profile.json 2>&1
   ```

4. **Save to `~/.job-search/profile.json`** using the Write tool.

5. **Print a confirmation summary using the actual extracted values:**
```
✅ Profile saved to ~/.job-search/profile.json

Name:        <name from profile>
Current:     <most recent title> at <most recent company> (<start> – Present)
Experience:  <total years calculated from earliest start to today>
Companies:   <list all companies, comma-separated>

Top Skills (from resume):
  <each skill category>: <comma-separated skills>

Run /job-scan to find matching roles at target companies.
Run /job-resume <JD URL> to generate a tailored resume.
```

6. **Compile Base Resume PDF**
   - Read the template `~/.job-search/templates/jake.tex`.
   - Populate the LaTeX sections (contact details, summary, experience bullets, skills, education) using the newly structured, refined profile JSON data.
   - Determine target output path and naming:
     - Convert the candidate's `name` from the refined profile JSON to snake_case (e.g., "Rahul Sharma" becomes "Rahul_Sharma").
     - Target output directory: If an input PDF path was passed as an argument, use that directory (e.g. `~/Downloads/`). Otherwise, use the current working directory.
     - Filename: `<candidate_name>_Base_Resume.tex` (e.g. `Rahul_Sharma_Base_Resume.tex`) and `<candidate_name>_Base_Resume.pdf`.
   - Save the populated LaTeX code to the target directory.
   - Compile the LaTeX code to PDF using tectonic:
     ```bash
     cd <target_directory> && tectonic <candidate_name>_Base_Resume.tex 2>&1
     ```
   - Confirm to the user that the base resume PDF has been compiled and show the full path of the compiled PDF.

## Notes

- Do NOT hardcode any profile data — always extract fresh from the provided file.
- If the PDF is a LinkedIn export, it will have a different layout than a traditional resume — handle both.
- Proactively identify and ask questions to refine experience bullet points that lack metrics before saving the final profile.
- If a field is missing from the resume (e.g. no publications), set it to an empty array `[]`.
