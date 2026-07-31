# /job-build — Build Base Profile & Resume PDF

Build your first base resume from scratch. This skill helps you construct a structured profile (`~/.job-search/profile.json`) either by pasting unstructured free text or through an interactive, step-by-step interview in the chat, and compiles it into a clean, single-page LaTeX base PDF resume.

## Usage

- `/job-build` — starts interactive wizard (prompts you to choose between interview, free-text parsing, or recompiling existing profile)
- `/job-build --text` — skips greeting and prompts you to paste raw text directly
- `/job-build --pdf-only` — skips interview/parsing, compiles a fresh base PDF from the existing `profile.json`

---

## Step 1 — Check Starting Point

Check if `~/.job-search/profile.json` exists:
```bash
test -f ~/.job-search/profile.json && echo "exists" || echo "missing"
```

### Case A: Profile exists
Show a brief summary of the existing profile:
```
I found an existing profile:
  Name:        <name>
  Title:       <current_title> at <current_company>
  Last update: <last_modified_date>

What would you like to do?
  1. Compile base PDF (recompile the clean, non-tailored base resume PDF)
  2. Edit profile (modify specific sections in your profile)
  3. Start from scratch (Interactive Interview - will overwrite current profile)
  4. Start from scratch (Paste Free-Text - will overwrite current profile)
```

### Case B: Profile is missing
Prompt the user with these options:
```
Welcome to job-search-ai! Let's build your first base resume. How would you like to provide your details?
  1. Step-by-Step Interactive Interview (Recommended - I will ask you questions and help you write strong, quantified bullet points)
  2. Paste Free-Text (Quickest - paste your raw LinkedIn profile, old resume text, or rough notes, and I will structure it)
`## Step 2 — Option 1: Interactive Interview

Walk the user through the following sections sequentially. Format your questions clearly and friendly. Let the user skip optional sections by typing "skip".

### 0. Target Domain & Role
Before asking for contact info, ask the user:
*"What is your target role and professional domain? (e.g., Software Engineering, Product Management, UI/UX Design, Data Science, Marketing, Sales, Finance, etc.)"*
This input will dynamically shape the subsequent questions, skill categories, and metrics.

### 1. Contact Information
Ask for:
- Full Name
- Email Address
- Phone Number
- Location (City, State/Country)
- LinkedIn URL (optional)
- **Domain-Specific Links** (optional):
  - *Tech/Data*: GitHub URL
  - *Design*: Behance, Dribbble, or Portfolio URL
  - *Other*: Personal website or writing link

### 2. Professional Summary (Optional)
Ask the user to write 2-3 sentences about their professional background, focus areas, and goals. 
*Tip: If the user is unsure, tell them you will auto-generate a professional summary for them at the end of the interview based on their experience and skills.*

### 3. Work Experience (Repeat for each role)
Ask:
- Company Name
- Job Title
- Location (City, State/Country)
- Start Date (Month Year)
- End Date (Month Year or "Present")
- **Bullet points (The Value Add)**: 
  Ask: *"What did you do in this role? Don't worry about formatting—just tell me what projects you worked on, what tools/technologies you used, and what the outcomes were."*
  
  **AI Bullet Refiner (X-Y-Z Formula)**:
  Once the user provides their raw input, do NOT save it raw. Convert their input into 2-4 high-impact, professional resume bullets.
  - Lead each bullet with a strong action verb (e.g., *Designed*, *Optimized*, *Spearheaded*, *Scaled*, *Launched*, *Drove*).
  - Use the Google X-Y-Z formula: *"Accomplished [X] as measured by [Y], by doing [Z]"*.
  - Suggest realistic, domain-specific metrics in **bold** or brackets (letting the user know they are placeholders they can adjust):
    - *Software Engineering/Tech*: Latency reduction (e.g., `[20%]`), cost savings (`[$15K/mo]`), scalability (`[10M+ requests]`), uptime (`[99.99%]`), developer velocity (`[15%]`).
    - *Product Management*: User growth (`[35%]`), feature adoption (`[40%]`), conversion rate (`[12%]`), revenue generated (`[$2M]`), time-to-market reduction (`[3 weeks]`).
    - *UI/UX Design*: Usability score improvements (`[25%]`), task completion rates (`[90%]`), design system adoption rate (`[80%]`), conversion rate uplift (`[15%]`).
    - *Marketing/Sales*: Lead generation (`[50%]`), CAC reduction (`[20%]`), ROAS (`[4.5x]`), sales quota achieved (`[120%]`), organic traffic increase (`[60%]`).
    - *Other/General*: Hours saved (`[10 hrs/week]`), budget managed (`[$100K]`), processing time reduction (`[30%]`), customer satisfaction (CSAT) score (`[4.8/5]`).
  - Present the refined bullets to the user and ask: *"Here are the refined bullet points for this role. Do they look good, or would you like to make any adjustments?"*

Once the bullets are approved, ask: *"Would you like to add another work experience entry? (yes/no)"*
Repeat until the user says no.

### 4. Technical / Professional Skills
Group the skills by domain-specific categories to make the resume look highly professional:

* **Software Engineering & Tech**:
  - Languages (e.g., Python, Go, TypeScript)
  - Backend/API (e.g., Node.js, Spring Boot, gRPC)
  - Frontend (e.g., React, Next.js, CSS)
  - Databases/Caches (e.g., PostgreSQL, Redis, DynamoDB)
  - Infrastructure / DevOps (e.g., AWS, Docker, Kubernetes, Terraform)
  - Testing & Tools (e.g., Jest, Git, CI/CD)

* **Product Management**:
  - Product Strategy & Execution (e.g., Roadmapping, Product Analytics, Market Research)
  - Agile/Project Management (e.g., Scrum, Kanban, JIRA)
  - Data & Metrics (e.g., SQL, Amplitude, Tableau, A/B Testing)
  - Technical/Domain Knowledge (e.g., System Architecture, APIs, UX Design Principles)

* **UI/UX & Product Design**:
  - Design Tools (e.g., Figma, Sketch, Adobe Creative Suite)
  - UX Research & Prototyping (e.g., User Interviews, Wireframing, High-fidelity prototypes)
  - Core Design (e.g., Design Systems, Information Architecture, Visual Design)
  - Development (optional) (e.g., HTML/CSS, Webflow)

* **Marketing & Sales**:
  - Growth & Channels (e.g., SEO, SEM, Paid Social, Email Marketing)
  - Platforms & CRMs (e.g., HubSpot, Salesforce, Google Analytics)
  - Strategy & Creative (e.g., Copywriting, Brand Strategy, Content Marketing, A/B Testing)
  - Metrics (e.g., Customer Acquisition, Funnel Optimization, ROAS)

* **Other / General Domains**:
  - Core Competencies / Areas of Expertise
  - Tools & Software Systems (e.g., Excel, specific ERP/CRM tools)
  - Methodologies / Processes
  - Soft Skills / Collaboration

*Tip: Suggest skills to the user based on the work experience they just entered, e.g., "Based on your experience at X, I've added Python, AWS, and Docker. Any other skills you'd like to add?"*

### 5. Education (Repeat if necessary)
Ask:
- Institution Name
- Degree & Field of Study (e.g., B.S. in Computer Science, MBA, B.A. in Graphic Design)
- Location
- Graduation Date (Month Year)

Ask if they want to add another. Repeat until done.

### 6. Certifications & Awards (Optional)
Ask if they have any certifications (e.g., AWS Certified Solutions Architect, Certified Scrum Product Owner, PMP) or awards they'd like to include.

---

## Step 3 — Option 2: Paste Free-Text

If the user selects Free-Text parsing:
1. Ask the user to paste their unstructured text (e.g., raw LinkedIn profile, copy-pasted old resume, or rough notes).
2. Extract the data into the strict JSON schema matching the `profile.json` format (defined in `job-profile.md`).
3. Refine the experience bullets using the **AI Bullet Refiner** (Step 2.3) so they start with strong action verbs and include metrics.
4. Show the extracted information to the user in a clean Markdown layout (Name, Title, Companies, Education, Skills) and ask: *"Here is the structured profile I parsed. Does this look accurate, or are there any corrections you'd like to make?"*
5. Once confirmed, proceed to Step 4.

---

## Step 4 — Compile Base LaTeX PDF

Once `profile.json` is ready (or when the user requests `--pdf-only`), compile a clean, non-tailored base resume PDF:

1. **Read the profile**: Read `~/.job-search/profile.json`.
2. **Read the template**: Read the user's default template from `~/.job-search/config.yml` (either `jake` or `classic`). If no config is set, default to `jake`. Read the template file from `~/.job-search/templates/<template>.tex`.
3. **Assemble the LaTeX code**:
   - Keep the preamble and commands from the template exactly as-is.
   - Insert the header using the contact details from `profile.json`.
   - If a professional summary exists in `profile.json` (or was auto-generated), include it under a `\section{Summary}` (for Jake's template).
   - In `\section{Experience}`:
     - Map every experience entry in `profile.json` in chronological order (most recent first).
     - Include all bullets for each company in their original order.
     - Escape LaTeX special characters:
       - Ampersands `&` $\rightarrow$ `\&`
       - Percent signs `%` $\rightarrow$ `\%`
       - Date en-dashes `–` or `-` $\rightarrow$ `--`
       - Dollar signs `$` $\rightarrow$ `\$`
       - Hashtags `#` $\rightarrow$ `\#`
       - Underscores `_` $\rightarrow$ `\_`
   - In `\section{Skills}`:
     - Group the skills by category and format them cleanly.
   - In `\section{Education}`:
     - List all education entries in chronological order.
   - In `\section{Certifications}` (if present):
     - List certifications.
4. **Write the file**: Save the compiled LaTeX code to `~/.job-search/output/base-resume.tex`.
5. **Compile**:
   ```bash
   cd ~/.job-search/output && tectonic base-resume.tex 2>&1
   ```
   - If compile fails: read the error, fix the LaTeX escaping or syntax, and retry (up to 2 times).
6. **Verify Page Count**:
   Ensure it is exactly 1 page:
   ```bash
   pdfinfo base-resume.pdf 2>/dev/null | grep "Pages:" || echo "Pages: unknown"
   ```
   If it spills over: reduce vertical spacing, remove 1-2 minor bullets from oldest jobs, or shrink the font size to 9.5pt until it fits on exactly one page.
7. **Open the PDF**:
   ```bash
   open ~/.job-search/output/base-resume.pdf
   ```

---

## Step 5 — Save & Confirm

1. Write/save the final verified profile to `~/.job-search/profile.json`.
2. Print a congratulations summary:

```
✅ Base resume built and compiled successfully!

  Profile:   ~/.job-search/profile.json
  LaTeX source: ~/.job-search/output/base-resume.tex
  PDF Output:   ~/.job-search/output/base-resume.pdf
  Template:     <template name>
  Pages:        1 page

The PDF has been opened in your system viewer. 

Next steps:
  1. Verify the PDF matches your expectations.
  2. Run /job-scan to search for matching open roles.
  3. Run /job-intel <company> to get salary + interview info.
  4. Run /job-resume <JD-url> to tailor this base resume for a specific job.
```

---

## Notes

- **Never output unescaped LaTeX characters**: A single unescaped `%` or `&` will break `tectonic` compilation. Check all user-inputted strings carefully.
- **Tone**: Maintain a collaborative, supportive tone during the interview. Help the user recognize their value and frame accomplishments in terms of business impact.
- **One-page rule**: The base resume must fit on one page unless the user has 10+ years of experience and explicitly requests a 2-page resume.
