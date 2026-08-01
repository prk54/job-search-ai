---
name: job-interview
description: Interactive mock interview simulator that asks company-specific questions, evaluates answers using the STAR method, and provides detailed feedback.
---

# /job-interview — Interactive Mock Interview Simulator

Conduct an interactive, step-by-step mock interview for a target company and role. The assistant asks realistic technical or behavioral questions, evaluates your answers, provides real-time coaching using the STAR method, and saves a feedback report.

## Usage

- `/job-interview <company> <role>` — start a simulated interview (e.g., `/job-interview Stripe Backend`)
- `/job-interview` (no args) — assistant will ask you which company and role you want to practice for

---

## Step 1 — Initialize Interview Parameters

Ask the user if they want to focus on:
1. **Behavioral/Leadership** (STAR method focus, conflict resolution, project delivery)
2. **System Design / Technical Architecture** (scalability, API design, database modeling)
3. **Coding/Problem Solving** (algorithms, code structure, edge cases)

---

## Step 2 — Generate Questions

Based on the company (e.g. Google, Stripe, Airbnb) and role (e.g. Backend Engineer, iOS Developer, Staff Engineer), generate 3 realistic, highly relevant questions.
- *Google*: Focus on complex scalability, distributed systems, or standard algorithms.
- *Stripe*: Focus on payment API design, idempotency, data consistency, or customer empathy.
- *Airbnb*: Focus on service mesh, developer platforms, search indexing, or trust and safety.

---

## Step 3 — Step-by-Step Simulation Flow

Do NOT print all questions at once. Ask them one by one.

For each question:
1. Present the question clearly.
2. Wait for the user's response.
3. Once the user submits their response, evaluate it:
   - **Relevance**: Did they answer the core question?
   - **Structure**: Did they use the STAR method (Situation, Task, Action, Result) for behavioral, or clarify requirements for system design?
   - **Metrics**: Did they include numbers or measurable impact?
4. Provide constructive feedback:
   - **What was strong**: Highlight correct technical terms or good structuring.
   - **Where to improve**: Point out missing numbers, gaps in architecture, or unclear points.
   - **Suggested Answer**: Provide a polished, high-impact version of how a senior engineer would answer this question using the same context.
5. Move to the next question.

---

## Step 4 — Final Score and Feedback Report

After the final question, provide:
- An overall **Interview Readiness Score** (e.g., *7.5/10*)
- A summary of strengths and core improvement areas.
- Save the full transcript and feedback as a markdown report:
  `~/.job-search/output/interview_feedback_<company>_<role>_<date>.md`
