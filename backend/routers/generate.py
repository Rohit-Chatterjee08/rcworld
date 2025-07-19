from fastapi import APIRouter, Request
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("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")

router = APIRouter(prefix="/generate", tags=["AI"])

@router.post("/coverletter")
async def generate_cover_letter(request: Request):
    body = await request.json()
    job_title = body.get("job_title")
    user_intro = body.get("user_intro", "I am a skilled automation specialist...")

    client = OpenAI(api_key=openai_api_key)
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional career assistant."},
            {"role": "user", "content": f"Write a cover letter for the role: {job_title}. My background: {user_intro}"}
        ]
    )
    return {"cover_letter": completion.choices[0].message.content}
