# Iteration 156: GET /api/app/switches carries the store addresses for the browser copy's "get the app" card.
import os

import pytest
import requests
from dotenv import dotenv_values

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"]).rstrip("/")
PLAY = "https://play.google.com/store/apps/details?id=com.emergent.jeelivemobile.kt2g15"


@pytest.fixture(scope="module")
def switches():
    r = requests.get(f"{BASE_URL}/api/app/switches", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


def test_stores_present(switches):
    assert switches["stores"] == {"android": PLAY, "ios": ""}


def test_other_keys_kept(switches):
    for k in ("pictures", "matched", "classes", "keep", "background"):
        assert k in switches, k
    assert isinstance(switches["pictures"], int) and isinstance(switches["matched"], bool)
    assert isinstance(switches["classes"], int) and isinstance(switches["keep"], int) and isinstance(switches["background"], int)


def test_android_link_is_https_play(switches):
    assert switches["stores"]["android"].startswith("https://play.google.com/")


def test_arena_copy_served():
    r = requests.get(f"{BASE_URL}/api/arena/rapid/duel?review=x", timeout=20)
    assert r.status_code == 200 and "<html" in r.text.lower()
