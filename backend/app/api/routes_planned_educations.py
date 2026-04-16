from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.planned_educations import adult_education_events, education_events_search

router = APIRouter(prefix="/planned-educations", tags=["planned-educations"])


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
        data = adult_education_events(geographical_area_code=code, page=0, size=20)
        if data.get("error"):
            raise HTTPException(status_code=502, detail=data)

        events = data.get("body", {}).get("_embedded", {}).get("adultEducationEvents", []) or []
        items = [
            {
                "id": item.get("id"),
                "title": item.get("name"),
                "name": item.get("name"),
                "organizer": item.get("principalOrganizerName"),
                "municipalityCode": code,
                "educationForm": "komvux",
                "startDate": item.get("eventStartDate"),
                "url": ((item.get("_links") or {}).get("self") or {}).get("href"),
            }
            for item in events
        ]

        return {"source": "skolverket:adult-education-events", "items": items}

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
