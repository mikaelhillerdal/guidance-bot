from __future__ import annotations
from typing import Any, Dict, Optional
import requests

# För PoC: enkel requests-wrapper. Lägg på caching senare (Redis).
# Du behöver fylla i korrekt endpoint/params baserat på swagger.
BASE_URL = "https://api.skolverket.se/planned-educations"

def planned_search(
        *,
        query: str,
        municipality_code: str,
        education_form: str = "komvux",
        start_from: Optional[str] = None,
        limit: int = 10
) -> Dict[str, Any]:
    """
    Söker planerade utbildningstillfällen.
    - query: "matematik", "svenska", "programmering"...
    - municipality_code: t.ex. "0486"
    - start_from: ISO datum "2026-01-01" (valfritt)
    """

    # OBS: Parameternamn nedan är EXEMPEL. Justera efter swagger.
    params = {
        "q": query,
        "municipalityCode": municipality_code,
        "educationForm": education_form,
        "limit": limit,
    }
    if start_from:
        params["startFrom"] = start_from

    headers = {
        # Skolverket versionerar via Accept. Hämta exakt value från swagger/docs.
        "Accept": "application/json"
    }

    url = f"{BASE_URL}/api/v3/planned-educations"  # EXEMPEL: justera path efter swagger
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()
