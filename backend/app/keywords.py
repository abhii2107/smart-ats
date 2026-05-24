import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .text_utils import normalize_text, unique_sorted


TECHNICAL_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "ruby", "php", "scala", "kotlin", "swift", "rust", "sql", "nosql",
    "html", "css", "machine learning", "deep learning", "nlp", "computer vision",
    "data analysis", "data engineering", "etl", "rest api", "graphql", "microservices",
    "system design", "oop", "data structures", "algorithms", "linux", "ci/cd",
}

TOOLS = {
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "github", "gitlab",
    "jenkins", "terraform", "ansible", "jira", "postgresql", "postgres", "mysql",
    "mongodb", "redis", "elasticsearch", "kafka", "rabbitmq", "spark", "hadoop",
    "tableau", "power bi", "excel", "figma", "postman", "nginx", "linux",
}

FRAMEWORKS = {
    "react", "vite", "next.js", "nextjs", "node.js", "nodejs", "express",
    "fastapi", "flask", "django", "spring boot", "spring", "angular", "vue",
    "tailwind", "bootstrap", "pandas", "numpy", "scikit-learn", "sklearn",
    "pytorch", "tensorflow", "keras", "langchain", "llamaindex", "pytest",
}

SOFT_SKILLS = {
    "communication", "leadership", "collaboration", "teamwork", "problem solving",
    "analytical thinking", "ownership", "mentoring", "stakeholder management",
    "adaptability", "time management", "critical thinking", "attention to detail",
}

DEGREES = {
    "bachelor", "bachelors", "bs", "b.s", "btech", "b.tech", "master", "masters",
    "ms", "m.s", "mtech", "m.tech", "phd", "mba", "degree", "computer science",
    "engineering", "information technology",
}

ALIASES = {
    "postgres": "postgresql",
    "sklearn": "scikit-learn",
    "nextjs": "next.js",
    "nodejs": "node.js",
    "golang": "go",
    "rest": "rest api",
}


@dataclass(frozen=True)
class KeywordExtraction:
    technical_skills: list[str]
    tools: list[str]
    frameworks: list[str]
    soft_skills: list[str]

    @property
    def all_keywords(self) -> list[str]:
        return unique_sorted(
            self.technical_skills + self.tools + self.frameworks + self.soft_skills
        )


def canonicalize(term: str) -> str:
    normalized = normalize_text(term).replace(" / ", "/")
    return ALIASES.get(normalized, normalized)


def _contains_term(text: str, term: str) -> bool:
    escaped = re.escape(term).replace(r"\ ", r"[\s/-]+")
    return bool(re.search(rf"(?<![a-z0-9+#.]){escaped}(?![a-z0-9+#.])", text))


def _extract_from_lexicon(text: str, lexicon: set[str]) -> list[str]:
    normalized = normalize_text(text)
    found = [canonicalize(term) for term in lexicon if _contains_term(normalized, term)]
    return unique_sorted(found)


def extract_job_keywords(jd_text: str) -> KeywordExtraction:
    return KeywordExtraction(
        technical_skills=_extract_from_lexicon(jd_text, TECHNICAL_SKILLS),
        tools=_extract_from_lexicon(jd_text, TOOLS),
        frameworks=_extract_from_lexicon(jd_text, FRAMEWORKS),
        soft_skills=_extract_from_lexicon(jd_text, SOFT_SKILLS),
    )


def fuzzy_contains_keyword(text: str, keyword: str, threshold: float = 0.88) -> bool:
    normalized_text = normalize_text(text)
    keyword = canonicalize(keyword)

    if _contains_term(normalized_text, keyword):
        return True

    words = normalized_text.split()
    target_words = keyword.split()
    window_size = max(1, len(target_words))

    for index in range(0, max(1, len(words) - window_size + 1)):
        phrase = " ".join(words[index:index + window_size])
        if SequenceMatcher(None, phrase, keyword).ratio() >= threshold:
            return True

    return False


def match_keywords(resume_text: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    unique_keywords = unique_sorted(canonicalize(keyword) for keyword in keywords)
    matched = [keyword for keyword in unique_keywords if fuzzy_contains_keyword(resume_text, keyword)]
    missing = [keyword for keyword in unique_keywords if keyword not in matched]
    return matched, missing


def extract_required_years(text: str) -> int:
    normalized = normalize_text(text)
    patterns = [
        r"(\d+)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience",
        r"minimum\s+(\d+)\s*(?:years|yrs)",
        r"at least\s+(\d+)\s*(?:years|yrs)",
    ]
    years = [int(match.group(1)) for pattern in patterns for match in re.finditer(pattern, normalized)]
    return max(years) if years else 0


def extract_resume_years(text: str) -> int:
    normalized = normalize_text(text)
    explicit = extract_required_years(normalized)
    ranges = []
    for start, end in re.findall(r"\b(20\d{2}|19\d{2})\s*[-–]\s*(20\d{2}|present|current)\b", normalized):
        start_year = int(start)
        end_year = 2026 if end in {"present", "current"} else int(end)
        if end_year >= start_year:
            ranges.append(min(end_year - start_year, 40))
    return max([explicit] + ranges) if ranges or explicit else 0


def extract_degree_terms(text: str) -> list[str]:
    return _extract_from_lexicon(text, DEGREES)

