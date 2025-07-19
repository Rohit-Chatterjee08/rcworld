# 📁 backend/automation/remoteok.py
import requests

def get_remoteok_jobs():
    jobs = []
    try:
        response = requests.get("https://remoteok.com/api", headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        for job in data[1:11]:  # Skip the first item (metadata)
            jobs.append({
                "title": job.get("position") or job.get("title", "No Title"),
                "company": job.get("company", "Unknown Company"),
                "url": f"https://remoteok.com{job.get('url', '')}"
            })
    except Exception as e:
        jobs.append({
            "title": "RemoteOK Error",
            "company": "RemoteOK",
            "url": str(e)
        })

    return jobs
