# /job-apply — Auto-Fill Job Applications

Automatically opens a browser window, navigates to the job posting, fills in your profile details (Name, Email, Phone, Location, LinkedIn, GitHub, Portfolio), uploads the correct tailored resume PDF, and leaves the browser open for you to verify and submit.

## Usage

- `/job-apply <JD-url>` — finds the latest tailored resume for this company and fills the form
- `/job-apply <JD-url> /path/to/specific/resume.pdf` — uses a specific resume PDF

---

## Steps

### 1. Identify Target Resume
If no resume path is specified:
1. Parse the company name from the JD URL (e.g., `boards.greenhouse.io/stripe` or `lever.co/airbnb` $\rightarrow$ company is "stripe" or "airbnb").
2. Search for the most recently generated tailored resume PDF for that company in `~/.job-search/output/`:
   ```bash
   ls -t ~/.job-search/output/*<company-slug>*.pdf 2>/dev/null | head -1
   ```
3. If a matching tailored resume is found:
   - Output: `Found tailored resume: ~/.job-search/output/<filename>.pdf`
   - Use this file.
4. If no tailored resume is found:
   - Check if a base resume exists:
     ```bash
     test -f ~/.job-search/output/base-resume.pdf && echo "base" || echo "missing"
     ```
   - If `base-resume.pdf` exists, notify the user: `No tailored resume found for <company>. Falling back to base-resume.pdf.`
   - If even the base resume is missing, notify the user: `No resumes found. Starting the browser without resume upload. (Run /job build to create a resume first).`

### 2. Verify Profile
Check that `~/.job-search/profile.json` exists:
```bash
test -f ~/.job-search/profile.json && echo "exists" || echo "missing"
```
If missing, stop and prompt the user: *"No profile found. Run '/job build' first to enter your contact info and experience."*

### 3. Run the Auto-Apply Script
Launch the browser automation script with the target URL and resume path:
```bash
python3 ~/.job-search/scripts/apply.py "<JD-url>" "<resume_pdf_path>"
```

### 4. Provide Terminal Instructions
While the script runs, explain to the user:
```
🚀 Launching Chromium browser...
→ Loading target application page...
→ Auto-filling form fields (Name, Email, Phone, Location, Social URLs)...
→ Attaching resume PDF...

======================================================================
  THE AUTOMATED BROWSER WINDOW IS NOW OPEN.
======================================================================
  
  What to do next:
  1. Look at the Chromium window that just opened.
  2. Review the pre-filled fields to ensure they are correct.
  3. Answer any custom employer questions (e.g., work authorization).
  4. Complete any CAPTCHA screens.
  5. Click the "Submit Application" button manually.
  
  Press Ctrl+C in this terminal when you are done to close the browser.
======================================================================
```

---

## Notes
- **User Review is Critical**: The script purposefully does *not* click the final submit button. This ensures you can verify correctness, fill custom questions, and maintain control of your applications.
- **Form Compatibility**: The script uses generalized label heuristics. It is fully compatible with Greenhouse, Lever, Ashby, and most custom job application forms.
- **Headless Mode**: The browser is run in *non-headful* mode (`headless=False`) so the UI is fully visible to the user.
