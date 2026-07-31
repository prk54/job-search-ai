import os
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from job_search.core.config import APP_DIR, load_config, save_config, AppConfig
from job_search.core.db import get_db, DBCompany, DBProfile, DBApplication, init_db
from job_search.core.scraper import JobScraper, harvest_live_companies, fetch_jd_text_from_url
from job_search.core.llm import detect_llm_driver, parse_json_from_llm
from job_search.core.builder import render_resume, render_cover_letter

app = FastAPI(title="job-search-ai Local UI API")

# Allow CORS for localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on server start
init_db()

# Request Models
class ProfileUpdate(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    linkedin: str
    github: str
    summary: str
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: Dict[str, List[str]]

class JDRequest(BaseModel):
    url: str

class CompanyScanRequest(BaseModel):
    company_name: str

class ScrapeRequest(BaseModel):
    city: str
    keywords: List[str]

# API helper functions
def execute_llm_query(prompt: str) -> str:
    config = load_config()
    driver = detect_llm_driver(config.llm.provider, config.llm.custom_command)
    return driver.execute(prompt)

def tailor_experience_with_llm(profile_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
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
    try:
        response = execute_llm_query(prompt)
        data = parse_json_from_llm(response)
        if isinstance(data, list):
            tailored_profile["experience"] = data
    except Exception as e:
        pass
    return tailored_profile

def draft_cover_letter_with_llm(profile_data: Dict[str, Any], company_name: str, role_title: str, jd_text: str) -> List[str]:
    prompt = (
        f"Draft a targeted, single-page cover letter for a {role_title} position at {company_name}.\n"
        f"Candidate Profile:\n{json.dumps(profile_data)}\n\n"
        f"Job Description:\n{jd_text}\n\n"
        "Instructions:\n"
        "- Write exactly 3 body paragraphs: Paragraph 1 (Introduction & alignment with company mission), "
        "Paragraph 2 (Deep technical fit & matching achievements), Paragraph 3 (Closing and call to action).\n"
        "- Keep it portfolio-appropriate so it compiles cleanly on a single page.\n"
        "Output the cover letter as a JSON array of three strings (one for each paragraph), strictly enclosed in <json> and </json> tags."
    )
    try:
        response = execute_llm_query(prompt)
        data = parse_json_from_llm(response)
        if isinstance(data, list) and len(data) >= 3:
            return [str(item) for item in data]
    except Exception as e:
        pass
        
    return [
        f"I am writing to express my interest in the {role_title} role at {company_name}.",
        f"With my background in engineering, I am confident I can contribute to your team.",
        f"Thank you for your consideration. I look forward to discussing how my skills align with your needs."
    ]


# API ENDPOINTS

@app.get("/api/status")
def get_status():
    """Retrieve funnel status counts and general settings"""
    db = next(get_db())
    config = load_config()
    
    # Counts
    wishlist = db.query(DBApplication).filter(DBApplication.status == "Wishlist").count()
    tailored = db.query(DBApplication).filter(DBApplication.status == "Tailored").count()
    applied = db.query(DBApplication).filter(DBApplication.status == "Applied").count()
    interviewing = db.query(DBApplication).filter(DBApplication.status == "Interviewing").count()
    offer = db.query(DBApplication).filter(DBApplication.status == "Offer").count()
    rejected = db.query(DBApplication).filter(DBApplication.status == "Rejected").count()
    
    companies_count = db.query(DBCompany).count()
    profile_exists = db.query(DBProfile).first() is not None
    
    db.close()
    
    return {
        "funnel": {
            "wishlist": wishlist,
            "tailored": tailored,
            "applied": applied,
            "interviewing": interviewing,
            "offer": offer,
            "rejected": rejected
        },
        "companies_count": companies_count,
        "profile_exists": profile_exists,
        "config": {
            "city": config.target.city,
            "tc_target": config.target.tc_target,
            "role_keywords": config.target.role_keywords,
            "llm_provider": config.llm.provider
        }
    }


@app.get("/api/profile")
def get_profile():
    """Fetch stored candidate profile"""
    db = next(get_db())
    profile = db.query(DBProfile).first()
    db.close()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not created yet.")
        
    return json.loads(profile.raw_profile_json)


@app.post("/api/profile")
def update_profile(data: ProfileUpdate):
    """Save/update candidate profile details"""
    db = next(get_db())
    db.query(DBProfile).delete()
    
    profile_dict = data.model_dump()
    
    db_profile = DBProfile(
        name=data.name,
        email=data.email,
        phone=data.phone,
        location=data.location,
        linkedin=data.linkedin,
        github=data.github,
        raw_profile_json=json.dumps(profile_dict)
    )
    db.add(db_profile)
    db.commit()
    db.close()
    
    # Backup file
    with open(APP_DIR / "profile.json", "w") as f:
        json.dump(profile_dict, f, indent=2)
        
    return {"status": "success", "message": "Profile updated."}

# Chat session memory store
chat_sessions = {}

@app.post("/api/interview/start")
def start_interview_api():
    """Start conversational profile builder interview"""
    session_id = "default"
    chat_sessions[session_id] = [
        {"role": "system", "content": (
            "You are conducting an interactive interview to build the candidate's resume. "
            "Ask ONE brief question at a time to collect their name, email, phone, location, education, and experience. "
            "Proactively probe for metrics using the Google STAR/XYZ formula (Accomplished X, measured by Y, by doing Z). "
            "Be friendly. Keep questions short. "
            "Once you have gathered all necessary information (name, email, phone, location, education, at least 1 job, and skills), "
            "compile the profile into a JSON matching this schema: "
            '{"name": "", "email": "", "phone": "", "location": "", "linkedin": "", "github": "", "summary": "", '
            '"experience": [{"company": "", "title": "", "start": "", "end": "", "location": "", "bullets": [""]}], '
            '"education": [{"institution": "", "degree": "", "field": "", "start": "", "end": "", "location": ""}], '
            '"skills": {"languages": [], "frameworks_and_tools": [], "databases": []}} '
            "Output the final JSON strictly enclosed in <json> and </json> tags, and append the keyword 'INTERVIEW_COMPLETE' at the very end."
        )}
    ]
    
    prompt = "Generate a friendly opening greeting to the candidate, introducing yourself as the Job Search AI Assistant and asking for their name to start."
    chat_sessions[session_id].append({"role": "user", "content": prompt})
    
    try:
        greeting = execute_llm_query(json.dumps(chat_sessions[session_id]))
        chat_sessions[session_id].append({"role": "assistant", "content": greeting})
        return {"status": "chatting", "message": greeting.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/chat")
def chat_interview_api(data: ChatMessage):
    """Continue conversational profile builder interview"""
    session_id = "default"
    if session_id not in chat_sessions:
        # Auto start if session expired
        start_interview_api()
        
    chat_sessions[session_id].append({"role": "user", "content": data.message})
    
    try:
        response = execute_llm_query(json.dumps(chat_sessions[session_id]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
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
            
            # Clear chat session
            if session_id in chat_sessions:
                del chat_sessions[session_id]
            
            return {"status": "complete", "message": "Interview completed! Profile saved.", "profile": profile_data}
        except Exception as ex:
            chat_sessions[session_id].append({"role": "system", "content": f"JSON parsing failed: {ex}. Please output clean JSON wrapped in <json>...</json> tags."})
            return {"status": "chatting", "message": "Compiling your profile JSON. Let me process that..."}
            
    chat_sessions[session_id].append({"role": "assistant", "content": response})
    return {"status": "chatting", "message": response.strip()}


@app.get("/api/companies")
def get_companies():
    """Retrieve target companies"""
    db = next(get_db())
    companies = db.query(DBCompany).order_by(DBCompany.tier.asc()).all()
    res = []
    for c in companies:
        res.append({
            "id": c.id,
            "name": c.name,
            "api_type": c.api_type,
            "api_slug": c.api_slug,
            "careers_url": c.careers_url,
            "tier": c.tier,
            "notes": c.notes,
            "is_discovered": c.is_discovered
        })
    db.close()
    return res


@app.post("/api/discover")
def run_discovery():
    """Trigger seed filtering and DDG crawling for company discovery"""
    config = load_config()
    city = config.target.city
    keywords = config.target.role_keywords
    
    # Load Seeds
    seed_path = APP_DIR / "companies_seed.json"
    seed_list = []
    if seed_path.exists():
        with open(seed_path, "r") as f:
            seed_list = json.load(f)
            
    db = next(get_db())
    
    # Filter seeds
    seed_matches = []
    for company in seed_list:
        locations = [l.lower() for l in company.get("locations", [])]
        if city.lower() in locations or "remote" in locations:
            seed_matches.append(company)
            
    # DDG Discovery
    live_matches = harvest_live_companies(city, keywords)
    
    # DB Upsert
    added = 0
    for c in seed_matches:
        slug = c.get("api_slug")
        api_type = c.get("api")
        if not slug or not api_type:
            continue
            
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
                tier=c.get("tier", 2),
                notes=f"Seed company footprint in {city}",
                is_discovered=False
            )
            db.add(db_c)
            added += 1
            
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
            added += 1
            
    db.commit()
    db.close()
    return {"status": "success", "added": added}


@app.get("/api/jobs")
def get_jobs():
    """Retrieve funnel application positions"""
    db = next(get_db())
    apps = db.query(DBApplication).order_by(DBApplication.status.desc(), DBApplication.fit_score.desc()).all()
    res = []
    for a in apps:
        comp_name = a.company.name if a.company else "Unknown"
        res.append({
            "id": a.id,
            "company_name": comp_name,
            "role_title": a.role_title,
            "jd_url": a.jd_url,
            "jd_text": a.jd_text,
            "fit_rating": a.fit_rating,
            "fit_score": a.fit_score,
            "status": a.status,
            "tailored_resume_path": a.tailored_resume_path,
            "tailored_cover_path": a.tailored_cover_path,
            "applied_date": a.applied_date.isoformat() if a.applied_date else None
        })
    db.close()
    return res


@app.post("/api/scan")
def run_scan():
    """Scan all company boards for open roles and match fit levels"""
    config = load_config()
    db = next(get_db())
    companies = db.query(DBCompany).all()
    
    if not companies:
        db.close()
        return {"status": "error", "message": "No target companies configured."}
        
    scraper = JobScraper(
        city=config.target.city,
        keywords=config.target.role_keywords,
        exclude_keywords=config.target.exclude_keywords
    )
    
    profile = db.query(DBProfile).first()
    profile_summary = profile.raw_profile_json if profile else ""
    
    matched_jobs = []
    for c in companies:
        if not c.api_type or not c.api_slug:
            continue
        jobs = scraper.scan_company(c.api_type, c.api_slug)
        for j in jobs:
            j["company_id"] = c.id
            j["company_name"] = c.name
            matched_jobs.append(j)
            
    # Fit Evaluation in single batched subprocess
    if profile_summary and matched_jobs:
        # Evaluate up to 30 jobs at a time to prevent overflow context issues
        batch_size = 30
        for i in range(0, len(matched_jobs), batch_size):
            batch = matched_jobs[i:i+batch_size]
            
            jobs_payload = [{"id": j["id"], "title": j["title"], "location": j["location"]} for j in batch]
            prompt = (
                "You are an expert recruiter. Evaluate candidate profile compatibility for these roles.\n"
                f"Candidate Summary:\n{profile_summary}\n\n"
                f"Jobs List:\n{json.dumps(jobs_payload)}\n\n"
                "Return JSON array of fit objects: "
                '[{"id": "...", "fit_rating": "High/Medium/Low", "fit_score": 85}] enclosed in <json> and </json> tags.'
            )
            try:
                response = execute_llm_query(prompt)
                data = parse_json_from_llm(response)
                lookup = {str(item.get("id")): item for item in data if "id" in item}
                for j in batch:
                    item = lookup.get(str(j["id"]))
                    if item:
                        j["fit_rating"] = item.get("fit_rating", "Medium")
                        j["fit_score"] = int(item.get("fit_score", 50))
                    else:
                        j["fit_rating"] = "Medium"
                        j["fit_score"] = 50
            except:
                for j in batch:
                    j["fit_rating"] = "Medium"
                    j["fit_score"] = 50
    else:
        for j in matched_jobs:
            j["fit_rating"] = "Medium"
            j["fit_score"] = 50
            
    # Persist
    added = 0
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
            added += 1
            
    db.commit()
    db.close()
    return {"status": "success", "scanned_companies": len(companies), "jobs_found": len(matched_jobs), "wishlist_added": added}


@app.post("/api/jobs/{job_id}/tailor")
def tailor_resume_api(job_id: int):
    """Trigger LLM subprocess tailoring for a specific job ID and compile PDF"""
    db = next(get_db())
    app_entry = db.query(DBApplication).filter(DBApplication.id == job_id).first()
    if not app_entry:
        db.close()
        raise HTTPException(status_code=404, detail="Job position not found.")
        
    profile = db.query(DBProfile).first()
    if not profile:
        db.close()
        raise HTTPException(status_code=400, detail="Base profile not built. Edit profile first.")
        
    profile_data = json.loads(profile.raw_profile_json)
    
    # Get JD Details
    comp_name, role_title, jd_text = fetch_jd_text_from_url(app_entry.jd_url)
    if not jd_text:
        jd_text = app_entry.jd_text or app_entry.role_title
        
    # Run LLM Subprocess Tailoring
    tailored_data = tailor_experience_with_llm(profile_data, jd_text)
    
    # Save Tex
    config = load_config()
    clean_company = app_entry.company.name.lower().replace(" ", "_") if app_entry.company else "company"
    output_tex = APP_DIR / "output" / f"resume_{clean_company}.tex"
    
    try:
        pdf_path = render_resume(tailored_data, config.resume.default_template, output_tex)
        app_entry.tailored_resume_path = str(pdf_path)
        app_entry.status = "Tailored"
        db.commit()
        db.close()
        return {"status": "success", "pdf_path": str(pdf_path)}
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"LaTeX compilation failed: {e}")


@app.post("/api/jobs/{job_id}/cover")
def tailor_cover_api(job_id: int):
    """Trigger LLM subprocess Cover Letter drafting and compile PDF"""
    db = next(get_db())
    app_entry = db.query(DBApplication).filter(DBApplication.id == job_id).first()
    if not app_entry:
        db.close()
        raise HTTPException(status_code=404, detail="Job position not found.")
        
    profile = db.query(DBProfile).first()
    if not profile:
        db.close()
        raise HTTPException(status_code=400, detail="Base profile not built.")
        
    profile_data = json.loads(profile.raw_profile_json)
    comp_name = app_entry.company.name if app_entry.company else "Target Company"
    
    # Fetch JD details
    _, _, jd_text = fetch_jd_text_from_url(app_entry.jd_url)
    if not jd_text:
        jd_text = app_entry.jd_text or app_entry.role_title
        
    # Draft paragraphs via LLM Subprocess
    paragraphs = draft_cover_letter_with_llm(profile_data, comp_name, app_entry.role_title, jd_text)
    
    # Render PDF cover letter matching styling
    config = load_config()
    clean_company = comp_name.lower().replace(" ", "_")
    output_tex = APP_DIR / "output" / f"cover_{clean_company}.tex"
    
    try:
        pdf_path = render_cover_letter(
            profile_data,
            comp_name,
            app_entry.role_title,
            paragraphs,
            config.resume.default_template,
            output_tex
        )
        app_entry.tailored_cover_path = str(pdf_path)
        db.commit()
        db.close()
        return {"status": "success", "pdf_path": str(pdf_path)}
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"LaTeX compilation failed: {e}")


@app.post("/api/jobs/{job_id}/apply")
def trigger_application_api(job_id: int, background_tasks: BackgroundTasks):
    """Trigger headed Playwright form-filler for target job ID"""
    db = next(get_db())
    app_entry = db.query(DBApplication).filter(DBApplication.id == job_id).first()
    if not app_entry:
        db.close()
        raise HTTPException(status_code=404, detail="Job position not found.")
        
    # Check pdf path
    resume_path = ""
    if app_entry.tailored_resume_path and os.path.exists(app_entry.tailored_resume_path):
        resume_path = app_entry.tailored_resume_path
    else:
        base_resume = APP_DIR / "output" / "base-resume.pdf"
        if base_resume.exists():
            resume_path = str(base_resume)
            
    if not resume_path:
        db.close()
        raise HTTPException(status_code=400, detail="Tailor resume or build profile first.")
        
    script_path = APP_DIR / "scripts" / "apply.py"
    if not script_path.exists():
        script_path = Path(__file__).parent.parent / "scripts" / "apply.py"
        
    if not script_path.exists():
        db.close()
        raise HTTPException(status_code=500, detail="Playwright application script not found.")
        
    # Trigger subprocess automation in background so server does not block
    def run_automation(url: str, resume_p: str, j_id: int):
        cmd = ["python3", str(script_path), url, resume_p]
        try:
            subprocess.run(cmd, check=True)
            # Update status
            inner_db = next(get_db())
            entry = inner_db.query(DBApplication).filter(DBApplication.id == j_id).first()
            if entry:
                entry.status = "Applied"
                entry.applied_date = datetime.utcnow()
                inner_db.commit()
            inner_db.close()
        except Exception as e:
            pass
            
    background_tasks.add_task(run_automation, app_entry.jd_url, resume_path, app_entry.id)
    db.close()
    return {"status": "success", "message": "Automation browser launching."}


@app.get("/api/pdf")
def serve_pdf_file(path: str):
    """Serve local compiled PDF resumes securely to render in UI"""
    # Restrict serving only files located under output directory
    pdf_p = Path(path)
    if not pdf_p.exists() or not pdf_p.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found.")
        
    # Validate it is under ~/.job-search
    if not str(pdf_p.resolve()).startswith(str(APP_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied.")
        
    return FileResponse(pdf_p, media_type="application/pdf")

# Serve static UI files from job_search/ui
ui_dir = Path(__file__).parent.parent / "ui"
if ui_dir.exists():
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")

