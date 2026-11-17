"""Builds backend/rank_data/jee_main_2026.json.gz, the only data the Rank tab reads.

Sources (all official, 2026 cycle):
  * JoSAA 2026 opening/closing ranks, rounds 1-5   josaa.admissions.nic.in/Applicant/SeatAllotmentResult/CurrentORCR.aspx
  * CSAB Special 2026, rounds 1-2                   admissions.nic.in/csabspl/Applicant/seatallotmentresult/currentorcr.aspx
  * JAC Delhi 2026 round 1-4 cut-off PDFs           jacdelhi.admissions.nic.in/or-cr/
  * NTA JEE Main 2026 press release (20 Apr 2026)   candidate counts and JEE Advanced cut-off counts (typed in below)
  * Shift-wise marks vs percentile: public 2026 tables (Competishun / Careers360), the only marks source there is.

Usage:  python build_rank_data.py fetch <raw_dir>      # downloads everything (about 8 minutes)
        python build_rank_data.py build <raw_dir>      # parses and writes the data file
Needs `requests` and `pdfplumber` (build-time only; the server only reads the JSON).
"""
import gzip, html, json, re, sys, time
from pathlib import Path

from institutes import INSTITUTES, DELHI, NSUT_BRANCHES, IIITD_BRANCHES, IGDTUW_BRANCHES

OUT = Path(__file__).resolve().parents[2] / "rank_data" / "jee_main_2026.json.gz"
JOSAA = "https://josaa.admissions.nic.in/Applicant/SeatAllotmentResult/CurrentORCR.aspx"
CSAB = "https://admissions.nic.in/csabspl/Applicant/seatallotmentresult/currentorcr.aspx"
JAC = "https://jacdelhi.admissions.nic.in/or-cr/"
JAC_PDF = "https://cdnbbsr.s3waas.gov.in/s3e45823afe1e5120cec11fc4c379a0c67/uploads/2026/"
JAC_FILES = {  # round 1-4 cut-off PDFs listed on the JAC OR-CR page (2026)
    "DTU": ["06/202606172143622056", "07/202607021961586254", "07/202607091707226292", "07/20260715952726882"],
    "NSUT": ["06/20260617545513258", "07/202607021272551822", "07/202607091516947066", "07/202607151464672174"],
    "IIITD": ["06/20260617929808660", "07/20260702737623821", "07/202607091962797998", "07/202607161964653245"],
    "IGDTUW": ["06/202606181840071240", "07/202607021225577462", "07/202607091316184882", "07/20260715741279300"],
}
P = "ctl00$ContentPlaceHolder1$"

# ---------- NTA 2026 official numbers (press release, 20 April 2026) ----------
NTA = {
    "candidates": 1538468,
    "categories": {"GEN": 538239, "EWS": 180086, "OBC-NCL": 611953, "SC": 156038, "ST": 52152, "PwD": 4800},
    # JEE Advanced 2026 cut-off table: (category, percentile from, percentile to, candidates)
    "advanced_cutoff": [
        ("UR", 100.0, 93.4123549, 96873), ("UR-PwBD", 93.3244144, 0.0023186, 4391),
        ("EWS", 93.4105172, 82.4164528, 25009), ("OBC-NCL", 93.4105172, 80.9232583, 67597),
        ("SC", 93.4105172, 63.9172792, 37522), ("ST", 93.4041748, 52.0174712, 18790),
    ],
}

# ---------- Public shift-wise marks for each percentile (2026) ----------
PCT_ROWS = [99.9, 99.5, 99, 98.5, 98, 97.5, 97, 96.5, 96, 95.5, 95, 94, 93, 92, 91, 90]
SHIFTS = {  # Competishun 2026 matrix, marks needed for each row of PCT_ROWS
    "21 Jan S1": [224, 189, 158, 143, 132, 125, 119, 113, 108, 104, 100, 93, 87, 82, 78, 74],
    "21 Jan S2": [230, 200, 174, 162, 153, 145, 139, 133, 128, 124, 121, 113, 106, 100, 95, 91],
    "22 Jan S1": [243, 212, 186, 173, 163, 156, 149, 143, 138, 134, 129, 121, 114, 108, 102, 97],
    "22 Jan S2": [219, 184, 154, 140, 130, 122, 116, 110, 105, 101, 97, 89, 83, 78, 74, 70],
    "23 Jan S1": [227, 193, 166, 152, 141, 134, 127, 121, 116, 112, 108, 100, 94, 88, 82, 78],
    "23 Jan S2": [224, 188, 158, 144, 134, 126, 120, 114, 108, 104, 100, 92, 86, 81, 76, 72],
    "24 Jan S1": [232, 200, 174, 160, 149, 141, 134, 128, 123, 119, 115, 107, 101, 96, 91, 87],
    "24 Jan S2": [236, 205, 178, 164, 154, 146, 138, 132, 127, 123, 119, 112, 105, 99, 94, 89],
    "28 Jan S1": [242, 213, 188, 173, 162, 154, 146, 140, 134, 130, 125, 117, 110, 104, 99, 94],
    "28 Jan S2": [237, 207, 180, 165, 155, 148, 140, 134, 129, 124, 119, 112, 105, 100, 95, 91],
    "2 Apr S1": [233, 200, 175, 161, 151, 143, 137, 132, 128, 128, 125, 117, 110, 104, 99, 95],
    "2 Apr S2": [221, 189, 165, 151, 141, 134, 128, 123, 119, 118, 118, 110, 104, 99, 95, 91],
    "4 Apr S1": [230, 199, 175, 164, 153, 146, 140, 135, 130, 131, 130, 121, 114, 108, 103, 98],
    "4 Apr S2": [229, 198, 174, 161, 151, 144, 138, 132, 128, 124, 124, 116, 109, 104, 99, 95],
    "5 Apr S1": [252, 218, 190, 175, 165, 156, 149, 143, 138, 137, 137, 128, 121, 114, 108, 103],
    "5 Apr S2": [231, 200, 175, 161, 151, 143, 137, 132, 128, 128, 125, 117, 110, 104, 99, 95],
    "6 Apr S1": [218, 184, 160, 146, 136, 129, 123, 118, 113, 105, 105, 97, 91, 87, 83, 80],
    "6 Apr S2": [241, 209, 183, 168, 158, 150, 144, 138, 134, 131, 131, 122, 115, 109, 104, 99],
}
# 8 Apr S2 is missing from that matrix; Careers360 gives bands for 99/98/95/90 (mid-points used).
APR8 = {99: 158, 98: 138, 95: 103, 90: 68}
# Below 90 percentile no shift table exists; marks fall as this share of the 90-percentile marks (rough).
LOW_SHAPE = [(85, 0.78), (80, 0.65), (75, 0.56), (70, 0.48), (60, 0.37), (50, 0.29), (40, 0.21), (30, 0.13), (20, 0.06), (10, -0.03)]


def interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def marks_curves():
    shifts = {k: list(v) for k, v in SHIFTS.items()}
    median = [sorted(col)[len(col) // 2] for col in zip(*shifts.values())]
    known = sorted(APR8)
    apr8 = []
    for i, p in enumerate(PCT_ROWS):
        if p > 99:
            apr8.append(round(APR8[99] + median[i] - median[PCT_ROWS.index(99)]))
        else:
            apr8.append(round(interp(p, known, [APR8[k] for k in known])))
    shifts["8 Apr S2"] = apr8
    for v in shifts.values():  # a higher percentile never needs fewer marks
        for i in range(len(v) - 2, -1, -1):
            v[i] = max(v[i], v[i + 1])
    order = sorted(shifts, key=lambda k: shifts[k][PCT_ROWS.index(99)])
    n = len(order)
    groups = {"tough": order[: n // 3], "normal": order[n // 3: n - n // 3], "easy": order[n - n // 3:]}
    curves = {}
    for level, names in groups.items():
        rows = [sorted(shifts[s][i] for s in names)[len(names) // 2] for i in range(len(PCT_ROWS))]
        m90, m999 = rows[-1], rows[0]
        pts = [(100.0, 300), (99.99, min(295, m999 + 40))] + list(zip(PCT_ROWS, rows))
        pts += [(p, round(m90 * f)) for p, f in LOW_SHAPE] + [(0.0, -75)]
        pts.sort()
        curves[level] = {"pct": [p for p, _ in pts], "marks": [m for _, m in pts]}
    return curves, {lvl: names for lvl, names in groups.items()}


# ---------- fetching ----------
def _hidden(h):
    return {m.group(1): html.unescape(m.group(2)) for m in re.finditer(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', h)}


def _rows(h):
    m = re.search(r'<table[^>]*id="ctl00_ContentPlaceHolder1_GridView1"[^>]*>(.*?)</table>', h, re.S)
    out = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(1) if m else "", re.S):
        cells = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if cells:
            out.append(cells)
    return out


def fetch_orcr(url, rnd, seat_type):
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    h = s.get(url, timeout=60).text
    values = {}
    picks = [("ddlroundno", str(rnd)), ("ddlInstype", "ALL"), ("ddlInstitute", "ALL"), ("ddlBranch", "ALL")]
    for name, value in picks:
        values[P + name] = value
        h = s.post(url, data={**_hidden(h), **values, "__EVENTTARGET": P + name, "__EVENTARGUMENT": ""}, timeout=180).text
    if seat_type:
        values[P + "ddlSeattype"] = "ALL"
    h = s.post(url, data={**_hidden(h), **values, "__EVENTTARGET": "", "__EVENTARGUMENT": "", P + "btnSubmit": "Submit"}, timeout=300).text
    return _rows(h)


def fetch_types(raw):
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    h = s.get(JOSAA, timeout=60).text
    values, out = {P + "ddlroundno": "5"}, {}
    h = s.post(JOSAA, data={**_hidden(h), **values, "__EVENTTARGET": P + "ddlroundno", "__EVENTARGUMENT": ""}, timeout=120).text
    for t in ("NIT", "3IT", "CFI"):
        values[P + "ddlInstype"] = t
        h = s.post(JOSAA, data={**_hidden(h), **values, "__EVENTTARGET": P + "ddlInstype", "__EVENTARGUMENT": ""}, timeout=120).text
        m = re.search(r'<select[^>]*name="%s"[^>]*>(.*?)</select>' % re.escape(P + "ddlInstitute"), h, re.S)
        out[t] = [html.unescape(n).strip() for v, n in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', m.group(1)) if v not in ("0", "ALL")]
    json.dump(out, open(raw / "inst_types.json", "w"))


def fetch(raw):
    import requests
    raw.mkdir(parents=True, exist_ok=True)
    fetch_types(raw)
    for r in range(1, 6):
        json.dump(fetch_orcr(JOSAA, r, True), open(raw / f"josaa_r{r}.json", "w"))
        print("JoSAA round", r)
    for r in (1, 2):
        json.dump(fetch_orcr(CSAB, r, False), open(raw / f"csab_r{r}.json", "w"))
        print("CSAB round", r)
    for inst, files in JAC_FILES.items():
        for i, f in enumerate(files, 1):
            (raw / f"jac_{inst}_{i}.pdf").write_bytes(requests.get(JAC_PDF + f + ".pdf", timeout=60).content)
    print("JAC PDFs done")


# ---------- parsing ----------
def norm(s):
    return re.sub(r'\s+', ' ', s or "").strip()


def institute_meta(name):
    low = norm(name).lower()
    hits = [m for m in INSTITUTES if m[0] in low]
    return max(hits, key=lambda m: len(m[0])) if hits else None


def split_program(full):
    full = norm(full)
    starts = [m.start() for m in re.finditer(r'\s\((\d) Years?,', full)]
    if not starts:
        return full, ""
    base, deg = full[: starts[-1]].strip(), full[starts[-1] + 2: -1]
    years = deg[0]
    if "Architecture" in deg or "Planning" in deg:
        return None, None
    if years == "4" and ("Technology" in deg or "B. Tech" in deg):
        return base, ""
    if years == "4":
        return base, "4-yr " + ("BS" if "Science" in deg else "B.Des" if "Design" in deg else deg.split(",")[-1].strip())
    return base, "5-yr " + ("dual" if "Dual" in deg else "integrated")


GROUPS = [
    ("Robotics & Mechatronics", r"robot|mechatronic"),
    ("Mathematics & Computing", r"mathematics (and|&) (computing|data)|computational math|mathematics and computing"),
    ("Instrumentation", r"instrumentation"),
    ("Electrical", r"el?ctrical|power system"),
    ("Electronics & Communication", r"electronic|vlsi|communication|\bece\b"),
    ("AI & Data Science", r"artificial intelligence|data science|machine learning|data analytics|big data|\bai\b"),
    ("Computer Science", r"computer|software|cyber|internet of things"),
    ("Information Technology", r"information technology|informatics|\(it\)"),
    ("Production & Industrial", r"production|industrial|manufactur"),
    ("Aerospace", r"aero|aviation|avionics"),
    ("Mechanical", r"mechanical|automobile|automotive|electric vehicle|mechanics"),
    ("Civil", r"civil|construction|infrastructure|geoinformatics"),
    ("Chemical", r"chemical"),
    ("Metallurgy & Materials", r"metallurg|material"),
    ("Biotechnology", r"bio"),
    ("Engineering Physics", r"engineering physics"),
    ("Mining", r"mining"),
    ("Environmental", r"environment"),
    ("Food/Textile/Ceramic", r"food|textile|ceramic|carpet|handloom|agricultur|leather|dairy|polymer|plastic"),
    ("Science & integrated courses", r"."),
]


def branch_group(name):
    low = name.lower()
    for g, rx in GROUPS:
        if re.search(rx, low):
            return g
    return GROUPS[-1][0]


QUOTA = {"AI": "AI", "HS": "HS", "OS": "OS", "GO": "GO", "JK": "JK", "LA": "LA", "All India": "AI", "Home State": "HS",
         "Other State": "OS", "Home State for Goa": "GO", "Jammu & Kashmir (UT)": "JK", "Ladakh (UT)": "LA"}
SEAT = {"OPEN": ("OPEN", 0), "EWS": ("EWS", 0), "OBC-NCL": ("OBC-NCL", 0), "SC": ("SC", 0), "ST": ("ST", 0),
        "OPEN (PwD)": ("OPEN", 1), "EWS (PwD)": ("EWS", 1), "OBC-NCL (PwD)": ("OBC-NCL", 1), "SC (PwD)": ("SC", 1), "ST (PwD)": ("ST", 1)}


def rank_value(v):
    v = (v or "").replace(",", "").strip()
    return int(v) if v.isdigit() else None  # "123P" preparatory ranks are IIT-only and skipped


class Store:
    def __init__(self):
        self.inst, self.inst_ix = [], {}
        self.prog, self.prog_ix = [], {}
        self.seats = {}

    def institute(self, key, record):
        if key not in self.inst_ix:
            self.inst_ix[key] = len(self.inst)
            self.inst.append(record)
        return self.inst_ix[key]

    def program(self, inst, name, degree):
        key = (inst, name, degree)
        if key not in self.prog_ix:
            self.prog_ix[key] = len(self.prog)
            self.prog.append({"inst": inst, "name": name, "degree": degree, "group": branch_group(name)})
        return self.prog_ix[key]

    def seat(self, prog, quota, cat, pwd, female, slots):
        key = (prog, quota, cat, pwd, female)
        if key not in self.seats:
            self.seats[key] = [[None, None] for _ in range(slots)]
        return self.seats[key]


def parse_counselling(raw, store, types):
    kind_of = {}
    for t, names in types.items():
        for n in names:
            kind_of[norm(n).lower()] = {"NIT": "NIT", "3IT": "IIIT", "CFI": "GFTI"}[t]
    sources = [(f"josaa_r{r}.json", r - 1) for r in range(1, 6)] + [("csab_r1.json", 5), ("csab_r2.json", 6)]
    unknown = set()
    for fname, slot in sources:
        rows = json.load(open(raw / fname))
        for row in rows:
            if len(row) < 7 or row[0] == "Institute":
                continue
            name = norm(row[0])
            kind = kind_of.get(name.lower())
            meta = institute_meta(name)
            if not kind or not meta:
                if "Indian Institute of Technology" not in name or "Information" in name:
                    unknown.add(name)
                continue
            quota, seat = QUOTA.get(row[2]), SEAT.get(row[3])
            if not quota or not seat:
                continue
            base, degree = split_program(row[1])
            if base is None:
                continue
            inst = store.institute(name.lower(), {"name": name, "short": meta[1], "city": meta[2], "state": meta[3], "type": kind, "body": "josaa"})
            prog = store.program(inst, base, degree)
            cell = store.seat(prog, quota, seat[0], seat[1], int(row[4].startswith("Female")), 7)[slot]
            cell[0], cell[1] = rank_value(row[5]), rank_value(row[6])
    return unknown


CODE = re.compile(r'^(GN|EW|OB|BC|SC|ST)(GN|GL|PD|PH)(D|O|OD)$')
CAT = {"GN": "OPEN", "EW": "EWS", "OB": "OBC-NCL", "BC": "OBC-NCL", "SC": "SC", "ST": "ST"}
HEAD = re.compile(r'^(GN|EW|OB|BC|SC|ST)[A-Z]{2,4}$')  # any category column, incl. defence / single-girl ones we skip
NUM = re.compile(r'^(\d{2,8})')


def _lines(page):
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    lines = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if lines and abs(lines[-1][0] - w["top"]) < 3.5:
            lines[-1][1].append(w)
        else:
            lines.append([w["top"], [w]])
    return [(top, sorted(ws, key=lambda w: w["x0"])) for top, ws in lines]


def _cx(w):
    return (w["x0"] + w["x1"]) / 2


def parse_rows_by_branch(pdf, names):
    """DTU / NSUT: one row per branch, one column per category code."""
    out = []
    for page in pdf.pages:
        region = "O" if re.search(r'OUT\s*SIDE DELHI', page.extract_text() or "", re.I) else "D"
        cols, pending = None, []
        for _, ws in _lines(page):
            codes = [w for w in ws if HEAD.match(w["text"]) or w["text"] in ("KM", "SG")]
            if len(codes) >= 3:
                first = min(w["x0"] for w in codes)
                cols = [w for w in ws if w["x0"] >= first - 2]
                pending = []
                continue
            if not cols:
                continue
            first_x = min(w["x0"] for w in cols)
            label = [w["text"] for w in ws if w["x1"] < first_x - 4]
            nums = [w for w in ws if w["x0"] >= first_x - 25 and NUM.match(w["text"])]
            if not nums:
                pending = [t for t in label if not t.isdigit()]
                continue
            if label and label[0].isdigit():
                label = label[1:]
            text = re.sub(r'^Branch\s+', '', " ".join(pending + label).strip())
            pending = []
            code = text.replace("*", "").strip()
            branch = names.get(code, text) if names else text
            if not branch or "Arch" in branch or "Kashmiri" in branch:
                continue
            for w in nums:
                col = min(cols, key=lambda c: abs(_cx(c) - _cx(w)))
                m = CODE.match(col["text"])
                if m:
                    out.append((branch, region, CAT[m.group(1)], int(m.group(2) in ("PD", "PH")), int(m.group(2) == "GL"), int(NUM.match(w["text"]).group(1))))
    return out


def parse_rows_by_category(pdf, names, female_only, pages=None):
    """IIIT-Delhi / IGDTUW: one row per category code, one column per branch."""
    out = []
    for pi, page in enumerate(pdf.pages):
        if pages is not None and pi not in pages:
            continue
        lines = _lines(page)
        text = page.extract_text() or ""
        default_region = "O" if re.search(r'OUT\s*SIDE DELHI', text, re.I) else "D"
        heads = [w for _, ws in lines for w in ws if w["text"] in names]
        labels = [(top, w) for top, ws in lines for w in ws if CODE.match(w["text"]) and w["x0"] < 120]
        if not heads or not labels:
            continue
        cells = {}
        for top, ws in lines:
            for w in ws:
                if not NUM.match(w["text"]) or w["x0"] < 60:
                    continue
                near = min(labels, key=lambda lw: abs(lw[0] - top))
                if abs(near[0] - top) > 14:
                    continue
                col = min(heads, key=lambda h: abs(_cx(h) - _cx(w)))
                key = (near[1]["text"], col["text"])
                cells[key] = max(cells.get(key, 0), int(NUM.match(w["text"]).group(1)))  # JEE rank > institute rank
        for (code, branch), value in cells.items():
            m = CODE.match(code)
            region = "O" if m.group(3) in ("O", "OD") else ("D" if m.group(3) == "D" and default_region == "D" else default_region)
            if m.group(3) == "OD":
                region = "O"
            out.append((names[branch], region, CAT[m.group(1)], int(m.group(2) in ("PD", "PH")), 1 if female_only else int(m.group(2) == "GL"), value))
    return out


def parse_jac(raw, store):
    import pdfplumber
    found = {}
    for inst, files in JAC_FILES.items():
        long_name, short = DELHI[inst]
        iid = store.institute(inst, {"name": long_name, "short": short, "city": "Delhi", "state": "Delhi", "type": "DELHI", "body": "jac"})
        for rnd in range(1, len(files) + 1):
            with pdfplumber.open(raw / f"jac_{inst}_{rnd}.pdf") as pdf:
                if inst == "DTU":
                    rows = parse_rows_by_branch(pdf, None)
                elif inst == "NSUT":
                    rows = parse_rows_by_branch(pdf, NSUT_BRANCHES)
                elif inst == "IIITD":  # the "Without Bonus Point" page is the plain JEE rank list
                    pages = [i for i, p in enumerate(pdf.pages) if "Without Bonus" in (p.extract_text() or "")]
                    rows = parse_rows_by_category(pdf, IIITD_BRANCHES, False, set(pages) or None)
                else:
                    rows = parse_rows_by_category(pdf, IGDTUW_BRANCHES, True)
            found[(inst, rnd)] = len(rows)
            for branch, region, cat, pwd, female, close in rows:
                prog = store.program(iid, branch, "")
                cell = store.seat(prog, "DL" if region == "D" else "OD", cat, pwd, female, 7)[rnd - 1]
                cell[1] = max(cell[1] or 0, close)
    return found


def demand(store):
    """Smaller = filled sooner on the general list (OPEN, gender-neutral, all-India / other-state / outside-Delhi)."""
    best = {}
    for (prog, quota, cat, pwd, female), cells in store.seats.items():
        if cat != "OPEN" or pwd or female:
            continue
        last = next((c[1] for c in reversed(cells[:5]) if c[1]), None)
        if not last:
            continue
        pref = {"AI": 0, "OS": 0, "OD": 0, "HS": 1, "DL": 1}.get(quota, 2)
        if prog not in best or (pref, last) < best[prog]:
            best[prog] = (pref, last)
    for i, p in enumerate(store.prog):
        p["demand"] = best[i][1] if i in best else None


def build(raw):
    store = Store()
    types = json.load(open(raw / "inst_types.json"))
    unknown = parse_counselling(raw, store, types)
    found = parse_jac(raw, store)
    demand(store)
    curves, groups = marks_curves()
    seats = [[prog, quota, cat, pwd, female, [c[0] for c in cells], [c[1] for c in cells]]
             for (prog, quota, cat, pwd, female), cells in store.seats.items() if any(c[1] for c in cells)]
    data = {
        "meta": {"year": 2026, "built": time.strftime("%Y-%m-%d"), "nta": NTA, "shift_groups": groups,
                 "jac_rows": {f"{k[0]} R{k[1]}": v for k, v in found.items()}},
        "marks": curves,
        "institutes": store.inst,
        "programs": store.prog,
        "seats": seats,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print("institutes", len(store.inst), "programs", len(store.prog), "seats", len(seats), "->", OUT, OUT.stat().st_size, "bytes")
    print("JAC rows", data["meta"]["jac_rows"])
    if unknown:
        print("UNMAPPED institutes:", sorted(unknown))


if __name__ == "__main__":
    step, raw = sys.argv[1], Path(sys.argv[2])
    fetch(raw) if step == "fetch" else build(raw)
