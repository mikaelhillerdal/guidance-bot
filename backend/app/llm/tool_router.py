# guidance-bot/backend/app/llm/tool_router.py

import json
import re
from typing import Dict, List, Tuple

from app.llm.gemini_client import generate
from app.tools.alvis import alvis_search_courses
from app.tools.planned_educations import (
    adult_education_events,
    education_events_search,
)

# -----------------------------
# Helpers
# -----------------------------

def is_empty_adult_events(data: dict) -> bool:
    if not isinstance(data, dict):
        return True
    if data.get("error"):
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
        ],
    }


def education_events_llm_view(data: dict) -> dict:
    events = data.get("body", {}).get("_embedded", {}).get("educationEvents", []) or []
    out = []
    for e in events:
        out.append(
            {
                "school_unit_name": e.get("schoolUnitName"),
                "school_unit_code": e.get("schoolUnitCode"),
                "type_of_schooling": (e.get("typeOfSchooling") or {}).get("code"),
                "type_of_schooling_name": (e.get("typeOfSchooling") or {}).get("displayName"),
                "study_path_name": e.get("studyPathName"),
                "study_path_code": e.get("studyPathCode"),
                "study_path_category": e.get("studyPathCategory"),
                "start_date": e.get("startDate"),
                "end_date": e.get("endDate"),
                "city": e.get("visitingAddressCity"),
                "admission_points_min": e.get("admissionPointsMin"),
                "admission_points_avg": e.get("admissionPointsAverage"),
                "admission_points_semester": e.get("admissionPointsSemester"),
                "school_unit_url": (((e.get("_links") or {}).get("school-unit") or {}).get("href")),
            }
        )
    page = data.get("body", {}).get("page", {}) or {}
    return {
        "total": page.get("totalElements"),
        "page": page.get("number"),
        "size": page.get("size"),
        "events": out,
    }


def extract_search_term(last_user_text: str) -> str:
    """
    PoC: enkel ämnesextraktion för Alvis.
    - Fångar vanliga ämnen om de finns i texten.
    - Fallback: ett kort, rimligt sökord (inte hela meningen).
    """
    q = (last_user_text or "").lower()

    # superenkel "matematik"-fallback (fångar även "matematikkurser" osv)
    if "matem" in q:
        return "matematik"

    # annars prova ordlista
    m = re.search(r"\b(svensk\w*|engelsk\w*|naturkunskap\w*|programmering\w*)\b", q)
    if m:
        token = m.group(1)
        if token.startswith("svensk"):
            return "svenska"
        if token.startswith("engelsk"):
            return "engelska"
        if token.startswith("naturkunskap"):
            return "naturkunskap"
        if token.startswith("programmering"):
            return "programmering"
        return token

    # fallback: sista "meningsfulla" ordet
    words = [w for w in re.findall(r"[a-zåäö]+", q) if w not in {"kan", "jag", "läsa", "finns", "kurser", "på", "i", "komvux", "strängnäs"}]
    return words[-1] if words else "kurser"


def classify_query(last_user_text: str) -> Tuple[bool, bool]:
    """
    Returns (is_komvux, is_gymnasium)
    """
    q = (last_user_text or "").lower()

    is_komvux = any(w in q for w in ["komvux", "vuxenutbild", "vux", "sfi", "prövning", "komvuxarbete", "hittakurser"])
    is_gymnasium = any(w in q for w in ["gymnas", "program", "inrikt", "antagningspoäng", "merit", "gyan", "studieväg", "study path"])

    return is_komvux, is_gymnasium


# -----------------------------
# Main router
# -----------------------------

def run_with_tools(contents, tools, tenant, last_user_text: str) -> tuple[str, List[Dict]]:
    sources: List[Dict] = []

    is_komvux, is_gymnasium = classify_query(last_user_text)
    municipality_code = tenant["geo"]["municipality_code"]

    # -------------------------
    # 1) Deterministic: KOMVUX -> Alvis (kommunens katalog)
    # -------------------------
    if is_komvux:
        fallback = tenant.get("fallback_sources", {}).get("komvux_catalog")
        if fallback and fallback.get("enabled"):
            alvis_url = fallback["url"]
            search_term = extract_search_term(last_user_text)

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
                "error": alvis_data.get("error"),
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
                            + "\n\nInstruktion: Svara kort på svenska och lista ALLA träffar som matchar användarens fråga."
                    )
                }]
            }]

            resp2 = generate(followup)
            return resp2.text or "", sources

        # Om ingen fallback källa är konfigurerad:
        return (
            "Jag har ingen konfigurerad kurskatalog för Komvux i den här kommunen. "
            "Kontakta kommunens vuxenutbildning för aktuellt kursutbud.",
            sources,
        )

    # -------------------------
    # 2) Deterministic: GYMNASIUM -> Skolverket education-events
    # -------------------------
    if is_gymnasium:
        args = {
            "geographical_area_code": municipality_code,
            "type_of_schooling": "gy",
            "page": 0,
            "size": 50,
        }

        data = education_events_search(**args)
        sources.append({"type": "skolverket_api", "tool": "education_events_search", "args": args})

        payload = education_events_llm_view(data)
        followup = contents + [{
            "role": "user",
            "parts": [{
                "text": (
                        "VERKTYGSRESULTAT (Skolverket education-events, JSON):\n"
                        + json.dumps(payload, ensure_ascii=False)
                        + "\n\nInstruktion: Svara kort på svenska. "
                          "Om användaren frågar 'vilka program finns', lista alla och gruppera per skola. "
                          "Om antagningspoäng finns, visa min/medel + termin."
                )
            }]
        }]

        resp2 = generate(followup)
        return resp2.text or "", sources

    # -------------------------
    # 3) Fallback: låt modellen välja verktyg via function calling (som innan)
    # -------------------------
    resp = generate(contents, tools)

    try:
        parts = resp.candidates[0].content.parts
    except Exception:
        return resp.text or "", sources

    for part in parts:
        fc = getattr(part, "function_call", None)
        if not fc:
            continue

        if fc.name == "education_events_search":
            args = fc.args or {}
            gac = args.get("geographical_area_code")
            if not (isinstance(gac, str) and gac.isdigit()):
                args["geographical_area_code"] = municipality_code
            args.setdefault("page", 0)
            args.setdefault("size", 20)

            data = education_events_search(**args)
            sources.append({"type": "skolverket_api", "tool": fc.name, "args": args})

            followup = contents + [{
                "role": "user",
                "parts": [{
                    "text": (
                            "VERKTYGSRESULTAT (Skolverket education-events, JSON):\n"
                            + json.dumps(education_events_llm_view(data), ensure_ascii=False)
                    )
                }]
            }]

            resp2 = generate(followup)
            return resp2.text or "", sources

        if fc.name == "adult_education_events":
            args = fc.args or {}
            gac = args.get("geographical_area_code")
            if not (isinstance(gac, str) and gac.isdigit()):
                args["geographical_area_code"] = municipality_code
            args.setdefault("page", 0)
            args.setdefault("size", 20)

            data = adult_education_events(**args)
            sources.append({"type": "skolverket_api", "tool": fc.name, "args": args})

            followup = contents + [{
                "role": "user",
                "parts": [{"text": json.dumps(data, ensure_ascii=False)[:12000]}],
            }]

            resp2 = generate(followup)
            return resp2.text or "", sources

    return resp.text or "", sources
