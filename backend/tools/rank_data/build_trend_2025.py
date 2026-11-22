"""Adds last year's (JoSAA 2025, final round) closing rank to the 2026 seats, for the Rank tab's 2025 vs 2026 trend.

Source: josaa.admissions.nic.in/applicant/seatmatrix/openingclosingrankarchieve.aspx (official archive).
Writes backend/rank_data/jee_main_2025_close.json.gz : [[prog, quota, cat, pwd, female, close], ...] keyed to the
2026 program ids, so it must be rebuilt whenever jee_main_2026.json.gz is rebuilt.

Usage:  python build_trend_2025.py fetch <raw_dir>   # about 2 minutes
        python build_trend_2025.py build <raw_dir>
"""
import gzip, json, re, sys
from pathlib import Path

from build_rank_data import P, QUOTA, SEAT, _hidden, _rows, norm, rank_value, split_program

ARCHIVE = "https://josaa.admissions.nic.in/applicant/seatmatrix/openingclosingrankarchieve.aspx"
DATA = Path(__file__).resolve().parents[2] / "rank_data"


def _options(h, name):
    m = re.search(r'<select[^>]*name="%s"[^>]*>(.*?)</select>' % re.escape(P + name), h, re.S)
    return [v for v, _ in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', m.group(1) if m else "")]


def fetch(raw):
    import requests
    raw.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    h = s.get(ARCHIVE, timeout=60).text
    values = {}

    def post(name, value):
        nonlocal h
        values[P + name] = value
        h = s.post(ARCHIVE, data={**_hidden(h), **values, "__EVENTTARGET": P + name, "__EVENTARGUMENT": ""}, timeout=180).text

    post("ddlYear", "2025")
    last = max(int(v) for v in _options(h, "ddlroundno") if v.isdigit())
    post("ddlroundno", str(last))
    for name in ("ddlInstype", "ddlInstitute", "ddlBranch", "ddlSeatType"):
        post(name, "ALL")
    h = s.post(ARCHIVE, data={**_hidden(h), **values, "__EVENTTARGET": "", "__EVENTARGUMENT": "", P + "btnSubmit": "Submit"}, timeout=300).text
    rows = _rows(h)
    json.dump({"round": last, "rows": rows}, open(raw / "josaa_2025_final.json", "w"))
    print("JoSAA 2025 round", last, "rows", len(rows))


def build(raw):
    data = json.load(gzip.open(DATA / "jee_main_2026.json.gz", "rt", encoding="utf-8"))
    inst_ix = {norm(i["name"]).lower(): n for n, i in enumerate(data["institutes"])}
    prog_ix = {(p["inst"], p["name"], p["degree"]): n for n, p in enumerate(data["programs"])}
    got = json.load(open(raw / "josaa_2025_final.json"))
    out, miss = {}, 0
    for row in got["rows"]:
        if len(row) < 7 or row[0] == "Institute":
            continue
        inst = inst_ix.get(norm(row[0]).lower())
        quota, seat = QUOTA.get(row[2]), SEAT.get(row[3])
        if inst is None or not quota or not seat:
            continue
        base, degree = split_program(row[1])
        prog = prog_ix.get((inst, base, degree))
        close = rank_value(row[6])
        if prog is None or not close:
            miss += prog is None
            continue
        out[(prog, quota, seat[0], seat[1], int(row[4].startswith("Female")))] = close
    rows = [list(k) + [v] for k, v in out.items()]
    with gzip.open(DATA / "jee_main_2025_close.json.gz", "wt", encoding="utf-8") as f:
        json.dump({"round": got["round"], "seats": rows}, f, separators=(",", ":"))
    print("2025 closing ranks matched", len(rows), "unmatched program rows", miss)


if __name__ == "__main__":
    step, raw = sys.argv[1], Path(sys.argv[2])
    fetch(raw) if step == "fetch" else build(raw)
