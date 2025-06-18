# lc/job_processor.py

import os
import json
from datetime import date
import time
import pandas as pd
import requests
from jobspy import scrape_jobs
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup

# (All other imports and scraper functions remain the same)
# ...
from api.routes.utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    get_resume_path,
    ANALYSIS_FILE,
    CACHE_DIR
)
from .job_tools import score_job_match


def scrape_with_jobspy(search_query: str):
    print(f"🔎 Scraping Indeed & Glassdoor with query: '{search_query}' using jobspy...")
    all_jobs = []
    try:
        jobs_df: pd.DataFrame = scrape_jobs(
            site_name=["indeed", "glassdoor"],
            search_term=search_query,
            location="United States",
            results_wanted=20,
            country_indeed='USA'
        )
        if not jobs_df.empty:
            for index, row in jobs_df.iterrows():
                all_jobs.append({
                    "site": row.get('site'), "title": row.get('title'), "company": row.get('company'),
                    "location": row.get('location'), "url": row.get('job_url'), "description": row.get('description')
                })
        print(f"✅ Scraped {len(all_jobs)} jobs via jobspy.")
        return all_jobs
    except Exception as e:
        print(f"❌ An error occurred during jobspy scraping: {e}")
        return []

def scrape_remotive(search_query: str):
    print(f"🔎 Scraping Remotive with query: '{search_query}' using its free API...")
    url = f"https://remotive.com/api/remote-jobs?search={search_query.replace(' ', '+')}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()
        jobs = [
            {"site": "remotive", "title": j.get('title'), "company": j.get('company_name'), "location": j.get('candidate_required_location', 'Remote'), "url": j.get('url'), "description": j.get('description')}
            for j in data.get('jobs', [])[:20]
        ]
        print(f"✅ Scraped {len(jobs)} jobs from Remotive.")
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not scrape Remotive: {e}")
        return []

def scrape_linkedin_with_playwright(search_query: str):
    print(f"🔎 Scraping LinkedIn with query: '{search_query}' using Playwright Stealth...")
    scraped_jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        stealth_sync(page)
        try:
            url = f"https://www.linkedin.com/jobs/search?keywords={'+'.join(search_query.split())}&location=United+States&f_TPR=r86400"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector('ul.jobs-search__results-list', timeout=15000)
            for _ in range(2):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(1.5)
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            job_cards = soup.find_all('div', class_='base-search-card')
            for card in job_cards[:20]:
                title = card.find('h3', class_='base-search-card__title').get_text(strip=True) if card.find('h3', class_='base-search-card__title') else 'N/A'
                company = card.find('h4', class_='base-search-card__subtitle').get_text(strip=True) if card.find('h4', class_='base-search-card__subtitle') else 'N/A'
                location = card.find('span', class_='job-search-card__location').get_text(strip=True) if card.find('span', class_='job-search-card__location') else 'N/A'
                job_url = card.find('a', class_='base-card__full-link')['href'] if card.find('a', class_='base-card__full-link') else 'N/A'
                scraped_jobs.append({"site": "linkedin", "title": title, "company": company, "location": location, "url": job_url, "description": ""})
        except Exception as e:
            print(f"An error occurred during LinkedIn scraping: {e}")
        finally:
            browser.close()
    print(f"✅ Scraped {len(scraped_jobs)} jobs from LinkedIn.")
    return scraped_jobs

def scrape_ziprecruiter_with_playwright(search_query: str):
    print(f"🔎 Scraping ZipRecruiter with query: '{search_query}' using Playwright...")
    scraped_jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        stealth_sync(page)
        try:
            url = f"https://www.ziprecruiter.com/jobs-search?search={search_query.replace(' ', '+')}&location=United+States&days=1"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            job_list_selector = "div.job_results_list"
            page.wait_for_selector(job_list_selector, timeout=20000)
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            job_cards = soup.select(f'{job_list_selector} article.job_result')
            for card in job_cards[:20]:
                title_element = card.select_one('h2.job_title > a')
                company_element = card.select_one('a.company_name')
                location_element = card.select_one('a.company_location')
                title = title_element.get_text(strip=True) if title_element else 'N/A'
                job_url = title_element['href'] if title_element else 'N/A'
                company = company_element.get_text(strip=True) if company_element else 'N/A'
                location = location_element.get_text(strip=True) if location_element else 'N/A'
                description = card.find('p', class_='job_snippet').get_text(strip=True) if card.find('p', class_='job_snippet') else ''
                scraped_jobs.append({"site": "ziprecruiter", "title": title, "company": company, "location": location, "url": job_url, "description": description})
        except Exception as e:
            print(f"❌ An error occurred during ZipRecruiter scraping: {e}")
            page.screenshot(path="ziprecruiter_error_screenshot.png")
            print("📸 Screenshot saved to ziprecruiter_error_screenshot.png")
        finally:
            browser.close()
    print(f"✅ Scraped {len(scraped_jobs)} jobs from ZipRecruiter.")
    return scraped_jobs


def process_and_cache_jobs():
    print("🚀 Starting new job processing and caching session with multi-platform strategy...")
    if not os.path.exists(ANALYSIS_FILE):
        print("🔴 Job processing stopped: Resume analysis file not found.")
        return

    with open(ANALYSIS_FILE, 'r') as f: analysis = json.load(f)
    target_roles = analysis.get("suggested_roles")
    if not target_roles: return

    resume_path = get_resume_path()
    if not resume_path: return

    with open(resume_path, "rb") as f: resume_contents = f.read()
    resume_text = extract_text_from_pdf(resume_contents) if resume_path.endswith(".pdf") else extract_text_from_docx(resume_contents)

    all_scraped_jobs = []
    # --- FIX: Use a set to track processed URLs to avoid duplicates ---
    seen_urls = set()
    
    print(f"🎯 Targeting all {len(target_roles)} roles: {target_roles}")
    
    # --- FIX: Loop through each suggested role ---
    for role in target_roles:
        search_query = f'"{role}"'
        print(f"\n--- Now searching for role: {search_query} ---")
        
        # Create a temporary list for this role's scraped jobs
        current_scrapes = []
        current_scrapes.extend(scrape_with_jobspy(search_query))
        current_scrapes.extend(scrape_ziprecruiter_with_playwright(search_query))
        current_scrapes.extend(scrape_remotive(search_query))
        current_scrapes.extend(scrape_linkedin_with_playwright(search_query))

        # --- FIX: Add new unique jobs to the main list ---
        new_jobs_found = 0
        for job in current_scrapes:
            job_url = job.get('url')
            # Check for URL and ensure it hasn't been seen before
            if job_url and job_url not in seen_urls:
                all_scraped_jobs.append(job)
                seen_urls.add(job_url)
                new_jobs_found += 1
        
        if new_jobs_found > 0:
            print(f"Found {new_jobs_found} new unique jobs for role '{role}'.")

    # --- The rest of the scoring logic remains the same ---
    print(f"\nFound {len(all_scraped_jobs)} total unique jobs to score across all platforms.")
    all_scored_jobs = []
    for i, job in enumerate(all_scraped_jobs):
        job_description = job.get('description') or job.get('title')
        if pd.isna(job_description) or not job_description:
            print(f"Skipping job {i+1} due to missing description: {job.get('title')}")
            continue
        
        print(f"\n🤖 Scoring Job {i+1}/{len(all_scraped_jobs)}: {job.get('title')} from {job.get('site').upper()}")
        
        score_result = score_job_match.invoke(input={
            "resume_text": resume_text,
            "job_description_text": str(job_description)
        })
        
        if score_result:
            all_scored_jobs.append({
                "title": job.get('title'), "company": job.get('company'), "location": job.get('location'),
                "url": job.get('url'), "description": str(job_description), "match_score": score_result.match_score,
                "match_reason": score_result.reason, "id": f"{job.get('site')}-{i}"
            })
        time.sleep(1)

    sorted_jobs = sorted(all_scored_jobs, key=lambda j: j.get('match_score', 0), reverse=True)
    top_20_jobs = sorted_jobs[:20]
    today_str = date.today().isoformat()
    cache_file = os.path.join(CACHE_DIR, f"todays_jobs_{today_str}.json")
    with open(cache_file, 'w') as f: json.dump(top_20_jobs, f, indent=2)
    print(f"\n✅ Job processing complete. Saved top {len(top_20_jobs)} matched jobs to cache for {today_str}.")