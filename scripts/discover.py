#!/usr/bin/env python3
import os
import sys
import json
import re
import urllib.request
import urllib.parse

def load_yaml(file_path):
    # Extremely basic YAML parser to avoid external PyYAML dependency
    if not os.path.exists(file_path):
        return {}
    
    data = {}
    current_key = None
    
    with open(file_path, "r") as f:
        for line in f:
            # Strip comments and whitespace
            clean_line = line.split('#')[0].strip()
            if not clean_line:
                continue
                
            if ":" in clean_line:
                parts = clean_line.split(":", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                
                # Check for list start
                if v.startswith("-") or clean_line.startswith("-"):
                    # We handle lists manually below if needed, but we keep basic parsing
                    pass
                else:
                    # Strip quotes
                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                        v = v[1:-1]
                    data[k] = v
                    
    # Let's write a specific loader for user config.yml targeting key preferences
    try:
        with open(file_path, "r") as f:
            content = f.read()
            
        # Target extracts via regex (most robust for simple configs)
        city_match = re.search(r"city:\s*['\"]?([^'\"]+)['\"]?", content)
        tc_match = re.search(r"tc_target:\s*['\"]?([^'\"]+)['\"]?", content)
        currency_match = re.search(r"currency:\s*['\"]?([^'\"]+)['\"]?", content)
        
        # Extract lists
        role_levels = re.findall(r"role_levels:\s*\n((?:\s*-\s*\w+\n*)+)", content)
        levels = []
        if role_levels:
            levels = [x.strip().replace("-", "").strip() for x in role_levels[0].strip().split("\n")]
            
        role_keywords = re.findall(r"role_keywords:\s*\n((?:\s*-\s*[^\n]+\n*)+)", content)
        keywords = []
        if role_keywords:
            keywords = [x.strip().replace("-", "").strip().strip('"').strip("'") for x in role_keywords[0].strip().split("\n")]
            
        return {
            "target": {
                "city": city_match.group(1) if city_match else "San Francisco",
                "tc_target": tc_match.group(1) if tc_match else "$200K USD",
                "currency": currency_match.group(1) if currency_match else "USD",
                "role_levels": levels if levels else ["Senior", "Staff"],
                "role_keywords": keywords if keywords else ["Software Engineer", "SWE"]
            }
        }
    except Exception as e:
        print(f"Warning parsing config: {e}. Using defaults.")
        return {
            "target": {
                "city": "San Francisco",
                "tc_target": "$200K USD",
                "currency": "USD",
                "role_levels": ["Senior", "Staff"],
                "role_keywords": ["Software Engineer", "SWE"]
            }
        }

def load_seed():
    seed_path = os.path.expanduser("~/.job-search/companies_seed.json")
    if not os.path.exists(seed_path):
        # Fallback to local workspace copy during dev
        seed_path = os.path.join(os.path.dirname(__file__), "../templates/companies_seed.json")
        
    if not os.path.exists(seed_path):
        return []
        
    with open(seed_path, "r") as f:
        return json.load(f)

def filter_seed_companies(seed, city):
    print(f"Filtering seed database for companies in '{city}' or 'Remote'...")
    filtered = []
    for company in seed:
        locations = [l.lower() for l in company.get("locations", [])]
        if city.lower() in locations or "remote" in locations:
            filtered.append({
                "name": company["name"],
                "careers_url": company["careers_url"],
                "api": company["api"],
                "api_slug": company["api_slug"],
                "tc_range": "Varies",
                "tier": 2,
                "notes": f"Discovered from seed list for {city}"
            })
    return filtered

def search_live_boards(city, keywords):
    print("Performing live DuckDuckGo harvest search for new companies...")
    discovered = []
    
    # We query for Greenhouse and Lever boards
    search_term = f'site:boards.greenhouse.io OR site:lever.co "software engineer" "{city}" 2026'
    query = urllib.parse.quote(search_term)
    url = f"https://html.duckduckgo.com/html/?q={query}"
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # Parse greenhouse slugs
        greenhouse_matches = re.findall(r'boards\.greenhouse\.io/([^/?\'"\s>]+)', html)
        for slug in greenhouse_matches:
            if slug not in ["embed", "v1", "search"] and not slug.startswith("http"):
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
            if slug not in ["apply", "jobs"] and not slug.startswith("http"):
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
        print(f"Warning: Live board scraping failed ({e}). Relying on seed database.")
        
    return discovered

def write_yaml_companies(companies, output_path):
    # Formats the company list into companies.yml
    with open(output_path, "w") as f:
        f.write("# ~/.job-search/companies.yml\n")
        f.write("# Generated automatically by /job discover\n\n")
        f.write("companies:\n")
        
        for c in companies:
            f.write(f"  - name: \"{c['name']}\"\n")
            f.write(f"    careers_url: \"{c['careers_url']}\"\n")
            if c['api'] and c['api'] != "null":
                f.write(f"    api: {c['api']}\n")
                f.write(f"    api_slug: \"{c['api_slug']}\"\n")
            else:
                f.write(f"    api: null\n")
            f.write(f"    tc_range: \"{c['tc_range']}\"\n")
            f.write(f"    tier: {c['tier']}\n")
            f.write(f"    notes: \"{c['notes']}\"\n\n")

def main():
    config_path = os.path.expanduser("~/.job-search/config.yml")
    output_path = os.path.expanduser("~/.job-search/companies.yml")
    
    config = load_yaml(config_path)
    city = config.get("target", {}).get("city", "San Francisco")
    keywords = config.get("target", {}).get("role_keywords", ["Software Engineer"])
    
    # 1. Load seed
    seed = load_seed()
    filtered_seed = filter_seed_companies(seed, city)
    
    # 2. Live search
    live_discovered = search_live_boards(city, keywords)
    
    # 3. Merge lists
    seen_slugs = set()
    merged = []
    
    # Add seed companies first (higher preference)
    for c in filtered_seed:
        slug = f"{c['api']}:{c['api_slug']}"
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            merged.append(c)
            
    # Add new live discovered companies
    for c in live_discovered:
        slug = f"{c['api']}:{c['api_slug']}"
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            merged.append(c)
            
    print(f"\n✓ Found {len(merged)} target companies (matching location '{city}'):")
    for c in merged:
        print(f"  • {c['name']} (API: {c['api'] or 'scrape'}, slug: {c['api_slug'] or 'N/A'}, tier: {c['tier']})")
        
    write_yaml_companies(merged, output_path)
    print(f"\n✓ Saved updated list to {output_path}")

if __name__ == "__main__":
    main()
