"""Switches the app asks for when it starts (GET /api/app/switches).

Changing a switch here and publishing reaches every phone the next time the app is opened: no new app build."""
from fastapi import APIRouter

import class_levels
import matched
from database import db

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

# Home's "Matched" card (the JEE Main questions that matched ours) in place of the All India series card, and the same
# offer on the sign-in screen (the whole story: memory/MATCHED_CONTRACT.md):
#   "auto"  from the first published Matched shift (the day of JEE Main's first shift: the All India series then keeps a
#           bar under the card for its remaining days), and in any case from the day after the series' last day; the
#           website's own schedule decides that day (matched.py)
#   "on"    now, whatever is published and whatever the series' dates are
#   "off"   never: Home keeps the All India series card
# A phone learns the answer when the app is opened (and again when it is brought back after half an hour).
MATCHED_CARD = "auto"

# Finished papers a phone keeps for itself, so a result opens at once on a weak line and without one (frontend
# src/offline/papers.ts): the result with its questions, answers and solutions, and its pictures in the website's parts
# of 12 (never the one-picture route, so only while PICTURES_STEP is 4 or more). The number is how many papers a phone
# may fetch in one run (a run: the app opened or brought back, at most once in 15 minutes; one paper every few
# seconds). JEE Main first, then BITSAT, then the rest, newest first; a paper already kept is not fetched again.
#   0   off: no phone fetches a paper in the background (what a phone already keeps stays readable)
KEEP_RESULTS = 10

# The phone's own background run while the app is closed (frontend src/offline/background.ts, a real app build only):
# the same keeping as above (Rapid Fire's cards, rounds played without a line, finished papers), started by the phone
# itself now and then, on Wi-Fi or mobile data. 1 = on. 0 = every phone stops it at its next run (and does not start it
# again); what is kept stays, and the app keeps things while it is open as before.
KEEP_BACKGROUND = 1

router = APIRouter()


@router.get("/app/switches")
async def switches():
    # "classes": the number of the Class 11 / Class 12 chapter list (class_levels.py). An app that carries an older list
    # asks for the new one (GET /api/app/classes); an app that carries this one asks for nothing.
    return {"pictures": PICTURES_STEP, "matched": await matched.card_on(db, MATCHED_CARD), "classes": class_levels.VERSION, "keep": KEEP_RESULTS,
            "background": KEEP_BACKGROUND}
