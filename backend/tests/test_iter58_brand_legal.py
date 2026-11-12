# Iteration 58: brand rename (JEELIVE -> JEECIRCLE.AI) on public legal page. Read-only GET.
import os
import re
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", os.environ.get("EXPO_BACKEND_URL", "")).rstrip("/")


def _get():
    assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL/EXPO_BACKEND_URL env var required"
    return requests.get(f"{BASE_URL}/api/legal/privacy", timeout=20)


def test_privacy_page_status_and_title():
    r = _get()
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert re.search(r"<title>[^<]*JEECIRCLE\.AI[^<]*</title>", r.text)


def test_privacy_page_has_no_old_brand_text():
    text = _get().text
    # jeelive.ai domain links are intentionally kept; only the brand word must be gone.
    stripped = re.sub(r"jeelive\.ai", "", text, flags=re.I)
    assert "JEELIVE" not in stripped.upper()
    assert text.count("JEECIRCLE") >= 3
