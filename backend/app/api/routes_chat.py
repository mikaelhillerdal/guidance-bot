from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from app.schemas.chat import ChatRequest, ChatResponse
from app.core.tenants import load_tenant
from app.rag.service import get_rag
from app.rag.format import format_rag
from app.llm.history import history_to_contents
from app.llm.prompts import system_prompt
from app.llm.tool_router import run_with_tools

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_tenant: Optional[str] = Header(default=None)):
    tenant_id = req.tenant_id or x_tenant
    if not tenant_id:
        raise HTTPException(400, "Missing tenant_id")

    tenant = load_tenant(tenant_id)

    rag = get_rag(tenant)
    last_user = next(m.content for m in reversed(req.messages) if m.role == "user")
    snips = rag.retrieve(last_user, k=tenant.get("rag", {}).get("top_k", 4))

    contents = [
        {"role": "user", "parts": [{"text": system_prompt(tenant)}]}
    ]

    if snips:
        contents.append({
            "role": "user",
            "parts": [{"text": format_rag(snips)}]
        })

    contents.extend(history_to_contents(req.messages))

    tools = [{
        "function_declarations": [{
            "name": "adult_education_events",
            "description": "Hämtar planerade utbildningstillfällen inom vuxenutbildning för ett geografiskt område (t.ex. kommunkod).",
            "parameters": {
                "type": "object",
                "properties": {
                    "geographical_area_code": {
                        "type": "string",
                        "description": "Geographical area code (kommun kod), t.ex. '0486' för Strängnäs."
                    },
                    "page": {"type": "integer", "description": "Sida (0-baserad).", "default": 0},
                    "size": {"type": "integer", "description": "Antal per sida.", "default": 20}
                },
                "required": []
            }
        }]
    }]

    last_user = next((m.content for m in reversed(req.messages) if m.role == "user"), "")

    answer, sources = run_with_tools(contents, tools, tenant, last_user_text=last_user)
    return ChatResponse(answer=answer, sources=sources)
