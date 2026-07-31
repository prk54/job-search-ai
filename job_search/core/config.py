import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field

# Base Directory: ~/.job-search
APP_DIR = Path.home() / ".job-search"
CONFIG_PATH = APP_DIR / "config.yml"

class TargetConfig(BaseModel):
    city: str = "San Francisco"
    tc_target: str = "$200K USD"
    currency: str = "USD"
    role_levels: List[str] = Field(default_factory=lambda: ["Senior", "Staff", "Principal", "Lead"])
    role_keywords: List[str] = Field(default_factory=lambda: [
        "Software Engineer", "SWE", "Full Stack Engineer", "Backend Engineer", "Platform Engineer"
    ])
    exclude_keywords: List[str] = Field(default_factory=lambda: [
        "Intern", "Junior", "Graduate", "Manager", "Sales", "Recruiter"
    ])

class LLMConfig(BaseModel):
    provider: str = "claude" # options: claude, gemini, agy, copilot, ollama, custom
    custom_command: Optional[str] = None

class ResumeConfig(BaseModel):
    default_template: str = "jake"
    max_pages: int = 1

class AppConfig(BaseModel):
    target: TargetConfig = Field(default_factory=TargetConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    resume: ResumeConfig = Field(default_factory=ResumeConfig)

def ensure_app_dirs():
    """Ensure all required directories exist under ~/.job-search/"""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "templates").mkdir(exist_ok=True)
    (APP_DIR / "output").mkdir(exist_ok=True)
    (APP_DIR / "intel").mkdir(exist_ok=True)
    (APP_DIR / "scripts").mkdir(exist_ok=True)

def load_config() -> AppConfig:
    """Load config.yml from ~/.job-search/"""
    ensure_app_dirs()
    if not CONFIG_PATH.exists():
        # Save default config
        config = AppConfig()
        save_config(config)
        return config
        
    try:
        with open(CONFIG_PATH, "r") as f:
            raw_data = yaml.safe_load(f) or {}
        return AppConfig(**raw_data)
    except Exception as e:
        # Fallback to default config on error
        return AppConfig()

def save_config(config: AppConfig):
    """Save config.yml to ~/.job-search/"""
    ensure_app_dirs()
    try:
        with open(CONFIG_PATH, "w") as f:
            yaml.safe_dump(config.model_dump(), f, default_flow_style=False)
    except Exception as e:
        print(f"Error saving configuration: {e}")
