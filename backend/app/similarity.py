import os
from functools import lru_cache
from math import sqrt
from collections import Counter

from .text_utils import normalize_text


@lru_cache(maxsize=1)
def _embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def _use_transformer_similarity() -> bool:
    return os.getenv("USE_TRANSFORMER_SIMILARITY", "false").lower() in {"1", "true", "yes"}


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _token_cosine(left: str, right: str) -> float:
    left_counts = Counter(left.split())
    right_counts = Counter(right.split())
    vocabulary = sorted(set(left_counts) | set(right_counts))
    left_vector = [left_counts[token] for token in vocabulary]
    right_vector = [right_counts[token] for token in vocabulary]
    return _cosine_similarity(left_vector, right_vector)


def semantic_similarity_percent(resume_text: str, jd_text: str) -> float:
    resume = normalize_text(resume_text)
    jd = normalize_text(jd_text)
    if not resume or not jd:
        return 0.0

    if _use_transformer_similarity():
        try:
            from sklearn.metrics.pairwise import cosine_similarity

            model = _embedding_model()
            embeddings = model.encode([resume, jd], normalize_embeddings=True)
            score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return round(max(0.0, min(float(score), 1.0)) * 100, 2)
        except Exception:
            pass

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectors = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform([resume, jd])
        score = cosine_similarity(vectors[0], vectors[1])[0][0]
    except Exception:
        score = _token_cosine(resume, jd)

    return round(max(0.0, min(float(score), 1.0)) * 100, 2)
