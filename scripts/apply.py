#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess

def install_and_import_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        print("Playwright not found. Installing playwright and chromium browser...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            from playwright.sync_api import sync_playwright
            return sync_playwright
        except Exception as e:
            print(f"Error installing Playwright: {e}")
            print("Please run: pip install playwright && playwright install chromium")
            sys.exit(1)

def load_profile():
    profile_path = os.path.expanduser("~/.job-search/profile.json")
    if not os.path.exists(profile_path):
        print(f"Error: Profile not found at {profile_path}")
        print("Please run '/job build' first to create your profile.")
        sys.exit(1)
    
    with open(profile_path, "r") as f:
        return json.load(f)

def fill_form(page, profile, resume_path):
    print("Analyzing form fields...")
    
    # Split name
    fullname = profile.get("name", "")
    names = fullname.split()
    firstname = names[0] if names else ""
    lastname = " ".join(names[1:]) if len(names) > 1 else ""

    # Common profile values
    email = profile.get("email", "")
    phone = profile.get("phone", "")
    location = profile.get("location", "")
    linkedin = profile.get("linkedin", "")
    
    # Look for github and portfolio in other social profiles
    github = ""
    portfolio = ""
    # In case there are custom links in profile, we check them:
    for skill_cat, items in profile.get("skills", {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if "github.com" in item.lower():
                github = item
            elif "portfolio" in item.lower() or "website" in item.lower():
                portfolio = item
    
    # Handle forms
    # 1. First search for file inputs for resume
    file_inputs = page.query_selector_all("input[type='file']")
    resume_uploaded = False
    
    if file_inputs and resume_path and os.path.exists(resume_path):
        for file_input in file_inputs:
            # Check if this file input is for resume/cv
            name_attr = file_input.get_attribute("name") or ""
            id_attr = file_input.get_attribute("id") or ""
            accept_attr = file_input.get_attribute("accept") or ""
            
            # Find associated labels or text
            parent_text = ""
            try:
                parent = file_input.evaluate_handle("el => el.parentElement")
                parent_text = parent.evaluate("el => el.innerText") or ""
            except:
                pass
                
            is_resume = any(k in (name_attr + id_attr + accept_attr + parent_text).lower() 
                            for k in ["resume", "cv", "attachment", "file", "upload"])
            
            if is_resume or len(file_inputs) == 1:
                print(f"Uploading resume: {os.path.basename(resume_path)}")
                try:
                    file_input.set_input_files(resume_path)
                    resume_uploaded = True
                    # Let UI process file upload
                    time.sleep(2)
                    break
                except Exception as e:
                    print(f"Warning: Failed to upload resume via selector: {e}")

    # 2. Fill text inputs
    inputs = page.query_selector_all("input:not([type='hidden']):not([type='submit']):not([type='file']), textarea")
    
    for element in inputs:
        # Skip if not visible or disabled
        if not element.is_visible() or not element.is_enabled():
            continue
            
        id_attr = (element.get_attribute("id") or "").lower()
        name_attr = (element.get_attribute("name") or "").lower()
        placeholder = (element.get_attribute("placeholder") or "").lower()
        aria_label = (element.get_attribute("aria-label") or "").lower()
        
        # Get label text if associated
        label_text = ""
        if id_attr:
            label = page.query_selector(f"label[for='{id_attr}']")
            if label:
                label_text = (label.inner_text() or "").lower()
                
        # Fallback to parent text if no label found
        if not label_text:
            try:
                parent = element.evaluate_handle("el => el.parentElement")
                label_text = (parent.evaluate("el => el.innerText") or "").lower()
            except:
                pass

        combined_context = f"{id_attr} {name_attr} {placeholder} {aria_label} {label_text}"
        
        # Determine value to fill based on heuristics
        value_to_fill = None
        
        # First Name
        if "first name" in combined_context or "firstname" in combined_context or "given name" in combined_context:
            value_to_fill = firstname
        # Last Name
        elif "last name" in combined_context or "lastname" in combined_context or "family name" in combined_context or "surname" in combined_context:
            value_to_fill = lastname
        # Full Name (only if we haven't already filled first/last name, or it's a single Name field)
        elif "full name" in combined_context or "name" in combined_context:
            # Check if there are separate first/last name fields on page
            has_first_name_field = any("first name" in (i.get_attribute("name") or "").lower() or "first name" in (page.query_selector(f"label[for='{i.get_attribute('id')}']").inner_text() if i.get_attribute("id") and page.query_selector(f"label[for='{i.get_attribute('id')}']") else "").lower() for i in inputs)
            if not has_first_name_field:
                value_to_fill = fullname
        # Email
        elif "email" in combined_context:
            value_to_fill = email
        # Phone
        elif "phone" in combined_context or "mobile" in combined_context or "tel" in combined_context or "contact number" in combined_context:
            value_to_fill = phone
        # LinkedIn
        elif "linkedin" in combined_context:
            value_to_fill = linkedin
        # GitHub
        elif "github" in combined_context:
            value_to_fill = github if github else profile.get("linkedin", "").replace("linkedin.com/in/", "github.com/") # fallback guestimate
        # Portfolio / Website / Link
        elif "portfolio" in combined_context or "website" in combined_context or "personal link" in combined_context or "url" in combined_context:
            value_to_fill = portfolio if portfolio else profile.get("linkedin", "")
        # Location / City
        elif "location" in combined_context or "city" in combined_context or "address" in combined_context:
            value_to_fill = location

        # Fill the element if we matched a value
        if value_to_fill:
            current_val = element.evaluate("el => el.value")
            if not current_val: # Only fill if empty to avoid overwriting existing data
                try:
                    element.focus()
                    element.fill(value_to_fill)
                    print(f"  Filled field: {name_attr or id_attr or placeholder} -> {value_to_fill}")
                except Exception as e:
                    pass

    print("\n✓ Auto-fill complete!")
    if resume_uploaded:
        print("✓ Resume uploaded.")
    else:
        print("⚠ Resume upload not automated. Please upload your resume PDF manually.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 apply.py <job-post-url> [resume-pdf-path]")
        sys.exit(1)
        
    url = sys.argv[1]
    resume_path = sys.argv[2] if len(sys.argv) > 2 else ""
    
    sync_playwright = install_and_import_playwright()
    profile = load_profile()
    
    print(f"Opening browser to navigate to: {url}")
    
    with sync_playwright() as p:
        # Launch non-headless browser so the user can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(url)
            # Wait for SPA load
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as e:
            print(f"Initial page load warning: {e}. Attempting to proceed...")
            
        # Give it a couple of seconds to settle
        time.sleep(3)
        
        # Fill the form
        fill_form(page, profile, resume_path)
        
        print("\n" + "="*70)
        print("  THE BROWSER IS NOW OPEN FOR YOU TO COMPLETE THE APPLICATION.")
        print("  Please review the filled fields, answer custom employer questions,")
        print("  complete any CAPTCHAs, and click Submit manually when ready.")
        print("="*70)
        print("  Press Ctrl+C in the terminal to close the browser when finished.\n")
        
        # Keep browser open until user terminates script
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing browser...")

if __name__ == "__main__":
    main()
