"""JoSAA 2026 seat matrix -> backend/rank_data/jee_main_2026_seat_matrix.json  {program index: total seats}.

Source: josaa.admissions.nic.in/applicant/seatmatrix/seatmatrixinfo.aspx (NITs, IIITs, GFTIs; IITs are not in the app).
Total = every category cell of every quota row (gender-neutral + female-only) of the program.

Usage:  python build_seat_matrix.py fetch <raw_dir>    then    python build_seat_matrix.py build <raw_dir>
"""
import gzip, html, json, re, sys
from pathlib import Path

import build_rank_data as b

URL = "https://josaa.admissions.nic.in/applicant/seatmatrix/seatmatrixinfo.aspx"
OUT = Path(b.OUT).parent / "jee_main_2026_seat_matrix.json"
TYPES = ("NIT", "3IT", "CFI")


def _rows(h):
    """Rows of the seat matrix grid (its table id is plain GridView1 on this page)."""
    m = re.search(r'<table[^>]*id="[^"]*GridView1"[^>]*>(.*)</table>', h, re.S)
    out = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(1) if m else "", re.S):
        cells = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if cells:
            out.append(cells)
    return out


def fetch(raw):
    import requests
    raw.mkdir(parents=True, exist_ok=True)
    for t in TYPES:
        s = requests.Session()
        s.headers["User-Agent"] = "Mozilla/5.0"
        h = s.get(URL, timeout=60).text
        values = {b.P + "ddlInstType": t}
        h = s.post(URL, data={**b._hidden(h), **values, "__EVENTTARGET": b.P + "ddlInstType", "__EVENTARGUMENT": ""}, timeout=120).text
        values.update({b.P + "ddlInstitute": "0", b.P + "ddlBranch": "0"})
        h = s.post(URL, data={**b._hidden(h), **values, "__EVENTTARGET": "", "__EVENTARGUMENT": "", b.P + "btnSubmit": "Submit"}, timeout=300).text
        rows = _rows(h)
        json.dump(rows, open(raw / f"seatmatrix_{t}.json", "w"))
        print(t, len(rows))


def build(raw):
    data = json.load(gzip.open(b.OUT, "rt", encoding="utf-8"))
    inst_ix = {i["name"].lower(): n for n, i in enumerate(data["institutes"])}
    prog_ix = {(p["inst"], p["name"], p["degree"]): n for n, p in enumerate(data["programs"])}
    totals, missing = {}, set()
    for t in TYPES:
        inst = prog = None
        for row in json.load(open(raw / f"seatmatrix_{t}.json")):
            if row and row[0].startswith("Female-only") and inst:
                cats = row[1:11]
            elif len(row) >= 14:
                inst, prog, cats = row[0], row[1], row[4:14]
            else:
                continue
            i = inst_ix.get(b.norm(inst).lower())
            base, degree = b.split_program(prog)
            p = prog_ix.get((i, base, degree)) if i is not None and base is not None else None
            if p is None:
                missing.add((b.norm(inst), prog))
                continue
            totals[p] = totals.get(p, 0) + sum(int(c) for c in cats if c.strip().isdigit())
    json.dump({"source": URL, "year": 2026, "seats": {str(k): v for k, v in sorted(totals.items())}}, open(OUT, "w"))
    print("programs with seats", len(totals), "of", len(data["programs"]), "| unmatched rows", len(missing), "->", OUT)
    for m in sorted(missing)[:15]:
        print("  unmatched", m)


if __name__ == "__main__":
    step, raw = sys.argv[1], Path(sys.argv[2])
    fetch(raw) if step == "fetch" else build(raw)
