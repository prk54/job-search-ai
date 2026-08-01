# Web Prompt Templates for Manual LLM Use (ChatGPT, Claude Web UI, Copilot)

For users who do not run the terminal CLI, these templates can be copied and pasted directly into standard Web UI chat assistants to perform high-quality tailoring, drafting, and outreach.

---

## 1. Resume Experience Tailoring Prompt
Use this to rewrite your resume accomplishments to match a target job description.

**Copy-Paste Prompt:**
```text
You are an expert resume writer. Help me tailor my resume experience section to align directly with a target Job Description (JD).

Here is my current profile:
<PASTE YOUR RESUME / PROFILE HERE>

Here is the target Job Description (JD):
<PASTE THE TARGET JOB DESCRIPTION HERE>

Instructions:
1. Rewrite my experience bullet points to naturally highlight skills, keywords, and frameworks mentioned in the JD.
2. Emphasize metrics and achievements (use Google's STAR/XYZ formula: "Accomplished X, measured by Y, by doing Z").
3. Do NOT invent new jobs, change company names, titles, or dates. Keep it truthful to my original profile.
4. Output the updated experience section in markdown format.
```

---

## 2. Dynamic Cover Letter Drafting Prompt
Use this to draft a single-page cover letter matching a target role.

**Copy-Paste Prompt:**
```text
Draft a highly targeted, single-page cover letter for me.

My Profile:
<PASTE YOUR RESUME / PROFILE HERE>

Target Company: <Insert Company Name, e.g., Stripe>
Target Role: <Insert Role Title, e.g., Backend Engineer>
Job Description:
<PASTE THE TARGET JOB DESCRIPTION HERE>

Instructions:
1. Write exactly three body paragraphs:
   - Paragraph 1: Direct introduction expressing enthusiasm for the role and alignment with the company's mission/product.
   - Paragraph 2: Core technical fit. Connect 2-3 specific accomplishments from my profile to requirements in the JD.
   - Paragraph 3: Wrap up, call to action, and professional closing.
2. Keep it concise so it compiles cleanly on a single page. Avoid generic buzzwords.
```

---

## 3. Recruiter Outreach Prompt (Apollo.io Integration)
Once you extract recruiter details (Name, Title, Email/LinkedIn) via extensions like **Apollo.io**, use this prompt to generate personalized cold messages.

**Copy-Paste Prompt:**
```text
Draft two cold outreach templates (one short LinkedIn connection request under 300 characters, and one email) to target this recruiter:

Recruiter Name: <Insert Recruiter Name>
Recruiter Title: <Insert Recruiter Title, e.g., Technical Recruiter>
Company: <Insert Company Name>
Target Role: <Insert Role Title>

My background:
<PASTE A 2-SENTENCE SUMMARY OF YOUR BACKGROUND OR RESUME>

Instructions:
- Keep the LinkedIn connection note punchy, conversational, and under 300 characters (LinkedIn limit).
- Keep the email under 150 words, focusing on my top achievement and how it relates to their hiring needs. Reference that I have already submitted an application.
```
