# Matched UI checks: test-only Playwright helpers (import into browser automation).
# Nothing here changes the app and nothing is written anywhere: the browser itself answers /api/matched and
# /api/matched/<shift>, and adds `matched` to the server's real /api/app/switches answer.
#
#     await fake_matched(page)                      # Matched is on; 4 shifts (Jan 2027: three, Apr 2027: one), 10 questions
#     await fake_matched(page, index=EMPTY)         # the day after the series ends, before the first shift is published
#     await fake_matched(page, on=False)            # the server says Matched is off: Home keeps the All India card
#     await fake_matched(page, status=500)          # the Matched lists cannot be read
#     await fake_matched(page, asked=calls)         # `calls` gets the path of every /api/matched request
#
# The stand-in shift 2027-01-25-s1 has every kind of question: Q7 options + right option + written solution (ours also a
# solution picture); Q31 pictures and NO solution at all; Q58 a number answer without options, and TWO of ours (the first
# with only its right option, the second with nothing); the last one has no number and no solution.
#
# The switch is asked once per app launch: register this FIRST, then load the app again (page.goto(base + "/entry")).
# The pictures in the stand-in shift are answered by the browser too (https://matched.test/...).
import json
import re
import struct
import zlib
from urllib.parse import urlparse


def _png(w, h, rgb=(236, 240, 247)):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    row = b"\x00" + bytes(rgb) * w
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(row * h, 9)) + chunk(b"IEND", b"")


def _side(text, options=(), images=(), correct=None, answer="", solution="", solution_images=(), **more):
    """A question as the server sends it. `correct` = the place of the right option, from 0."""
    return {"text": text, "options": list(options), "images": list(images), "correct": correct, "answer": answer, "solution": solution,
            "solution_images": list(solution_images), **more}


def _summary(shift_id, asked, items):
    subjects = [{"name": s, "n": n} for s in ("Physics", "Chemistry", "Mathematics") if (n := sum(1 for i in items if i["subject"] == s))]
    return {"id": shift_id, "day": shift_id[:10], "shift": int(shift_id[-1]), "asked": asked, "matched": len(items), "subjects": subjects, "updated_at": 1800000000}


JAN25_S1 = [
    {"n": 7, "subject": "Physics", "chapter": "Kinematics",
     "jee": _side("A ball is thrown vertically up with $u = 20\\,m/s$. The time taken to reach the highest point ($g = 10\\,m/s^2$) is", ["1 s", "2 s", "3 s", "4 s"],
                  correct=1, solution="At the top $v = 0$, so $t = u/g = 20/10 = 2$ s."),
     "ours": [_side("A stone is thrown vertically up with $u = 30\\,m/s$. The time taken to reach the highest point ($g = 10\\,m/s^2$) is", ["1 s", "2 s", "3 s", "4 s"],
                    correct=2, solution="At the top $v = 0$, so $t = u/g = 30/10 = 3$ s.", solution_images=[{"url": "https://matched.test/s7.png", "w": 800, "h": 240}],
                    source="AITS Day 12 · Q 7", tag="Same concept")]},
    {"n": 31, "subject": "Chemistry", "chapter": "Chemical Bonding",
     "jee": _side("The hybridisation of the central atom in the species shown is", ["sp3", "sp3d", "sp3d2", "sp3d3"], images=[{"url": "https://matched.test/q31.png", "w": 800, "h": 240}]),
     "ours": [_side("", images=[{"url": "https://matched.test/ours31.png", "w": None, "h": None}], source="Chapter test · Chemical Bonding · Q 14", tag="Same question")]},
    {"n": 58, "subject": "Mathematics", "chapter": "Quadratic Equations",
     "jee": _side("The sum of the roots of $x^2 - 5x + 6 = 0$ is ______.", answer="5"),
     "ours": [_side("The product of the roots of $x^2 - 5x + 6 = 0$ is", ["5", "6", "-5", "1"], correct=1, source="AITS Day 3 · Q 61", tag="Same concept"),
              _side("If the roots of $x^2 - px + 6 = 0$ add up to 5, then p is", ["5", "6", "-5", "1"], source="JEE Main PYQ practice · Q 12", tag="")]},
    {"n": None, "subject": "Physics", "chapter": "Units and Dimensions",
     "jee": _side("The dimensional formula of force is", ["MLT^-2", "ML^2T^-2", "MLT^-1", "ML^-1T^-2"]),
     "ours": [_side("The dimensional formula of impulse is", ["MLT^-2", "ML^2T^-2", "MLT^-1", "ML^-1T^-2"], source="AITS Day 20 · Q 2", tag="")]},
]


def _plain(n, subject, chapter):
    return {"n": n, "subject": subject, "chapter": chapter, "jee": _side(f"JEE Main question {n} of this shift, on {chapter}.", ["A1", "B1", "C1", "D1"]),
            "ours": [_side(f"Our question that matched question {n}, on {chapter}.", ["A2", "B2", "C2", "D2"], source=f"AITS Day {n % 50 + 1} · Q {n}", tag="Same concept")]}


ITEMS = {
    "2027-04-03-s1": [_plain(4, "Mathematics", "Limits"), _plain(66, "Chemistry", "Mole Concept")],
    "2027-01-25-s2": [_plain(12, "Mathematics", "Matrices"), _plain(29, "Physics", "Laws of Motion"), _plain(70, "Chemistry", "Solutions")],
    "2027-01-25-s1": JAN25_S1,
    "2027-01-24-s1": [_plain(40, "Physics", "Current Electricity")],
}
ASKED = {"2027-01-24-s1": None}
SHIFTS = {k: {**_summary(k, ASKED.get(k, 75), v), "items": v} for k, v in ITEMS.items()}
INDEX = {"total": sum(len(v) for v in ITEMS.values()), "updated_at": 1800000000, "shifts": [{k: v for k, v in s.items() if k != "items"} for s in SHIFTS.values()]}
EMPTY = {"total": 0, "updated_at": 0, "shifts": []}


async def fake_matched(page, on=True, index=INDEX, shifts=SHIFTS, status=None, asked=None):
    async def switches(route):
        try:
            response = await route.fetch()
            body = await response.json()
        except Exception:  # noqa: BLE001 - the stand-in must work whatever the server says
            body = {"pictures": 0}
        body["matched"] = on
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    async def lists(route):
        path = urlparse(route.request.url).path
        if asked is not None:
            asked.append(path)
        if status:
            await route.fulfill(status=status, content_type="application/json", body=json.dumps({"detail": "Matched is not answering."}))
            return
        key = path.rsplit("/", 1)[1]
        body = index if path.endswith("/api/matched") else shifts.get(key)
        if body is None:
            await route.fulfill(status=404, content_type="application/json", body=json.dumps({"detail": "This shift is not here."}))
            return
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    async def picture(route):
        await route.fulfill(status=200, content_type="image/png", body=_png(800, 240))

    await page.route("**/api/app/switches", switches)
    await page.route(re.compile(r".*/api/matched(/[^/?]+)?(\?.*)?$"), lists)
    await page.route("https://matched.test/**", picture)
