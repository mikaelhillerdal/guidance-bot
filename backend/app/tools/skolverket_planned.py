from __future__ import annotations

from typing import Any, Dict, Optional

import requests

BASE_URL = "https://api.skolverket.se/planned-educations"
ACCEPT_V3 = "application/vnd.skolverket.plannededucations.api.v3.hal+json"

_session = requests.Session()


def planned_search(
        *,
        query: str,
        municipality_code: str,
        education_form: str = "komvux",
        start_from: Optional[str] = None,
        limit: int = 10,
) -> Dict[str, Any]:
    """
    Searches planned education events (v3).

    NOTE: The exact path and parameter names must match Skolverket Swagger.
    If they differ, this function will return a skolverket_api_error payload.
    """
    params: Dict[str, Any] = {
        "q": query,
        "municipalityCode": municipality_code,
        "educationForm": education_form,
        "limit": limit,
    }
    if start_from:
        params["startFrom"] = start_from

    headers = {
        "Accept": ACCEPT_V3,
        "User-Agent": "guidance-bot/0.1",
    }

    # If Swagger shows a different path for v3, update it here.
    url = f"{BASE_URL}/v3/adult-education-events"

    try:
        r = _session.get(url, params=params, headers=headers, timeout=(5, 30))
    except requests.RequestException as e:
        return {
            "error": "skolverket_request_failed",
            "url": url,
            "params": params,
            "details": str(e),
        }

    if not r.ok:
        return {
            "error": "skolverket_api_error",
            "status": r.status_code,
            "url": r.url,
            "response_headers": dict(r.headers),
            "body": r.text[:2000],
        }

    try:
        return r.json()
    except ValueError:
        return {
            "error": "skolverket_invalid_json",
            "status": r.status_code,
            "url": r.url,
            "body": r.text[:2000],
        }