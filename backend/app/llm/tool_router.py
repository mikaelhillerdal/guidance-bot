import json
from typing import Any, Dict, List
from app.tools.planned_educations import adult_education_events
from app.llm.gemini_client import generate
from app.tools.alvis import alvis_search_courses

def is_empty_adult_events(data: dict) -> bool:
    # Om toolen returnerar {"error": ...} vill vi också trigga fallback
    if isinstance(data, dict) and data.get("error"):
        return True
    try:
        return int(data.get("body", {}).get("page", {}).get("totalElements", 0)) == 0
    except Exception:
        return True

def alvis_llm_view(alvis_data: dict) -> dict:
    return {
        "hits": alvis_data.get("hits"),
        "results": [
            {
                "title": r.get("title"),
                "course_code": r.get("course_code"),
                "study_form": r.get("study_form"),
                "points": r.get("points"),
                "school_form": r.get("school_form"),
                "status": r.get("status"),
                "url": r.get("url"),
            }
            for r in alvis_data.get("results", [])
        ]
    }

def run_with_tools(contents, tools, tenant, last_user_text: str) -> tuple[str, List[Dict]]:
    resp = generate(contents, tools)
    sources = []

    import re

    # Extrahera ett rimligt ämnesord för Alvis-sökning
    m = re.search(
        r"\b(matematik|svenska|engelska|naturkunskap|programmering)\b",
        last_user_text.lower()
    )

    search_term = m.group(1) if m else last_user_text.strip()[:40]

    # absolut sista fallback
    if not search_term:
        search_term = "matematik"


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

                    alvis_data = alvis_search_courses(
                        base_url=alvis_url,
                        search=search_term,
                    )

                    sources.append({
                        "type": "municipal_catalog",
                        "tool": "alvis_search_courses",
                        "url": alvis_url,
                        "search": search_term,
                        "hits": alvis_data.get("hits"),
                    })

                    if alvis_data.get("error"):
                        return (
                            "Jag kunde inte läsa Strängnäs kurskatalog (Alvis) just nu p.g.a. ett tekniskt fel. "
                            "Testa igen senare eller gå direkt till kurskatalogen.",
                            sources,
                        )

                    llm_payload = alvis_llm_view(alvis_data)

                    followup = contents + [{
                        "role": "user",
                        "parts": [{
                            "text": (
                                    "VERKTYGSRESULTAT (Alvis kurskatalog, JSON):\n"
                                    + json.dumps(llm_payload, ensure_ascii=False)
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
