import os
import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Tuple
from job_search.core.config import APP_DIR

class JobScraper:
    def __init__(self, city: str, keywords: List[str], exclude_keywords: List[str]):
        self.city = city.lower()
        self.keywords = [k.lower() for k in keywords]
        self.exclude_keywords = [e.lower() for e in exclude_keywords]

    def _matches_filters(self, title: str, location: str) -> bool:
        title_lower = title.lower()
        loc_lower = location.lower()
        
        # Location match (target city or Remote)
        loc_match = self.city in loc_lower or "remote" in loc_lower
        if not loc_match:
            return False
            
        # Exclude keywords filter
        if any(e in title_lower for e in self.exclude_keywords):
            return False
            
        # Match positive keywords
        has_keyword = any(k in title_lower for k in self.keywords)
        return has_keyword

    def scan_greenhouse(self, slug: str) -> List[Dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
        jobs = []
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                raw_jobs = data.get("jobs", [])
                
                for rj in raw_jobs:
                    title = rj.get("title", "")
                    location = rj.get("location", {}).get("name", "")
                    
                    if self._matches_filters(title, location):
                        jobs.append({
                            "title": title,
                            "url": rj.get("absolute_url", ""),
                            "location": location,
                            "id": str(rj.get("id", ""))
                        })
        except Exception as e:
            # Silently log errors for individual company scrapes
            pass
        return jobs

    def scan_lever(self, slug: str) -> List[Dict[str, Any]]:
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        jobs = []
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_jobs = json.loads(response.read().decode())
                
                for rj in raw_jobs:
                    title = rj.get("title", "")
                    location = rj.get("categories", {}).get("location", "")
                    
                    if self._matches_filters(title, location):
                        jobs.append({
                            "title": title,
                            "url": rj.get("hostedUrl", ""),
                            "location": location,
                            "id": str(rj.get("id", ""))
                        })
        except Exception as e:
            pass
        return jobs

    def scan_ashby(self, slug: str) -> List[Dict[str, Any]]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
        jobs = []
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                raw_jobs = data.get("jobs", [])
                
                for rj in raw_jobs:
                    title = rj.get("title", "")
                    location = rj.get("location", "")
                    
                    if self._matches_filters(title, location):
                        jobs.append({
                            "title": title,
                            "url": rj.get("jobUrl", ""),
                            "location": location,
                            "id": str(rj.get("id", ""))
                        })
        except Exception as e:
            pass
        return jobs

    def scan_company(self, api_type: str, slug: str) -> List[Dict[str, Any]]:
        """Unified entry point to scan an individual company board"""
        if api_type == "greenhouse":
            return self.scan_greenhouse(slug)
        elif api_type == "lever":
            return self.scan_lever(slug)
        elif api_type == "ashby":
            return self.scan_ashby(slug)
        return []

def harvest_live_companies(city: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """Query DuckDuckGo search to dynamically harvest company slugs on Greenhouse and Lever"""
    discovered = []
    seen_slugs = set()
    
    keyword_query = " OR ".join(f'"{k}"' for k in keywords[:2]) # keep query short
    search_term = f'site:boards.greenhouse.io OR site:lever.co {keyword_query} "{city}" 2026'
    query = urllib.parse.quote(search_term)
    url = f"https://html.duckduckgo.com/html/?q={query}"
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # Parse greenhouse slugs
        greenhouse_matches = re.findall(r'boards\.greenhouse\.io/([^/?\'"\s>]+)', html)
        for slug in greenhouse_matches:
            if slug not in ["embed", "v1", "search", "cards", "job"] and not slug.startswith("http") and slug not in seen_slugs:
                seen_slugs.add(slug)
                company_name = slug.replace("-", " ").title()
                discovered.append({
                    "name": company_name,
                    "careers_url": f"https://boards.greenhouse.io/{slug}",
                    "api": "greenhouse",
                    "api_slug": slug,
                    "tc_range": "Varies",
                    "tier": 3,
                    "notes": f"Discovered live in {city} postings"
                })
                
        # Parse lever slugs
        lever_matches = re.findall(r'lever\.co/([^/?\'"\s>]+)', html)
        for slug in lever_matches:
            if slug not in ["apply", "jobs"] and not slug.startswith("http") and slug not in seen_slugs:
                seen_slugs.add(slug)
                company_name = slug.replace("-", " ").title()
                discovered.append({
                    "name": company_name,
                    "careers_url": f"https://jobs.lever.co/{slug}",
                    "api": "lever",
                    "api_slug": slug,
                    "tc_range": "Varies",
                    "tier": 3,
                    "notes": f"Discovered live in {city} postings"
                })
    except Exception as e:
        # Silently fail if scraping blocked/timed out
        pass
        
    return discovered

def fetch_jd_text_from_url(url: str) -> Tuple[str, str, str]:
    """
    Fetch the company name, role title, and job description text from a job URL.
    Returns (company_name, role_title, jd_text).
    """
    url_lower = url.lower()
    try:
        # 1. Greenhouse Board API URL mapping
        # e.g., https://boards.greenhouse.io/stripe/jobs/6990425002
        gh_match = re.search(r'boards\.greenhouse\.io/([^/]+)/jobs/(\d+)', url_lower)
        if gh_match:
            slug = gh_match.group(1)
            job_id = gh_match.group(2)
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}?content=true"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                title = data.get("title", "")
                content = data.get("content", "")
                # Strip HTML tags
                jd_text = re.sub(r'<[^>]+>', ' ', content)
                # Clean multiple spaces
                jd_text = re.sub(r'\s+', ' ', jd_text).strip()
                company_name = slug.replace("-", " ").title()
                return company_name, title, jd_text
                
        # 2. Lever Posting API URL mapping
        # e.g. https://jobs.lever.co/anthropic/5ff794bd-1234-5678-abcd-ef0123456789
        lever_match = re.search(r'jobs\.lever\.co/([^/]+)/([^/]+)', url_lower)
        if lever_match:
            slug = lever_match.group(1)
            posting_id = lever_match.group(2)
            api_url = f"https://api.lever.co/v0/postings/{slug}/{posting_id}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                title = data.get("title", "")
                description = data.get("descriptionPlain", "")
                lists = ""
                for section in data.get("lists", []):
                    lists += "\n" + section.get("text", "") + "\n" + "\n".join(section.get("content", []))
                jd_text = (description + "\n" + lists).strip()
                company_name = slug.replace("-", " ").title()
                return company_name, title, jd_text
    except Exception as e:
        pass
        
    # 3. Fallback: Parse company from domain
    domain_match = re.search(r'https?://(?:www\.)?([^/.]+)\.', url_lower)
    company_name = domain_match.group(1).title() if domain_match else "Target Company"
    return company_name, "", ""

from typing import Tuple

