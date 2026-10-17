"""
JEE Advanced Archive Service
Fetch and parse PDF links from official JEE Advanced archive
"""
from __future__ import annotations
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

JEA_ARCHIVE_URL = "https://jeeadv.ac.in/archive.html"

LANG_MAP = {"EN": "English", "HI": "Hindi"}


def fetch_archive_html(timeout: int = 30) -> str:
    """Fetch the HTML content from JEE Advanced archive page"""
    r = requests.get(
        JEA_ARCHIVE_URL, 
        timeout=timeout, 
        headers={"User-Agent": "JEA-TPE/1.0"}
    )
    r.raise_for_status()
    return r.text


def extract_pdf_links(
    html: str, 
    start_year: int, 
    end_year: int, 
    language: str
) -> List[Dict]:
    """
    Extract PDF links from archive HTML.
    Returns list of: {year, paper_no, language, official_url}
    """
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)
    pdfs = []
    
    for a in anchors:
        href = a["href"].strip()
        if not href.lower().endswith(".pdf"):
            continue
            
        # Build absolute URL
        if href.startswith("/"):
            url = "https://jeeadv.ac.in" + href
        elif href.startswith("http"):
            url = href
        else:
            url = "https://jeeadv.ac.in/" + href

        # Pattern: 2025_1_English.pdf or variations
        m = re.search(r"/(\d{4})_(\d)_(English|Hindi)\.pdf$", url, re.IGNORECASE)
        if not m:
            # Try alternate pattern: 2025-Paper1-English.pdf
            m = re.search(r"/(\d{4}).*Paper\s*(\d).*(English|Hindi)\.pdf$", url, re.IGNORECASE)
            if not m:
                continue
                
        yr = int(m.group(1))
        pn = int(m.group(2))
        lang = "EN" if m.group(3).lower() == "english" else "HI"

        if yr < start_year or yr > end_year:
            continue
        if lang != language:
            continue

        pdfs.append({
            "year": yr, 
            "paper_no": pn, 
            "language": lang, 
            "official_url": url
        })

    # Dedupe by (year, paper, lang)
    seen = set()
    out = []
    for p in sorted(pdfs, key=lambda x: (x["year"], x["paper_no"])):
        k = (p["year"], p["paper_no"], p["language"])
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    
    return out
