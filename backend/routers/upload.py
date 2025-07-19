from fastapi import APIRouter, UploadFile, File
import shutil
import os

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "uploaded_resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_resume(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "Resume uploaded", "filename": file.filename}
