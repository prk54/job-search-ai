import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from job_search.core.config import APP_DIR, load_config

def escape_latex(text: str) -> str:
    """Escape special LaTeX characters to prevent compilation failures"""
    if not text:
        return ""
    
    # We first replace backslashes to avoid double-escaping later replacements
    text = text.replace("\\", "\\textbackslash{}")
    
    # Escape other LaTeX characters
    escapes = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "–": "--",  # standard en-dash
        "—": "---", # standard em-dash
    }
    
    for key, val in escapes.items():
        # Make sure we don't double escape if already escaped
        text = re.sub(r'(?<!\\)' + re.escape(key), val, text)
        
    return text

def build_experience_latex(experience: List[Dict[str, Any]]) -> str:
    """Build the LaTeX experience block using the subheadings schema"""
    lines = []
    for job in experience:
        company = escape_latex(job.get("company", ""))
        title = escape_latex(job.get("title", ""))
        start = escape_latex(job.get("start", ""))
        end = escape_latex(job.get("end", ""))
        location = escape_latex(job.get("location", ""))
        
        # Heading
        lines.append(f"  \\resumeSubheading{{{company}}}{{{start} -- {end}}}{{{title}}}{{{location}}}")
        
        # Bullets
        bullets = job.get("bullets", [])
        if bullets:
            lines.append("  \\resumeItemListStart")
            for bullet in bullets:
                lines.append(f"    \\resumeItem{{{escape_latex(bullet)}}}")
            lines.append("  \\resumeItemListEnd")
            
    return "\n".join(lines)

def build_skills_latex(skills: Dict[str, List[str]]) -> str:
    """Build the categorized LaTeX skills list"""
    lines = []
    for category, items in skills.items():
        if not items:
            continue
        # Format key to nice title, e.g. frontend -> Frontend
        cat_title = escape_latex(category.replace("_", " ").title())
        items_str = escape_latex(", ".join(items))
        lines.append(f"    \\textbf{{{cat_title}}}: {items_str} \\\\")
        
    return "\n".join(lines)

def build_education_latex(education: List[Dict[str, Any]]) -> str:
    """Build the LaTeX education block"""
    lines = []
    for school in education:
        inst = escape_latex(school.get("institution", ""))
        degree = escape_latex(school.get("degree", ""))
        field = escape_latex(school.get("field", ""))
        start = escape_latex(school.get("start", ""))
        end = escape_latex(school.get("end", ""))
        location = escape_latex(school.get("location", ""))
        
        degree_str = f"{degree} in {field}" if field else degree
        lines.append(f"  \\resumeSubheading{{{inst}}}{{{start} -- {end}}}{{{escape_latex(degree_str)}}}{{{location}}}")
        
    return "\n".join(lines)

def compile_pdf(tex_path: Path) -> Path:
    """Compile LaTeX file using tectonic subprocess"""
    output_dir = tex_path.parent
    
    # Verify tectonic exists
    if not shutil.which("tectonic"):
        raise FileNotFoundError(
            "Tectonic is not installed. PDF compilation failed.\n"
            "Please install it using: brew install tectonic"
        )
        
    cmd = ["tectonic", str(tex_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Tectonic compilation failed:\n{result.stderr or result.stdout}")
        
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        raise FileNotFoundError(f"Tectonic finished but could not find PDF at: {pdf_path}")
        
    return pdf_path

def get_pdf_page_count(pdf_path: Path) -> int:
    """Read PDF page count using pdfinfo"""
    if shutil.which("pdfinfo"):
        try:
            r = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if "Pages:" in line:
                    return int(line.split()[-1])
        except:
            pass
    return 1 # Fallback assumption

def render_resume(profile_data: Dict[str, Any], template_name: str, output_tex_path: Path) -> Path:
    """Generate LaTeX source code and compile it into a PDF resume"""
    template_path = APP_DIR / "templates" / f"{template_name}.tex"
    if not template_path.exists():
        # Fallback to local copy
        template_path = Path(__file__).parent.parent / "templates" / f"{template_name}-resume.tex"
        if not template_path.exists():
            template_path = Path(__file__).parent.parent / "templates" / f"{template_name}.tex"
            
    if not template_path.exists():
        raise FileNotFoundError(f"Template '{template_name}' not found.")
        
    with open(template_path, "r") as f:
        template_content = f.read()
        
    # Build sections
    exp_latex = build_experience_latex(profile_data.get("experience", []))
    skills_latex = build_skills_latex(profile_data.get("skills", {}))
    edu_latex = build_education_latex(profile_data.get("education", []))
    
    # Optional Professional Summary
    summary_text = escape_latex(profile_data.get("summary", ""))
    summary_section = f"\\section{{Summary}}\n\\small{{\n  {summary_text}\n}}\n\\vspace{{-2pt}}" if summary_text else ""
    
    # Optional Certifications
    certs = profile_data.get("certifications", [])
    certs_section = ""
    if certs:
        certs_section = "\\section{Certifications}\n\\resumeSubHeadingListStart\n"
        for c in certs:
            certs_section += f"  \\item[] \\small{{ \\textbf{{{escape_latex(c)}}} }}\n"
        certs_section += "\\resumeSubHeadingListEnd"
        
    # Optional Website line
    website = profile_data.get("portfolio", "") or profile_data.get("github", "")
    website_line = f" \\quad $|$ \\quad \\href{{{website}}}{{\\faGlobe\\ Website}}" if website else ""
    
    # Replace placeholders
    content = template_content
    content = content.replace("<<NAME>>", escape_latex(profile_data.get("name", "")))
    content = content.replace("<<EMAIL>>", escape_latex(profile_data.get("email", "")))
    content = content.replace("<<PHONE>>", escape_latex(profile_data.get("phone", "")))
    content = content.replace("<<LOCATION>>", escape_latex(profile_data.get("location", "")))
    content = content.replace("<<WEBSITE_LINE>>", website_line)
    content = content.replace("<<SUMMARY_SECTION>>", summary_section)
    content = content.replace("<<EXPERIENCE>>", exp_latex)
    content = content.replace("<<SKILLS>>", skills_latex)
    content = content.replace("<<EDUCATION>>", edu_latex)
    content = content.replace("<<CERTIFICATIONS_SECTION>>", certs_section)
    
    # Write tex file
    output_tex_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_tex_path, "w") as f:
        f.write(content)
        
    # Compile
    return compile_pdf(output_tex_path)

def render_cover_letter(profile_data: Dict[str, Any], company_name: str, role_title: str, paragraphs: List[str], template_name: str, output_tex_path: Path) -> Path:
    """Generate LaTeX source code and compile it into a matching PDF cover letter"""
    template_path = APP_DIR / "templates" / f"{template_name}.tex"
    if not template_path.exists():
        # Fallback to local copy
        template_path = Path(__file__).parent.parent / "templates" / f"{template_name}-resume.tex"
        if not template_path.exists():
            template_path = Path(__file__).parent.parent / "templates" / f"{template_name}.tex"
            
    if not template_path.exists():
        raise FileNotFoundError(f"Template '{template_name}' not found.")
        
    with open(template_path, "r") as f:
        template_content = f.read()
        
    # Extract only the preamble (everything up to \begin{document})
    preamble_match = re.search(r"^(.*?\\begin\{document\})", template_content, re.DOTALL)
    if not preamble_match:
        raise ValueError(f"Invalid template format: Could not find \\begin{{document}} in {template_name}")
        
    preamble = preamble_match.group(1)
    
    # Replace header placeholders in the preamble / doc start
    website = profile_data.get("portfolio", "") or profile_data.get("github", "")
    website_line = f" \\quad $|$ \\quad \\href{{{website}}}{{\\faGlobe\\ Website}}" if website else ""
    
    # Construct cover letter body
    body_lines = []
    
    # Header Info (Name, contact details)
    body_lines.append(f"\\begin{{center}}")
    body_lines.append(f"    {{\\LARGE \\scshape {escape_latex(profile_data.get('name', ''))}}} \\\\[2pt]")
    body_lines.append(f"    \\small ")
    body_lines.append(f"    \\href{{mailto:{profile_data.get('email', '')}}}{{\\faEnvelope\\ {profile_data.get('email', '')}}} \\quad $|$ \\quad")
    body_lines.append(f"    \\faPhone\\ {profile_data.get('phone', '')} \\quad $|$ \\quad")
    body_lines.append(f"    \\href{{{profile_data.get('linkedin', '')}}}{{\\faLinkedin\\ LinkedIn}} \\quad $|$ \\quad")
    body_lines.append(f"    {escape_latex(profile_data.get('location', ''))}")
    if website_line:
        body_lines.append(website_line)
    body_lines.append(f"\\end{{center}}")
    body_lines.append(f"\\vspace{{-4pt}}")
    
    # Date
    body_lines.append(f"\\hfill \\today \\\\")
    body_lines.append(f"\\vspace{{10pt}}")
    
    # Recipient
    body_lines.append(f"\\begin{{flushleft}}")
    body_lines.append(f"\\textbf{{Hiring Team}} \\\\")
    body_lines.append(f"\\textit{{{escape_latex(company_name)}}} \\\\")
    body_lines.append(f"\\end{{flushleft}}")
    body_lines.append(f"\\vspace{{10pt}}")
    
    # Opening Salutation
    body_lines.append(f"Dear Hiring Team at {escape_latex(company_name)}, \\\\")
    body_lines.append(f"\\vspace{{8pt}}")
    
    # Paragraphs
    for p in paragraphs:
        body_lines.append(f"{escape_latex(p)} \\\\")
        body_lines.append(f"\\vspace{{8pt}}")
        
    # Sign-off
    body_lines.append(f"\\vspace{{10pt}}")
    body_lines.append(f"Sincerely, \\\\")
    body_lines.append(f"\\vspace{{20pt}}")
    body_lines.append(f"{escape_latex(profile_data.get('name', ''))}")
    
    body_lines.append(f"\\end{{document}}")
    
    # Combine preamble and body (ignoring the original template body)
    full_content = preamble + "\n" + "\n".join(body_lines)
    
    # Replace basic name, email, phone, location placeholders if they are defined inside the preamble
    full_content = full_content.replace("<<NAME>>", escape_latex(profile_data.get("name", "")))
    full_content = full_content.replace("<<EMAIL>>", escape_latex(profile_data.get("email", "")))
    full_content = full_content.replace("<<PHONE>>", escape_latex(profile_data.get("phone", "")))
    full_content = full_content.replace("<<LOCATION>>", escape_latex(profile_data.get("location", "")))
    full_content = full_content.replace("<<WEBSITE_LINE>>", website_line)
    
    # Write tex file
    output_tex_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_tex_path, "w") as f:
        f.write(full_content)
        
    # Compile
    return compile_pdf(output_tex_path)


import shutil
