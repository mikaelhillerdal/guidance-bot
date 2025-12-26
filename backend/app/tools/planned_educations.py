from __future__ import annotations
from typing import Any, Dict
import requests

BASE_URL = "https://api.skolverket.se/planned-educations"
ACCEPT_V3 = "application/vnd.skolverket.plannededucations.api.v3.hal+json"

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
