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

3. **Save to `~/.job-search/profile.json`** using the Write tool.

4. **Print a confirmation summary:**
```
✅ Profile saved to ~/.job-search/profile.json

Name:        Prateek Lalwani
Current:     Senior Software Engineer at LinkedIn (Sept 2024 – Present)
Experience:  8 years
Companies:   LinkedIn, Salesforce, Nutanix, JPMorgan Chase

Top Skills:
  Languages:  Java, Python, TypeScript, JavaScript, SQL
  Backend:    Spring Boot, FastAPI, Django, Express.js
  Frontend:   React, Redux, GraphQL
  Streaming:  Kafka, Spark, PySpark, Elasticsearch
  Infra:      AWS, Docker, Kubernetes

Run /job-scan to find matching roles at target companies.
Run /job-resume <JD URL> to generate a tailored resume.
```

## Notes

- Do NOT hardcode any profile data — always extract fresh from the provided file.
- If the PDF is a LinkedIn export, it will have a different layout than a traditional resume — handle both.
- Preserve all bullet points from the experience section exactly as written. The user will refine them later.
- If a field is missing from the resume (e.g. no publications), set it to an empty array `[]`.
