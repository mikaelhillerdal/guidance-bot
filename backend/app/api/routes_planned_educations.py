import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.planned_educations import education_events_search
from app.tools.alvis import alvis_search_courses
from app.llm.tool_router import extract_search_term

router = APIRouter(prefix="/planned-educations", tags=["planned-educations"])

_TENANT_DIR = Path("./tenants")


def _find_tenant_by_municipality(code: str) -> dict | None:
    for path in _TENANT_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("geo", {}).get("municipality_code") == code:
                return data
        except Exception:
            continue
    return None


class PlannedEducationsRequest(BaseModel):
    municipalityCode: str
    educationForm: str
    question: str


@router.post("/search")
def search_planned_educations(req: PlannedEducationsRequest):
    code = (req.municipalityCode or "").strip()
    education_form = (req.educationForm or "").strip().lower()

    if not code:
        raise HTTPException(status_code=400, detail="municipalityCode is required")

    if education_form == "komvux":
        tenant = _find_tenant_by_municipality(code)
        fallback = (tenant or {}).get("fallback_sources", {}).get("komvux_catalog", {})

        if not tenant or not fallback.get("enabled"):
            return {"source": "none", "items": [], "message": "No komvux catalog configured for this municipality."}

        search_term = extract_search_term(req.question)
        alvis_data = alvis_search_courses(base_url=fallback["url"], search=search_term)

        if alvis_data.get("error"):
            raise HTTPException(status_code=502, detail=alvis_data)

        items = [
            {
                "id": r.get("course_code") or r.get("url"),
                "title": r.get("title"),
                "name": r.get("title"),
                "organizer": tenant.get("display_name"),
                "municipalityCode": code,
                "educationForm": "komvux",
                "startDate": None,
                "url": r.get("url"),
            }
            for r in alvis_data.get("results", [])
        ]

        return {"source": "alvis", "hits": alvis_data.get("hits"), "items": items}

    data = education_events_search(
        geographical_area_code=code,
        type_of_schooling="gy",
        page=0,
        size=20,
    )
    if data.get("error"):
        raise HTTPException(status_code=502, detail=data)

    events = data.get("body", {}).get("_embedded", {}).get("educationEvents", []) or []
    items = [
        {
            "id": item.get("id"),
            "title": item.get("studyPathName"),
            "name": item.get("schoolUnitName"),
            "organizer": item.get("principalOrganizerName"),
            "municipalityCode": code,
            "educationForm": education_form,
            "startDate": item.get("startDate"),
            "url": ((item.get("_links") or {}).get("self") or {}).get("href"),
        }
        for item in events
    ]
    return {"source": "skolverket:education-events", "items": items}
