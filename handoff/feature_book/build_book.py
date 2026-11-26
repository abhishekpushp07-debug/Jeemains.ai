#!/usr/bin/env python3
"""Builds the book of Student Choice and Matched for the JE Live website agent and super admin.

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
VERSION = "2"
PARTS = ["00_start", "10_choice_today", "11_choice_doors", "12_choice_rest", "20_matched_student", "21_matched_website", "22_matched_admin", "30_reference"]
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


def state():
    rows, facts = [], {}
    status, body = ask(PRODUCTION + "/app/switches")
    on = json.loads(body).get("matched") if status == 200 else None
    rows.append(("The app's server in production: `GET /api/app/switches`", f'{status}, `"matched": {json.dumps(on)}`' if status == 200 else status,
                 "Home shows the All India series card; no Matched bar on the sign-in screen" if on is False else "Home shows the Matched card" if on else "not read"))
    status, body = ask(PRODUCTION + "/matched")
    data = json.loads(body) if status == 200 else {}
    rows.append(("The app's server in production: `GET /api/matched`", f'{status}, {len(data.get("shifts", []))} shifts, {data.get("total", 0)} questions' if status == 200 else status,
                 "no shift is published in production" if status == 200 and not data.get("shifts") else "shifts are published" if status == 200 else "not read"))
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
    return table(["What was asked", "The answer", "What it means"], rows), facts


def tests_line():
    run = subprocess.run([sys.executable, "-m", "pytest", "tests/test_choice.py", "tests/test_matched.py", "tests/test_matched_sync.py", "-q"], cwd=BACKEND, capture_output=True, text=True)
    passed = re.search(r"(\d+) passed", run.stdout)
    assert run.returncode == 0 and passed, run.stdout[-800:]
    return f"all {passed[1]} pass on {TODAY}"


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
              "RATIO_FACTS": facts_text, "SHAPED_SHIFT": shaped_text(check_examples()), "STATE_TABLE": state_table, "TESTS_LINE": tests_line(), **facts, **state_facts}
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


LEAD = ("Everything about the app's two new features, for the two people who have to make them work on jeelive.ai: what a student sees, "
        "what the website has to build, what the super admin does after every JEE Main shift, every field, every limit, every sentence on screen, "
        "and what has not been checked yet.")


def cover(body):
    toc = "".join(f'<li class="{"part" if level == 1 else "sec"}"><a href="#{slugify(title, "-")}">{html.escape(title, quote=False)}</a></li>' for level, title in headings(body))
    strip = "".join(f'<img src="shots/{name}.jpg" alt="">' for name in ("s02_landing", "s05_search", "s08_chapter_tests", "m08_home_card", "m03_shift_top"))
    return (f'<section class="cover"><div class="brand">JEELIVE.AI</div><div class="eyebrow">App &rarr; website hand-off</div>'
            f'<div class="title">Student Choice and Matched:<br>the complete book</div><p class="lead">{LEAD}</p>'
            f'<div class="meta"><span>FOR <b>the JE Live website agent</b></span><span>FOR <b>the JE Live super admin</b></span>'
            f'<span>WRITTEN <b>{TODAY}</b></span><span>VERSION <b>{VERSION}</b></span></div><div class="strip">{strip}</div>'
            f'<div class="toc-title">Contents</div><ul class="toc">{toc}</ul></section>')


FOOT = ('<div style="width:100%;font-family:Figtree,Arial,sans-serif;font-size:8px;color:#8C8C96;padding:0 48px;display:flex;justify-content:space-between">'
        f'<span>JEELIVE.AI &middot; Student Choice and Matched: the complete book &middot; v{VERSION} &middot; {TODAY}</span>'
        '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
README = f"""# Student Choice and Matched: the complete book (v{VERSION}, {TODAY})

For the JE Live website agent and the JE Live super admin. Written by the app side from the app's code on {TODAY}.

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
    MD.write_text(f"# JEELIVE.AI — Student Choice and Matched: the complete book\n\nFor the JE Live website agent and the JE Live super admin. "
                  f"Written by the app side on {TODAY}. Version {VERSION}.\n\n{LEAD}\n\n" + md_text)
    body = text(as_html=True)
    page_html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>JEELIVE.AI: Student Choice and Matched, the complete book</title>'
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
