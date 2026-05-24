import os

from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .llm import (
    evaluate_mock_answer,
    explain_analysis,
    generate_improvements,
    generate_mock_question,
    generate_chat_reply,
    is_groq_configured,
)
from .scoring import analyze_resume
from .schemas import (
    AnalyzeRequest,
    ChatRequest,
    ImproveRequest,
    MockFeedbackRequest,
    MockQuestionRequest,
    SkillGapRequest,
)
from .text_utils import extract_text_from_pdf, normalize_text


app = FastAPI(title="Smart ATS Resume Analyzer", version="2.0.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


def _validate_text_inputs(resume_text: str, jd_text: str) -> tuple[str, str]:
    resume = normalize_text(resume_text)
    jd = normalize_text(jd_text)
    if len(resume.split()) < 20:
        raise HTTPException(status_code=400, detail="Resume text is too short for analysis")
    if len(jd.split()) < 10:
        raise HTTPException(status_code=400, detail="Job description is too short for analysis")
    return resume, jd


@router.get("/")
def root():
    return {
        "status": "Backend running",
        "scoring": "deterministic-hybrid",
        "groq_configured": is_groq_configured(),
    }


@router.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    text = extract_text_from_pdf(file)
    return {"text": text, "normalized_text": normalize_text(text)}


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    resume, jd = _validate_text_inputs(request.resume_text, request.jd_text)
    analysis = analyze_resume(resume, jd)
    analysis["suggestions"] = analysis["suggestions"]
    analysis["explanation"] = explain_analysis(analysis)
    return analysis


@router.post("/improve")
async def improve(request: ImproveRequest):
    resume, jd = _validate_text_inputs(request.resume_text, request.jd_text)
    analysis = analyze_resume(resume, jd)
    return {
        "ats_score": analysis["ats_score"],
        "improvements": generate_improvements(resume, jd, analysis),
        "missing_skills": analysis["missing_skills"],
    }


@router.post("/skill-gap")
async def skill_gap(request: SkillGapRequest):
    resume, jd = _validate_text_inputs(request.resume_text, request.jd_text)
    analysis = analyze_resume(resume, jd)
    return {
        "matched_skills": analysis["matched_skills"],
        "missing_skills": analysis["missing_skills"],
        "job_keywords": analysis["job_keywords"],
        "keyword_score": analysis["keyword_score"],
    }


@router.post("/mock-question")
async def mock_question(request: MockQuestionRequest):
    resume, jd = _validate_text_inputs(request.resume_text, request.jd_text)
    return {"question": generate_mock_question(resume, jd)}


@router.post("/mock-feedback")
async def mock_feedback(request: MockFeedbackRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    if not request.answer.strip():
        raise HTTPException(status_code=400, detail="Answer is required")

    return {
        "feedback": evaluate_mock_answer(
            request.question.strip(),
            request.answer.strip(),
            normalize_text(request.resume_text or ""),
            normalize_text(request.jd_text or ""),
        )
    }


@router.post("/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        return {"reply": "Please ask something."}

    system_prompt = """
You are SageAI, an AI resume assistant.
Rules:
- The backend calculates ATS scores; never calculate or estimate an ATS score.
- Explain, coach, and suggest improvements only.
- Keep answers concise and practical.
"""
    messages = [{"role": "system", "content": system_prompt}]

    if request.resume_text and request.jd_text:
        messages.append(
            {
                "role": "system",
                "content": f"""
Resume excerpt:
{normalize_text(request.resume_text)[:1200]}

Job description excerpt:
{normalize_text(request.jd_text)[:1200]}
""",
            }
        )

    for message in request.chat_history[-8:]:
        if message.role in {"user", "assistant"}:
            messages.append({"role": message.role, "content": message.content})

    messages.append({"role": "user", "content": request.message})
    reply = generate_chat_reply(messages, max_tokens=450)
    return {
        "reply": reply
        or "SageAI is not connected to Groq right now. Check GROQ_API_KEY in your .env file and restart the backend."
    }


app.include_router(router)
app.include_router(router, prefix="/api")
