# Finished papers kept on the phone, in a browser (27 Nov 2026): after sign-in the app fetches the results of the papers
# the student has FINISHED (JEE Main first, then BITSAT, then the rest) with their pictures in the website's parts of 12,
# keeps them in the account's encrypted store (512 MB, the oldest-used copy gives way first), and opens them from the
# phone on a weak line and with no line at all. Signing out removes them.
#   python3 /app/tests/offline_papers_check.py           the app (web preview), 390 x 844
#   python3 /app/tests/offline_papers_check.py small     the same on a 360 x 640 phone
# The QA learner is the owner's real account, so NOTHING is written for it and no paper is started: every call the
# keeper makes is a GET. Any write under /api/jl outside /auth is listed; one that touches an attempt, a start or the
# profile is stopped as well (there must be none).
# "No line" is made by the browser: every call to /api/jl, /api/rf, /api/app and to the picture CDN is cut.
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
SMALL = "small" in sys.argv[1:]
W, H = (360, 640) if SMALL else (390, 844)
TAG = "papers" + ("_small" if SMALL else "")
OUT = Path("/tmp/offline_runs"); OUT.mkdir(exist_ok=True)
RULES = ("Rendered more hooks", "Rendered fewer hooks", "order of Hooks", "Cannot update a component", "Maximum update depth", "state update on an unmounted", "Each child in a list")
MB = 1024 * 1024
checks = []
keeper = {"t": time.time(), "list": [], "results": [], "links": [], "pack": [], "cdn": [], "one": []}  # what was asked, with the second it was asked
got = {"list": None, "results": {}, "parts": set(), "hosts": set(), "owner": {}, "empty": {}, "full": {}}  # empty / full: parts per attempt that brought no picture / pictures
written = []

T = """(id) => { const el = document.querySelector(`[data-testid="${id}"]`); return el ? (el.innerText || '').replace(/[\\u{F0000}-\\u{FFFFD}]/gu, '').trim().replace(/\\s*\\n\\s*/g, ' ') : null; }"""
ROWS = """() => [...document.querySelectorAll('[data-testid^="kept-row-score-"]')].map((el) => ({ id: el.dataset.testid.slice(15),
  whole: /Solutions aur pictures phone par/.test(document.querySelector(`[data-testid="kept-row-pictures-${el.dataset.testid.slice(15)}"]`)?.innerText || ''),
  pictures: document.querySelector(`[data-testid="kept-row-pictures-${el.dataset.testid.slice(15)}"]`)?.innerText || '', score: el.innerText.replace(/\\s+/g, ' ').trim() }))"""
STORE = """() => new Promise((resolve) => { const r = indexedDB.open('jeelive-private-images-v1'); r.onerror = () => resolve(null);
  r.onsuccess = () => { const db = r.result; if (!db.objectStoreNames.contains('catalog')) { db.close(); resolve(null); return; }
    const tx = db.transaction(['images', 'catalog'], 'readonly'), images = tx.objectStore('images').count(), all = tx.objectStore('catalog').getAll();
    tx.oncomplete = () => { db.close(); resolve({ images: images.result, copies: all.result.length, bytes: all.result.reduce((n, e) => n + e.size, 0), ids: all.result.filter((e) => String(e.id).startsWith('test-')).map((e) => e.id) }); }; }; })"""
SEED = """(limit) => new Promise((resolve) => { const r = indexedDB.open('jeelive-private-images-v1');
  r.onsuccess = () => { const db = r.result, tx = db.transaction('catalog', 'readwrite'), s = tx.objectStore('catalog'), all = s.getAll();
    all.onsuccess = () => { const real = all.result.reduce((n, e) => n + e.size, 0), over = limit - real + 40 * 1024 * 1024;
      const a = Math.floor(over * 0.4), b = Math.floor(over * 0.4), c = over - a - b;
      s.put({ id: 'test-oldest', size: a, used: 1 }); s.put({ id: 'test-older', size: b, used: 2 }); s.put({ id: 'test-old', size: c, used: 3 });
      tx.oncomplete = () => { db.close(); resolve({ real, copies: all.result.length, a, b, c }); }; }; }; })"""
UNSEED = """() => new Promise((resolve) => { const r = indexedDB.open('jeelive-private-images-v1');
  r.onsuccess = () => { const db = r.result, tx = db.transaction('catalog', 'readwrite'), s = tx.objectStore('catalog');
    for (const id of ['test-oldest', 'test-older', 'test-old']) s.delete(id); tx.oncomplete = () => { db.close(); resolve(true); }; }; })"""
# The first two pictures of a question are taken out of the store, as if they had given way to newer things
# (the app's own key of a picture: src/assets/assetGrants.ts `pictureKeys`; its name in the store: SHA-256 of that key).
GIVE_WAY = """async (q) => {
  const pieces = Array.isArray(q.pieces) && q.pieces.length ? q.pieces : null, kind = pieces ? 'piece' : 'question';
  const count = pieces ? pieces.length : Number(q.asset_count) || 0, ids = [];
  for (let i = 0; i < Math.min(2, count); i++) {
    const key = JSON.stringify([q.id, kind, i, 'original', count, q.asset_revision ?? q.source_revision ?? q.source_ref ?? null, ...(pieces ? [pieces[i].part, pieces[i].w, pieces[i].h] : [])]);
    const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key));
    ids.push([...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, '0')).join(''));
  }
  return new Promise((resolve) => { const r = indexedDB.open('jeelive-private-images-v1');
    r.onsuccess = () => { const db = r.result, tx = db.transaction(['images', 'catalog'], 'readwrite'), had = ids.map((id) => tx.objectStore('catalog').count(id));
      for (const id of ids) { tx.objectStore('images').delete(id); tx.objectStore('catalog').delete(id); }
      tx.oncomplete = () => { db.close(); resolve(had.map((h) => h.result)); }; }; });
}"""
# Every picture inside the open solution card: drawn (decoded, with a size), still loading, or failed.
PICTURES = """() => { const card = document.querySelector('[data-testid="kept-solution-card"]'); if (!card) return null;
  const imgs = [...card.querySelectorAll('img')];
  return { drawn: imgs.filter((i) => i.complete && i.naturalWidth > 0).length, all: imgs.length,
    waiting: card.querySelectorAll('[data-testid$="-loading"]').length, failed: card.querySelectorAll('[data-testid$="-retry"], [data-testid$="-error"]').length }; }"""
NUMBERS = """() => [...document.querySelectorAll('[data-testid^="kept-question-"]')].map((el) => el.dataset.testid).filter((t) => /^kept-question-\\d+$/.test(t)).map((t) => Number(t.slice(14)))"""


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""), flush=True)


async def text(page, test_id):
    return await page.evaluate(T, test_id)


def rank(exam):
    return 0 if re.search("jee", exam or "", re.I) else 1 if re.search("bitsat", exam or "", re.I) else 2


def number(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def finished(items):
    """The app's own reading of the list (src/offline/papers.ts `finished`)."""
    rows = [t for t in items if isinstance(t.get("id"), str) and t["id"] and not t.get("resumable") and t.get("result_available") is not False
            and (t.get("status") in ("completed", "expired") or t.get("result_available") is True)]
    return sorted(rows, key=lambda t: (rank(t.get("exam")), -number(t.get("submitted_at"))))


def inner(body):
    """The website's answers come wrapped: {"data": ..., "meta": {"api_version": ...}}."""
    return body["data"] if isinstance(body, dict) and "data" in body and isinstance(body.get("meta"), dict) and body["meta"].get("api_version") else body


def without_pictures():
    """Attempts whose parts were asked for and brought no picture: the website's picture store did not answer for them."""
    asked = {m.group(1) for _, path in keeper["links"] for m in [re.match(r"/attempts/([^/]+)/", path)] if m}
    return {i for i in asked if not got["full"].get(i)}


def watch(page):
    def on_request(req):
        url = req.url
        if "/api/jl/" in url:
            path = url.split("/api/jl", 1)[1]
            now = time.time()
            if path.startswith("/my/tests?") and "tab=completed" in path and req.method == "GET":
                keeper["list"].append(now); keeper["t"] = now
            m = re.match(r"/attempts/([^/]+)/results\?score_version=original", path)
            if m:
                keeper["results"].append((now, m.group(1))); keeper["t"] = now
            if re.match(r"/attempts/[^/]+/assets/links", path):
                keeper["links"].append((now, path)); keeper["t"] = now
            if re.match(r"/attempts/[^/]+/assets/pack", path):
                keeper["pack"].append((now, path)); keeper["t"] = now
            if re.search(r"/asset/(question|solution|piece)/\d+", path):
                keeper["one"].append((now, path))
        elif any(url == p or url.endswith(p) for p in got["parts"]):
            keeper["cdn"].append((time.time(), url)); keeper["t"] = time.time()
            got["hosts"].add(urlparse(url).hostname)

    async def on_response(res):
        url = res.url
        if res.status != 200:
            return
        if "/api/jl/" not in url:
            part = next((p for p in got["parts"] if url == p or url.endswith(p)), None)
            if part:
                try:
                    body = await res.body()
                    n = int.from_bytes(body[:4], "big")
                    kind = "full" if json.loads(body[4:4 + n]).get("items") else "empty"
                    got[kind][got["owner"][part]] = got[kind].get(got["owner"][part], 0) + 1
                except Exception:
                    pass
            return
        path = url.split("/api/jl", 1)[1]
        try:
            if path.startswith("/my/tests?") and "tab=completed" in path and "page=1" in path:
                got["list"] = inner(await res.json())
            m = re.match(r"/attempts/([^/]+)/results\?score_version=original", path)
            if m:
                got["results"][m.group(1)] = inner(await res.json())
            m = re.match(r"/attempts/([^/]+)/assets/links", path)
            if m:
                for part in inner(await res.json()).get("parts") or []:
                    got["parts"].add(part)
                    got["owner"][part] = m.group(1)
        except Exception:
            pass

    def done(req):
        if any(req.url == p or req.url.endswith(p) for p in got["parts"]) or "/assets/pack" in req.url:
            keeper["t"] = time.time()

    page.on("request", on_request)
    page.on("response", lambda res: asyncio.ensure_future(on_response(res)))
    page.on("requestfinished", done)


async def guard(route):
    req = route.request
    path = req.url.split("/api/jl", 1)[1].split("?")[0]
    if req.method in ("GET", "HEAD", "OPTIONS") or path.startswith("/auth/"):
        await route.fallback()
        return
    written.append(f"{req.method} {path}")
    if re.search(r"/attempts|/start|/profile", path):
        await route.abort()
    else:
        await route.fallback()


async def cut(route):
    await route.abort()


async def quiet(page, seconds=30, limit=900):
    """Waits until the keeper has asked for nothing for `seconds`."""
    start = time.time()
    while time.time() - start < limit:
        if time.time() - keeper["t"] >= seconds:
            return True
        await page.wait_for_timeout(1000)
    return False


async def drawn(page, limit=20):
    """Waits until every picture of the open question is drawn; says what the card holds."""
    seen = None
    for _ in range(limit * 2):
        seen = await page.evaluate(PICTURES)
        if seen and not seen["waiting"] and seen["drawn"] == seen["all"]:
            return seen
        await page.wait_for_timeout(500)
    return seen


def pictures_of(q):
    pieces = q.get("pieces") or []
    return (len(pieces) if pieces else int(q.get("asset_count") or 0)), int(q.get("solution_asset_count") or 0)


async def read_paper(page, result, where):
    """The kept result screen in view, against what the website said for it."""
    s = result["summary"]
    said = (await text(page, "kept-result-score") or "").replace(" ", "")
    check(f"{where}: the score, the counts and the title are the website's", said == f"{s['score']}/{s['maximum']}".replace(" ", "")
          and str(s["correct"]) in (await text(page, "kept-result-correct") or "") and str(s["incorrect"]) in (await text(page, "kept-result-incorrect") or "")
          and str(s["skipped"]) in (await text(page, "kept-result-skipped") or "") and (result.get("title") or "") in (await text(page, "kept-result-header") or ""), said)
    numbers = await page.evaluate(NUMBERS)
    subjects = []
    for q in result["questions"]:
        name = (q.get("subject") or "").strip() or "Uncategorised"
        if name not in subjects:
            subjects.append(name)
    first = [q for q in result["questions"] if ((q.get("subject") or "").strip() or "Uncategorised") == subjects[0]]
    # the rail draws the numbers near the open question only (a long list is not drawn whole)
    check(f"{where}: the rail starts with the first subject's questions, in order", len(numbers) >= min(8, len(first)) and numbers == [q["number"] for q in first][:len(numbers)], f"{len(numbers)} drawn of {len(first)}")
    bad, total = [], 0
    for q in first[:6]:
        await page.click(f'[data-testid="kept-question-{q["number"]}"]')
        await page.wait_for_timeout(250)
        seen = await drawn(page)
        want = sum(pictures_of(q))
        total += want
        key = await text(page, "kept-answer-key")
        if not seen or seen["failed"] or seen["waiting"] or seen["drawn"] != seen["all"] or (want and not seen["all"]) or not key:
            bad.append((q["number"], seen, want))
    check(f"{where}: six questions open with every picture drawn from the phone, and the answer key", not bad and total > 0, bad[:3] or f"{total} pictures")
    if len(subjects) > 1:
        last = subjects[-1]
        await page.click(f'[data-testid="kept-subject-{re.sub("[^a-z0-9]+", "-", last.lower())}"]')
        await page.wait_for_timeout(400)
        rows = [q for q in result["questions"] if ((q.get("subject") or "").strip() or "Uncategorised") == last]
        seen = await drawn(page)
        numbers = await page.evaluate(NUMBERS)
        check(f"{where}: another subject ({last}) opens the same way", len(numbers) >= min(8, len(rows)) and numbers == [q["number"] for q in rows][:len(numbers)] and seen and not seen["failed"] and not seen["waiting"] and seen["drawn"] == seen["all"]
              and (seen["all"] or not sum(pictures_of(rows[0]))), seen)


async def main():
    limit = int(requests.get(BASE + "/api/app/switches", timeout=20).json().get("keep") or 0)
    source = Path("/app/frontend/src/assets/deviceCache/types.ts").read_text()
    check("A0 the owner's switch is on, and the store's limit is 512 MB", limit > 0 and "DISK_BUDGET = 512 * 1024 * 1024" in source, f"keep={limit}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": W, "height": H})
        page = await context.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" and any(r in m.text for r in RULES) else None)
        watch(page)
        await page.route(re.compile(r".*/api/jl/.*"), guard)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W, height=H)
        started = time.time()

        # A. The first run, by itself, while the student is on Home
        for _ in range(180):
            if keeper["results"]:
                break
            await page.wait_for_timeout(1000)
        check("A1 the keeper starts by itself after sign-in", bool(keeper["results"]) and bool(got["list"]), f"{round(time.time() - started)} s after Home")
        await quiet(page)
        items = (got["list"] or {}).get("items") or []
        print("   the list's first row:", {k: (v if not isinstance(v, (dict, list)) else "…") for k, v in (items[0] if items else {}).items()}, flush=True)
        want = finished(items)
        asked = [i for _, i in keeper["results"]]
        check("A2 only finished papers, in the owner's order (JEE Main, then BITSAT, then the rest; newest first), at most the switch's number", asked == [t["id"] for t in want[:limit]] and len(asked) > 0,
              f"{len(asked)} of {len(want)} listed; exams {[t.get('exam') for t in want[:limit]]}")
        gaps = [round(b[0] - a[0], 1) for a, b in zip(keeper["results"], keeper["results"][1:])]
        check("A3 one paper every few seconds, never all at once", all(g >= 3.5 for g in gaps), gaps)
        check("A4 the pictures came in the website's parts only: not one picture was asked for by itself", keeper["one"] == [] and len(keeper["links"]) > 0 and len(keeper["cdn"]) + len(keeper["pack"]) > 0,
              f"links {len(keeper['links'])}, CDN parts {len(keeper['cdn'])}, parts through our server {len(keeper['pack'])}, one by one {len(keeper['one'])}")
        check("A5 nothing was written for the QA learner, no paper was started", not [w for w in written if re.search(r"/attempts|/start|/profile", w)], written[:6])
        store = await page.evaluate(STORE)
        check("A6 the copies are in the account's encrypted store", store and store["copies"] > len(asked) and store["images"] == store["copies"] and store["bytes"] < 512 * MB, store and f"{store['copies']} copies, {round(store['bytes'] / MB, 1)} MB")
        await page.wait_for_timeout(1500)
        away = without_pictures()  # papers whose parts came back without a single picture (or did not come at all)
        links = {i: sum(1 for _, path in keeper["links"] if f"/attempts/{i}/" in path) for i in away}
        # one part from the CDN (answered without pictures), or that part once more through our server when the CDN did not answer
        parts = {i: got["empty"].get(i, 0) + sum(1 for _, path in keeper["pack"] if f"/attempts/{i}/" in path) for i in away}
        names = [got["results"][i].get("title") for i in away if i in got["results"]]
        check("A7 a paper whose pictures the website is not giving just now costs one part, not all of them", all(n <= 2 for n in parts.values()) and all(got["empty"].get(i, 0) <= 1 for i in away) and all(n == 1 for n in links.values()),
              (f"{len(away)} such papers now: {names}; parts {sorted(parts.values())}, links {sorted(links.values())}") if away else "the website gave every paper's pictures")
        first_run = {k: len(keeper[k]) for k in ("list", "results", "links", "pack", "cdn")}

        # B. The app is opened again: what is kept is not fetched again, what was left is fetched now
        await page.goto(BASE + "/offline/results", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="kept-results-list"]', timeout=60000)
        for _ in range(60):
            if len(keeper["list"]) > first_run["list"]:
                break
            await page.wait_for_timeout(1000)
        await quiet(page)
        again = [i for _, i in keeper["results"][first_run["results"]:]]
        check("B1 opened again: only the papers the first run left are fetched", again == [t["id"] for t in want[limit:limit * 2]], f"{len(again)} more")
        await page.wait_for_function(f"""() => document.querySelectorAll('[data-testid^="kept-row-score-"]').length >= {min(len(want), limit * 2)}""", timeout=30000)
        rows = await page.evaluate(ROWS)
        check("B2 the list on the phone: every kept paper, in the same order, with its score", [r["id"] for r in rows] == [t["id"] for t in want[:limit * 2]]
              and all(str(got["results"][r["id"]]["summary"]["score"]) in r["score"] for r in rows), f"{len(rows)} rows")
        away = without_pictures()
        check("B3 every paper whose pictures the website gave has all of them on the phone; the others say how many they have", all(r["whole"] == (r["id"] not in away) for r in rows)
              and all(re.match(r"0 / \d+ pictures phone par", r["pictures"]) for r in rows if r["id"] in away), f"{sum(r['whole'] for r in rows)} whole, {len(away)} without pictures: {[r['pictures'] for r in rows if not r['whole']][:5]}")
        await page.screenshot(path=str(OUT / f"{TAG}_1_list.jpeg"), type="jpeg", quality=45)
        store = await page.evaluate(STORE)
        print(f"   on the phone now: {store['copies']} copies, {round(store['bytes'] / MB, 1)} MB for {len(rows)} papers", flush=True)

        # C. The 512 MB limit: the store is made to look 40 MB too full with three old stand-in copies (sizes only);
        #    the next thing written must push out the OLDEST of them, and nothing newer.
        seeded = await page.evaluate(SEED, 512 * MB)
        second_run = {k: len(keeper[k]) for k in ("list", "results", "links", "pack", "cdn")}
        await page.goto(BASE + "/offline/results", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="kept-results-list"]', timeout=60000)
        after = None
        for _ in range(90):
            after = await page.evaluate(STORE)
            if after and "test-oldest" not in after["ids"]:
                break
            await page.wait_for_timeout(1000)
        check("C1 over 512 MB: the oldest-used copy gave way, the newer ones and every real copy stayed", after and after["ids"] == ["test-old", "test-older"] and after["copies"] >= seeded["copies"] + 2
              and after["bytes"] <= 512 * MB, after and f"{round((seeded['real'] + seeded['a'] + seeded['b'] + seeded['c']) / MB)} MB before, {round(after['bytes'] / MB)} MB after, left {after['ids']}")
        await quiet(page, 10)
        check("C2 a third opening fetches no paper and no picture again", len(keeper["results"]) == second_run["results"] and len(keeper["cdn"]) == second_run["cdn"] and len(keeper["pack"]) == second_run["pack"]
              and len(keeper["list"]) > second_run["list"], {k: len(keeper[k]) - second_run[k] for k in second_run})
        await page.evaluate(UNSEED)
        rows = await page.evaluate(ROWS)
        check("C3 and the list is as it was", [r["id"] for r in rows] == [t["id"] for t in want[:limit * 2]] and all(r["whole"] == (r["id"] not in away) for r in rows), len(rows))

        # C4. Real copies give way: the first two pictures of one whole paper are taken out of the store. The next
        #     opening must notice (it looks at a few pictures of every paper, asks the server nothing) and say so.
        victim = [r["id"] for r in rows if r["whole"]][-1]
        first_q = got["results"][victim]["questions"][0]
        had = await page.evaluate(GIVE_WAY, first_q)
        before = {k: len(keeper[k]) for k in ("results", "links", "pack", "cdn")}
        await page.goto(BASE + "/offline/results", wait_until="domcontentloaded")
        await page.wait_for_selector(f'[data-testid="kept-row-pictures-{victim}"]', timeout=60000)
        try:
            await page.wait_for_function(f"""() => /^\\d+ \\/ \\d+ pictures phone par/.test(document.querySelector('[data-testid="kept-row-pictures-{victim}"]')?.innerText || '')""", timeout=60000)
        except Exception:
            pass
        said = await text(page, f"kept-row-pictures-{victim}")
        m = re.match(r"(\d+) / (\d+) pictures phone par", said or "")
        check("C4 copies that gave way are noticed: the list says how many pictures that paper has now", had == [1, 1] and bool(m) and int(m.group(2)) - int(m.group(1)) == 2, f"{said}; taken out {had}")
        await quiet(page, 10)
        check("C5 and nothing is fetched back at once (a full phone would only push something else out): tried again after 6 hours", all(len(keeper[k]) == before[k] for k in before), {k: len(keeper[k]) - before[k] for k in before})
        rows = await page.evaluate(ROWS)

        # D. A kept result, opened from the phone while on the line
        pick = next((r["id"] for r in rows if r["whole"] and any(sum(pictures_of(q)) for q in got["results"][r["id"]]["questions"])), rows[0]["id"])
        one = len(keeper["one"])
        await page.click(f'[data-testid="kept-row-{pick}"]')
        await page.wait_for_selector('[data-testid="kept-solution-card"]', timeout=30000)
        await read_paper(page, got["results"][pick], "D on the line")
        check("D4 and not one picture was asked of the server for it", len(keeper["one"]) == one, len(keeper["one"]) - one)
        await page.screenshot(path=str(OUT / f"{TAG}_2_kept_result.jpeg"), type="jpeg", quality=45)

        # E. The result screen itself, on a weak line and on a dead one: the kept copy is offered
        hold = {"how": "slow"}

        async def results_line(route):
            if hold["how"] == "slow":
                await asyncio.sleep(9)
                try:
                    await route.fallback()
                except Exception:
                    pass
            else:
                await route.abort()

        await page.route(re.compile(rf".*/api/jl/attempts/{pick}/results.*"), results_line)
        await page.goto(BASE + f"/result/{pick}", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="result-screen"]', timeout=60000)
        t0 = time.time()
        await page.wait_for_selector('[data-testid="kept-offer-open"]', timeout=8000)
        took = time.time() - t0
        check("E1 a weak line: after about 2.5 seconds the kept copy is offered, before the result has answered", took <= 6 and not await page.locator('[data-testid="result-tab-analysis"]').count(), round(took, 1))
        await page.screenshot(path=str(OUT / f"{TAG}_3_offer.jpeg"), type="jpeg", quality=45)
        await page.click('[data-testid="kept-offer-open"]')
        await page.wait_for_selector('[data-testid="kept-solution-card"]', timeout=20000)
        s = got["results"][pick]["summary"]
        check("E2 and it opens at once from the phone", (await text(page, "kept-result-score") or "").replace(" ", "") == f"{s['score']}/{s['maximum']}".replace(" ", ""), await text(page, "kept-result-score"))
        hold["how"] = "dead"
        await page.goto(BASE + f"/result/{pick}", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="result-error"]', timeout=90000)
        check("E3 a dead line: the error and the kept copy's offer, side by side", await page.locator('[data-testid="kept-offer-open"]').count() == 1, await text(page, "result-error"))
        hold["how"] = "slow"
        await page.unroute(re.compile(rf".*/api/jl/attempts/{pick}/results.*"), results_line)
        t0 = time.time()
        await page.goto(BASE + f"/result/{pick}", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="result-tab-analysis"]', timeout=60000)
        check("E4 on a good line the result screen is what it always was: no offer", not await page.locator('[data-testid="kept-offer"]').count(), f"result on screen {round(time.time() - t0, 1)} s after the page was asked for")

        # F. No line at all: the door, the phone's list, a whole result with its pictures
        hosts = {h for h in got["hosts"] if h}

        no_line = re.compile(r".*/api/(jl|rf|app)/.*")

        def cdn(url):
            return urlparse(url).hostname in hosts

        await page.route(no_line, cut)
        await page.route(cdn, cut)
        one = len(keeper["one"])
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="offline-door-button"]', timeout=75000)
        await page.click('[data-testid="offline-door-button"]')
        await page.wait_for_selector('[data-testid="offline-results-open"]', timeout=20000)
        await page.screenshot(path=str(OUT / f"{TAG}_4_offline_home.jpeg"), type="jpeg", quality=45)
        await page.click('[data-testid="offline-results-open"]')
        await page.wait_for_function(f"""() => document.querySelectorAll('[data-testid^="kept-row-score-"]').length >= {len(rows)}""", timeout=30000)
        offline_rows = await page.evaluate(ROWS)
        check("F1 no line: the door leads to the phone's results, all of them", [r["id"] for r in offline_rows] == [r["id"] for r in rows], len(offline_rows))
        await page.click(f'[data-testid="kept-row-{pick}"]')
        await page.wait_for_selector('[data-testid="kept-solution-card"]', timeout=30000)
        await read_paper(page, got["results"][pick], "F no line")
        check("F5 nothing had to be asked for: every picture was on the phone", len(keeper["one"]) == one, len(keeper["one"]) - one)
        await page.screenshot(path=str(OUT / f"{TAG}_5_no_line_result.jpeg"), type="jpeg", quality=45)
        # a result that has not been opened once yet (the Mission card's lock) stays shut here too
        other = next((r["id"] for r in rows if r["id"] != pick), None)
        if other:
            await page.evaluate("(k) => localStorage.setItem(k, 'true')", f"share_gate.{other}")
            await page.click('[data-testid="kept-result-back"]')
            await page.wait_for_selector(f'[data-testid="kept-row-{other}"]', timeout=20000)
            await page.click(f'[data-testid="kept-row-{other}"]')
            await page.wait_for_selector('[data-testid="kept-result-locked"]', timeout=20000)
            check("F6 a result still behind its share card is not opened from the phone either", not await page.locator('[data-testid="kept-solution-card"]').count(), "")
            await page.evaluate("(k) => localStorage.removeItem(k)", f"share_gate.{other}")
        await page.unroute(cdn, cut)
        await page.unroute(no_line, cut)

        # G. Signing out removes every kept result and picture from the phone
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="account-offline-results"]', timeout=60000)
        await page.wait_for_function(f"""() => /{len(rows)} results phone par/.test(document.querySelector('[data-testid="account-offline-results"]')?.innerText || '')""", timeout=30000)
        check("G1 Account says how many results the phone keeps", True, await text(page, "account-offline-results"))
        await page.screenshot(path=str(OUT / f"{TAG}_6_account.jpeg"), type="jpeg", quality=45)
        await page.click('[data-testid="account-signout-button"]')
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=45000)
        await page.wait_for_timeout(2500)
        gone = await page.evaluate(STORE)
        check("G2 signed out: the phone holds no result and no picture any more", gone is not None and gone["images"] == 0 and gone["copies"] == 0, gone)
        await page.route(no_line, cut)
        await page.goto(BASE + "/offline/results", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="kept-results-empty"]', timeout=60000)
        check("G3 and the phone's results are shut", "Pehle ek baar internet" in (await text(page, "kept-results-empty") or "") and not await page.locator('[data-testid^="kept-row-"]').count(), await text(page, "kept-results-empty"))
        await page.unroute(no_line, cut)

        # I. A result opened on screen is kept at once, with no call of its own (another browser, with nothing kept;
        #    the keeper's list is cut here, so whatever the phone keeps afterwards was kept by the result screen)
        other = await browser.new_context(viewport={"width": W, "height": H})
        page2 = await other.new_page()
        page2.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" and any(r in m.text for r in RULES) else None)
        asked = []
        page2.on("request", lambda req: asked.append(req.url.split("/api/jl", 1)[1]) if f"/api/jl/attempts/{pick}/results" in req.url else None)
        await page2.route(re.compile(r".*/api/jl/.*"), guard)
        await page2.route(re.compile(r".*/api/jl/my/tests\?.*tab=completed.*"), cut)
        await page2.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page2, width=W, height=H)
        await page2.goto(BASE + f"/result/{pick}", wait_until="domcontentloaded")
        await page2.wait_for_selector('[data-testid="result-tab-analysis"]', timeout=60000)
        await page2.wait_for_timeout(20000)  # the result screen's own parts bring the pictures meanwhile
        await page2.goto(BASE + "/offline/results", wait_until="domcontentloaded")
        await page2.wait_for_selector(f'[data-testid="kept-row-{pick}"]', timeout=60000)
        mine = await page2.evaluate(ROWS)
        check("I1 a result opened on screen is on the phone at once, asked for once", [r["id"] for r in mine] == [pick] and len(asked) == 1, f"{mine[0]['pictures'] if mine else ''}; asked {len(asked)} time(s)")
        await page2.click(f'[data-testid="kept-row-{pick}"]')
        await page2.wait_for_selector('[data-testid="kept-solution-card"]', timeout=30000)
        seen = await drawn(page2)
        s = got["results"][pick]["summary"]
        check("I2 and it opens from the phone with its pictures", (await text(page2, "kept-result-score") or "").replace(" ", "") == f"{s['score']}/{s['maximum']}".replace(" ", "") and seen and seen["all"] > 0
              and seen["drawn"] == seen["all"] and not seen["failed"], seen)
        await other.close()

        check("H1 nothing was written for the QA learner in the whole walk", not [w for w in written if re.search(r"/attempts|/start|/profile", w)], written[:8])
        check("H2 no React rule was broken", errors == [], errors[:3])
        await browser.close()
    print(f"\n{sum(checks)}/{len(checks)} passed ({TAG})")
    sys.exit(0 if all(checks) else 1)


asyncio.run(main())
