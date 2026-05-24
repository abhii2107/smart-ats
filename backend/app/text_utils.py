import io
import re
from typing import Iterable

from fastapi import HTTPException, UploadFile
from PyPDF2 import PdfReader


MAX_PDF_SIZE_BYTES = 8 * 1024 * 1024


def normalize_text(text: str) -> str:
    """Normalize user-provided text before deterministic matching."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9+#.\s/-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(file: UploadFile) -> str:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_bytes = file.file.read()
    file.file.seek(0)

    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="PDF must be smaller than 8 MB")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {exc}") from exc

    if not text:
        raise HTTPException(status_code=422, detail="Could not extract text from this PDF")

    return text


def unique_sorted(values: Iterable[str]) -> list[str]:
    return sorted({value.strip().lower() for value in values if value and value.strip()})


def section_text(text: str, section_names: list[str], stop_names: list[str] | None = None) -> str:
    normalized = normalize_text(text)
    stops = stop_names or [
        "education",
        "experience",
        "work experience",
        "employment",
        "projects",
        "skills",
        "certifications",
        "summary",
    ]
    section_pattern = "|".join(re.escape(name) for name in section_names)
    stop_pattern = "|".join(re.escape(name) for name in stops if name not in section_names)
    match = re.search(rf"\b({section_pattern})\b(.+?)(?=\b({stop_pattern})\b|$)", normalized)
    return match.group(2).strip() if match else ""

