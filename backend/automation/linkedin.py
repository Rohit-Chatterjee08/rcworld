# 📁 backend/automation/linkedin.py
import requests
from bs4 import BeautifulSoup

def get_linkedin_jobs():
    jobs = []
    try:
        res = requests.get(
            "https://www.linkedin.com/jobs/search/?keywords=remote",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(".base-card")[:10]

        for job in listings:
            title = job.select_one("h3.base-search-card__title")
            company = job.select_one("h4.base-search-card__subtitle")
            url_tag = job.select_one("a.base-card__full-link")
            jobs.append({
                "title": title.text.strip() if title else "Unknown Title",
                "company": company.text.strip() if company else "Unknown Company",
                "url": url_tag["href"].split("?")[0] if url_tag else "#"
            })
    except Exception as e:
        jobs.append({
            "title": "LinkedIn Error",
            "company": "LinkedIn",
            "url": str(e)
        })
    return jobs
