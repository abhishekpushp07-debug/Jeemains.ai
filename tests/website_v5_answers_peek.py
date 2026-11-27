# Read-only answers for the website's reply v5 questions (QA learner on LIVE: sign-in, then GETs only; one Mongo read).
# Writes /tmp/v5_peek.json (the 81 chapter tests with the app's class) and prints the rest.
import asyncio, json, os, sys, time, uuid, urllib.request
sys.path.insert(0, "/app/tests"); sys.path.insert(0, "/app/backend")
from shine_helpers import PHONE, PIN  # noqa: E402
import class_levels  # noqa: E402

B, SID = os.environ.get("BACKEND", "http://localhost:8001"), str(uuid.uuid4())

def call(path, body=None, base="/api/jl"):
    req = urllib.request.Request(B + base + path, data=None if body is None else json.dumps(body).encode(), method="GET" if body is None else "POST",
                                 headers={"Accept": "application/json", "Content-Type": "application/json", "X-JL-Sid": SID})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

mask = lambda t: t.replace(PHONE, "XXXXXX" + PHONE[-4:])
print("sign-in", call("/auth/phone", {"phone": PHONE, "pin": PIN})[0])

# 1. the name: auth/me and a leaderboard's `you`, in the same minute
t0 = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
s1, me = call("/auth/me")
s2, lb = call("/attempts/c0061f81-7ae9-432b-8ca5-312c8d39d4b5/leaderboard")
t1 = time.strftime("%H:%M:%S UTC", time.gmtime())
you = (json.loads(lb).get("data") or {}).get("you") if s2 == 200 else lb.decode()[:300]
print(f"\n[1] {t0} .. {t1}\nGET /api/auth/me -> {s1}\n{mask(me.decode())}\nleaderboard (PYQ 22 Jan 2026 S1) -> {s2}, you = {json.dumps(you)}")
uid = json.loads(me)["data"]["id"]

async def kept_name():
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv("/app/backend/.env")
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    return await db.rf_profiles.find_one({"uid": uid}, {"_id": 0, "chosen_name": 1, "display_name": 1})
print("app server's copy of the name (rf_profiles):", asyncio.run(kept_name()))

# 2. the 81 chapter tests with the app's class
rows = []
for subject in ["Physics", "Chemistry", "Mathematics"]:
    page = 1
    while True:
        s, raw = call(f"/exam-navigation/jee-main/catalogue?kind=chapters&subject={subject}&q=&page={page}")
        d = json.loads(raw).get("data") or {}
        for r in d.get("items") or []:
            rows.append({"id": r["id"], "title": r["title"], "subject": r.get("chapter_subject"), "chapter_number": r.get("chapter_number"),
                         "count": r.get("count"), "minutes": (r.get("rules") or {}).get("minutes"),
                         "app_class": class_levels.level_of("jee-main", r.get("chapter_subject") or subject, r["title"])})
        if page >= (d.get("pages") or 1):
            break
        page += 1
json.dump(rows, open("/tmp/v5_peek.json", "w"), indent=1)
print(f"\n[2] {len(rows)} chapter tests; by class:", {k: sum(1 for r in rows if (r['subject'], r['app_class']) == k) for k in sorted({(r['subject'], r['app_class']) for r in rows}, key=str)})

# 4. Dream and Mission on live, signed in
for path in ["/dream", "/mission/me"]:
    s, raw = call(path)
    print(f"\n[4] GET https://jeelive.ai/api{path} -> {s}\n{mask(raw.decode()[:700])}")
