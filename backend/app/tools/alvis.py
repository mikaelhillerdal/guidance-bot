from __future__ import annotations

from typing import Any, Dict, List, Optional
import re
import requests

from bs4 import BeautifulSoup

def _extract_token(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    inp = soup.select_one('input[name="__RequestVerificationToken"]')
    if inp and inp.get("value"):
        return inp["value"]
    m = re.search(r'name="__RequestVerificationToken"\s+value="([^"]+)"', html)
    return m.group(1) if m else None


def _parse_search_results(html: str, base_url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    # antal träffar
    hits = None
    hits_el = soup.select_one("#js-hits-filter")
    if hits_el:
        try:
            hits = int(hits_el.get_text(strip=True))
        except Exception:
            hits = None

    results: List[Dict[str, Any]] = []

    for li in soup.select("#js-results li.c-search-results__item"):
        a = li.select_one("a.c-search-results__link")
        title = a.get_text(" ", strip=True) if a else li.get_text(" ", strip=True)

        href = a.get("href") if a else None
        if href and href.startswith("/"):
            href = base_url.rstrip("/") + href

        # topic: [Skolform, Ämne]
        topic_spans = [s.get_text(" ", strip=True) for s in li.select("p.c-search-results__topic span")]
        school_form = topic_spans[0] if len(topic_spans) >= 1 else None
        subject = topic_spans[1] if len(topic_spans) >= 2 else None

        # meta: ofta [Distans/Dagtid, Poäng, Kurskod]
        meta_spans = [s.get_text(" ", strip=True) for s in li.select("p.c-search-results__meta span")]
        study_form = None
        points = None
        course_code = None

        for v in meta_spans:
            # 100 poäng
            m = re.match(r"^(\d+)\s*poäng$", v, re.IGNORECASE)
            if m:
                points = int(m.group(1))
                continue
            # “Distans” / “Dagtid” etc
            if v.lower() in {"distans", "dagtid", "kväll", "flex"}:
                study_form = v
                continue
            # kurskod brukar vara typ MATO1B00X-D
            if course_code is None and re.search(r"[A-ZÅÄÖ]{2,}\w", v):
                course_code = v

        # ansökningsstatus (grön badge etc)
        status_el = li.select_one(".c-custom-badge__discription")
        status = status_el.get_text(" ", strip=True) if status_el else None

        results.append({
            "title": title,
            "url": href,
            "school_form": school_form,
            "subject": subject,
            "study_form": study_form,
            "points": points,
            "course_code": course_code,
            "status": status,
        })

    return {"hits": hits, "results": results}


def alvis_search_courses(
        *,
        base_url: str,
        search: str,
        search_all_courses: bool = False,   # motsvarar "Sök bland alla kurser"
        site_id: str = "132219",
        timeout_s: int = 20,
) -> Dict[str, Any]:
    with requests.Session() as s:
        # 1) GET token + cookies
        r1 = s.get(base_url, timeout=timeout_s)
        if not r1.ok:
            return {"error": "alvis_get_failed", "status": r1.status_code, "url": r1.url}

        token = _extract_token(r1.text)
        if not token:
            return {"error": "alvis_token_missing", "url": base_url, "html_head": r1.text[:2000]}

        # 2) POST search (i din HTML ser action="/hittakurser", så detta är rätt för Strängnäs)
        post_url = base_url  # om du vill: gör tenant-konfigurerbart

        data = {
            "HittaKurserViewModel.Search": search,
            # IMPORTANT: på sidan betyder value=true "Sök bland alla kurser"
            "HittaKurserViewModel.Kommande": "true" if search_all_courses else "false",
            "HittaKurserViewModel.SokMetod": "sok",
            "environment": "fritext",
            "id": site_id,
            "__RequestVerificationToken": token,
            "HittaKurserViewModel.FilterTypeUsed": "FilterButtonClicked",
        }

        headers = {
            "Referer": base_url,
            "Origin": "https://strangnas.alvis.se",
            "User-Agent": "Mozilla/5.0",
        }

        r2 = s.post(post_url, data=data, headers=headers, timeout=timeout_s)
        if not r2.ok:
            return {"error": "alvis_post_failed", "status": r2.status_code, "url": r2.url, "body": r2.text[:800]}

        parsed = _parse_search_results(r2.text, base_url="https://strangnas.alvis.se")
        return {
            "source": "alvis",
            "url": base_url,
            "search": search,
            **parsed,
        }
