import json
from typing import Any, Dict, List
from app.tools.skolverket_planned import planned_search
from app.llm.gemini_client import generate
from app.tools.planned_educations import BASE_URL, ACCEPT_V3

def run_with_tools(contents, tools, tenant) -> tuple[str, List[Dict]]:
    resp = generate(contents, tools)
    sources = []

    try:
        parts = resp.candidates[0].content.parts
    except Exception:
        return resp.text or "", sources

    for part in parts:
        fc = getattr(part, "function_call", None)
        if not fc:
            continue

        if fc.name == "planned_search":
            args = fc.args or {}
            args.setdefault("municipality_code", tenant["geo"]["municipality_code"])
            args.setdefault("education_form", "komvux")
            args.setdefault("limit", 10)

            data = planned_search(**args)
            sources.append({"type": "skolverket_api", "tool": fc.name, "args": args})

            followup = contents + [{
                "role": "user",
                "parts": [{"text": json.dumps(data, ensure_ascii=False)[:12000]}]
            }]

            resp2 = generate(followup)
            return resp2.text or "", sources

    return resp.text or "", sources
