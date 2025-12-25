from typing import Any, Dict, List
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    tenant_id: str
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
