import json
from typing import Any, Dict, List
from app.tools.planned_educations import adult_education_events
from app.llm.gemini_client import generate
from app.tools.alvis import alvis_search_courses

def is_empty_adult_events(data: dict) -> bool:
    try:
        return data.get("body", {}).get("page", {}).get("totalElements", 0) == 0
    except Exception:
        return True


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

        if fc.name == "adult_education_events":
            args = fc.args or {}

            # Force the code from tenant if model sends anything else
            gac = args.get("geographical_area_code")
            if not (isinstance(gac, str) and gac.isdigit()):
                args["geographical_area_code"] = tenant["geo"]["municipality_code"]

            args.setdefault("page", 0)
            args.setdefault("size", 20)

            # PRIMÄR KÄLLA: Skolverket
            data = adult_education_events(**args)
            sources.append({
                "type": "skolverket_api",
                "tool": fc.name,
                "args": args
            })

            # 3. OM TOMT RESULTAT → fallback till Alvis
            if is_empty_adult_events(data):
                fallback = tenant.get("fallback_sources", {}).get("komvux_catalog")
                if fallback and fallback.get("enabled"):
                    alvis_url = fallback["url"]

                    alvis_data = alvis_search_courses(base_url=alvis_url, search="matematik")
                    sources.append({
                        "type": "municipal_catalog",
                        "tool": "alvis",
                        "url": alvis_url,
                        "result": alvis_data,
                    })

                    followup = contents + [{
                        "role": "user",
                        "parts": [{
                            "text": (
                                "Skolverket gav inga träffar för komvux i kommunen.\n"
                                "Här är data från kommunens kurskatalog (Alvis):\n\n"
                                f"{json.dumps(alvis_data, ensure_ascii=False)[:12000]}"
                            )
                        }]
                    }]

                    resp2 = generate(followup)
                    return resp2.text or "", sources

            # Om Skolverket hade data → fortsätt som vanligt
            followup = contents + [{
                "role": "user",
                "parts": [{"text": json.dumps(data, ensure_ascii=False)[:12000]}]
            }]

            resp2 = generate(followup)
            return resp2.text or "", sources

    return resp.text or "", sources
