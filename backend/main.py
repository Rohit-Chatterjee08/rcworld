from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-resume")
async def upload_resume(resume: UploadFile = File(...)):
    content = await resume.read()
    return {"message": f"Received {resume.filename}", "size": len(content)}

class Job(BaseModel):
    job_title: str

@app.post("/generate-cover-letter")
def generate_cover_letter(job: Job):
    return {"cover_letter": f"Dear Hiring Manager, I am excited to apply for the {job.job_title} role... (AI generated)"}
