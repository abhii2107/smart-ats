from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
    chat_history: List[ChatMessage] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    resume_text: str
    jd_text: str


class ImproveRequest(BaseModel):
    resume_text: str
    jd_text: str
    ats_score: Optional[float] = None


class SkillGapRequest(BaseModel):
    resume_text: str
    jd_text: str


class MockQuestionRequest(BaseModel):
    resume_text: str
    jd_text: str


class MockFeedbackRequest(BaseModel):
    question: str
    answer: str
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
