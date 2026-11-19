"""JEELIVE.AI Rank: print-friendly PDFs (white A4) of the Rank tab's college lists.

Every PDF is built from the same functions that answer the screen (rank_predictor, rank_comedk, rank_bitsat, rank_tools),
so the paper and the app always show the same numbers. Made on the server, so the app itself does not grow at all;
the two fonts are subset into each file (a 50-row list is ~40-70 KB).
"""
import io, re
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional
from xml.sax.saxutils import escape

from fastapi import Response
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import rank_bitsat as rb
import rank_comedk as ck
import rank_predictor as rp
import rank_tools as rt

# FreeSans (GNU FreeFont, font-embedding exception) has the ₹ sign that the PDF base fonts lack.
_FONTS = rp.DIR / "fonts"
pdfmetrics.registerFont(TTFont("JL", str(_FONTS / "FreeSans.ttf")))
pdfmetrics.registerFont(TTFont("JLB", str(_FONTS / "FreeSansBold.ttf")))
pdfmetrics.registerFontFamily("JL", normal="JL", bold="JLB", italic="JL", boldItalic="JLB")

RED, INK, MUTED = colors.HexColor("#A3122A"), colors.HexColor("#1B1B1F"), colors.HexColor("#5F6368")
LINE, ZEBRA, HEAD, BOX = colors.HexColor("#DADADA"), colors.HexColor("#F7F7F8"), colors.HexColor("#F3ECEC"), colors.HexColor("#FBF6F6")
TAGS = {"safe": ("Safe", "#1E7B34", "#E6F4EA"), "likely": ("Likely", "#1F5FAD", "#E7EFFA"), "borderline": ("Borderline", "#B8461B", "#FDECE4")}
KIND = {"NIT": "NIT", "IIIT": "IIIT", "GFTI": "GFTI", "DELHI": "JAC Delhi"}
SEGMENT = {"all": "Sab colleges", "NIT": "Sirf NIT", "IIIT": "Sirf IIIT", "GFTI": "Sirf GFTI", "DELHI": "Sirf Delhi (JAC)"}
CATEGORY = {"GEN": "General", "EWS": "EWS", "OBC-NCL": "OBC-NCL", "SC": "SC", "ST": "ST"}
AREA = {"all": "Sab shehar", "blr": "Sirf Bengaluru", "other": "Bengaluru ke bahar"}
M = 12 * mm
W = A4[0] - 2 * M
ESTIMATE = "2026 ke official data par estimate, guarantee nahi. Asli cutoff har saal badalta hai."
IST = timezone(timedelta(hours=5, minutes=30))
NUM = 6.8  # every number cell


def _st(size=8.0, bold=False, color=INK, align=0, lead=None, after=0.0, keep=False):
    return ParagraphStyle("jl", fontName="JLB" if bold else "JL", fontSize=size, leading=lead or size * 1.28, textColor=color,
                          alignment=align, spaceAfter=after, keepWithNext=keep)


TITLE, SUB, H2 = _st(15, True, lead=19), _st(8.6, color=MUTED, after=6), _st(10.5, True, RED, after=4)
CELL, CELL_C, SMALL, NOTE = _st(7.4), _st(NUM, align=1), _st(6.4, color=MUTED), _st(6.9, color=MUTED, after=1.5)
BOX_BIG, BOX_TXT = _st(10, True, lead=13), _st(7.8, lead=10.4)


def e(v):
    return escape(str(v)) if v is not None else ""


def n(v):
    return rp.fmt(v) if v else "—"


def rupees(v):
    return f"₹{rp.fmt(v)}" if v else "—"


def rng(r):
    return rp.fmt(r[0]) if r[0] == r[1] else f"{rp.fmt(r[0])} – {rp.fmt(r[1])}"


def pct_rng(r):
    return f"{r[0]:.2f}" if r[0] == r[1] else f"{r[0]:.2f} – {r[1]:.2f}"


def short_gap(g):
    """'lagbhag +6 marks aur' -> '+6 marks' (fits the narrow chance column)."""
    return re.sub(r"^lagbhag |\s+aur$", "", g or "").strip()


def tag_cell(tag):
    if not tag:
        return Paragraph("—", CELL_C)
    label, ink, _ = TAGS[tag]
    return Paragraph(f'<font name="JLB" color="{ink}">{label}</font>', CELL_C)


def gap_cell(text):
    return Paragraph(f'<font color="#B8461B">{e(short_gap(text))}</font>', _st(6.4, align=1, lead=7.6))


def p(text, style=CELL):
    return Paragraph(text, style)


# ---------- page chrome: brand header, estimate line and "Page 2 / 5" on every page ----------
def _chrome(c, title, page, total):
    width, height = A4
    c.saveState()
    c.setFillColor(RED)
    c.setFont("JLB", 13)
    c.drawString(M, height - 13 * mm, "JEELIVE.AI")
    c.setFillColor(MUTED)
    c.setFont("JLB", 7.5)
    c.drawString(M + pdfmetrics.stringWidth("JEELIVE.AI", "JLB", 13) + 6, height - 13 * mm, "RANK")
    c.setFont("JL", 8.5)
    c.drawRightString(width - M, height - 13 * mm, title)
    c.setStrokeColor(RED)
    c.setLineWidth(1.1)
    c.line(M, height - 15.5 * mm, width - M, height - 15.5 * mm)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(M, 12.5 * mm, width - M, 12.5 * mm)
    c.setFillColor(MUTED)
    c.setFont("JL", 6.8)
    c.drawString(M, 8.5 * mm, ESTIMATE)
    c.drawRightString(width - M, 8.5 * mm, f"jeelive.ai  ·  {datetime.now(IST).strftime('%d %b %Y')}  ·  Page {page} / {total}")
    c.restoreState()


def _canvas_for(title):
    class PagedCanvas(rl_canvas.Canvas):
        """Keeps every page until the end, so each footer can say how many pages there are."""

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._pages = []

        def showPage(self):
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            pages = self._pages
            for i, state in enumerate(pages, 1):
                self.__dict__.update(state)
                _chrome(self, title, i, len(pages))
                super().showPage()
            super().save()

    return PagedCanvas


def _pdf(story, title, filename):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=21 * mm, bottomMargin=17 * mm,
                            title=f"JEELIVE.AI · {title}", author="JEELIVE.AI", creator="JEELIVE.AI Rank", subject=ESTIMATE)
    doc.build(story, canvasmaker=_canvas_for(title))
    name = re.sub(r"[^A-Za-z0-9.-]+", "-", filename).strip("-")
    return Response(buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


def _head(title, sub):
    return [p(e(title), TITLE), p(e(sub), SUB)]


def _box(big, lines):
    """The student's score in a soft panel with a blood-red edge, like the top of the Rank Card."""
    cells = [[p(e(big), BOX_BIG)]] + [[p(x, BOX_TXT)] for x in lines if x]
    t = Table(cells, colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BOX), ("LINEBEFORE", (0, 0), (0, -1), 2.2, RED),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
                           ("TOPPADDING", (0, 0), (-1, 0), 7), ("BOTTOMPADDING", (0, -1), (-1, -1), 7)]))
    return [t, Spacer(1, 7)]


def _legend(extra=""):
    parts = [f'<font name="JLB" color="{TAGS[k][1]}">{TAGS[k][0]}</font> {d}' for k, d in
             (("safe", "aaram se mil sakti hai"), ("likely", "milne ke achhe chances"), ("borderline", "pakki nahi"))]
    return [p("Chance:  " + "   ·   ".join(parts) + (f"   ·   {extra}" if extra else ""), _st(7, color=MUTED, after=5))]


def _table(head, rows, widths, center_from, extra=(), tags=()):
    """A clean list table: tinted header with a red rule, zebra rows, numbers centred. tags = (col, row, tag) tints."""
    t = Table([head] + rows, colWidths=widths, repeatRows=1)
    style = [("FONT", (0, 0), (-1, 0), "JLB", 6.7), ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("LINEBELOW", (0, 0), (-1, 0), 0.9, RED),
             ("FONT", (0, 1), (-1, -1), "JL", NUM), ("TEXTCOLOR", (0, 0), (-1, -1), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ALIGN", (center_from, 0), (-1, -1), "CENTER"), ("LINEBELOW", (0, 1), (-1, -1), 0.25, LINE),
             ("LEFTPADDING", (0, 0), (-1, -1), 2.4), ("RIGHTPADDING", (0, 0), (-1, -1), 2.4),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2)]
    style += [("BACKGROUND", (0, r), (-1, r), ZEBRA) for r in range(2, len(rows) + 1, 2)]
    style += [("BACKGROUND", (c, r), (c, r), colors.HexColor(TAGS[tag][2])) for c, r, tag in tags if tag]
    t.setStyle(TableStyle(style + list(extra)))
    return t


def _mine(col, row):
    """The round whose closing decided the chance: bold blood red."""
    return [("FONT", (col, row), (col, row), "JLB", NUM), ("TEXTCOLOR", (col, row), (col, row), RED)]


def _notes(lines):
    return [Spacer(1, 6)] + [p(x, NOTE) for x in lines if x]


# ---------- JEE Main college predictor ----------
class JeePdfIn(rp.Form):
    segment: Literal["all", "NIT", "IIIT", "GFTI", "DELHI"] = "all"


def _jee_table(entries, near=False):
    """entries = [(prog, close, rnd, label, seat, tag or gap)], in the screen's order. JAC Delhi rows fill R1–R4 only
    (JAC has no R5 / CSAB, and its Upgrade / Spot ranks were never published)."""
    rows, extra, tags = [], [], []
    for r, (prog, close, rnd, label, s, mark) in enumerate(entries, 1):
        pr, inst = rp.PROGS[prog], rp.INST[rp.PROGS[prog]["inst"]]
        unit = label + (" · JAC: sirf R1–R4" if s.jac else "" if label == "CRL" else " · CSAB = CRL")
        name = (f'<b>{e(inst["short"])}</b> <font size="6" color="#5F6368">{KIND[inst["type"]]}</font><br/>'
                f'{e(pr["name"])}{" (" + e(pr["degree"]) + ")" if pr["degree"] else ""}<br/>'
                f'<font size="6.1" color="#5F6368">{e(rp.path_label(s))} · {e(unit)}</font>')
        closes = [n(s.closes[i]) if i < len(s.closes) and not (s.jac and i >= 4) else "—" for i in range(len(rp.JOSAA_ROUNDS))]
        seats = rt.JEE_SEATS.get(prog) if not s.jac else None
        rows.append([str(r), p(name), *closes, n(s.y25), str(seats) if seats else "—", gap_cell(mark) if near else tag_cell(mark)])
        extra += _mine(2 + rnd, r)
        if not near:
            tags.append((11, r, mark))
    head = ["#", "College · Branch · Seat"] + rp.JOSAA_ROUNDS + [rp.Y25_LABEL, "Seats*", "Kitna door" if near else "Chance"]
    return _table(head, rows, [15, 165] + [33.5] * 7 + [36, 28, 48.5], 2, extra, tags)


def jee(body: JeePdfIn):
    st, best, near, lists, near_sorted = rp._ranked(body.key())
    res = rp.result_block(st)
    chosen = lists[body.segment]
    entries = [(prog, *best[prog][3:6], best[prog][6], best[prog][2]) for prog in chosen]
    seg_ok = lambda prog: body.segment == "all" or rp.INST[rp.PROGS[prog]["inst"]]["type"] == body.segment  # noqa: E731
    near_entries = []
    for prog in near_sorted:
        if seg_ok(prog):
            _, close, rnd, label, s = near[prog]
            near_entries.append((prog, close, rnd, label, s, rp.marks_gap(st, close, label, s)))
            if len(near_entries) == 5:
                break
    count = {k: sum(1 for x in entries if x[5] == k) for k in TAGS}
    who = " · ".join(x for x in [res["summary"], body.state] if x)
    lines = [f"Expected percentile <b>{pct_rng(res['percentile'])}</b>   ·   Expected rank (CRL) <b>{rng(res['crl'])}</b>"
             + (f"   ·   {e(res['cat_rank']['label'])} <b>{rng(res['cat_rank']['range'])}</b>" if res.get("cat_rank") else "")
             + (f"   ·   {e(res['pwd_rank']['label'])} <b>{rng(res['pwd_rank']['range'])}</b>" if res.get("pwd_rank") else ""),
             e(res.get("spread")), e(res.get("paper")), e(res.get("delhi_note")),
             f"List: <b>{SEGMENT[body.segment]}</b> · Branch: <b>{e(', '.join(body.branches) or 'All branches')}</b> · "
             f"Top {len(entries)} college-branch (Borderline {count['borderline']}, Likely {count['likely']}, Safe {count['safe']}) · "
             f"aapki pahunch mein kul {sum(1 for prog in best if seg_ok(prog))}"]
    story = _head("College predictor · JEE Main 2026", "Har college-branch ki round-wise closing rank, 2025 ka final round, seats aur aapka chance.")
    story += _box(who, lines) + _legend('<font name="JLB" color="#A3122A">Laal number</font> = jis round ki closing se chance nikala')
    story.append(p(f"Top {len(entries)} college-branch", H2))
    story += [_jee_table(entries)] if entries else [p("Is filter mein 2026 ki koi seat aapki rank tak nahi gayi.", CELL)]
    if near_entries:
        story += [Spacer(1, 8), p("Bas thoda sa door", H2), _jee_table(near_entries, near=True)]
    story += _notes(["* Seats = JoSAA 2026 seat matrix: us branch ki saari seats (sab quota aur category). JAC Delhi: R1–R4 hi hote hain; Upgrade / Spot round ki rank JAC ne publish nahi ki.",
                     "Closing: JoSAA rounds mein seat ke apne rank type par (CRL / category rank / PwD rank), CSAB rounds hamesha CRL par.",
                     "Data: NTA JEE Main 2026, JoSAA 2026 Round 1–5, CSAB Special 2026 Round 1–2, JAC Delhi 2026 Round 1–4. Trend: JoSAA 2025 final round.",
                     *rp.MISSING, f"Official: {rp.OFFICIAL['josaa']}  ·  {rp.OFFICIAL['jac']}"])
    score = f"{body.marks}-marks" if body.marks is not None and body.percentile is None else f"{body.percentile}-percentile"
    tail = "" if body.segment == "all" else f"-{body.segment}"
    return _pdf(story, "College predictor · JEE Main 2026", f"JEELIVE-JEE-colleges-{score}{tail}.pdf")


# ---------- COMEDK college predictor ----------
class ComedkPdfIn(ck.Form):
    area: Literal["all", "blr", "other"] = "all"


def _comedk_table(seats, marks_of, near=False):
    rows, extra, tags = [], [], []
    for i, s in enumerate(seats, 1):
        c = ck.INFO[s.code]
        name = (f'<b>{e(c["short"])}</b> <font size="6" color="#5F6368">{e(c["city"])}</font><br/>'
                f'{e(ck._D["courses"].get(s.cc, s.cc))}')
        mark = marks_of(s)
        rows.append([str(i), p(name), *[n(x) for x in s.rounds], n(s.y25), str(s.gm) if s.gm else "—", rupees(s.fee),
                     gap_cell(mark) if near else tag_cell(mark)])
        extra += _mine(2 + s.rnd, i)
        if not near:
            tags.append((9, i, mark))
    head = ["#", "College · Course"] + list(ck.ROUNDS) + ["2025 final", "GM seats", "Fee / saal", "Kitna door" if near else "Chance"]
    return _table(head, rows, [15, 198] + [38] * 4 + [38, 32, 46, 46], 2, extra, tags)


def comedk(body: ComedkPdfIn):
    st, tags, lists, near, in_reach, total, _ = ck._ranked(body.marks, body.rank, tuple(body.branches))
    res = ck.result_block(st, in_reach, total)
    chosen = lists[body.area]
    near_seats = [s for s in near if ck.in_area(s, body.area)][:5]
    count = {k: sum(1 for s in chosen if tags[id(s)] == k) for k in TAGS}
    lines = [f"{'Expected rank' if res['from_marks'] else 'Rank'} (GM) <b>{rng(res['rank'])}</b>   ·   "
             f"<b>{in_reach}</b> of {total} GM college-course pahunch mein", e(res.get("spread")), e(res.get("check")),
             f"List: <b>{AREA[body.area]}</b> · Branch: <b>{e(', '.join(body.branches) or 'All branches')}</b> · "
             f"Top {len(chosen)} college-course (Borderline {count['borderline']}, Likely {count['likely']}, Safe {count['safe']})"]
    story = _head("College predictor · COMEDK UGET 2026", "Sirf GM (General Merit, All India) seats: round-wise closing rank, 2025 final, GM seats, fee aur chance.")
    story += _box(res["summary"], lines) + _legend('<font name="JLB" color="#A3122A">Laal number</font> = final closing (sabse aakhri allotment)')
    story.append(p(f"Top {len(chosen)} college-course", H2))
    story += [_comedk_table(chosen, lambda s: tags[id(s)])] if chosen else [p("Is filter mein 2026 ki koi GM seat aapki rank tak nahi gayi.", CELL)]
    if near_seats:
        story += [Spacer(1, 8), p("Bas thoda sa door", H2), _comedk_table(near_seats, lambda s: st.gap(s.close), near=True)]
    story += _notes([*ck.NOTES, "Fee = COMEDK 2026 seat matrix ki saalana fee (GM). — = us round mein allotment nahi.",
                     "Data: COMEDK 2026 Round 1–4 cut-off ranks, 2025 final cut-off, 2026 seat matrix & fee. Marks se rank: 3 public analyses (2024–2026).",
                     f"Official: {ck.OFFICIAL}"])
    score = f"{body.marks}-marks" if body.rank is None else f"rank-{body.rank}"
    tail = "" if body.area == "all" else f"-{body.area}"
    return _pdf(story, "College predictor · COMEDK 2026", f"JEELIVE-COMEDK-colleges-{score}{tail}.pdf")


# ---------- BITSAT ----------
def _bitsat_table(rows_in, score, chance=True):
    rows, tags = [], []
    for i, r in enumerate(rows_in, 1):
        d = score - r["cutoff"]
        name = f'<b>{e(r["college"])}</b><br/>{e(r["program"])}'
        rows.append([str(i), p(name), *[str(h) if h is not None else "—" for h in r["history"]],
                     f"+{d}" if d >= 0 else f"−{-d}", tag_cell(r.get("tag")) if chance else gap_cell(f"+{-d} marks")])
        if chance:
            tags.append((8, i, r.get("tag")))
    head = ["#", "Campus · Program"] + [str(y) for y in rb.YEARS] + ["Aapka score", "Chance" if chance else "Kitna door"]
    extra = [("FONT", (6, 1), (6, -1), "JLB", NUM)]  # the 2026 cutoff column
    return _table(head, rows, [15, 238] + [36] * 5 + [46, 48], 2, extra, tags)


def bitsat(body: rb.BitsatIn):
    out = rb.predict(body)
    r = out["result"]
    lines = [f"2026 cutoff se <b>{r['cleared_all']}</b> of {r['total_all']} BITS programs clear",
             f"Best: <b>{e(r['best']['college'])} · {e(r['best']['program'])}</b> (cutoff {r['best']['cutoff']})" if r["best"] else "Abhi koi program clear nahi.",
             f"Agla target: {e(r['target']['college'])} · {e(r['target']['program'])}, +{r['target']['gap']} marks aur (cutoff {r['target']['cutoff']})" if r["target"] else None,
             f"List: <b>{'Sab campus' if body.campus == 'all' else body.campus}</b> · Degree: <b>{'Sab' if body.degree == 'all' else body.degree}</b>"]
    story = _head("College predictor · BITSAT 2026", "Har BITS program ki official 2022–2026 final cutoff (score / 390) aur aapka chance.")
    story += _box(f"{r['score']} / {r['max']} · BITSAT 2026", lines) + _legend("Aapka score = aapka score minus 2026 cutoff")
    story += [p("Aapki pahunch mein", H2), _bitsat_table(out["items"], r["score"])] if out["items"] else [p("Is score par koi program 2026 cutoff ke paas nahi.", CELL)]
    if out["near"]:
        story += [Spacer(1, 8), p("Bas thoda sa door", H2), _bitsat_table(out["near"], r["score"], chance=False)]
    if out["rest"]:
        story += [Spacer(1, 8), p("Baaki programs", H2), _bitsat_table(out["rest"], r["score"], chance=False)]
    story += _notes([*rb.NOTES, f"Data: {e(rb.SOURCE)}" if isinstance(rb.SOURCE, str) else None])
    tail = "".join(f"-{x}" for x in (body.campus, body.degree) if x != "all")
    return _pdf(story, "College predictor · BITSAT 2026", f"JEELIVE-BITSAT-{r['score']}-score{tail}.pdf")


# ---------- Target marks ----------
def target_jee(body: rt.TargetJeeIn):
    d = rt.target_jee(body)
    c = d["college"]
    rounds = d["rounds"]
    lead = 52
    col = (W - lead) / len(rounds)
    story = _head(f"Target marks · {c['short']}", "Har branch ke liye: 2026 ki closing rank tak pahunchne ke liye lagbhag kitne marks (Tough / Normal / Easy paper).")
    profile = " · ".join(x for x in [CATEGORY[body.category], "Female" if body.female else None, "PwD" if body.pwd else None,
                                      f"Home state {body.state}" if body.state else "Home state nahi chuna"] if x)
    story += _box(c["name"], [f"{e(c['city'])}, {e(c['state'])} · {KIND[c['type']]} · {len(d['rows'])} branches", f"Aapki details: <b>{e(profile)}</b>"])
    if not d["rows"]:
        story.append(p("Aapke category / state / gender ke liye is college mein 2026 ki koi seat nahi thi.", CELL))
    for i, r in enumerate(d["rows"], 1):
        f = r["final"]
        title = (f'<b>{i}. {e(r["branch"])}{" (" + e(r["degree"]) + ")" if r["degree"] else ""}</b>   '
                 f'<font size="6.6" color="#5F6368">{e(r["path"])} · {e(r["rank_type"])}{" · " + str(r["seats"]) + " seats" if r["seats"] else ""}</font>')
        aim = (f'Target ({e(f["label"])} closing {n(f["close"])}): <font name="JLB" color="#A3122A">Normal {f["marks"]["normal"]}+</font>'
               f'  ·  Tough {f["marks"]["tough"]}+  ·  Easy {f["marks"]["easy"]}+  ·  {f["pct"]:.2f} percentile'
               + (f"  ·  2025 final closing {n(r['y25'])}" if r.get("y25") else ""))
        rows = [[p(title, _st(7.8))] + [""] * len(rounds), [p(aim, _st(7.2))] + [""] * len(rounds), ["Round"] + rounds,
                ["Closing"] + [n(x["close"]) if x["close"] else ("—*" if x.get("unpublished") else "—") for x in r["cells"]]]
        for lvl in ("tough", "normal", "easy"):
            rows.append([lvl.capitalize() + " marks"] + [str(x["marks"][lvl]) if x.get("marks") else "—" for x in r["cells"]])
        t = Table(rows, colWidths=[lead] + [col] * len(rounds))
        t.setStyle(TableStyle([("SPAN", (0, 0), (-1, 0)), ("SPAN", (0, 1), (-1, 1)), ("BACKGROUND", (0, 0), (-1, 1), BOX),
                               ("LINEBEFORE", (0, 0), (0, 1), 2, RED), ("FONT", (0, 2), (-1, -1), "JL", NUM),
                               ("FONT", (0, 2), (-1, 2), "JLB", 6.7), ("BACKGROUND", (0, 2), (-1, 2), HEAD), ("LINEBELOW", (0, 2), (-1, 2), 0.8, RED),
                               ("FONT", (0, 5), (-1, 5), "JLB", NUM), ("TEXTCOLOR", (0, 2), (-1, -1), INK), ("TEXTCOLOR", (0, 3), (0, -1), MUTED),
                               ("ALIGN", (1, 2), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("LINEBELOW", (0, 3), (-1, -1), 0.25, LINE), ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                               ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                               ("TOPPADDING", (0, 0), (-1, -1), 2.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8)]))
        story += [KeepTogether([t]), Spacer(1, 7)]
    story += _notes([*d["notes"], "Closing: JoSAA rounds mein seat ke apne rank type par, CSAB rounds CRL par. —* = JAC ne Upgrade / Spot round ki rank publish nahi ki.",
                     f"Official: {d['official']}"])
    return _pdf(story, f"Target marks · {c['short']}", f"JEELIVE-target-{c['short']}.pdf")


def target_comedk(body: rt.TargetComedkIn):
    d = rt.target_comedk(body)
    c = d["college"]
    rows, extra = [], []
    for i, r in enumerate(d["rows"], 1):
        cells = [p(f'{e(x["close"] and n(x["close"]))}<br/><font size="6" color="#5F6368">{x["mid"]} marks</font>', CELL_C) if x["close"] else "—"
                 for x in r["cells"]]
        f = r["final"]
        rows.append([str(i), p(f"<b>{e(r['course'])}</b>"), *cells,
                     p(f'<font name="JLB" color="#A3122A">{f["mid"]}+</font><br/><font size="6" color="#5F6368">{f["marks"][0]}–{f["marks"][1]}</font>', CELL_C),
                     rupees(r["fee"]), str(r["seats"]) if r["seats"] else "—", n(r["y25"])])
    head = ["#", "Course"] + list(d["rounds"]) + ["Target", "Fee / saal", "GM seats", "2025 final"]
    story = _head(f"Target marks · {c['short']}", "Har course ke liye: 2026 ki GM closing rank tak pahunchne ke liye lagbhag kitne marks (out of 180).")
    story += _box(c["name"], [f"{e(c['city'])} · Sirf GM (All India) seats · {len(d['rows'])} courses"])
    story += [_table(head, rows, [15, 177] + [44] * 4 + [44, 48, 32, 35], 2, extra)]
    story += _notes([*d["notes"], "Har round: closing rank aur neeche us rank ke liye lagbhag marks (3 analyses ka beech ka andaaza).",
                     f"Official: {d['official']}"])
    return _pdf(story, f"Target marks · {c['short']}", f"JEELIVE-target-{c['short']}.pdf")


class TargetBitsatPdfIn(BaseModel):
    campus: Literal["all", "Pilani", "Goa", "Hyderabad"] = "all"


def target_bitsat(body: TargetBitsatPdfIn):
    d = rt.target_bitsat()
    rows_in = [r for r in d["rows"] if body.campus in ("all", r["campus"])]
    rows = [[str(i), p(f'<b>{e(r["college"])}</b><br/>{e(r["program"])}'), *[str(h) if h is not None else "—" for h in r["history"]],
             p(f'<font name="JLB" color="#A3122A">{r["cutoff"]}+</font>', CELL_C), f"{r['safe']}+"] for i, r in enumerate(rows_in, 1)]
    head = ["#", "Campus · Program"] + [str(y) for y in d["years"]] + ["Target 2026", "Safe target"]
    story = _head("Target marks · BITSAT 2026", "Har BITS program ka target score (out of 390): official 2026 final cutoff, aur safe target = cutoff + 10.")
    story += _box("Sab campus" if body.campus == "all" else f"BITS {body.campus}", [f"{len(rows)} programs · score / {d['max']}"])
    story += [_table(head, rows, [15, 245] + [36] * 5 + [42, 45], 2)]
    story += _notes(d["notes"])
    return _pdf(story, "Target marks · BITSAT 2026", f"JEELIVE-target-BITSAT-{body.campus}.pdf")


# ---------- Saved colleges + compare ----------
class SavedPdfIn(BaseModel):
    items: List[rt.CompareItem] = Field(min_length=1, max_length=50)
    tags: List[Optional[Literal["safe", "likely", "borderline"]]] = []
    pick: List[int] = Field(default=[], max_length=3)


EXAM = {"jee": "JEE Main", "comedk": "COMEDK", "bitsat": "BITSAT"}


def _round_line(c):
    return "  ·  ".join(f'{e(x["label"])} <b>{n(x["close"])}</b>{" CRL" if x.get("crl") and x["close"] else ""}' for x in c.get("rounds") or [])


def _side_by_side(cols, tags):
    same = all(c["exam"] == cols[0]["exam"] and c.get("rank_label") == cols[0].get("rank_label") and not c.get("missing") and c.get("final") for c in cols)
    finals = [c["final"]["close"] if c.get("final") else 0 for c in cols]
    best = finals.index((min if cols[0].get("higher_is_harder") else max)(finals)) if same else -1
    k = len(cols)
    lead = 78
    wcol = (W - lead) / k
    n_rounds = max(len(c.get("rounds") or []) for c in cols)
    get = lambda c, f: "—" if c.get("missing") else f(c)  # noqa: E731
    rows = [["", *[p(f'<font size="6.3" color="#5F6368">{EXAM[c["exam"]]}</font><br/><b>{e(c.get("title") or "—")}</b>', CELL) for c in cols]],
            ["College", *[p(e(c.get("name")) or "Ye seat 2026 ke data mein nahi mili.", _st(6.8)) for c in cols]],
            ["Branch / course", *[p(e(c.get("sub")), _st(6.8)) for c in cols]],
            ["Seat", *[p(e(c.get("path")), _st(6.8)) for c in cols]],
            ["Final cutoff", *[p(get(c, lambda c: f'<font name="JLB" size="9">{n(c["final"]["close"])}</font>  '
                                              f'<font size="6.2" color="#5F6368">{e(c["final"]["label"])} · {e(c["rank_label"])}</font>'
                                              + ('<br/><font name="JLB" color="#1E7B34" size="6.4">sabse aasaan</font>' if cols.index(c) == best else "")
                                              if c.get("final") else "—"), CELL) for c in cols]]]
    for r in range(n_rounds):
        rows.append(["Round-wise closing" if r == 0 else "", *[
            p(f'<font color="#5F6368">{e(c["rounds"][r]["label"])}</font>  <b>{n(c["rounds"][r]["close"])}</b>'
              + (' <font size="5.8" color="#5F6368">CRL</font>' if c["rounds"][r].get("crl") and c["rounds"][r]["close"] else ""), _st(6.9))
            if not c.get("missing") and r < len(c.get("rounds") or []) else "" for c in cols]])
    rows += [["Pichhla saal", *[p(get(c, lambda c: f'{n(c["prev"]["close"])}  <font size="6" color="#5F6368">{e(c["prev"]["label"])}</font>' if c.get("prev") and c["prev"].get("close") else "—"), _st(6.9)) for c in cols]],
             ["Seats", *[p(get(c, lambda c: f'<b>{c["seats"]}</b>  <font size="6" color="#5F6368">{e(c.get("seats_label") or "")}</font>' if c.get("seats") else "—"), _st(6.9)) for c in cols]],
             ["Fee / saal", *[p(get(c, lambda c: f"<b>{rupees(c['fee'])}</b>" if c.get("fee") else "website par *"), _st(6.9)) for c in cols]],
             ["Aapka chance", *[tag_cell(t) for t in tags]]]
    t = Table(rows, colWidths=[lead] + [wcol] * k)
    style = [("FONT", (0, 0), (0, -1), "JLB", 6.5), ("TEXTCOLOR", (0, 0), (0, -1), MUTED), ("BACKGROUND", (0, 0), (0, -1), HEAD),
             ("BACKGROUND", (1, 0), (-1, 0), BOX), ("LINEBELOW", (0, 0), (-1, 0), 0.9, RED), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, 1), (-1, -1), 0.25, LINE), ("LINEBEFORE", (1, 0), (-1, -1), 0.25, LINE), ("BOX", (0, 0), (-1, -1), 0.4, LINE),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if best >= 0:
        style.append(("BACKGROUND", (best + 1, 1), (best + 1, -2), colors.HexColor("#F3FAF4")))
    style += [("BACKGROUND", (i + 1, len(rows) - 1), (i + 1, len(rows) - 1), colors.HexColor(TAGS[tg][2])) for i, tg in enumerate(tags) if tg]
    t.setStyle(TableStyle(style))
    return t


def saved(body: SavedPdfIn):
    cols = [rt._compare_one(it) for it in body.items]
    tags = [body.tags[i] if i < len(body.tags) else None for i in range(len(cols))]
    pick = [i for i in dict.fromkeys(body.pick) if 0 <= i < len(cols)][:3]
    story = _head("Meri colleges · Compare + saved list", "Saved colleges ki puri details: round-wise closing, final, pichhla saal, seats, fee aur aapka chance.")
    by_exam = ", ".join(f"{EXAM[x]} {sum(1 for c in cols if c['exam'] == x)}" for x in EXAM if any(c["exam"] == x for c in cols))
    story += _box(f"{len(cols)} saved colleges", [by_exam, f"Side by side: {len(pick)} chune hue" if len(pick) >= 2 else None])
    if len(pick) >= 2:
        story += [p("Side by side", H2), _side_by_side([cols[i] for i in pick], [tags[i] for i in pick]), Spacer(1, 10)]
    rows, extra = [], []
    for i, c in enumerate(cols, 1):
        if c.get("missing"):
            rows.append([str(i), EXAM[c["exam"]], p("Ye seat 2026 ke data mein nahi mili. App mein isko dobara save karo.", _st(6.8, color=RED)), "", "", "", ""])
            continue
        name = (f'<b>{e(c["title"])}</b> <font size="6" color="#5F6368">{e(c["place"])}</font><br/>{e(c["sub"])}<br/>'
                f'<font size="6.1" color="#5F6368">{e(c["path"])} · {e(c["rank_label"])}</font>')
        final = (f'<b>{n(c["final"]["close"])}</b> <font size="6" color="#5F6368">{e(c["final"]["label"])}</font>' if c.get("final") else "—") + \
                (f'<br/><font size="6" color="#5F6368">{e(c["prev"]["label"])}: {n(c["prev"]["close"])}</font>' if c.get("prev") and c["prev"].get("close") else "")
        money = (f'<b>{c["seats"]}</b> seats' if c.get("seats") else "") + (f'<br/>{rupees(c["fee"])}' if c.get("fee") else "")
        rows.append([str(i), EXAM[c["exam"]], p(name), p(_round_line(c), _st(6.6)), p(final, CELL_C), p(money or "—", CELL_C), tag_cell(tags[i - 1])])
    t = _table(["#", "Exam", "College · Branch · Seat", "Round-wise closing", "Final · pichhla", "Seats · fee", "Chance"], rows,
               [15, 40, 160, 168, 54, 44, 46], 4, extra, [(6, i, tg) for i, tg in enumerate(tags, 1)])
    story += [p(f"Saved colleges ({len(cols)})", H2), t]
    fee_notes = list(dict.fromkeys(c["fee_note"] for c in cols if not c.get("missing") and not c.get("fee") and c.get("fee_note")))
    story += _notes([*[f"* {x}" for x in fee_notes], "Closing rank: chhota number = mushkil seat. BITSAT mein ulta: zyada cutoff score = mushkil.",
                     "JEE seats = JoSAA 2026 seat matrix (us branch ki saari quota-category seats). COMEDK seats = sirf GM. CRL = CSAB round, CRL par band.",
                     "Aapka chance = jab save kiya tab ke score se."])
    return _pdf(story, "Meri colleges", f"JEELIVE-saved-colleges-{len(cols)}.pdf")


def register(router):
    router.post("/pdf/jee")(jee)
    router.post("/pdf/comedk")(comedk)
    router.post("/pdf/bitsat")(bitsat)
    router.post("/pdf/target/jee")(target_jee)
    router.post("/pdf/target/comedk")(target_comedk)
    router.post("/pdf/target/bitsat")(target_bitsat)
    router.post("/pdf/saved")(saved)
