from __future__ import annotations
from typing import Any, Dict, Optional
import requests

BASE_URL = "https://api.skolverket.se/planned-educations"
ACCEPT_V3 = "application/vnd.skolverket.plannededucations.api.v3.hal+json"

def education_events_search(
        *,
        geographical_area_code: str,
        type_of_schooling: Optional[str] = None,   # "gy" eller "gyan"
        name: Optional[str] = None,                # skolenhetsnamn (hela ord)
        study_path_code: Optional[str] = None,
        principal_organizer_type: Optional[str] = None,
        school_orientation: Optional[str] = None,
        page: int = 0,
        size: int = 20,
        sort: Optional[str] = None,
) -> Dict[str, Any]:
    url = f"{BASE_URL}/v3/education-events"
    headers = {"Accept": ACCEPT_V3}

    params: Dict[str, Any] = {
        "geographicalAreaCode": geographical_area_code,
        "page": page,
        "size": size,
    }
    if type_of_schooling:
        params["typeOfSchooling"] = type_of_schooling
    if name:
        params["name"] = name
    if study_path_code:
        params["studyPathCode"] = study_path_code
    if principal_organizer_type:
        params["principalOrganizerType"] = principal_organizer_type
    if school_orientation:
        params["schoolOrientation"] = school_orientation
    if sort:
        params["sort"] = sort

    r = requests.get(url, params=params, headers=headers, timeout=20)
    if not r.ok:
        return {"error": "skolverket_api_error", "status": r.status_code, "url": r.url, "body": r.text[:800]}
    return r.json()

def adult_education_events(
        *,
        geographical_area_code: str,   # <-- this is the one from swagger
        page: int = 0,
        size: int = 20,
) -> Dict[str, Any]:
    url = f"{BASE_URL}/v3/adult-education-events"
    headers = {"Accept": ACCEPT_V3}
    params = {
        "geographicalAreaCode": geographical_area_code,
        "page": page,
        "size": size,
    }

    r = requests.get(url, params=params, headers=headers, timeout=20)

    # Never crash your API while iterating
    if not r.ok:
        return {
            "error": "skolverket_api_error",
            "status": r.status_code,
            "url": r.url,
            "body": r.text[:800],
        }

    return r.json()
