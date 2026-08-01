# 🎤 Live Demo Cheat Sheet — Job Hunt Session (1st August)

This file contains the exact commands and URLs to copy-paste into your **`yolo` (Antigravity CLI)** session and macOS terminal during the live workshop. Keep this tab open on the side!

---

## 💻 Part 1: Starting the Session
Open your terminal, navigate to the project directory, and launch the Antigravity shell:

```bash
yolo
```

---

## 📊 Step 1: Check Sourcing Status Dashboard
*Explain that the assistant tracks your target profile, location, and configurations locally.*

**In the `yolo` shell:**
```text
/job
```

---

## 📄 Step 2: Show Base Resume Generation
*Demonstrate how the tool parses a PDF into JSON and compiles a base XeLaTeX resume.*

**In the `yolo` shell:**
```text
/job-profile ~/Downloads/Profile.pdf
```

**In your macOS terminal (to open the compiled base PDF):**
```bash
open ~/.job-search/output/base-resume.pdf
```

---

## 🔍 Step 3: Discover Bangalore Target Companies
*Harvest career boards and seed databases matching your location preference (Bangalore).*

**In the `yolo` shell:**
```text
/job-discover
```

---

## 📋 Step 4: Scan and Score Open Job Listings
*Perform live parallel crawls to fetch postings and check compatibility.*

**In the `yolo` shell:**
```text
/job-scan
```

---

## 🛠️ Step 5: Tailor Resume for Stripe India
*Tailor your experience points for Stripe's payments backend role and compile the PDF.*

**In the `yolo` shell:**
```text
/job-resume https://boards.greenhouse.io/stripe/jobs/7826765
```

**In your macOS terminal (to open the tailored Stripe PDF):**
```bash
open ~/.job-search/output/resume_stripe.pdf
```

---

## 🏡 Step 6: Tailor Resume for Airbnb India
*Tailor your experience points for Airbnb's staff platform role and compile the PDF.*

**In the `yolo` shell:**
```text
/job-resume https://careers.airbnb.com/jobs/staff-software-engineer-india/
```

**In your macOS terminal (to open the tailored Airbnb PDF):**
```bash
open ~/.job-search/output/resume_airbnb.pdf
```

---

## 📨 Step 7: Draft Recruiter Cold Outreach
*Generate a personalized email and connection note matching your qualifications.*

**In the `yolo` shell:**
```text
/job-linkedin outreach stripe
```

**In your macOS terminal (to show the pre-generated outreach text file):**
```bash
cat ~/.job-search/output/outreach_stripe.txt
```
