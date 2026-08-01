---
name: job-linkedin
description: Optimize your LinkedIn profile and generate recruiter outbound messages.
---

# /job-linkedin — LinkedIn Profile Optimization & Outreach Guide

A guide to optimizing your LinkedIn presence for recruiters and sourcers, paired with cold outreach templates to target hiring teams directly.

## Usage

- `/job-linkedin` — show summary checklist and optimization checklist
- `/job-linkedin summary` — generate customized LinkedIn Summary (About section) based on your profile
- `/job-linkedin outreach <company> <role>` — draft cold messaging templates targeting recruiters/hiring managers

---

## 1. LinkedIn Profile Optimization Blueprint

Recruiters spend 80% of their time sourcing directly on LinkedIn. Optimize these 4 sections to rank high in their search queries.

### A. Headline (Tagline)
Do NOT use the default: `[Title] at [Company]`. This wastes indexable real estate.
* **Formula**: `[Core Role] | [Top 2-3 Skill Keywords] | [High-Impact Value Proposition / Accomplishment]`
* **Example (SWE)**: `Senior Backend Engineer | Python, Go, Distributed Systems | Scaling Payments Infrastructure to $10M+ GMV`
* **Example (AI)**: `Staff Machine Learning Engineer | PyTorch, LLMs, MLOps | Built LLM Fine-Tuning Pipelines reducing latency by 40%`

### B. The About Section (Professional Summary)
Keep it readable, impact-driven, and rich in skill keywords.
* **Paragraph 1**: Elevator pitch. Define your seniority, core domain specialization, and what problems you love to solve.
* **Paragraph 2**: Career Highlights. List 3 bullet points using the Google STAR/XYZ formula: *“Accomplished X, measured by Y, by doing Z.”*
* **Section 3 (Core Tech Stack Block)**:
  `🛠️ Tech Stack: Python • Go • Kubernetes • PostgreSQL • AWS`

### C. Experience Bullets
Use the exact same metric-driven bullets from your tailored resume.
* **Pro-Tip**: Add high-quality images, slides, or github links as "Media" under each experience card to show visual proof of work.

### D. Settings & Hacks
* **Open to Work (Recruiter Only)**: Turn this on. It flags you in Recruiter Search without showing the green banner to your current colleagues.
* **Skills Endorsements**: Pin your top 3 keywords. Ensure they match the keywords in your target job descriptions.
* **Custom URL**: Claim your clean URL (`linkedin.com/in/first-last`) for your resume header.

---

## 2. Cold Outreach Templates

Combine these templates with contacts extracted using extensions like **Apollo.io**.

### Template 1: The Soft Connection (Targeting Peer Engineers/Team Leads)
> **Subject**: Engineering inquiry: [Topic related to their work]
>
> *"Hi [Name],*
>
> *I came across your profile and noticed your work on [specific project/tech stack at company]. I’m a backend engineer specializing in [skills], and I’ve been following how [Company] scales its [systems/infrastructure].*
>
> *I saw you are hiring a [Role Title] on your team. I’d love to connect and ask a quick question about the team culture and what architectural challenges you are working on. Are you open to a brief chat?*
>
> *Best,*
> *[Your Name]"*

### Template 2: The Direct Outreach (Targeting Recruiters / Hiring Managers)
> **Subject**: [Role Title] Application — [Your Name]
>
> *"Hi [Name],*
>
> *I recently submitted an application for the [Role Title] opening (Req #[Number]) and wanted to reach out directly to express my interest.*
>
> *By way of background, I'm a [Current Title] with experience in [Top 2 Skills]. At [Previous Company], I led the rewrite of [System], which [quantifiable metric, e.g., cut API response times by 30%]. My background aligns directly with your requirement for [specific skill in JD].*
>
> *I've attached my tailored resume here for your convenience. I’d love to sync briefly to see if my background matches what you are looking for on this team.*
>
> *Best regards,*
> *[Your Name]*
> *[LinkedIn Link] | [Portfolio Link]"*

---

## 3. Skill Execution Prompt

When the user runs `/job-linkedin summary`, generate a tailored LinkedIn Summary block:
1. Read `~/.job-search/profile.json`.
2. Extract name, skills, and top achievements.
3. Draft a professional, engaging 3-part About section matching the blueprint.
4. Output the result in markdown code blocks.
