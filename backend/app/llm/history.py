from typing import List, Dict
from app.schemas.chat import ChatMessage

def to_genai_role(role: str) -> str:
    return "model" if role in {"assistant", "model"} else "user"

def history_to_contents(messages: List[ChatMessage]) -> List[Dict]:
    return [
        {"role": to_genai_role(m.role), "parts": [{"text": m.content}]}
        for m in messages
    ]
