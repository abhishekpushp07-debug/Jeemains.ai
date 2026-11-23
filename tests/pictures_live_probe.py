"""Is the website's new picture way live on jeelive.ai?  READ-ONLY check with the owner's test number.

Run:  python /app/tests/pictures_live_probe.py
It signs in through the app's own server (the way a phone does), opens one FINISHED attempt, and looks at every answer
the app's new picture code depends on (memory/PICTURES_APP.md, memory/WEBSITE_PICTURES_REPLY_2.md). It never starts,
answers or submits anything, never prints a part link, a cookie or the PIN, and signs out at the end.
Exit code 0 = every new answer is there (the switch in backend/app_switches.py may be turned on); 1 = not yet."""
import json
import os
import struct
import sys
import uuid
from pathlib import Path

import requests

BASE = ""
for line in Path("/app/frontend/.env").read_text().splitlines():
    if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
        BASE = line.split("=", 1)[1].strip().strip('"').rstrip("/")
WEBSITE = "https://jeelive.ai"
PHONE, PIN = "7004186276", "5524"
sid = "PROBE" + uuid.uuid4().hex
H = {"X-JL-Sid": sid}
checks = []


def check(name, ok, seen=""):
    checks.append(ok)
    print(f"{'YES' if ok else 'NO '}  {name}{'  [' + str(seen) + ']' if seen != '' else ''}")


def data_of(r):
    body = r.json()
    return body["data"] if isinstance(body, dict) and "data" in body and isinstance(body.get("meta"), dict) else body


def kind_of(b):
    return "png" if b[:2] == b"\x89P" else "webp" if b[:4] == b"RIFF" and b[8:12] == b"WEBP" else "jpeg" if b[:2] == b"\xff\xd8" else "other"


def read_part(b):
    n = struct.unpack(">I", b[:4])[0]
    header = json.loads(b[4:4 + n])
    at, pictures = 4 + n, []
    for item in header["items"]:
        pictures.append((item, b[at:at + item["size"]]))
        at += item["size"]
    return header, pictures


def main():
    s = requests.Session()
    r = s.post(f"{BASE}/api/jl/auth/phone", json={"phone": PHONE, "pin": PIN}, headers=H, timeout=30)
    if r.status_code != 200:
        print("sign-in failed", r.status_code)
        return 2
    try:
        r = s.get(f"{BASE}/api/jl/my/tests", params={"tab": "completed", "page": "1", "q": "", "status": "all", "exam": ""}, headers=H, timeout=30)
        items = data_of(r).get("items") or []
        attempt = rows = None
        for item in items:  # the first finished attempt whose result is released and has solution pictures
            for key in ("attempt_id", "id", "latest_attempt_id"):
                if not isinstance(item.get(key), str):
                    continue
                res = s.get(f"{BASE}/api/jl/attempts/{item[key]}/results", params={"score_version": "original"}, headers=H, timeout=60)
                if res.status_code != 200:
                    continue
                result = data_of(res)
                qs = result.get("questions") or []
                if result.get("summary") and result.get("status") != "embargoed" and any(q.get("solution_asset_count") for q in qs):
                    attempt, rows = item[key], qs
                    break
            if attempt:
                break
        if not attempt:
            print("no finished attempt with released solutions found on the test account")
            return 2
        print(f"attempt {attempt[:8]}…  {len(rows)} questions, {sum(q.get('asset_count') or 0 for q in rows)} question pictures, "
              f"{sum(q.get('solution_asset_count') or 0 for q in rows)} solution pictures")
        base = f"{BASE}/api/jl/attempts/{attempt}"

        # 1. asset_revision on every row, the same in the paper answer and the result answer
        revs = [q.get("asset_revision") for q in rows]
        check("asset_revision on every result row", all(isinstance(v, str) and v for v in revs), f"{sum(1 for v in revs if v)}/{len(revs)}")
        paper = s.get(base, headers=H, timeout=60)
        if paper.status_code == 200:
            mine = {q["id"]: q.get("asset_revision") for q in rows}
            theirs = {q["id"]: q.get("asset_revision") for q in data_of(paper).get("questions") or []}
            both = [k for k in mine if k in theirs]
            check("the same asset_revision in GET /attempts/{id}", bool(both) and all(mine[k] and mine[k] == theirs[k] for k in both), f"{len(both)} rows compared")

        # 2. one-picture route: ETag, 304 / 206, format=webp
        q = next(q for q in rows if q.get("asset_count") and q.get("solution_asset_count"))
        for kind in ("question", "solution"):
            one = f"{base}/questions/{q['id']}/asset/{kind}/0"
            png = s.get(one, headers={**H, "Accept": "image/png,image/*"}, timeout=60)
            etag = png.headers.get("etag", "")
            check(f"{kind}: 200 with a strong ETag", png.status_code == 200 and etag.startswith('"'), f"{png.status_code} {kind_of(png.content)} {len(png.content)} B")
            if etag:
                again = s.get(one, headers={**H, "Accept": "image/png,image/*", "Range": "bytes=0-0", "If-None-Match": etag, "If-Range": etag}, timeout=60)
                check(f"{kind}: the app's re-check answers 304 (or 206 with the same ETag)", again.status_code == 304 or (again.status_code == 206 and again.headers.get("etag") == etag),
                      f"{again.status_code} {len(again.content)} B")
            webp = s.get(one, params={"format": "webp"}, headers={**H, "Accept": "image/png,image/*"}, timeout=60)
            light = kind_of(webp.content)
            check(f"{kind}: format=webp answers a picture with its own ETag", webp.status_code == 200 and light in ("webp", "png") and bool(webp.headers.get("etag")) and
                  (light == "png" or webp.headers.get("etag") != etag), f"{light} {len(webp.content)} B, header says {webp.headers.get('content-type')}, {round(100 * len(webp.content) / max(1, len(png.content)))} % of the PNG")
            check(f"{kind}: private, no-store", "no-store" in png.headers.get("cache-control", ""), png.headers.get("cache-control", ""))

        # 3. parts for the finished attempt, questions and solutions
        for name, words, flag in (("questions", {"format": "webp"}, 4), ("solutions", {"kind": "solution", "format": "webp"}, 8)):
            links = s.get(f"{base}/assets/links", params=words, headers=H, timeout=60)
            if links.status_code != 200:
                check(f"links for {name} of a finished attempt", False, links.status_code)
                pack = s.get(f"{base}/assets/pack", params={"offset": 0, "limit": 12, **words}, headers=H, timeout=60)
                check(f"pack for {name} of a finished attempt", pack.status_code == 200, pack.status_code)
                continue
            body = data_of(links)
            parts = body.get("parts") or []
            flags = [int(p.rsplit("/", 1)[-1].split("-")[2]) for p in parts]
            check(f"links for {name}: 200, limit 12, flags carry {flag}", body.get("limit") == 12 and bool(parts) and all(f & flag for f in flags), f"total {body.get('total')}, {len(parts)} parts, flags {sorted(set(flags))}")
            if not parts:
                continue
            got = requests.get(parts[0] if parts[0].startswith("http") else WEBSITE + parts[0], timeout=60)  # no cookies, as the phone does
            check(f"first {name} part opens without sign-in", got.status_code == 200, f"{got.status_code}, {len(got.content)} B, cache-control {got.headers.get('cache-control', '')[:40]}, cf {got.headers.get('cf-cache-status', '-')}")
            if got.status_code != 200:
                continue
            header, pictures = read_part(got.content)
            kinds = sorted({item.get("kind") or "question" for item, _ in pictures})
            wanted = ["solution"] if name == "solutions" else [k for k in kinds if k in ("question", "piece")]
            check(f"{name} part: every item is of the kind asked for", kinds == wanted and bool(kinds), kinds)
            check(f"{name} part: every item carries an etag", all(isinstance(item.get("etag"), str) and item["etag"] for item, _ in pictures), f"{len(pictures)} items")
            types = sorted({kind_of(b) for _, b in pictures})
            check(f"{name} part: pictures are WebP or PNG", all(t in ("webp", "png") for t in types), types)
            item, picture = pictures[0]
            route = "solution" if name == "solutions" else "piece" if item.get("kind") == "piece" else "question"
            one = s.get(f"{base}/questions/{item['question_id']}/asset/{route}/{item['index']}", params={"format": "webp"},
                        headers={**H, "If-None-Match": '"' + str(item.get("etag", "")).strip('"') + '"'}, timeout=60)
            check(f"{name} part: the item's etag is the one-picture route's ETag (304)", one.status_code == 304, one.status_code)
    finally:
        s.post(f"{BASE}/api/jl/auth/logout", headers=H, timeout=30)
    live = bool(checks) and all(checks)
    print("\nNEW PICTURE ANSWERS ON jeelive.ai:", "ALL THERE" if live else "NOT YET (the app keeps loading pictures the old way)")
    return 0 if live else 1


if __name__ == "__main__":
    sys.exit(main())
