from typing import List, Literal, Optional

from pydantic import BaseModel, Field


ChatMode = Literal["llm_only", "rag", "rag_prompt"]


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    mode: ChatMode = Field(default="llm_only")


class SourceItem(BaseModel):
    file_name: str
    title: Optional[str] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    content_preview: Optional[str] = None
    content: Optional[str] = None
    distance: Optional[float] = None


class ChatResponse(BaseModel):
    mode: ChatMode
    answer: str
    sources: List[SourceItem] = Field(default_factory=list)
