# 📁 backend/automation/naukri.py
import requests
from bs4 import BeautifulSoup

def get_naukri_jobs():
    jobs = []
    try:
        url = "https://www.naukri.com/remote-jobs"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        listings = soup.select("article.jobTuple")[:10]
        for listing in listings:
            title = listing.select_one("a.title").text.strip()
            company = listing.select_one("a.subTitle").text.strip()
            job_url = listing.select_one("a.title")["href"]
            jobs.append({
                "title": title,
                "company": company,
                "url": job_url
            })
    except Exception as e:
        jobs.append({
            "title": "Naukri Error",
            "company": "Naukri",
            "url": str(e)
        })

    return jobs
