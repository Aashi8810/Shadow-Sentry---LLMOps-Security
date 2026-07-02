from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    prompt: str = Field(..., description="The prompt to send to the LLM")

class DocumentChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    prompt: str = Field(..., description="The user's query about the document")
    document_content: str = Field(..., description="The untrusted text content to evaluate")

class ChatResponse(BaseModel):
    response: str
    risk_score: int
    risk_level: str
    blocked: bool
    reasons: List[str] = []