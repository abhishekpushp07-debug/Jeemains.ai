"""Browser arena: the app's own web build (Rapid Fire only), served at /api/arena so it works on the live server.

Build it with /app/scripts/build_arena_web.sh before Publish. Only files inside ARENA_DIR are ever sent.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

ARENA_DIR = (Path(__file__).parent / "arena_web").resolve()
router = APIRouter()
SAFE = {"X-Content-Type-Options": "nosniff", "Referrer-Policy": "strict-origin-when-cross-origin"}
# git never carries a folder named node_modules, so a copy that kept the icon font there reached production without it
# (empty boxes in place of every icon). The build keeps that folder as assets/_modules; the pages ask for the old name.
PACKAGES = ("assets/node_modules/", "assets/_modules/")


def _index():
    index = ARENA_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(503, "The browser arena is being prepared. Please try again in a few minutes.")
    # The page itself is always fresh, so a new Publish reaches every browser at once.
    return FileResponse(index, media_type="text/html", headers={**SAFE, "Cache-Control": "no-cache"})


@router.get("/arena", include_in_schema=False)
@router.head("/arena", include_in_schema=False)
async def arena_root():
    return _index()


@router.get("/arena/{path:path}", include_in_schema=False)
@router.head("/arena/{path:path}", include_in_schema=False)
async def arena_file(path: str):
    kept = PACKAGES[1] + path[len(PACKAGES[0]):] if path.startswith(PACKAGES[0]) else path
    target = (ARENA_DIR / kept).resolve()
    try:
        found = bool(path) and target.is_file() and target.is_relative_to(ARENA_DIR)
    except OSError:  # a name longer than the file system allows is simply not one of the copy's files
        found = False
    if found:
        # Bundles and assets carry a content hash in their name: they can be kept for a year.
        hashed = path.startswith(("_expo/", "assets/"))
        return FileResponse(target, headers={**SAFE, "Cache-Control": "public, max-age=31536000, immutable" if hashed else "public, max-age=3600"})
    if Path(path).suffix and path.startswith(("_expo/", "assets/")):
        raise HTTPException(404, "Not found")
    return _index()  # every arena screen (/api/arena/rapid/...) is the same single page

