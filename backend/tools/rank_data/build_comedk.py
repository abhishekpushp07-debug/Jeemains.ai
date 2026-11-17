"""Builds backend/rank_data/comedk_2026.json, the only data the Rank tab's COMEDK part reads.

Sources (all official, comedk.org -> Counselling Documents 2026):
  * Engineering cut-off ranks after Round 1, 2, 3 and 4 (final) allotment, 2026 (GM and KKR, college x course)
  * 2025 Engineering cut-off ranks after all rounds (for the 2025 vs 2026 trend)
  * Engineering final seat availability and fee before Round 1, 2026 (seats GM / KKR, fees)
  * Marks vs rank: COMEDK publishes no table; MARKS_RANK below is the public 2026 analysis (estimate), typed in.

Usage:  python build_comedk.py fetch <raw_dir>
        python build_comedk.py build <raw_dir>
Needs `requests` and `pdfplumber` (build-time only).
"""
import json, re, sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "rank_data" / "comedk_2026.json"
U = "https://www.comedk.org/uploads/"
FILES = {
    "r1": "Engineering_Round-1_Cutoff_Ranks.%20Notified_on_27.07.2026.pdf",
    "r2": "Engineering_Cut_Off_Ranks_after_Round_2_Allotment__Notified_on_07_08_2026.pdf",
    "r3": "Engineering-Cut-off-Ranks-after-Round-3-Allotment%20Notified-on-18.08.2026.pdf",
    "r4": "Engineering-Cut-Off-Ranks-after-Round-4-Allotment-Notified-on%20-01.09.2026.pdf",
    "y25": "2025-Engineering%20Cut-Off%20Ranks-After-All-Rounds.%20Notified-on-07.07.2026.pdf",
    "fee": "Engineering-Final-Seat-Availability%20&%20Fee-before-start-of-Round-1.%20Notified-on-14.07.2026.pdf",
}
ROUNDS = ["r1", "r2", "r3", "r4"]


def fetch(raw):
    import requests
    raw.mkdir(parents=True, exist_ok=True)
    for k, f in FILES.items():
        (raw / f"{k}.pdf").write_bytes(requests.get(U + f, timeout=120, headers={"User-Agent": "Mozilla/5.0"}).content)
        print("got", k)


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\n", " ")).strip()


def course_of(head):
    m = re.match(r"^([A-Z]{2,4})\s*-\s*(.+)$", clean(head))
    return (m.group(1), m.group(2)) if m else (None, None)


def parse_cutoffs(pdf_path):
    """College x course matrix -> {(college, course, cat): rank}, plus names seen."""
    import pdfplumber
    out, colleges, courses = {}, {}, {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or not table[0] or "College" not in clean(table[0][0]):
                    continue
                heads = [course_of(h) for h in table[0]]
                for row in table[1:]:
                    code, name, cat = clean(row[0]), clean(row[1]), clean(row[2])
                    if not re.match(r"^E\d{3}$", code) or cat not in ("GM", "KKR"):
                        continue
                    colleges.setdefault(code, name)
                    for (cc, cname), v in zip(heads[3:], row[3:]):
                        v = clean(v).replace(",", "")
                        if cc and v.isdigit():
                            courses.setdefault(cc, cname)
                            out[(code, cc, cat)] = int(v)
    return out, colleges, courses


def parse_fee(pdf_path):
    import pdfplumber
    seats = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    cells = [clean(c) for c in row]
                    if len(cells) < 9 or not re.match(r"^E\d{3}$", cells[0]):
                        continue
                    cc, cname = course_of(cells[2])
                    if not cc:
                        continue
                    num = lambda s: int(s.replace(",", "")) if s.replace(",", "").isdigit() else None
                    seats[(cells[0], cc)] = {"name": cells[1], "course": cname, "total": num(cells[3]), "gm": num(cells[4]),
                                             "kkr": num(cells[5]), "fee": num(cells[8])}
    return seats


# COMEDK UGET 2026: 180 questions, 1 mark each, no negative marking; 1.29 lakh appeared (9 May 2026).
# COMEDK publishes no marks-vs-rank table, so three public analyses are kept side by side; the app shows the range they span.
# Each curve: (marks, rank) points, higher marks -> better rank; the server interpolates in log(rank).
CANDIDATES = 129000
MARKS_RANK = [
    {"label": "CollegeDekho, COMEDK 2026 result analysis",
     "url": "https://www.collegedekho.com/news/comedk-result-2026-live-updates-link-toppers-college-wise-cutoffs-78958/",
     "points": [(180, 1), (140, 90), (130, 155), (120, 330), (110, 850), (100, 2350), (90, 5900), (80, 12500), (70, 17500),
                (60, 41500), (50, 76500), (0, CANDIDATES)]},
    {"label": "Shiksha, COMEDK 2026 marks vs rank",
     "url": "https://www.shiksha.com/engineering/articles/comedk-2026-marks-vs-rank-blogId-230113",
     "points": [(180, 1), (150, 100), (130, 500), (110, 2300), (80, 20500), (60, 37000), (50, 43000), (0, CANDIDATES)]},
    {"label": "COMEDK 2024-2025 marks vs rank trend (PW, Careers360)",
     "url": "https://www.pw.live/kseab/exams/comedk-uget-marks-vs-rank-2025",
     "points": [(180, 1), (170, 10), (160, 50), (150, 150), (140, 350), (130, 800), (120, 1700), (110, 3200), (100, 5500),
                (90, 9700), (80, 14000), (70, 23000), (60, 36000), (50, 43000), (0, CANDIDATES)]},
]
CITY_FIX = {"Bangalore": "Bengaluru", "Bangalore Rural": "Bengaluru Rural", "Tumkur": "Tumakuru", "Dakshin Kannada": "Dakshina Kannada",
            "Kalaburgi": "Kalaburagi", "Mandya District": "Mandya", "Bagalkot": "Bagalkote"}


def college_parts(full):
    """'Acharya Institute of Technology-Soladevanahalli, Bengaluru' -> ('Acharya Institute of Technology', 'Bengaluru')."""
    short = re.split(r"\s*-\s*|,", full, maxsplit=1)[0].strip()
    tail = [p.strip() for p in full.split(",") if p.strip()]
    city = tail[-1] if len(tail) > 1 else (re.split(r"\s*-\s*", full)[-1].strip(" ,") if "-" in full else "")
    return short, CITY_FIX.get(city, city)


def course_name(s):
    return re.sub(r"(\w)- (\w)", r"\1\2", clean(s))  # 'Communicat- ion' -> 'Communication' (PDF line breaks)


def build(raw):
    rounds = {}
    colleges, courses = {}, {}
    for r in ROUNDS:
        rounds[r], c, k = parse_cutoffs(raw / f"{r}.pdf")
        colleges.update({a: b for a, b in c.items() if a not in colleges})
        courses.update({a: b for a, b in k.items() if a not in courses})
        print(r, "cells", len(rounds[r]), "colleges", len(c), "courses", len(k))
    y25, _, _ = parse_cutoffs(raw / "y25.pdf")
    print("2025 cells", len(y25))
    fee = parse_fee(raw / "fee.pdf")
    print("fee rows", len(fee))
    keys = sorted({k for r in ROUNDS for k in rounds[r]})
    rows = []
    for code, cc, cat in keys:
        rows.append([code, cc, cat, [rounds[r].get((code, cc, cat)) for r in ROUNDS], y25.get((code, cc, cat))])
    for (code, cc), f in fee.items():
        colleges.setdefault(code, f["name"])
        courses.setdefault(cc, f["course"])
    data = {
        "year": 2026, "rounds": ["R1", "R2", "R3", "R4"], "marks_rank": MARKS_RANK, "candidates": CANDIDATES,
        "colleges": {code: [name, *college_parts(name)] for code, name in colleges.items()},
        "courses": {cc: course_name(n) for cc, n in courses.items()}, "rows": rows,
        "seats": {f"{code}|{cc}": [f["total"], f["gm"], f["kkr"], f["fee"]] for (code, cc), f in fee.items()},
        "sources": {k: U + v for k, v in FILES.items()},
    }
    OUT.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    print("rows", len(rows), "colleges", len(colleges), "courses", len(courses), "->", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    step, raw = sys.argv[1], Path(sys.argv[2])
    fetch(raw) if step == "fetch" else build(raw)
