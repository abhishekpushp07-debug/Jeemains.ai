import json, time
ls = json.loads(open('/tmp/jl_ls.json').read())
await page.add_init_script("localStorage.setItem('jl_sid', %s); localStorage.setItem('jl_user', %s);" % (json.dumps(ls['sid']), json.dumps(ls['user'])))
B = "https://rapid-fire-208--04cp9c5d.preview.emergentagent.com"
NOW = int(time.time())
SUBJ = ['Physics','Physics','Chemistry','Chemistry','Mathematics','Mathematics','Mathematics']
QS = []
for i, s in enumerate(SUBJ):
    n = i + 1
    q = {"id": f"fxq{n}", "number": n, "subject": s, "type": "mcq", "text": f"Fixture question {n} ({s}): which option is correct?", "options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "asset_count": 0}
    if n == 7:
        q = {"id": "fxq7", "number": 7, "subject": s, "type": "integer", "text": "Fixture integer question 7: enter an integer.", "asset_count": 0}
    QS.append(q)
ATT = {"id": "fx-tablet", "title": "Fixture paper", "status": "active", "server_now": NOW, "deadline": NOW + 3600, "rules": {"correct": 4, "wrong": -1}, "answers": {}, "visited": [], "questions": QS}
PUTS = []
async def guard(route):
    r = route.request
    if r.method != "GET":
        print("ABORT", r.method, r.url[-70:]); await route.abort(); return
    await route.continue_()
async def fx(route):
    r = route.request
    u = r.url.split('?')[0]
    if r.method == "GET" and u.endswith("/attempts/fx-tablet"):
        ATT["server_now"] = int(time.time())
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(ATT)); return
    if r.method == "POST" and u.endswith("/attempts/fx-tablet/visit"):
        await route.fulfill(status=200, content_type="application/json", body="{}"); return
    if r.method == "PUT" and "/attempts/fx-tablet/answers/" in u:
        body = json.loads(r.post_data or "{}")
        PUTS.append(body)
        acc = {"value": body.get("value", ""), "marked": body.get("marked", False), "revision": 1}
        await route.fulfill(status=200, content_type="application/json", body=json.dumps({"accepted": acc, "current_revision": 1, "server_now": int(time.time())})); return
    if r.method != "GET":
        print("ABORT-FX", r.method, u[-60:]); await route.abort(); return
    await route.continue_()
await page.route("**/api/jl/**", guard)
await page.route("**/attempts/fx-tablet**", fx)
GEOM = """() => {
  const box = s => { const e=document.querySelector(`[data-testid="${s}"]`); if(!e) return null; const b=e.getBoundingClientRect(); return [Math.round(b.left),Math.round(b.top),Math.round(b.width),Math.round(b.height)]; };
  const vis = s => { const e=document.querySelector(`[data-testid="${s}"]`); return !!(e && e.getBoundingClientRect().width>0); };
  const sideQ = document.querySelectorAll('[data-testid^="side-q-"]').length;
  return {vw: innerWidth, screen: box('player-screen'), reading: box('question-reading-surface'), qtext: box('player-question-text'), timer: box('player-timer'), submitTop: box('player-submit-top'), progress: box('player-progress'), mark: box('player-mark-button'), next: box('player-next-button'), prev: box('player-prev-button'), paletteBtn: vis('player-palette-button'), side: box('player-side-panel'), sideLabel: document.querySelector('[data-testid="side-palette-label"]')?.textContent, sideQ, optA: box('player-option-A'), docW: document.documentElement.scrollWidth};
}"""
