from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import JobApplication
router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/")
def get_jobs():
    return {"jobs": ["Example job 1", "Example job 2"]}
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/track")
def track_job(job_title: str, company: str, portal: str, db: Session = Depends(get_db)):
    job = JobApplication(
        job_title=job_title,
        company=company,
        portal=portal,
        status="Applied"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"message": "Job tracked", "job": job.id}    
