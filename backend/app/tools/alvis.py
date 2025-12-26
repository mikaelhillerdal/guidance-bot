from __future__ import annotations

from typing import Any, Dict, Optional
import requests

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None


def _extract_token(html: str) -> Optional[str]:
    """
    Alvis använder __RequestVerificationToken (ASP.NET antiforgery).
    Token brukar ligga i en hidden input.
    """
    if BeautifulSoup is None:
        return None
    soup = BeautifulSoup(html, "html.parser")
    inp = soup.select_one('input[name="__RequestVerificationToken"]')
    return inp["value"] if inp and inp.has_attr("value") else None


def alvis_search_courses(
        *,
        base_url: str,
        search: str,
        include_upcoming: bool = False,
        timeout_s: int = 20,
) -> Dict[str, Any]:
    """
    PoC: Hämtar hittakurser-sidan (GET), plockar token + cookies,
    gör POST med form-data. Returnerar HTML-utdrag som LLM kan extrahera.
    """
    with requests.Session() as s:
        # 1) GET för att få token + cookies
        r1 = s.get(base_url, timeout=timeout_s)
        if not r1.ok:
            return {"error": "alvis_get_failed", "status": r1.status_code, "url": r1.url}

        token = _extract_token(r1.text)
        if not token:
            return {
                "error": "alvis_token_missing",
                "url": base_url,
                "hint": "Installera beautifulsoup4 eller kontrollera att sidan innehåller __RequestVerificationToken.",
            }

        # 2) POST sök (ofta samma URL; annars kolla Network och byt post_url)
        post_url = base_url

        # Bygg minimal payload: du kan lägga på fler filter senare
        data = {
            "HittaKurserViewModel.Search": search,
            "HittaKurserViewModel.Kommande": "true" if include_upcoming else "false",
            "HittaKurserViewModel.SokMetod": "sok",
            "environment": "fritext",

            # Dessa två finns i din payload och verkar vara “site id” + token
            "id": "132219",
            "__RequestVerificationToken": token,

            # Den här finns i din payload – brukar hjälpa backend att veta att filterknappen användes
            "HittaKurserViewModel.FilterTypeUsed": "FilterButtonClicked",
        }

        r2 = s.post(post_url, data=data, timeout=timeout_s)
        if not r2.ok:
            return {"error": "alvis_post_failed", "status": r2.status_code, "url": r2.url, "body": r2.text[:800]}

        # PoC: returnera HTML som LLM kan plocka ut kurser ur
        return {
            "source": "alvis",
            "url": base_url,
            "search": search,
            "html_excerpt": r2.text[:12000],
        }
