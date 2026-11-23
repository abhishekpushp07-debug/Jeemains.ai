"""Switches the app asks for when it starts (GET /api/app/switches).

Changing a switch here and publishing reaches every phone the next time the app is opened: no new app build."""
from fastapi import APIRouter

# How much of the website's new picture way the app uses, in the order of the website's note
# (memory/WEBSITE_PICTURES_REPLY_2.md, section 6; the whole story: memory/PICTURES_APP.md). Each step includes the ones
# before it, and every step is used only for a paper whose rows carry the website's asset_revision: against a website
# that gives its old answers nothing changes, whatever this number is.
#   0  off: every phone loads pictures exactly as it always has
#   2  a picture kept on the phone under its asset_revision is not asked about again
#   3  a finished paper's question pictures come in parts of 12
#   4  its solution pictures come in parts too (kind=solution)
#   5  every picture is asked for as a lighter WebP copy (format=webp, the same pixels)
# (Step 1, the small re-check with If-None-Match, is in every build and needs no switch.)
# To go back, lower the number and publish: the old routes are always kept as the fallback.
PICTURES_STEP = 5

router = APIRouter()


@router.get("/app/switches")
async def switches():
    return {"pictures": PICTURES_STEP}
