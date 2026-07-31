import os
import sys
import shutil
import json
import re
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from job_search.core.config import load_config, ensure_app_dirs, APP_DIR, CONFIG_PATH
from job_search.core.db import init_db, get_db, DBCompany, DBProfile, DBApplication
from job_search.core.scraper import JobScraper, harvest_live_companies, fetch_jd_text_from_url
from job_search.core.llm import detect_llm_driver, parse_json_from_llm
from job_search.core.builder import render_resume, render_cover_letter

app = typer.Typer(help="job-search-ai: E2E CLI-based automated job search assistant")
console = Console()

def query_llm(prompt: str) -> str:
    """Helper to query the configured LLM CLI subprocess"""
    config = load_config()
    driver = detect_llm_driver(config.llm.provider, config.llm.custom_command)
    return driver.execute(prompt)

def refine_bullets_with_llm(raw_bullets: List[str]) -> List[str]:
    """Query LLM to refine resume bullet points using STAR / XYZ formula"""
    prompt = (
        "Refine the following job achievements using Google's X-Y-Z formula (Accomplished [X] as measured by [Y], by doing [Z]). "
        "Provide realistic metric placeholders (e.g. '[15%]') if no metrics are present, so the user knows what to fill.\n"
        "Keep the language professional and impact-driven. "
        "Output the refined list strictly as a JSON array of strings wrapped in <json> and </json> tags.\n\n"
        f"Raw Achievements:\n{json.dumps(raw_bullets)}"
    )
    with console.status("[cyan]Refining achievements using Google STAR/XYZ formula...[/cyan]"):
        try:
            response = query_llm(prompt)
            data = parse_json_from_llm(response)
            if isinstance(data, list):
                return [str(item) for item in data]
        except Exception as e:
            console.print(f"[yellow]⚠ LLM bullet refinement failed: {e}. Using raw inputs.[/yellow]")
    return raw_bullets

def evaluate_fit_in_bulk(profile_summary: str, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rate job description fits in a single batched subprocess LLM call to save time"""
    if not jobs:
        return []
        
    jobs_payload = [{"id": j["id"], "title": j["title"], "location": j["location"]} for j in jobs]
    prompt = (
        "You are an expert technical recruiter. Evaluate the alignment of this candidate's profile with these job roles.\n"
        f"Candidate Summary:\n{profile_summary}\n\n"
        f"Job Listings:\n{json.dumps(jobs_payload)}\n\n"
        "For each job, provide a fit rating ('High', 'Medium', 'Low') and a fit score from 0 to 100.\n"
        "Output the result strictly as a JSON array of objects, matching the original job ID: "
        '[{"id": "...", "fit_rating": "...", "fit_score": 85}] enclosed in <json> and </json> tags.'
    )
    with console.status("[cyan]Evaluating job matches and estimating comp fits...[/cyan]"):
        try:
            response = query_llm(prompt)
            data = parse_json_from_llm(response)
            lookup = {str(item.get("id")): item for item in data if "id" in item}
            for j in jobs:
                jid = str(j["id"])
                item = lookup.get(jid)
                if item:
                    j["fit_rating"] = item.get("fit_rating", "Medium")
                    j["fit_score"] = int(item.get("fit_score", 50))
                else:
                    j["fit_rating"] = "Medium"
                    j["fit_score"] = 50
        except Exception as e:
            # Fallback values
            for j in jobs:
                j["fit_rating"] = "Medium"
                j["fit_score"] = 50
    return jobs

def tailor_experience_with_llm(profile_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
    """Tailor experience achievements based on the target Job Description (JD) using the LLM"""
    prompt = (
        "You are a professional resume writer. Tailor the candidate's achievements to align with this target Job Description (JD).\n"
        f"Job Description:\n{jd_text}\n\n"
        f"Candidate Experience:\n{json.dumps(profile_data.get('experience', []))}\n\n"
        "Instructions:\n"
        "- Modify the bullet points of achievements to highlight skills relevant to the JD (e.g. payments, cloud infra, system design) while maintaining truthfulness.\n"
        "- Emphasize keywords and technologies requested in the JD.\n"
        "- Do not alter the company names, dates, or titles.\n"
        "Output the tailored list of experience objects matching the input format, strictly enclosed in <json> and </json> tags."
    )
    tailored_profile = profile_data.copy()
    with console.status("[cyan]Tailoring resume achievements to match the job keywords...[/cyan]"):
        try:
            response = query_llm(prompt)
            data = parse_json_from_llm(response)
            if isinstance(data, list):
                tailored_profile["experience"] = data
        except Exception as e:
            console.print(f"[yellow]⚠ LLM tailoring failed: {e}. Using base profile.[/yellow]")
    return tailored_profile

def draft_cover_letter_with_llm(profile_data: Dict[str, Any], company_name: str, role_title: str, jd_text: str) -> List[str]:
    """Draft tailored cover letter paragraphs matching target JD using the LLM"""
    prompt = (
        f"Draft a targeted, single-page cover letter for a {role_title} position at {company_name}.\n"
        f"Candidate Profile:\n{json.dumps(profile_data)}\n\n"
        f"Job Description:\n{jd_text}\n\n"
        "Instructions:\n"
        "- Write exactly 3 body paragraphs: Paragraph 1 (Introduction & alignment with company mission), "
        "Paragraph 2 (Deep technical fit & matching achievements), Paragraph 3 (Closing and call to action).\n"
        "- Keep it concise so it compiles cleanly on a single page.\n"
        "Output the cover letter as a JSON array of three strings (one for each paragraph), strictly enclosed in <json> and </json> tags."
    )
    with console.status("[cyan]Drafting cover letter paragraphs...[/cyan]"):
        try:
            response = query_llm(prompt)
            data = parse_json_from_llm(response)
            if isinstance(data, list) and len(data) >= 3:
                return [str(item) for item in data]
        except Exception as e:
            console.print(f"[yellow]⚠ LLM cover drafting failed: {e}. Using generic paragraphs.[/yellow]")
            
    return [
        f"I am writing to express my interest in the {role_title} role at {company_name}.",
        f"With my background in engineering, I am confident I can contribute to your team.",
        f"Thank you for your consideration. I look forward to discussing how my skills align with your needs."
    ]


@app.command()
def init():
    """Initialize system configuration, directories, and SQLite database"""
    console.print("[cyan]→ Initializing job-search-ai app directory...[/cyan]")
    ensure_app_dirs()
    init_db()
    
    # Copy companies_seed.json from template if missing
    seed_src = Path(__file__).parent.parent / "templates" / "companies_seed.json"
    seed_dst = APP_DIR / "companies_seed.json"
    
    if seed_src.exists() and not seed_dst.exists():
        shutil.copy(seed_src, seed_dst)
        console.print("  ✓ Copied company seeds to ~/.job-search/companies_seed.json")
        
    config = load_config()
    console.print(f"  ✓ Initialized database and folder structure under {APP_DIR}")
    console.print(f"  ✓ Configuration loaded: target city = [green]{config.target.city}[/green]")
    console.print("\n[bold green]✓ Initialization complete![/bold green] Run 'job-search discover' to start.")


@app.command()
def discover():
    """Discover target companies matching your location and keywords"""
    config = load_config()
    city = config.target.city
    keywords = config.target.role_keywords
    
    console.print(f"[cyan]→ Starting company discovery for city '[green]{city}[/green]'...[/cyan]")
    
    # 1. Load Seed Database
    seed_path = APP_DIR / "companies_seed.json"
    seed_list = []
    if seed_path.exists():
        with open(seed_path, "r") as f:
            seed_list = json.load(f)
    else:
        console.print("[yellow]⚠ Seed database companies_seed.json not found. Running live search only.[/yellow]")
        
    db = next(get_db())
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        # A. Filter Seeds
        progress.add_task(description="Filtering company seed list...", total=None)
        seed_matches = []
        for company in seed_list:
            locations = [l.lower() for l in company.get("locations", [])]
            if city.lower() in locations or "remote" in locations:
                seed_matches.append(company)
                
        # B. Run Live Scraping
        progress.add_task(description="Scraping DuckDuckGo for active boards...", total=None)
        live_matches = harvest_live_companies(city, keywords)
        
    # C. Merge & Persist to Database (UPSERT logic)
    total_added = 0
    total_updated = 0
    
    for c in seed_matches:
        slug = c.get("api_slug")
        api_type = c.get("api")
        if not slug or not api_type:
            continue
            
        existing = db.query(DBCompany).filter(
            DBCompany.api_slug == slug,
            DBCompany.api_type == api_type
        ).first()
        
        if existing:
            existing.notes = f"Seed company footprint in {city}"
            total_updated += 1
        else:
            db_c = DBCompany(
                name=c.get("name"),
                api_slug=slug,
                api_type=api_type,
                careers_url=c.get("careers_url", ""),
                tier=c.get("tier", 2),
                notes=f"Seed company footprint in {city}",
                is_discovered=False
            )
            db.add(db_c)
            total_added += 1
            
    for c in live_matches:
        slug = c.get("api_slug")
        api_type = c.get("api")
        
        existing = db.query(DBCompany).filter(
            DBCompany.api_slug == slug,
            DBCompany.api_type == api_type
        ).first()
        
        if not existing:
            db_c = DBCompany(
                name=c.get("name"),
                api_slug=slug,
                api_type=api_type,
                careers_url=c.get("careers_url", ""),
                tier=3,
                notes=c.get("notes"),
                is_discovered=True
            )
            db.add(db_c)
            total_added += 1
            
    db.commit()
    db.close()
    
    console.print(f"[bold green]✓ Discovery complete![/bold green] Added {total_added} new companies, updated {total_updated} seeds.")
    console.print("Run 'job-search status' to view your target board.")


@app.command(name="build")
def build_profile():
    """Start an AI-driven interactive conversation to build your resume profile"""
    console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
    console.print("[bold white]   AI INTERACTIVE PROFILE BUILDER   [/bold white]")
    console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]\n")
    console.print("Starting chat with Claude to build your profile. Type 'exit' to quit at any time.\n")
    
    chat_history = [
        {"role": "system", "content": (
            "You are conducting an interactive interview to build the candidate's resume. "
            "Ask ONE brief question at a time to collect their name, email, phone, location, education, and experience. "
            "Focus heavily on achievements and proactively probe for metrics using the Google STAR/XYZ formula (Accomplished X, measured by Y, by doing Z). "
            "Be friendly and conversational. Keep questions short. "
            "Once you have gathered all necessary information (name, email, phone, location, education, at least 1 job, and skills), "
            "compile the profile into a JSON matching this schema: "
            '{"name": "", "email": "", "phone": "", "location": "", "linkedin": "", "github": "", "summary": "", '
            '"experience": [{"company": "", "title": "", "start": "", "end": "", "location": "", "bullets": [""]}], '
            '"education": [{"institution": "", "degree": "", "field": "", "start": "", "end": "", "location": ""}], '
            '"skills": {"languages": [], "frameworks_and_tools": [], "databases": []}} '
            "Output the final JSON strictly enclosed in <json> and </json> tags, and append the keyword 'INTERVIEW_COMPLETE' at the very end."
        )}
    ]
    
    llm_prompt = "Generate a friendly opening greeting to the candidate, introducing yourself as the Job Search AI Assistant and asking for their name to start."
    chat_history.append({"role": "user", "content": llm_prompt})
    
    with console.status("[cyan]Connecting to AI Assistant...[/cyan]"):
        try:
            greeting = query_llm(json.dumps(chat_history))
            console.print(f"\n[bold green]AI Assistant:[/bold green] {greeting.strip()}\n")
            chat_history.append({"role": "assistant", "content": greeting})
        except Exception as e:
            console.print(f"[red]Error starting interview: {e}[/red]")
            return
            
    while True:
        user_input = Prompt.ask("[bold blue]You[/bold blue]")
        if user_input.strip().lower() in ["exit", "quit"]:
            console.print("[yellow]Interview cancelled.[/yellow]")
            break
            
        chat_history.append({"role": "user", "content": user_input})
        
        with console.status("[cyan]AI is thinking...[/cyan]"):
            try:
                response = query_llm(json.dumps(chat_history))
            except Exception as e:
                console.print(f"[red]Error communicating with AI: {e}[/red]")
                break
                
        if "INTERVIEW_COMPLETE" in response or "<json>" in response:
            try:
                profile_data = parse_json_from_llm(response)
                
                db = next(get_db())
                db.query(DBProfile).delete()
                db_profile = DBProfile(
                    name=profile_data["name"],
                    email=profile_data["email"],
                    phone=profile_data["phone"],
                    location=profile_data["location"],
                    linkedin=profile_data.get("linkedin", ""),
                    github=profile_data.get("github", ""),
                    raw_profile_json=json.dumps(profile_data)
                )
                db.add(db_profile)
                db.commit()
                db.close()
                
                with open(APP_DIR / "profile.json", "w") as f:
                    json.dump(profile_data, f, indent=2)
                    
                config = load_config()
                base_tex = APP_DIR / "output" / "base-resume.tex"
                render_resume(profile_data, config.resume.default_template, base_tex)
                
                console.print("\n[bold green]✓ Profile successfully compiled and saved![/bold green]")
                console.print(f"  → Base PDF resume generated at: [cyan]{base_tex.with_suffix('.pdf')}[/cyan]\n")
                break
            except Exception as ex:
                chat_history.append({"role": "system", "content": f"JSON parsing failed: {ex}. Please output clean JSON wrapped in <json>...</json> tags."})
                console.print(f"\n[bold green]AI Assistant:[/bold green] Let me compile that again. Please hold...\n")
                continue
        
        console.print(f"\n[bold green]AI Assistant:[/bold green] {response.strip()}\n")
        chat_history.append({"role": "assistant", "content": response})


@app.command()
def scan(company: Optional[str] = None):
    """Scan company career boards for open roles matching your keywords"""
    config = load_config()
    db = next(get_db())
    
    # Determine which companies to scan
    if company:
        query = db.query(DBCompany).filter(DBCompany.name.ilike(f"%{company}%")).all()
    else:
        query = db.query(DBCompany).all()
        
    if not query:
        console.print("[yellow]No target companies found. Run 'job-search discover' first.[/yellow]")
        db.close()
        return
        
    scraper = JobScraper(
        city=config.target.city,
        keywords=config.target.role_keywords,
        exclude_keywords=config.target.exclude_keywords
    )
    
    matched_jobs = []
    
    # Fetch base profile summary for fit evaluation
    profile = db.query(DBProfile).first()
    profile_summary = ""
    if profile:
        profile_summary = profile.raw_profile_json
        
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task(description=f"Scanning {len(query)} companies...", total=len(query))
        
        for c in query:
            if not c.api_type or not c.api_slug:
                progress.advance(task)
                continue
            progress.update(task, description=f"Scanning {c.name}...")
            jobs = scraper.scan_company(c.api_type, c.api_slug)
            
            for j in jobs:
                j["company_id"] = c.id
                j["company_name"] = c.name
                matched_jobs.append(j)
                
            progress.advance(task)

    if not matched_jobs:
        console.print("[yellow]No open roles matching your keywords were found.[/yellow]")
        db.close()
        return

    # Bulk fit evaluation via LLM
    if profile_summary:
        matched_jobs = evaluate_fit_in_bulk(profile_summary, matched_jobs)
    else:
        for j in matched_jobs:
            j["fit_rating"] = "Medium"
            j["fit_score"] = 50

    # Save matching roles to DB applications as Wishlist
    app_added = 0
    for j in matched_jobs:
        existing = db.query(DBApplication).filter(DBApplication.jd_url == j["url"]).first()
        if not existing:
            db_app = DBApplication(
                company_id=j["company_id"],
                role_title=j["title"],
                jd_url=j["url"],
                fit_rating=j["fit_rating"],
                fit_score=j["fit_score"],
                status="Wishlist"
            )
            db.add(db_app)
            app_added += 1
            
    db.commit()
    db.close()

    # Print matching roles
    table = Table(title="ACTIVE RECRUITING POSITIONS")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Company", style="bold white")
    table.add_column("Role Title", style="white")
    table.add_column("Location", style="blue")
    table.add_column("Fit Score", justify="center", style="green")
    
    for idx, j in enumerate(matched_jobs):
        score_color = "green" if j["fit_rating"] == "High" else "yellow" if j["fit_rating"] == "Medium" else "red"
        table.add_row(
            str(idx + 1),
            j["company_name"],
            j["title"],
            j["location"],
            f"[{score_color}]{j['fit_score']}% ({j['fit_rating']})[/{score_color}]"
        )
        
    console.print(table)
    console.print(f"\n[bold green]✓ Scan complete![/bold green] Added {app_added} new roles to Wishlist.")
    console.print("Run 'job-search status' to see the funnel pipeline.")


@app.command()
def resume(company: str, url: str):
    """Tailor your resume for a specific job description and compile to PDF"""
    db = next(get_db())
    profile = db.query(DBProfile).first()
    if not profile:
        console.print("[red]Error: Base profile not found. Run 'job-search build-profile' first.[/red]")
        db.close()
        return
        
    profile_data = json.loads(profile.raw_profile_json)
    
    # 1. Fetch JD
    console.print(f"[cyan]→ Fetching Job Description from {url}...[/cyan]")
    comp_name, role_title, jd_text = fetch_jd_text_from_url(url)
    
    if not role_title or not jd_text:
        console.print("[yellow]Could not automatically fetch JD from URL. Please paste it below:[/yellow]")
        role_title = Prompt.ask("Role Title", default=role_title or "Software Engineer")
        jd_text = Prompt.ask("Job Description details (paste text and press Enter)")
        
    # 2. Tailor Experience bullets via LLM
    tailored_data = tailor_experience_with_llm(profile_data, jd_text)
    
    # 3. Render
    config = load_config()
    clean_company = company.lower().replace(" ", "_")
    output_tex = APP_DIR / "output" / f"resume_{clean_company}.tex"
    
    try:
        pdf_path = render_resume(tailored_data, config.resume.default_template, output_tex)
        console.print(f"\n[bold green]✓ Tailored Resume generated![/bold green] Saved at:")
        console.print(f"  [cyan]{pdf_path}[/cyan]\n")
        
        # Save application state to SQLite
        existing_company = db.query(DBCompany).filter(DBCompany.name.ilike(f"%{company}%")).first()
        comp_id = existing_company.id if existing_company else None
        
        # Update or create application entry
        existing_app = db.query(DBApplication).filter(DBApplication.jd_url == url).first()
        if existing_app:
            existing_app.tailored_resume_path = str(pdf_path)
            existing_app.status = "Tailored"
        else:
            new_app = DBApplication(
                company_id=comp_id,
                role_title=role_title,
                jd_url=url,
                jd_text=jd_text,
                tailored_resume_path=str(pdf_path),
                status="Tailored"
            )
            db.add(new_app)
            
        db.commit()
    except Exception as e:
        console.print(f"[red]Error compiling LaTeX resume: {e}[/red]")
        
    db.close()


@app.command()
def cover(company: str, url: str):
    """Generate a matching tailored LaTeX cover letter for the target job"""
    db = next(get_db())
    profile = db.query(DBProfile).first()
    if not profile:
        console.print("[red]Error: Base profile not found. Run 'job-search build-profile' first.[/red]")
        db.close()
        return
        
    profile_data = json.loads(profile.raw_profile_json)
    
    # 1. Fetch JD
    console.print(f"[cyan]→ Fetching Job Description from {url}...[/cyan]")
    comp_name, role_title, jd_text = fetch_jd_text_from_url(url)
    
    if not role_title or not jd_text:
        console.print("[yellow]Could not automatically fetch JD. Please paste detail:[/yellow]")
        role_title = Prompt.ask("Role Title", default=role_title or "Software Engineer")
        jd_text = Prompt.ask("Job Description details (paste text)")
        
    # 2. Draft Cover letter paragraphs via LLM
    paragraphs = draft_cover_letter_with_llm(profile_data, company, role_title, jd_text)
    
    # 3. Render cover letter matching styling
    config = load_config()
    clean_company = company.lower().replace(" ", "_")
    output_tex = APP_DIR / "output" / f"cover_{clean_company}.tex"
    
    try:
        pdf_path = render_cover_letter(
            profile_data, 
            company, 
            role_title, 
            paragraphs, 
            config.resume.default_template, 
            output_tex
        )
        console.print(f"\n[bold green]✓ Tailored Cover Letter generated![/bold green] Saved at:")
        console.print(f"  [cyan]{pdf_path}[/cyan]\n")
        
        # Save details to DB
        existing_app = db.query(DBApplication).filter(DBApplication.jd_url == url).first()
        if existing_app:
            existing_app.tailored_cover_path = str(pdf_path)
            db.commit()
    except Exception as e:
        console.print(f"[red]Error compiling LaTeX cover letter: {e}[/red]")
        
    db.close()


@app.command()
def apply(company: str, url: str):
    """Auto-fill job application forms and attach tailored PDF resume"""
    db = next(get_db())
    app_entry = db.query(DBApplication).filter(DBApplication.jd_url == url).first()
    
    resume_path = ""
    if app_entry and app_entry.tailored_resume_path:
        resume_path = app_entry.tailored_resume_path
    else:
        # Check fallback base resume
        base_resume = APP_DIR / "output" / "base-resume.pdf"
        if base_resume.exists():
            resume_path = str(base_resume)
            console.print("[yellow]⚠ Tailored resume not found. Falling back to base-resume.pdf[/yellow]")
        else:
            console.print("[red]Error: No PDF resumes found. Run 'job-search resume' or 'job-search build-profile' first.[/red]")
            db.close()
            return
            
    # Executing the browser automator script
    script_path = APP_DIR / "scripts" / "apply.py"
    if not script_path.exists():
        script_path = Path(__file__).parent.parent / "scripts" / "apply.py"
        
    if not script_path.exists():
        console.print(f"[red]Error: Form automation script not found at {script_path}[/red]")
        db.close()
        return
        
    console.print(f"[cyan]→ Launching Playwright Chromium browser to auto-fill form...[/cyan]")
    
    try:
        # Run scripts/apply.py as a subprocess passing the url and resume path
        cmd = [sys.executable, str(script_path), url, resume_path]
        
        # We start it as a visible headed browser process
        subprocess.run(cmd, check=True)
        
        # Update database application funnel state to 'Applied'
        if app_entry:
            app_entry.status = "Applied"
            app_entry.applied_date = datetime.now()
            db.commit()
            console.print(f"[bold green]✓ Application form filled![/bold green] Funnel status updated to 'Applied'.")
    except Exception as e:
        console.print(f"[red]Form auto-fill failed or terminated: {e}[/red]")
        
    db.close()

@app.command()
def status():
    """View application pipeline status and target companies"""
    db = next(get_db())
    companies = db.query(DBCompany).all()
    applications = db.query(DBApplication).all()
    
    if not companies:
        console.print("[yellow]No target companies in database. Run 'job-search discover' first.[/yellow]")
        db.close()
        return
        
    table = Table(title="TARGET COMPANIES IN SCOPE")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Company Name", style="bold white")
    table.add_column("API Type", style="magenta")
    table.add_column("Slug", style="green")
    table.add_column("Tier", justify="center", style="yellow")
    table.add_column("Source", style="blue")
    
    for c in companies:
        source = "Discovered" if c.is_discovered else "Seed List"
        table.add_row(
            str(c.id),
            c.name,
            c.api_type or "Scrape",
            c.api_slug or "N/A",
            f"T{c.tier}",
            source
        )
        
    console.print(table)
    
    if applications:
        app_table = Table(title="APPLICATION FUNNEL PIPELINE")
        app_table.add_column("ID", justify="right", style="cyan")
        app_table.add_column("Company", style="bold white")
        app_table.add_column("Role Title", style="white")
        app_table.add_column("Fit Score", justify="center", style="green")
        app_table.add_column("Status", style="yellow")
        app_table.add_column("Resume Path", style="cyan")
        
        for app in applications:
            comp_name = app.company.name if app.company else "Unknown"
            score_str = f"{app.fit_score}% ({app.fit_rating})" if app.fit_score else "N/A"
            resume_name = Path(app.tailored_resume_path).name if app.tailored_resume_path else "None"
            app_table.add_row(
                str(app.id),
                comp_name,
                app.role_title,
                score_str,
                app.status,
                resume_name
            )
        console.print(app_table)
        
    db.close()

@app.command()
def ui(port: int = 8000):
    """Launch the local keyless Web UI dashboard in your browser"""
    import uvicorn
    
    url = f"http://127.0.0.1:{port}"
    console.print(f"[bold green]✓ Starting local Web UI server...[/bold green]")
    console.print(f"  → Opening browser at: [cyan]{url}[/cyan]")
    
    def open_browser():
        webbrowser.open(url)
        
    threading.Timer(1.5, open_browser).start()
    
    uvicorn.run("job_search.core.server:app", host="0.0.0.0", port=port, log_level="info")

from datetime import datetime

def main():
    app()

if __name__ == "__main__":
    main()

