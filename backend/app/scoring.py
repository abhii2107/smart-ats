from .keywords import (
    extract_degree_terms,
    extract_job_keywords,
    extract_required_years,
    extract_resume_years,
    match_keywords,
)
from .similarity import semantic_similarity_percent
from .text_utils import section_text, unique_sorted


WEIGHTS = {
    "skills": 0.40,
    "experience": 0.30,
    "projects": 0.20,
    "education": 0.10,
}


def _ratio_score(matched_count: int, total_count: int) -> float:
    if total_count == 0:
        return 100.0
    return round((matched_count / total_count) * 100, 2)


def _experience_score(resume_text: str, jd_text: str, matched_skills: list[str], total_skills: int) -> float:
    required_years = extract_required_years(jd_text)
    resume_years = extract_resume_years(resume_text)
    year_score = 100.0 if required_years == 0 else min(resume_years / required_years, 1.0) * 100
    relevance_score = _ratio_score(len(matched_skills), total_skills)
    return round((year_score * 0.70) + (relevance_score * 0.30), 2)


def _projects_score(resume_text: str, job_keywords: list[str]) -> float:
    projects = section_text(resume_text, ["projects", "project"])
    if not projects:
        return 0.0 if job_keywords else 100.0
    matched, _ = match_keywords(projects, job_keywords)
    return _ratio_score(len(matched), len(job_keywords))


def _education_score(resume_text: str, jd_text: str) -> float:
    required_degrees = extract_degree_terms(jd_text)
    if not required_degrees:
        return 100.0
    resume_degrees = set(extract_degree_terms(resume_text))
    matched = [degree for degree in required_degrees if degree in resume_degrees]
    return _ratio_score(len(matched), len(required_degrees))


def deterministic_suggestions(missing_skills: list[str], component_scores: dict[str, float]) -> list[str]:
    suggestions = []
    if missing_skills:
        suggestions.append("Add evidence for missing JD keywords: " + ", ".join(missing_skills[:8]) + ".")
    if component_scores["experience"] < 70:
        suggestions.append("Quantify relevant experience with years, scale, business impact, and role-specific achievements.")
    if component_scores["projects"] < 70:
        suggestions.append("Add or rewrite projects so they explicitly mention the target stack and measurable outcomes.")
    if component_scores["education"] < 70:
        suggestions.append("Include the required degree, coursework, certifications, or equivalent training if applicable.")
    if not suggestions:
        suggestions.append("Resume is strongly aligned; tighten bullets with measurable impact to improve recruiter readability.")
    return suggestions


def analyze_resume(resume_text: str, jd_text: str) -> dict:
    extracted = extract_job_keywords(jd_text)
    job_keywords = extracted.all_keywords
    matched_skills, missing_skills = match_keywords(resume_text, job_keywords)

    skills_score = _ratio_score(len(matched_skills), len(job_keywords))
    component_scores = {
        "skills": skills_score,
        "experience": _experience_score(resume_text, jd_text, matched_skills, len(job_keywords)),
        "projects": _projects_score(resume_text, job_keywords),
        "education": _education_score(resume_text, jd_text),
    }
    keyword_score = round(
        sum(component_scores[name] * weight for name, weight in WEIGHTS.items()),
        2,
    )
    similarity_score = semantic_similarity_percent(resume_text, jd_text)
    ats_score = round((keyword_score * 0.70) + (similarity_score * 0.30), 2)

    return {
        "ats_score": ats_score,
        "keyword_score": keyword_score,
        "similarity_score": similarity_score,
        "component_scores": component_scores,
        "weights": WEIGHTS,
        "matched_skills": unique_sorted(matched_skills),
        "missing_skills": unique_sorted(missing_skills),
        "job_keywords": {
            "technical_skills": extracted.technical_skills,
            "tools": extracted.tools,
            "frameworks": extracted.frameworks,
            "soft_skills": extracted.soft_skills,
            "all": job_keywords,
        },
        "suggestions": deterministic_suggestions(missing_skills, component_scores),
    }

