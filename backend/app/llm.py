import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from .keywords import extract_job_keywords, match_keywords
from .text_utils import normalize_text


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

# Load environment variables no matter whether uvicorn is started from
# D:\Smart-ATS or D:\Smart-ATS\backend.
load_dotenv(PROJECT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None


def _message_content(messages: list[dict], role: str) -> str:
    for message in reversed(messages):
        if message.get("role") == role:
            return message.get("content", "") or ""
    return ""


def _extract_context(messages: list[dict]) -> tuple[str, str]:
    resume_text = ""
    jd_text = ""

    for message in messages:
        if message.get("role") != "system":
            continue

        content = message.get("content", "") or ""
        if "Resume excerpt:" in content and "Job description excerpt:" in content:
            resume_part = content.split("Resume excerpt:", 1)[1]
            if "Job description excerpt:" in resume_part:
                resume_text, jd_part = resume_part.split("Job description excerpt:", 1)
                resume_text = resume_text.strip()
                jd_text = jd_part.strip()
            break

    return resume_text, jd_text


def _top_terms(text: str, limit: int = 5) -> list[str]:
    extracted = extract_job_keywords(text)
    if extracted.all_keywords:
        return extracted.all_keywords[:limit]

    words = [word for word in normalize_text(text).split() if len(word) > 3]
    counts = Counter(words)
    return [word for word, _ in counts.most_common(limit)]


def _local_chat_reply(messages: list[dict]) -> str:
    user_message = _message_content(messages, "user")
    resume_text, jd_text = _extract_context(messages)
    lower_message = normalize_text(user_message)
    resume_terms = _top_terms(resume_text, 4)
    jd_terms = _top_terms(jd_text, 4)
    matched_skills, missing_skills = match_keywords(resume_text, jd_terms) if jd_terms else ([], [])

    if any(word in lower_message for word in ["ats", "score", "analysis"]):
        return (
            "I cannot calculate a live ATS score here, but I can still help you improve it.\n"
            f"- Strengthen these matching terms: {', '.join(matched_skills[:4]) or 'the core JD keywords'}\n"
            f"- Add these missing terms truthfully: {', '.join(missing_skills[:4]) or 'role-specific skills from the job description'}\n"
            "- Quantify impact with numbers, scale, and outcomes in your top bullets."
        )

    if any(word in lower_message for word in ["resume", "cv", "profile", "tailor", "improve"]):
        return (
            "Here is the fastest improvement path:\n"
            f"- Emphasize: {', '.join(resume_terms[:3]) or 'your strongest relevant experience'}\n"
            f"- Mirror the JD language: {', '.join(jd_terms[:3]) or 'the main job requirements'}\n"
            "- Rewrite bullets with action + tool + result, then keep only the claims you can defend in an interview."
        )

    if any(word in lower_message for word in ["interview", "answer", "question", "mock"]):
        focus = jd_terms[:2] or resume_terms[:2]
        return (
            "Use a concise STAR answer: situation, task, action, result.\n"
            f"- Anchor your example around: {', '.join(focus) or 'a recent high-impact project'}\n"
            "- State the tool or method you used, what you changed, and the measurable outcome.\n"
            "- Finish with one lesson learned and how you would apply it again."
        )

    if resume_terms or jd_terms:
        return (
            "I can help with that. Based on your resume and job description, the strongest directions are:\n"
            f"- Highlight: {', '.join(resume_terms[:3]) or 'your most relevant experience'}\n"
            f"- Align to: {', '.join(jd_terms[:3]) or 'the target role language'}\n"
            "- If you want, paste one bullet or one interview answer and I will tighten it."
        )

    return (
        "I can help with resume, ATS, and interview coaching. Paste your resume, a job description, or a specific question, and I will answer directly."
    )


def _local_mock_question(resume_text: str, jd_text: str) -> str:
    jd_terms = _top_terms(jd_text, 4)
    resume_terms = _top_terms(resume_text, 4)
    focus = jd_terms[0] if jd_terms else (resume_terms[0] if resume_terms else "your recent work")

    if jd_terms:
        return f"Tell me about a project where you used {focus} and how you measured the outcome."
    if resume_terms:
        return f"Walk me through a project from your resume that best demonstrates {focus}."
    return "Describe a challenging project you delivered, what you changed, and the result."


def _local_mock_feedback(question: str, answer: str, resume_text: str | None = None, jd_text: str | None = None) -> str:
    answer_words = normalize_text(answer).split()
    question_terms = _top_terms(question, 3)
    resume_terms = _top_terms(resume_text or "", 3)
    jd_terms = _top_terms(jd_text or "", 3)
    matched_terms = [term for term in question_terms + jd_terms if term in normalize_text(answer)]

    strengths = ["You answered the question directly."]
    if len(answer_words) > 50:
        strengths.append("You gave enough detail to show context and reasoning.")
    if matched_terms:
        strengths.append(f"You referenced relevant topics such as {', '.join(matched_terms[:3])}.")

    weaknesses = []
    if len(answer_words) < 45:
        weaknesses.append("Add more detail about the action you took and the result.")
    if not any(char.isdigit() for char in answer):
        weaknesses.append("Include a measurable result, scale, or outcome if that is truthful.")
    if not matched_terms and (resume_terms or jd_terms):
        weaknesses.append(f"Tie the answer more clearly to {', '.join((jd_terms or resume_terms)[:3])}.")

    if not weaknesses:
        weaknesses.append("Tighten the delivery so the answer stays focused and interview-ready.")

    structure = (
        "Situation, task, action, result. End with one sentence on what you learned or would do differently."
    )
    tip = (
        f"Practice this answer again and anchor it on {', '.join((jd_terms or resume_terms)[:2]) or 'one concrete project example'}."
    )

    return (
        "Strengths: " + " ".join(strengths) + "\n"
        "Weaknesses: " + " ".join(weaknesses) + "\n"
        f"Better structure: {structure}\n"
        f"Preparation tip: {tip}"
    )


def _call_or_fallback(messages: list[dict], fallback: str, max_tokens: int = 500) -> str:
    return groq_chat(messages, max_tokens=max_tokens) or fallback


def groq_chat(messages: list[dict], max_tokens: int = 500) -> str | None:
    if _client is None:
        return None

    try:
        response = _client.chat.completions.create(
            messages=messages,
            model=GROQ_MODEL,
            temperature=0,
            top_p=1,
            seed=42,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as exc:
        print("GROQ ERROR:", exc)
        return None


def is_groq_configured() -> bool:
    return _client is not None


def explain_analysis(analysis: dict) -> str:
    prompt = f"""
You are an ATS assistant. The backend has already calculated all scores.
Do not calculate or change any score. Explain the weaknesses and improvements only.

Calculated data:
ATS score: {analysis["ats_score"]}
Keyword score: {analysis["keyword_score"]}
Similarity score: {analysis["similarity_score"]}
Matched skills: {", ".join(analysis["matched_skills"][:25]) or "none"}
Missing skills: {", ".join(analysis["missing_skills"][:25]) or "none"}
Component scores: {analysis["component_scores"]}

Return 4 concise bullets:
- one overall interpretation
- one keyword weakness
- one resume improvement
- one interview preparation suggestion
"""
    return _call_or_fallback(
        [
            {"role": "system", "content": "You explain deterministic ATS results. Never compute scores."},
            {"role": "user", "content": prompt},
        ],
        "\n".join(f"- {item}" for item in analysis["suggestions"]),
        max_tokens=350,
    )


def generate_improvements(resume_text: str, jd_text: str, analysis: dict | None = None) -> str:
    score_line = f"ATS score: {analysis['ats_score']}" if analysis else "ATS score: not provided"
    missing = ", ".join((analysis or {}).get("missing_skills", [])[:20]) or "Use the JD context."
    prompt = f"""
You are an ATS resume improvement assistant.
The backend owns scoring. Do not calculate or invent an ATS score.
{score_line}
Missing skills: {missing}

Resume excerpt:
{resume_text[:2500]}

Job description excerpt:
{jd_text[:2500]}

Give specific rewrite guidance in 5 bullets.
"""
    return _call_or_fallback(
        [
            {"role": "system", "content": "Provide practical resume edits. Do not score."},
            {"role": "user", "content": prompt},
        ],
        "Add missing skills where truthful, quantify impact, and tailor project bullets to the job description.",
        max_tokens=500,
    )


def generate_mock_question(resume_text: str, jd_text: str) -> str:
    prompt = f"""
Generate exactly ONE mock interview question for this candidate and job.

Rules:
- Ask one clear interview question only.
- Prefer frontend, technical, project, behavioral, or role-fit topics from the JD.
- Do not include intro text, numbering, quotation marks, or explanation.

Resume excerpt:
{resume_text[:2500]}

Job description excerpt:
{jd_text[:2500]}
"""
    return _call_or_fallback(
        [
            {"role": "system", "content": "You are a senior technical interviewer. Return only one interview question."},
            {"role": "user", "content": prompt},
        ],
        _local_mock_question(resume_text, jd_text),
        max_tokens=180,
    )


def evaluate_mock_answer(question: str, answer: str, resume_text: str | None = None, jd_text: str | None = None) -> str:
    prompt = f"""
Evaluate the candidate's answer to this mock interview question.

Question:
{question}

Candidate answer:
{answer}

Resume context:
{(resume_text or "")[:1600]}

Job description context:
{(jd_text or "")[:1600]}

Return concise feedback with:
- Strengths
- Weaknesses
- A better answer structure
- One follow-up preparation tip
"""
    return _call_or_fallback(
        [
            {"role": "system", "content": "You are an honest interview coach. Be specific, fair, and practical."},
            {"role": "user", "content": prompt},
        ],
        _local_mock_feedback(question, answer, resume_text, jd_text),
        max_tokens=450,
    )


def generate_chat_reply(messages: list[dict], max_tokens: int = 450) -> str:
    resume_text, jd_text = _extract_context(messages)
    fallback = _local_chat_reply(messages)
    if _client is None:
        return fallback

    reply = groq_chat(messages, max_tokens=max_tokens)
    if reply:
        return reply

    if resume_text or jd_text:
        return fallback

    return "SageAI is not connected right now, but you can still paste a resume, job description, or question and I will help."
