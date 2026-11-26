"""The browser copy of Rapid Fire (backend/arena_web, served at /api/arena) must reach production whole.

Seen on 27 Nov 2026: production answered 404 for the icon font, so every icon in the browser arena was an empty box.
The build kept the font under assets/node_modules/, and git never carries a folder of that name, so a Publish left it
behind while the preview (which reads the workspace's own files) looked right. Since then the build keeps that folder
as assets/_modules and the server answers the old name from it. Nothing here needs the database or the network.
"""
import re
import subprocess
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import arena_web

ROOT = Path(__file__).resolve().parents[2]
DIR = arena_web.ARENA_DIR
FILES = sorted(p for p in DIR.rglob("*") if p.is_file())
BUNDLES = sorted((DIR / "_expo" / "static" / "js" / "web").glob("*.js"))
ASKED = sorted({m for b in BUNDLES for m in re.findall(r'"/api/arena/((?:assets|_expo)/[^"\s]+\.[A-Za-z0-9]{2,5})"', b.read_text(errors="replace"))})
FONT = [a for a in ASKED if "MaterialDesignIcons" in a and a.endswith(".ttf")]


@pytest.fixture(scope="module")
def site():
    app = FastAPI()
    app.include_router(arena_web.router, prefix="/api")
    return TestClient(app)


def test_the_copy_is_there():
    assert (DIR / "index.html").is_file() and len(BUNDLES) > 20 and len(FILES) > 100, (len(BUNDLES), len(FILES))


def test_git_leaves_no_file_of_the_copy_out():
    """A file git ignores is on the preview and missing after a Publish."""
    names = "\n".join(str(p.relative_to(ROOT)) for p in FILES)
    run = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin"], input=names, capture_output=True, text=True)
    assert run.returncode == 1 and not run.stdout.strip(), run.stdout[:600] or run.stderr[:300]  # 1 = none is ignored
    assert not [p for p in FILES if "node_modules" in p.relative_to(DIR).parts]


def test_the_page_and_everything_it_names_are_answered(site):
    page = site.get("/api/arena")
    assert page.status_code == 200 and "no-cache" in page.headers["cache-control"]
    named = re.findall(r'(?:src|href)="/api/arena/([^"]+)"', page.text)
    assert any(re.fullmatch(r"_expo/static/js/web/entry-[0-9a-f]+\.js", n) for n in named), named
    for name in named:
        got = site.get("/api/arena/" + name)
        assert got.status_code == 200 and len(got.content) > 0, name


def test_every_picture_and_font_the_screens_ask_for_is_answered(site):
    assert len(ASKED) > 100 and len(FONT) == 1, (len(ASKED), FONT)
    packages = [a for a in ASKED if a.startswith(arena_web.PACKAGES[0])]
    assert FONT[0] in packages and len(packages) >= 10, packages  # the icon font and the navigation's small pictures
    for name in ASKED:
        got = site.get("/api/arena/" + name)
        assert got.status_code == 200 and len(got.content) > 0, name
        assert got.headers["cache-control"] == "public, max-age=31536000, immutable", name


def test_the_icon_font_is_a_font(site):
    got = site.get("/api/arena/" + FONT[0])
    assert got.status_code == 200 and len(got.content) > 500_000 and got.content[:4] == b"\x00\x01\x00\x00", (got.status_code, len(got.content), got.content[:4])
    assert got.headers["x-content-type-options"] == "nosniff"
    # Kept under the name git carries; the old name is only how the pages ask for it.
    assert (DIR / FONT[0].replace(*arena_web.PACKAGES, 1)).is_file() and not (DIR / FONT[0]).exists()


def test_a_missing_file_and_a_way_out_of_the_folder_stay_closed(site):
    assert site.get("/api/arena/assets/node_modules/expo-router/assets/none.0123.png").status_code == 404
    assert site.get("/api/arena/_expo/static/js/web/entry-0000.js").status_code == 404
    for path in ("assets/node_modules/../../../server.py", "assets/node_modules/%2e%2e/%2e%2e/%2e%2e/server.py", "assets/_modules/../../../.env"):
        got = site.get("/api/arena/" + path)
        assert got.status_code in (200, 404) and "MONGO_URL" not in got.text and "FastAPI(" not in got.text, path
        if got.status_code == 200:  # a path without a file is a screen of the arena: the page itself
            assert got.headers["content-type"].startswith("text/html") and '<div id="root">' in got.text, path


def test_a_screen_address_gives_the_page(site):
    for path in ("rapid", "rapid/squads", "rapid/cup/abc", "entry"):
        got = site.get("/api/arena/" + path)
        assert got.status_code == 200 and got.headers["content-type"].startswith("text/html"), path


def test_the_copy_carries_no_workspace_address():
    """The arena talks to the server it came from; the address of the workspace that built it must not travel."""
    for path in [DIR / "index.html", *BUNDLES]:
        assert "emergentagent.com" not in path.read_text(errors="replace"), path.name


def test_a_name_too_long_for_the_file_system_is_not_a_server_error(site):
    long = "a" * 5000
    assert site.get(f"/api/arena/assets/{long}.js").status_code == 404
    assert site.get(f"/api/arena/{long}").status_code == 200  # any other address is the single page
