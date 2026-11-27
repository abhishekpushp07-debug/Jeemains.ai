# Paste into the screenshot tool (page = the app's preview). READ-ONLY: signs the owner's test number in, opens ONE finished
# result, looks at the Solutions tab and prints what the app asked the website for (no link, cookie or PIN is printed).
# Used after each picture step (backend/app_switches.py) to see the step working on jeelive.ai.
import re
import time
BASE = "https://revise-offline--6pwtbzuy.preview.emergentagent.com"
ATT = "1ea510f2-1d2a-41f7-9bb4-a8b28c16f98f"
await page.set_viewport_size({"width": 390, "height": 844})
log = []
def seen(resp):
    try:
        url = resp.url
        if "/api/" not in url:
            return
        path = url.split("/api/", 1)[1]
        if path.startswith("media/pack/"):
            name = path.rsplit("/", 1)[-1].split("-")
            path = f"PART offset {name[0]} flags {name[2]}"
        log.append((time.time(), path, resp.status, (resp.headers.get("content-type") or "").split(";")[0], int(resp.headers.get("content-length") or 0), resp.headers.get("cf-cache-status") or ""))
    except Exception as e:
        print("log error", repr(e))
page.on("response", seen)
try:
    await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=60000)
    await page.wait_for_timeout(2500)
    await page.evaluate("new Promise(r => { const q = indexedDB.deleteDatabase('jeelive-private-images-v1'); q.onsuccess = q.onerror = q.onblocked = () => r(1); })")
    for sel, val in (('[data-testid="entry-phone-input"]', "7004186276"), ('[data-testid="entry-pin-input"]', "5524")):
        await page.click(sel); await page.keyboard.type(val, delay=60)
        if not (await page.input_value(sel)):
            await page.fill(sel, val)
    await page.wait_for_timeout(600)
    await page.click('[data-testid="entry-continue-button"]', force=True)
    await page.wait_for_url(lambda u: "/entry" not in u, timeout=30000)
    await page.wait_for_timeout(2500)
    print("signed in:", page.url.replace(BASE, ""))
except Exception as e:
    print("SIGN-IN FAILED", repr(e))
picture = re.compile(r"jl/attempts/[^/]+/questions/[^/]+/asset/(question|solution|piece)/\d+(\?.*)?$")
def report(since, title):
    rows = [r for r in log if r[0] >= since]
    ones = [r for r in rows if picture.search(r[1])]
    parts = [r for r in rows if r[1].startswith("PART")]
    print(f"--- {title} ---")
    for r in rows:
        if "app/switches" in r[1] or "/assets/links" in r[1] or "/assets/pack" in r[1]:
            print("  ", r[2], r[1].split("attempts/")[-1][37:] if "attempts/" in r[1] else r[1], r[3])
    for kind in ("question", "solution", "piece"):
        mine = [r for r in ones if f"/asset/{kind}/" in r[1]]
        if mine:
            webp = [r for r in mine if "format=webp" in r[1]]
            print(f"   one by one, {kind}: {len(mine)} calls ({len(webp)} with format=webp), statuses {sorted(set(r[2] for r in mine))}, types {sorted(set(r[3] for r in mine))}, {sum(r[4] for r in mine) // 1024} KB")
    if parts:
        print(f"   parts: {len(parts)} fetched, flags {sorted(set(r[1].split()[-1] for r in parts))}, statuses {sorted(set(r[2] for r in parts))}, {sum(r[4] for r in parts) // 1024} KB, edge {sorted(set(r[5] for r in parts))}")
    last = max([r[0] for r in ones + parts], default=since)
    print(f"   picture traffic: {len(ones) + len(parts)} requests, {(sum(r[4] for r in ones) + sum(r[4] for r in parts)) // 1024} KB, last one {last - since:.1f} s after opening")
async def quiet(limit=75):
    start = time.time()
    while time.time() - start < limit:
        n = len(log)
        await page.wait_for_timeout(4000)
        if len(log) == n:
            return
async def shown(prefix, wait=30000):
    sel = f'[data-testid^="{prefix}"][data-testid$="-bitmap"]'
    t = time.time()
    await page.wait_for_selector(sel, timeout=wait)
    ok = await page.evaluate("""sel => new Promise(done => { const tick = n => { const all = [...document.querySelectorAll(sel + ' img, img' + sel)]; if ((all.length && all.every(i => i.complete && i.naturalWidth > 0)) || n > 80) done(all.map(i => i.naturalWidth + 'x' + i.naturalHeight)); else setTimeout(() => tick(n + 1), 100); }; tick(0); })""", sel)
    return ok, time.time() - t
try:
    t0 = time.time()
    await page.goto(f"{BASE}/result/{ATT}")
    await page.wait_for_selector('[data-testid="result-tab-solutions"]', timeout=90000)
    await page.click('[data-testid="result-tab-solutions"]', force=True)
    q, tq = await shown("solution-qimage-")
    s, ts = await shown("solution-simage-")
    print(f"first question picture drawn {q} after {time.time() - t0:.1f} s; its solution {s}")
    await quiet()
    report(t0, "opening the result (new phone: nothing kept)")
    t1 = time.time()
    await page.click('[data-testid="solution-question-7"]', force=True)
    await page.wait_for_selector('[data-testid^="solution-qimage-7-"][data-testid$="-bitmap"]', timeout=30000)
    q7, t7 = await shown("solution-qimage-7-")
    s7, u7 = await shown("solution-simage-7-")
    print(f"question 7 drawn {q7} in {t7:.2f} s, its solution {s7} in {u7:.2f} s")
    await page.wait_for_timeout(1500)
    report(t1, "jumping to question 7")
    errors = await page.evaluate("document.querySelectorAll('[data-testid$=\"-error\"]').length")
    print("picture error boxes on screen:", errors)
    await page.screenshot(path="/tmp/pictures_step.jpg", quality=20, full_page=False)
except Exception as e:
    print("RESULT CHECK FAILED", repr(e))
    report(0, "everything seen")
