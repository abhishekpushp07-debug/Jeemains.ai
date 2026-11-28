#!/usr/bin/env python3
"""Builds the app side's hand-off book (Student Choice, Matched, Misfire, Rapid Fire in a browser, one account, working
together) for the JE Live website agent and super admin.

    cd /app/handoff/feature_book && python3 build_book.py

Reads   parts/*.md (the text), examples/*.json (the JSON shown in it), shots/*.jpg (take_shots.py makes them).
Writes  BOOK.md (the whole text in one file), book.html, JEELIVE_Student_Choice_and_Matched_Book.pdf,
        and /app/handoff/JEELIVE_Student_Choice_and_Matched_Book.zip (PDF + BOOK.md + examples + shots).

So that the book cannot say something the app does not do:
  - every JSON example is run through the app server's own code (backend/choice.py, backend/matched.py);
  - the time tables are computed by backend/choice.py's own rule; the chapter table is the one in
    memory/WEBSITE_CHOICE_NOTE.md, checked against that rule (the ratio, three hours at most) row by row;
  - the state of production and of the website is read when the book is built.
Needs python-markdown, which is not one of the app server's packages:  pip install --target /tmp/mdlib markdown"""
import asyncio
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, "/tmp/mdlib")
sys.path.insert(0, str(BACKEND))
try:
    import markdown
    from markdown.extensions.toc import slugify
except ImportError:
    sys.exit("python-markdown is missing:  pip install --target /tmp/mdlib markdown")
from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")
import choice  # noqa: E402
import matched  # noqa: E402

NAME = "JEELIVE_Student_Choice_and_Matched_Book"
VERSION = "5"
PARTS = ["00_start", "10_choice_today", "11_choice_doors", "12_choice_rest", "20_matched_student", "21_matched_website", "22_matched_admin", "30_reference",
         "40_misfire", "41_misfire_offline", "42_misfire_mock", "50_rapid_fire", "60_one_account", "70_together"]
PDF, MD, ZIP = HERE / f"{NAME}.pdf", HERE / "BOOK.md", ROOT / "handoff" / f"{NAME}.zip"
IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(IST)
TODAY = f"{NOW.day} {NOW:%b %Y}"
PRODUCTION = "https://jeelive-mobile.emergent.host/api"
WEBSITE = "https://jeelive.ai/api"
SHORT = {"Physics": "Physics", "Chemistry": "Chemistry", "Mathematics": "Maths"}
PER = choice.MINUTES


def label(minutes: int) -> str:
    """The app's own way of writing a time (timeLabel in frontend/src/choice/api.ts)."""
    return f"{minutes // 60} hr" + (f" {minutes % 60} min" if minutes % 60 else "") if minutes >= 60 else f"{minutes} min"


def hours(minutes: int) -> str:
    return f"{minutes // 60} h {minutes % 60:02d} min"


def paper_minutes(p: int, c: int, m: int) -> int:
    return choice.minutes_for({s: n for s, n in (("Physics", p), ("Chemistry", c), ("Mathematics", m)) if n})


def split(n: int):
    """A random mock's split (splitOf in frontend/src/choice/api.ts): equally; what is left goes to Physics, then Chemistry."""
    return tuple(n // 3 + (1 if i < n % 3 else 0) for i in range(3))


def table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def time_table():
    rows = []
    for p, c, m in ((25, 25, 25), (10, 10, 10), (0, 0, 25), (25, 0, 0), (0, 25, 0), (5, 0, 0), (0, 1, 0), (1, 1, 1), (3, 2, 2), (20, 15, 10), (0, 0, 75)):
        words = " + ".join(f"{n} {SHORT[s]}" for s, n in (("Physics", p), ("Chemistry", c), ("Mathematics", m)) if n)
        parts = [f"{n * PER[s]:g}" for s, n in (("Physics", p), ("Chemistry", c), ("Mathematics", m)) if n]
        raw = p * PER["Physics"] + c * PER["Chemistry"] + m * PER["Mathematics"]
        total = paper_minutes(p, c, m)
        sums = (" + ".join(parts) + f" = {raw:g}" if len(parts) > 1 else f"{raw:g}") + (f", rounded up to {total}" if abs(raw - total) > 1e-9 else "")
        rows.append((words, sums, f"**{label(total)}**", (p + c + m) * 4))
    assert paper_minutes(25, 25, 25) == 180 and paper_minutes(10, 10, 10) == 72 and paper_minutes(3, 2, 2) == 17 and paper_minutes(0, 0, 25) == 80
    assert paper_minutes(0, 0, 75) == 240  # a made paper is not held at three hours (only a whole chapter test is)
    return table(["The paper", "Minutes its questions bring", "The paper's time", "Full marks"], rows)


def split_table():
    rows = []
    for n in (3, 4, 5, 10, 11, 15, 30, 31, 45, 50, 60, 74, 75):
        p, c, m = split(n)
        rows.append((n, p, c, m, label(paper_minutes(p, c, m)), n * 4))
    assert split(10) == (4, 3, 3) and split(11) == (4, 4, 3) and split(75) == (25, 25, 25)
    return '<div class="num" markdown="1">\n\n' + table(["`count`", "Physics", "Chemistry", "Mathematics", "The paper's time", "Full marks"], rows) + "\n\n</div>"


def chapters():
    """The 81 chapter-wise tests and their minutes by the owner's rule (the ratio, three hours at most), from the note
    to the website; every row is checked against the app server's own rule. A row: subject, number, title, questions,
    minutes by the rule, minutes by the ratio alone."""
    subject, rows = None, []
    for line in (ROOT / "memory" / "WEBSITE_CHOICE_NOTE.md").read_text().splitlines():
        head = re.match(r"\s+(Physics|Chemistry|Mathematics) \([\d.]+ minutes a question\)", line)
        if head:
            subject = head.group(1)
            continue
        row = re.match(r"\s+(\d+)\s+(.+?)\s+(\d+) questions\s+60 ->\s+(\d+) min(?:\s+\(the ratio alone: (\d+)\))?\s*$", line)
        if row and subject:
            count, minutes = int(row[3]), int(row[4])
            alone = choice.minutes_for({subject: count})
            assert minutes == choice.chapter_test_minutes(subject, count), (row[2], count, minutes)
            # A test held at three hours says what the ratio alone would give; no other row does.
            assert (int(row[5]) == alone > choice.TEST_MAX_MINUTES) if row[5] else alone <= choice.TEST_MAX_MINUTES, (row[2], alone, row[5])
            rows.append((subject, int(row[1]), row[2].strip(), count, minutes, alone))
    assert len(rows) == 81 and sum(r[3] for r in rows) == 3750, (len(rows), sum(r[3] for r in rows))
    assert [sum(1 for r in rows if r[0] == s) for s in choice.SUBJECTS] == [30, 24, 27]
    return rows


def chapter_table(rows):
    out = ['<div class="small num" markdown="1">', ""]
    for s in choice.SUBJECTS:
        mine = [r for r in rows if r[0] == s]
        out += [f'<div class="subject" markdown="1">', "", f"### {s}: {PER[s]} minutes a question ({len(mine)} tests, {sum(r[3] for r in mine)} questions)", "",
                table(["No.", "Chapter", "Questions", "Today", "By the rule"],
                      [(n, title, count, "60 min", f"**{minutes} min**" + (f" ({alone})" if alone > minutes else "")) for _, n, title, count, minutes, alone in mine]), "", "</div>", ""]
    return "\n".join(out + ["</div>"])


def ratio_facts(rows):
    held = sorted((r for r in rows if r[5] > r[4]), key=lambda r: -r[5])
    short = sorted((r for r in rows if r[4] < 60), key=lambda r: r[4])
    longer, same = sum(1 for r in rows if r[4] > 60), sum(1 for r in rows if r[4] == 60)
    big = sum(1 for r in rows if r[3] >= 68)
    assert max(r[4] for r in rows) == choice.TEST_MAX_MINUTES == 180 and len(held) == 7 and len(short) == 11
    facts = {"SHORTER_COUNT": str(len(short))}
    text = "\n".join([
        f"- Of the 81 tests, **{longer} get longer**, **{len(short)} get shorter**, and {'none stays' if not same else str(same) + ' stay'} at 60 minutes.",
        f"- **{len(held)} tests are held at 3 hours**; the ratio alone would give them more: " + "; ".join(f"{r[2]} ({hours(r[5])})" for r in held) + ".",
        "- **So no chapter test is longer than a full mock (180 minutes).** The student's session, the autosave and the attempt's picture links "
        "(`GET /attempts/<id>/assets/links`) need to last no longer than they already do for a full mock, plus the get-ready minute.",
        f"- **{len(short)} tests become shorter than today's 60 minutes:** " + "; ".join(f"{r[2]} {r[4]} min" for r in short) + ".",
        f"- {big} chapter tests have 68 questions or more. (These are the ones an older app version counted for the Dream College meter: Part 1.9.)",
    ])
    return text, facts


def check_examples():
    """Runs every example through the app server's own shaping code. Returns the shift as a phone would receive it."""
    read = lambda name: json.loads((HERE / "examples" / name).read_text())  # noqa: E731
    door_a = read("choice_door_A.json")
    bank = choice.shape_bank({**door_a, "subjects": [{"name": s, "chapters": [{"id": "chapter-" + s.lower(), "title": "A chapter", "count": 30}]} for s in choice.SUBJECTS]}, own=False)
    assert bank["pick"] is True and bank["random"] is True and bank["max_questions"] == 75 and bank["max_per_subject"] is None and bank["minutes"] == PER, bank
    closed = choice.shape_bank({"subjects": [{"name": "Physics", "chapters": [{"id": "chapter-physics", "title": "A chapter", "count": 30}]}]}, own=False)
    assert closed["pick"] is False and closed["random"] is False
    door_b = read("choice_door_B.json")
    chapter = choice.shape_chapter(door_b["chapter"]["id"], [door_b])
    assert chapter["total"] == len(door_b["items"]) == 2 and all(set(q) == {"id", "n", "type", "text", "stem"} for q in chapter["items"]), chapter
    assert chapter["items"][1]["stem"][0]["w"] == 506.5 and chapter["items"][1]["type"] == "integer"
    door_c = read("choice_door_C.json")
    assert all(re.match(matched.ID, door_c[k]["set_id"]) for k in ("answer_200_or_201",)) and matched.site_data(door_c["answer_in_the_envelope"])["set_id"] == door_c["answer_200_or_201"]["set_id"]
    listed = matched.site_rows(read("matched_list.json"))
    shift = read("matched_shift.json")
    shaped = matched.shape_shift({**shift, "_id": shift["id"]})
    assert shaped["matched"] == len(shift["items"]) == 3 and shaped["paper_questions"] == 4 and shaped["paper_id"] == shift["paper_id"] and shaped["asked"] == 75, shaped
    assert listed[shift["id"]] == shift["updated_at"] == shaped["updated_at"], "the list and the shift must carry the same updated_at"
    assert datetime.fromtimestamp(shift["updated_at"], IST).strftime("%Y-%m-%d") == shift["id"][:10]
    assert [s["n"] for s in shaped["subjects"]] == [1, 1, 1] and shaped["items"][0]["jee"]["correct"] == 1 and shaped["items"][0]["ours"][0]["correct"] == 1
    # The Misfire Mock (Part 4.8): the switch through the server's own rule, and the shapes the app sends and reads.
    ask_c, said = read("misfire_mock_ask.json"), read("misfire_mock_answers.json")
    one = {"subjects": [{"name": "Physics", "chapters": [{"id": "chapter-physics", "title": "A chapter", "count": 30}]}]}
    assert choice.shape_bank({**one, **said["door_A_with_only_the_misfire_mock_open"]}, own=False)["misfire"] is True and choice.shape_bank(one, own=False)["misfire"] is False
    shut = choice.shape_bank({**one, **said["door_A_with_only_the_misfire_mock_open"]}, own=False)
    assert shut["pick"] is False and shut["random"] is False  # Student Choice stays shut while only the Misfire Mock is open
    assert all(choice.misfire_on({"misfire": bad}) is False for bad in (False, "true", 1, None))
    assert ask_c["mode"] == "misfire" and ask_c["exam"] == "jee-main" and re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", ask_c["request_key"])
    assert set(ask_c["counts"]) == set(choice.SUBJECTS) and all(isinstance(n, int) and 0 <= n <= 25 for n in ask_c["counts"].values()) and sum(ask_c["counts"].values()) >= 1
    assert all(s in choice.SUBJECTS and ask_c["counts"][s] > 0 and names and all(isinstance(x, str) and x for x in names) for s, names in ask_c["chapters"].items())
    made = said["door_C_answer_200_or_201"]
    assert re.match(matched.ID, made["set_id"]) and 0 < made["given"] <= made["asked"] <= 75 and made["minutes"] > 0
    rows = said["my_misfire_mocks_page_1"]["items"]
    assert [r["created_at"] for r in rows] == sorted((r["created_at"] for r in rows), reverse=True) and rows[0]["attempt"] is None
    assert rows[1]["attempt"]["resumable"] is True and not rows[1]["attempt"]["summary"] and rows[2]["attempt"]["summary"]
    assert all(re.match(matched.ID, r["set_id"]) for r in rows) and said["my_misfire_mocks_page_1"]["pages"] >= 1
    m = said["result_adds"]
    assert m["test_kind"] == "misfire" and isinstance(m["misfire"]["understood"], int) and 0 <= m["misfire"]["understood"] <= m["misfire"]["total"]
    return shaped


def shaped_text(shaped):
    def cut(value):
        if isinstance(value, str):
            return value if len(value) <= 46 else value[:44].rstrip() + "…"
        if isinstance(value, list):
            return [cut(v) for v in value]
        if isinstance(value, dict):
            return {k: cut(v) for k, v in value.items()}
        return value
    head = json.dumps({k: v for k, v in shaped.items() if k != "items"}, ensure_ascii=False)
    second = json.dumps(cut(shaped["items"][1]), ensure_ascii=False, indent=2)
    second = "\n".join("    " + line for line in second.splitlines())
    return "```\n" + head[:-1] + ',\n  "items": [\n    … the first matched question …,\n' + second + ",\n    … the third matched question …\n  ]\n}\n```"


def ask(url):
    """(status, body) of a public read; ("no answer", "") when the build machine cannot reach it."""
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0 (JEELIVE book build)"})
    try:
        with urllib.request.urlopen(request, timeout=20) as res:
            return res.status, res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:  # noqa: BLE001 - a book can still be built without the network; the row then says so
        return "no answer", ""


def local_samples() -> dict:
    """The preview's made-up Matched shifts as {id: updated_at}: what must never be listed anywhere else."""
    from pymongo import MongoClient
    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=5000)
    try:
        return {d["_id"]: d.get("updated_at") for d in client[os.environ["DB_NAME"]].matched_shifts.find({"sample": True}, {"updated_at": 1})}
    finally:
        client.close()


PROD_NOTE = """<div class="box red" markdown="1">

### Production on {{TODAY}}: its database is not the real one

- The owner's Publish of 26 Nov 2026 (live at 14:40 UTC) was made from a **copy of the workspace**. It pointed production at a **copy of the preview's database** instead of production's own. (Read from the platform's own record of that Publish on 27 Nov 2026. No code of the app did this.)
- So production now holds the preview's test data, and **lists the preview's %(count)s made-up sample shifts as published** (%(ids)s). Home's Matched card is on because of them. **They are not real shifts.** The website has published nothing: its Matched doors are not built (Part 3.7).
- **The real production database was not deleted.** Putting it back is with the owner and the platform's support.
- **Built on the app side on 27 Nov 2026:** a server that is not the workspace's own never shows a sample and never follows the samples' own switch, whatever its database holds (Part 2.12). It reaches production with the next Publish.
- **Nothing for the website to do.** No student's `id` changed: the ids are the website's (Part 6).

</div>"""


def state():
    rows, facts = [], {}
    samples = local_samples()
    status, body = ask(PRODUCTION + "/matched")
    data = json.loads(body) if status == 200 else {}
    listed = data.get("shifts", [])
    leaked = [s["id"] for s in listed if s.get("id") in samples and s.get("updated_at") == samples[s["id"]]]
    real = len(listed) - len(leaked)
    switch_status, body = ask(PRODUCTION + "/app/switches")
    on = json.loads(body).get("matched") if switch_status == 200 else None
    rows.append(("The app's server in production: `GET /api/app/switches`", f'{switch_status}, `"matched": {json.dumps(on)}`' if switch_status == 200 else switch_status,
                 "Home shows the All India series card; no Matched bar on the sign-in screen" if on is False
                 else "Home shows the Matched card, **only because of the preview's samples** (Part 0.2)" if on and leaked and not real
                 else "Home shows the Matched card" if on else "not read"))
    rows.append(("The app's server in production: `GET /api/matched`", f'{status}, {len(listed)} shifts, {data.get("total", 0)} questions' if status == 200 else status,
                 "not read" if status != 200
                 else f"**{len(leaked)} of them are the preview's made-up samples, not real shifts** (Part 0.2); " + (f"{real} real shifts are published" if real else "no real shift is published") if leaked
                 else "shifts are published" if listed else "no shift is published in production"))
    facts["MATCHED_PROD"] = (f"In production **no real shift** is published; on {TODAY} it wrongly lists the preview's {len(leaked)} made-up samples (the red box under this table)" if leaked and not real
                             else "In production shifts are published" if listed else "In production the list is **empty** and the card is **off**")
    facts["CARD_PROD"] = ("**On in production, wrongly:** switched on by the preview's samples and by the samples' own switch, which came with them. With them gone it is off until the first real shift is published, "
                          "and on from **{{CARD_DAY}}** (India time) at the latest" if leaked and not real
                          else "**On in production**" if on
                          else "**Off in production:** no shift is published. They come on by themselves **when the first shift is published**, and on **{{CARD_DAY}}** (India time) at the latest")
    facts["CARD_WAITS"] = "the real database put back, or the next Publish (the red box under this table); then the first published shift (Part 2.6)" if leaked and not real else "the first published shift (Part 2.6)"
    facts["PROD_NOTE"] = PROD_NOTE % {"count": len(leaked), "ids": ", ".join(f"`{i}`" for i in sorted(leaked))} if leaked else ""
    facts["OWNER_PROD_LINE"] = ("**Sabse zaroori (production, {{TODAY}}):** 26 Nov ke Publish (14:40 UTC) ne production ko **preview ke database ki copy** par chala diya. Isliye students ko abhi preview ka test data dikh raha hai, "
                                f"aur Matched mein **{len(leaked)} banawati (sample) shifts** asli ki tarah dikh rahe hain. Asli database delete nahi hua; use wapas lagwana platform support ka kaam hai (Part 0.2 ka laal box). "
                                "App side par 27 Nov ko rok laga di gayi hai: workspace ke bahar sample kabhi nahi dikhega (agle Publish se)." if leaked
                                else "**Production:** is book ke bante waqt wahan koi banawati (sample) shift nahi mila.")
    facts["SAMPLES_PROD"] = ("**Production must have none of this. On {{TODAY}} it wrongly has it** (Part 0.2): a Publish made from a copy of the workspace pointed production at a copy of the preview's database, samples and switch included."
                             if leaked else "**Production has none of this** (checked, Part 3.7).")
    facts["OPEN_PROD"] = ("| 9 | **Production's database** (Part 0.2): putting the real one back; and how to publish from a copy of the workspace without changing the database | "
                          "with the owner and the platform's support. Until then production runs on a copy of the preview's database |" if leaked else "")
    status, _ = ask(PRODUCTION + "/choice/bank")
    rows.append(("The app's server in production: `GET /api/choice/bank`, signed out", status, "the door is there, for signed-in students only" if status == 401 else "not as expected"))
    for path, what in (("matched", "Matched: the list of shifts"), ("matched/2027-01-25-s1", "Matched: one shift"), ("choice/bank?exam=jee-main", "Student Choice: door A (asked signed out here; a signed-in student got 404 on 26 Nov 2026)")):
        status, _ = ask(f"{WEBSITE}/{path}")
        rows.append((f"The website: `GET /api/{path}`", status, f"{what}: not built yet" if status == 404 else f"{what}: the website answers; tell the app side"))
    status, body = ask(WEBSITE + "/series/all-india-jee")
    data = matched.site_data(json.loads(body)) if status == 200 else {}
    first, last = data.get("first_date"), data.get("last_date")
    assert isinstance(last, str) and matched.DAY.match(last), "the series' last day could not be read: the card's day cannot be written"
    day = lambda d: f"{d.day} {d:%b %Y}"  # noqa: E731
    end = datetime.strptime(last, "%Y-%m-%d")
    facts.update(SERIES_FIRST=day(datetime.strptime(first, "%Y-%m-%d")), SERIES_LAST=day(end), CARD_DAY=day(end + timedelta(days=1)))
    rows.append(("The website: `GET /api/series/all-india-jee`", f"{status}, {first} to {last}", f"with no shift published, Home's card turns to Matched on {facts['CARD_DAY']} (India time); a published shift turns it sooner, the switch at any time"))
    # Rapid Fire in a browser: the copy production serves, against the copy built here (the name of its entry file changes with every build).
    status, body = ask(PRODUCTION + "/arena")
    live = re.search(r"entry-[0-9a-f]+\.js", body) if status == 200 else None
    built = re.search(r"entry-[0-9a-f]+\.js", (BACKEND / "arena_web" / "index.html").read_text())
    newest = bool(live and built and live[0] == built[0])
    rows.append(("The app's server in production: `GET /api/arena` (Rapid Fire in a browser, Part 5)", status,
                 "the newest copy is live" if newest
                 else "an older copy is live; the copy built on the preview on 27 Nov 2026 comes with the owner's next Publish" if live else "not read"))
    # Its icon font: git never carried the folder the build kept it in, so production answered 404 for it (Part 5.2).
    font = next(m for m in (re.search(r'"/api/arena/(assets/node_modules/[^"]*MaterialDesignIcons\.[0-9a-f]+\.ttf)"', p.read_text(errors="replace"))
                            for p in sorted((BACKEND / "arena_web" / "_expo" / "static" / "js" / "web").glob("*.js"))) if m)[1]
    font_status, _ = ask(f"{PRODUCTION}/arena/{font}")
    rows.append(("The app's server in production: the icon font of Rapid Fire in a browser", font_status,
                 "the icons are drawn" if font_status == 200 else "**missing: its icons are empty boxes**, until the owner's next Publish (Part 5.2)" if font_status == 404 else "not read"))
    facts["ARENA_COPY"] = ("**Works** in production, from the newest copy (built on 27 Nov 2026)" if newest
                           else "**Works** in production, from the copy built on 26 Nov 2026 (with All India Rapid's \"Misfires\" tab; live since the Publish of that day). Built again on 27 Nov 2026 on the preview")
    facts["ARENA_ICONS"] = ("Its icons are drawn in production" if font_status == 200
                            else "**In production its icons are empty boxes** (the icon font never reached production; found and mended on the preview on 27 Nov 2026, Part 5.2)" if font_status == 404
                            else "Its icon font in production could not be read when this book was built")
    facts["ARENA_WAITS"] = "nothing; the website: a link (Part 5.3)" if newest and font_status == 200 else "the owner's next Publish; the website: a link (Part 5.3)"
    status, body = ask(WEBSITE + "/auth/session")
    try:
        session = json.loads(body) if status == 200 else {}
    except ValueError:
        session = {}
    inner = session.get("data", session) if isinstance(session.get("data", session), dict) else {}
    signed_out = status == 200 and "user" in inner and inner["user"] is None
    rows.append(("The website: `GET /api/auth/session`, signed out", f'{status}, `"user": null`' if signed_out else status,
                 "the website's sign-in doors answer; the app signs up and signs in only through them (Part 6)" if signed_out else "not as expected: tell the app side"))
    return table(["What was asked", "The answer", "What it means"], rows), facts


def tests_line():
    run = subprocess.run([sys.executable, "-m", "pytest", "tests/test_choice.py", "tests/test_matched.py", "tests/test_matched_sync.py", "tests/test_samples_stay_home.py", "-q"],
                         cwd=BACKEND, capture_output=True, text=True)
    passed = re.search(r"(\d+) passed", run.stdout)
    assert run.returncode == 0 and passed and passed[1] == "29", run.stdout[-800:]  # 12 + 6 + 5 + 6, as Part 3.6 says
    return f"all {passed[1]} pass on {TODAY}"


def doors_in_code():
    """Every door of the website that the app's screens name outright, as "GET /attempts/<id>/results": read from the
    app's own code (frontend/src and frontend/app), so that Part 7.2 cannot leave one out."""
    call = re.compile(r"(?<![\w.])(api|apiRaw|apiBytes|post|put|del)\s*(?:<[^>(]*>)?\(\s*([`\"'])(/[^`\"']*)\2")
    found = set()
    for folder in ("src", "app"):
        for f in sorted((ROOT / "frontend" / folder).rglob("*.ts*")):
            source = f.read_text()
            for m in call.finditer(source):
                method = {"post": "POST", "put": "PUT", "del": "DELETE"}.get(m[1], "GET")
                said = re.search(r"method:\s*[\"'](\w+)[\"']", source[m.end():m.end() + 160])
                if m[1] in ("api", "apiRaw") and said:
                    method = said[1]
                path = re.sub(r"\$\{[^}]+\}", "<id>", m[3]).split("?")[0]
                path = re.sub(r"(\.[a-z]{3})<id>$", r"\1", path)  # report.pdf${query}
                found.add(f"{method} {path + '<id>' if path.endswith('/') else path}")
    return sorted(found)


def check_doors():
    """Part 7.2 names every door found in the code, written the same way."""
    part = (HERE / "parts" / "70_together.md").read_text()
    code = doors_in_code()
    missing = [d for d in code if f"`{d}`" not in part]
    assert len(code) >= 40 and not missing, f"Part 7.2 does not name these doors of the app's code: {missing}"
    return str(len(re.findall(r"^\| `(?:GET|POST|PUT|DELETE) /", part[part.index("## 7.2"):part.index("## 7.3")], flags=re.M)))


def shots(line, as_html):
    figures = [tuple(x.strip() for x in part.split("|", 1)) for part in line.split(" ; ")]
    for name, _ in figures:
        assert (HERE / "shots" / f"{name}.jpg").exists(), name
    if not as_html:
        return "\n".join(f"- Picture `shots/{name}.jpg`: {caption}" for name, caption in figures)
    return '<div class="shots">' + "".join(f'<figure><img src="shots/{name}.jpg" alt=""><figcaption>{html.escape(caption, quote=False)}</figcaption></figure>' for name, caption in figures) + "</div>"


def text(as_html):
    rows = chapters()
    facts_text, facts = ratio_facts(rows)
    state_table, state_facts = state()
    values = {"TODAY": TODAY, "NOW": f"{NOW:%H:%M} India time on {TODAY}", "TIME_TABLE": time_table(), "SPLIT_TABLE": split_table(), "CHAPTER_TABLE": chapter_table(rows),
              "RATIO_FACTS": facts_text, "SHAPED_SHIFT": shaped_text(check_examples()), "STATE_TABLE": state_table, "TESTS_LINE": tests_line(), "DOOR_COUNT": check_doors(),
              **facts, **state_facts}
    body = "# Part 0 — Read this first\n\n" + "\n\n".join((HERE / "parts" / f"{p}.md").read_text().strip() for p in PARTS) + "\n"
    body = re.sub(r"\{\{file:([^}]+)\}\}", lambda m: "```json\n" + (HERE / m.group(1)).read_text().strip() + "\n```", body)
    # Twice: a value may hold another one (the tests line holds the day).
    for _ in range(2):
        body = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], body)
    body = re.sub(r"^\[\[shots: (.+)\]\]$", lambda m: shots(m.group(1), as_html), body, flags=re.M)
    assert "{{" not in body and "[[shots" not in body
    if not as_html:  # the one-file text: the boxes' wrappers are for the printed page only
        body = re.sub(r"^</?div[^>]*>\n\n?", "", body, flags=re.M)
    return body


def headings(body):
    out, fenced = [], False
    for line in body.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        found = None if fenced else re.match(r"^(#{1,2}) (.+)$", line)
        if found:
            out.append((len(found[1]), found[2]))
    return out


LEAD = ("The app side's final hand-off to jeelive.ai. The app's two new features, Student Choice and Matched: what a student sees, "
        "what the website has to build, what the super admin does after every JEE Main shift, every field, every limit, every sentence on screen. "
        "Then the three things that keep the website and the app one: Misfire (with Offline Misfire and the website's Misfire Mock, new in version 5), Rapid Fire in a browser, and one account. "
        "Then how the two sides work together: every door of the website the app uses, and how a change to one is agreed. And what has not been checked yet.")
TITLE = "Student Choice, Matched, Misfire, Rapid Fire and one account"


def cover(body):
    toc = "".join(f'<li class="{"part" if level == 1 else "sec"}"><a href="#{slugify(title, "-")}">{html.escape(title, quote=False)}</a></li>' for level, title in headings(body))
    strip = "".join(f'<img src="shots/{name}.jpg" alt="">' for name in ("s02_landing", "s08_chapter_tests", "m08_home_card", "x02_misfire_all", "a01_signin"))
    return (f'<section class="cover"><div class="brand">JEELIVE.AI</div><div class="eyebrow">App &rarr; website hand-off</div>'
            f'<div class="title">Student Choice, Matched, Misfire,<br>Rapid Fire and one account</div><p class="lead">{LEAD}</p>'
            f'<div class="meta"><span>FOR <b>the JE Live website agent</b></span><span>FOR <b>the JE Live super admin</b></span>'
            f'<span>WRITTEN <b>{TODAY}</b></span><span>VERSION <b>{VERSION}</b></span></div><div class="strip">{strip}</div>'
            f'<div class="toc-title">Contents</div><ul class="toc">{toc}</ul></section>')


FOOT = ('<div style="width:100%;font-family:Figtree,Arial,sans-serif;font-size:8px;color:#8C8C96;padding:0 48px;display:flex;justify-content:space-between">'
        f'<span>JEELIVE.AI &middot; {TITLE} &middot; v{VERSION} &middot; {TODAY}</span>'
        '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
README = f"""# {TITLE}: the website hand-off (v{VERSION}, {TODAY})

For the JE Live website agent and the JE Live super admin. Written by the app side from the app's code on {TODAY}.
Give the website agent `BOOK.md` (paste it into its chat) or the PDF. Nothing in it is a password, a key or a private link.

New in version 5 (28 Nov 2026). A reader who has version 4 needs only the box "New in version 5" at the start of Part 0:
- Part 4.7, Offline Misfire: Misfire's "Mock" tab is now "Offline Misfire", a practice mock of the student's own
  Misfire questions on the phone, also with no internet. Never a paper on the website; a right answer becomes
  "Samajh gaya" through the website's own Misfire doors when the line is back. Nothing for the website to build.
- Part 4.8, the Misfire Mock made by the website: built in the app and shut until door A says "misfire": true. What
  the website builds (door C mode "misfire", history kind=misfire, the result's "misfire" count), the JSON
  (examples/misfire_mock_*.json) and one question for the website.
- Rules 27 and 28 in Part 0.4; the new doors in Parts 7.2 and 7.5; the owner's Publish of 28 Nov 2026 in Part 0.2.

New in version 4 (27 Nov 2026):
- Where things stand after the owner's Publish of 26 Nov 2026 (Part 0.2), read when the book was built.
- Rapid Fire in a browser (Part 5.2): in production its icons are empty boxes, because its icon font never reached
  production. Found and mended on the app's preview on 27 Nov 2026; students get it with the owner's next Publish.
  The website has nothing to do. The same new copy rests its decoration and celebrations on a slow device.
- Part 7, working together: every door of the website the app uses (so that the website's own work never breaks the
  app unseen), how the app's server reaches the website, how a change to a door is agreed, and the doors the app
  already asks for.
- Two more rules in Part 0.4 (25 and 26). A made-up sample is never shown outside the app's own workspace (Part 2.12).

New in version 3 (the owner's later decisions of 26 Nov 2026):
- Student Choice's colours: a dark-red top card like the result page's, glossy subject tabs (Physics red, Chemistry amber,
  Maths teal); the cards below stay white. A made paper's subject minutes now add up to its time (Parts 1.2 and 1.7).
- Part 4, Misfire: the website's own, shown in the app; one calculation; six checks for the website agent.
- Part 5, Rapid Fire in a browser: the app's; the website only links to it. Its copy was built again with All India
  Rapid's "Misfires" tab. Rapid Fire's code was not changed.
- Part 6, one account: sign up on the website or in the app, sign in on both; what the website must keep.

New in version 2 (two decisions of the owner, 26 Nov 2026; both are on the app's preview and reach students with the next Publish):
- A whole chapter test follows the 80 / 60 / 40 ratio and is never longer than three hours (Part 1.8).
- Home's card turns to Matched as soon as the first shift is published; the All India series is a bar under it for its
  remaining days (Part 2.2 picture 10, Part 2.6).

- `{NAME}.pdf`: the book, with the app's screens. Start here.
- `BOOK.md`: the same text in one plain file, for pasting into the website project's chat.
- `examples/`: the JSON of the book's grey boxes. Every example was run through the app server's own code when the book was built.
- `shots/`: the pictures of the book (the app's web preview at a phone's size).

The Matched pictures show made-up sample shifts that exist on the app's preview only. The pictures of question picking and the random
mock show made-up questions marked "(Sample)": the website's doors for them do not exist yet.
"""


async def build():
    from playwright.async_api import async_playwright
    md_text = text(as_html=False)
    MD.write_text(f"# JEELIVE.AI — {TITLE}: the website hand-off\n\nFor the JE Live website agent and the JE Live super admin. "
                  f"Written by the app side on {TODAY}. Version {VERSION}.\n\n{LEAD}\n\n" + md_text)
    body = text(as_html=True)
    page_html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>JEELIVE.AI: {TITLE}, the website hand-off</title>'
                 '<link rel="stylesheet" href="book.css"></head><body>' + cover(body)
                 + markdown.markdown(body, extensions=["tables", "fenced_code", "md_in_html", "sane_lists", "toc"]) + "</body></html>")
    (HERE / "book.html").write_text(page_html)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 794, "height": 1123})
        await page.emulate_media(media="print")
        await page.goto((HERE / "book.html").as_uri(), wait_until="load")
        await page.evaluate("document.fonts.ready")
        broken = await page.evaluate("[...document.images].filter(i => !i.complete || !i.naturalWidth).length")
        dead = await page.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].filter(a => !document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)))).map(a => a.textContent)")
        assert not broken and not dead, (broken, dead)
        await page.pdf(path=str(PDF), width="210mm", height="297mm", print_background=True, display_header_footer=True,
                       header_template="<span></span>", footer_template=FOOT, margin={"top": "12mm", "bottom": "14mm", "left": "0", "right": "0"})
        await browser.close()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{NAME}/README.md", README)
        z.write(PDF, f"{NAME}/{PDF.name}")
        z.write(MD, f"{NAME}/BOOK.md")
        for folder in ("examples", "shots"):
            for f in sorted((HERE / folder).iterdir()):
                z.write(f, f"{NAME}/{folder}/{f.name}")
    pages = len(re.findall(rb"/Type\s*/Page[^s]", PDF.read_bytes()))
    print(f"wrote {PDF.name} ({PDF.stat().st_size // 1024} KB, {pages} pages), BOOK.md ({len(md_text.split())} words), {ZIP.name} ({ZIP.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    asyncio.run(build())
