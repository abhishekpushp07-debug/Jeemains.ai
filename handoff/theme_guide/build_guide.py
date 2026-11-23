#!/usr/bin/env python3
"""Builds the website hand-off PDF for the app's glossy theme.

    cd /app/handoff/theme_guide && /usr/local/bin/python3.11 build_guide.py

Writes guide.html (open it in a browser to see the pieces move) and JEELIVE_App_Glossy_Theme_Guide.pdf.
Every example piece in the document is drawn by shine.css + shine.js, the same files printed in its appendix.
Screenshots in shots/ come from the app's web preview (QA learner, read-only).
"""
import asyncio
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
THEME = (HERE.parents[1] / "frontend" / "src" / "theme.ts").read_text()
SHINE_CSS = (HERE / "shine.css").read_text()
SHINE_JS = (HERE / "shine.js").read_text()
PDF = HERE / "JEELIVE_App_Glossy_Theme_Guide.pdf"

# ---------------------------------------------------------------- colours (checked against theme.ts below)
FIVE = ["#FF3D9A", "#FFB020", "#10C7A8", "#3B82F6", "#9B5CFF", "#FF3D9A"]
INK = "#0F0F12"
TABS = {
    "completed": dict(label="Completed", name="Baby pink", on=("#FFAFC9", "#FF82AB"), rest=("#FFD3E1", "#FFBDD2"),
                      edge=["#FF2D7A", "#B45CFF", "#FF8A6B", "#FF2D7A"], glow="#FF4D8F", edge_name="rose, orchid, coral", count="5"),
    "progress": dict(label="In progress", name="Yellow", on=("#FFEE5C", "#FFD60A"), rest=("#FFF29A", "#FFE455"),
                     edge=["#FF7A00", "#FF4F3A", "#FFB300", "#FF7A00"], glow="#FFA200", edge_name="tangerine, vermilion, gold", count="0"),
    "saved": dict(label="Saved", name="Sky blue", on=("#9BDCFF", "#52BDFF"), rest=("#C4E8FF", "#96D5FF"),
                  edge=["#0A84FF", "#4F46E5", "#8E7BFF", "#0A84FF"], glow="#1E90FF", edge_name="azure, indigo, periwinkle", count="0"),
}
PASTEL = {
    "today": dict(label="Today", frm="#FFDDBF", to="#FFB9CC", ink="#8A3350", body="#5B4048", cta="#FFE3D6",
                  edge=["#FF6B4A", "#FF2D7A", "#FFB300", "#FF6B4A"], edge_name="coral, rose, gold", name="Peach to pink"),
    "done": dict(label="Done", frm="#DDF5C8", to="#BCE8A2", ink="#3A6B1F", body="#44603A", cta="#DDF5C8",
                 edge=["#22A45D", "#9BD22F", "#10B5A0", "#22A45D"], edge_name="emerald, lime, teal", name="Soft green"),
    "upcoming": dict(label="Upcoming", frm="#C7F2EC", to="#96D2FF", ink="#0F5F58", body="#2C5753", cta="#D2F6F1",
                     edge=["#10B5A0", "#1E90FF", "#8E7BFF", "#10B5A0"], edge_name="teal, azure, lavender", name="Teal to sky blue"),
    "missed": dict(label="Missed", frm="#F3E7D8", to="#ECD6DC", ink="#7A4A3C", body="#5E4A44", cta="#F3E7D8",
                   edge=["#C08552", "#D4728C", "#E0B15C", "#C08552"], edge_name="bronze, dusty rose, sand", name="Sand"),
}
PASTEL_GLOSS, PASTEL_GLINT = "rgba(255,255,255,0.55)", "rgba(255,255,255,0.92)"
CHIPS = {
    "upcoming": dict(label="Upcoming", name="Blood red", frm="#C1121F", to="#8A0B15", ink="#FFFFFF", soft="#FFE9EC",
                     edge=["#FFC857", "#FF5C7A", "#FFD9E0", "#FFC857"], edge_name="gold, rose, pearl",
                     gloss="rgba(255,255,255,0.26)", glint="rgba(255,255,255,0.58)"),
    "over": dict(label="Completed", name="Parrot green", frm="#96EA3A", to="#46BE1B", ink="#0F0F12", soft="#123F08",
                 edge=["#FFE14D", "#0B8A43", "#DFFF94", "#FFE14D"], edge_name="sun yellow, emerald, lime",
                 gloss="rgba(255,255,255,0.42)", glint="rgba(255,255,255,0.85)"),
    "today": dict(label="Today", name="Peach to pink", frm="#FFDDBF", to="#FFB9CC", ink="#111114", soft="#8A3350",
                  edge=["#FF6B4A", "#FF2D7A", "#FFB300", "#FF6B4A"], edge_name="coral, rose, gold",
                  gloss=PASTEL_GLOSS, glint=PASTEL_GLINT),
}
CHOSEN_EDGE = ["#0F0F12", "#0F0F12", "#FFC857", "#0F0F12", "#0F0F12"]
TILE_GLOSS, TILE_GLINT = "rgba(255,255,255,0.22)", "rgba(255,255,255,0.5)"
TILES = {
    "rank": dict(title="RANK PREDICTOR", value="marks se rank", icon="podium", name="Maroon", frm="#BC1F55", to="#7C1038", chip="#93143F",
                 line="#FF9DBA", soft="#FFE1EA", ink="#FFFFFF", badge="#7C1038", edge=["#FF7AA2", "#FFC857", "#FFD9E4", "#FF7AA2"],
                 edge_name="rose, gold, blush", gloss=TILE_GLOSS, glint=TILE_GLINT, new=False),
    "pct": dict(title="PERCENTILE SE RANK", value="NTA percentile", icon="chart", name="Indigo", frm="#5B4BE0", to="#3323A6", chip="#4132BC",
                line="#B9B0FF", soft="#E6E2FF", ink="#FFFFFF", badge="#3323A6", edge=["#9D8CFF", "#5CC8FF", "#E0DBFF", "#9D8CFF"],
                edge_name="lavender, sky, pale lilac", gloss=TILE_GLOSS, glint=TILE_GLINT, new=True),
    "target": dict(title="TARGET MARKS", value="college ke liye", icon="target", name="Teal", frm="#0A7B70", to="#06574F", chip="#07665D",
                   line="#6FE9D7", soft="#DFFBF6", ink="#FFFFFF", badge="#06574F", edge=["#3DE0C8", "#B5F23D", "#D5FFF7", "#3DE0C8"],
                   edge_name="aqua, lime, mint", gloss=TILE_GLOSS, glint=TILE_GLINT, new=True),
    "college": dict(title="COLLEGE PREDICTOR", value="colleges + cutoffs", icon="school", name="Blood red", frm="#D10F2A", to="#B00C22",
                    chip="#A80B21", line="#FF6B78", soft="#FFE1E5", ink="#FFFFFF", badge="#B00C22", edge=["#FFC857", "#FF8FA0", "#FFE1E5", "#FFC857"],
                    edge_name="gold, rose, pearl", gloss=TILE_GLOSS, glint=TILE_GLINT, new=False),
    "compare": dict(title="COLLEGE COMPARE", value="side by side", icon="compare", name="Gold", frm="#F2C14E", to="#C98C16", chip="#FFE08A",
                    line="#8A5D00", soft="#3A2700", ink="#1C1300", badge="#1C1300", edge=["#FFF3C4", "#FF8A3D", "#FFD60A", "#FFF3C4"],
                    edge_name="cream, tangerine, sun yellow", gloss="rgba(255,255,255,0.5)", glint="rgba(255,255,255,0.9)", new=True),
    "dream": dict(title="DREAM COLLEGE", value="kitne marks door", icon="shoot", name="Violet", frm="#8E3BD9", to="#58169A", chip="#6C22B5",
                  line="#D2A8FF", soft="#F0E2FF", ink="#FFFFFF", badge="#58169A", edge=["#C9A0FF", "#FF8AD8", "#7FE7FF", "#C9A0FF"],
                  edge_name="lilac, pink, cyan", gloss=TILE_GLOSS, glint=TILE_GLINT, new=True),
}
LIGHT_BAND = dict(gloss="rgba(255,255,255,0.46)", glint="rgba(255,255,255,0.9)")
DEEP_BAND = dict(gloss="rgba(255,255,255,0.18)", glint="rgba(255,255,255,0.5)")
FORMS = {
    "rank": dict(name="Rank predictor", colour="Bright yellow", title="Your marks", icon="podium", ink="#FFD60A", soft="rgba(255,214,10,0.12)",
                 line="rgba(255,214,10,0.62)", on="#0B0B0F", text="#FFD60A", edge=["#FFD60A", "#FF8A00", "#FFF3B0", "#FFD60A"],
                 edge_name="yellow, tangerine, cream", band="light"),
    "pct": dict(name="Percentile se rank", colour="Teal", title="Your NTA percentile", icon="chart", ink="#2DE1C2", soft="rgba(45,225,194,0.12)",
                line="rgba(45,225,194,0.62)", on="#0B0B0F", text="#2DE1C2", edge=["#2DE1C2", "#5CC8FF", "#D5FFF7", "#2DE1C2"],
                edge_name="aqua, sky blue, mint", band="light"),
    "target": dict(name="Target marks", colour="Lime", title="Aapki details", icon="target", ink="#B5F23D", soft="rgba(181,242,61,0.12)",
                   line="rgba(181,242,61,0.62)", on="#0B0B0F", text="#B5F23D", edge=["#B5F23D", "#FFE14D", "#22C55E", "#B5F23D"],
                   edge_name="lime, sun yellow, emerald", band="light"),
    "college": dict(name="College predictor", colour="Blood red", title="Your score", icon="school", ink="#D10F2A", soft="rgba(209,15,42,0.16)",
                    line="rgba(255,59,78,0.75)", on="#FFFFFF", text="#FF4D5E", edge=["#FF3B4E", "#FFC857", "#FF8FA0", "#FF3B4E"],
                    edge_name="ruby, gold, rose", band="deep"),
    "compare": dict(name="College compare", colour="Sky blue", title="Colleges compare", icon="compare", ink="#4CC3FF", soft="rgba(76,195,255,0.12)",
                    line="rgba(76,195,255,0.62)", on="#0B0B0F", text="#4CC3FF", edge=["#4CC3FF", "#2F80FF", "#B9B0FF", "#4CC3FF"],
                    edge_name="sky blue, azure, lavender", band="light"),
    "dream": dict(name="Dream college", colour="Violet", title="", icon="shoot", ink="#7B2CBF", soft="rgba(123,44,191,0.18)",
                  line="rgba(185,131,255,0.65)", on="#FFFFFF", text="#B983FF", edge=["#B983FF", "#FF8AD8", "#7FE7FF", "#B983FF"],
                  edge_name="lilac, pink, cyan", band="deep"),
}
SERIES_EDGE = ["#FF2D4A", "#FFC857", "#FF7A93", "#FF2D4A"]
SECTIONS = ["Overview", "Performance", "Score Potential", "Attempt Quality", "Time", "Difficulty", "Question Journey", "Qs by Qs"]


def check_against_theme():
    """Every colour typed above must exist in the app's theme.ts, so the document cannot drift from the app."""
    theme = THEME.replace(" ", "").upper()
    seen, missing = set(), []

    def walk(v):
        if isinstance(v, str):
            if re.fullmatch(r"#[0-9A-Fa-f]{6}", v) or v.startswith("rgba("):
                seen.add(v)
        elif isinstance(v, dict):
            [walk(x) for x in v.values()]
        elif isinstance(v, (list, tuple)):
            [walk(x) for x in v]

    for group in (FIVE, TABS, PASTEL, CHIPS, CHOSEN_EDGE, TILES, FORMS, SERIES_EDGE, LIGHT_BAND, DEEP_BAND, PASTEL_GLOSS, PASTEL_GLINT):
        walk(group)
    for c in sorted(seen):
        if c.replace(" ", "").upper() not in theme:
            missing.append(c)
    if missing:
        raise SystemExit("Not in theme.ts: " + ", ".join(missing))
    return len(seen)


# ---------------------------------------------------------------- small HTML helpers
def esc(s):
    return html.escape(s, quote=False)


def sw(c, wide=False):
    """A colour chip with its value. Whites with alpha are shown over a dark chip so they can be seen."""
    back = f"linear-gradient({c},{c}), #2B2B33" if c.startswith("rgba(255") else c
    return f'<span class="sw"><i{" class=wide" if wide else ""} style="background:{back}"></i><code>{c}</code></span>'


def grad(a, b):
    return f'<span class="sw"><i class="wide" style="background:linear-gradient(135deg,{a},{b})"></i><code>{a} &rarr; {b}</code></span>'


def edge(colours, name=""):
    """The colours that run round a piece, as a strip, with their values (the first colour comes back at the end)."""
    words = f"<span>{name}</span>" if name else ""
    return f'<span class="edge"><i style="background:linear-gradient(90deg,{",".join(colours)})"></i><code>{" ".join(colours[:-1])}</code>{words}</span>'


def table(head, rows):
    out = "<table><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>"
    for r in rows:
        out += "<tr>" + "".join(f'<td{" class=k" if i == 0 else ""}>{c}</td>' for i, c in enumerate(r)) + "</tr>"
    return out + "</table>"


def params(**kv):
    return '<div class="params">' + "".join(f"<span>{k.replace('_', ' ')} <b>{v}</b></span>" for k, v in kv.items()) + "</div>"


ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "download": '<path d="M12 4v10M8 10l4 4 4-4M5 19h14"/>',
    "lock": '<rect x="6" y="11" width="12" height="9" rx="2"/><path d="M9 11V8a3 3 0 0 1 6 0v3"/>',
    "fire": '<path d="M12 3c1 3 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 1-9z"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6-5.4-3-5.4 3 1.1-6L3.2 9.4l6.1-.8z"/>',
    "cancel": '<circle cx="12" cy="12" r="8"/><path d="M6.5 17.5l11-11"/>',
    "podium": '<path d="M4 20v-6h5v6M9 20V8h6v12M15 20v-9h5v9M3 20h18"/>',
    "chart": '<path d="M4 19h16M5 15l4-5 4 3 6-8"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="0.8"/>',
    "school": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11.5V16c2 2 10 2 12 0v-4.5"/>',
    "compare": '<path d="M4 8h14M14 4l4 4-4 4M20 16H6M10 12l-4 4 4 4"/>',
    "shoot": '<path d="M14 4l1.8 3.7 4 .6-2.9 2.8.7 4-3.6-1.9-3.6 1.9.7-4L8.2 8.3l4-.6z"/><path d="M3 21l6-6M4 15l2-2M9 20l2-2"/>',
    "person": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c1-4 4-5 7-5s6 1 7 5"/>',
    "people": '<circle cx="9" cy="9" r="3"/><circle cx="17" cy="10" r="2.4"/><path d="M3 19c1-3 3-4 6-4s5 1 6 4M15 15c3 0 5 1 6 4"/>',
    "calendar": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/>',
}


def ico(name, size=16, colour="currentColor", stroke=1.8):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{colour}" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


STAR = "M12 0 C12.8 7 17 11.2 24 12 C17 12.8 12.8 17 12 24 C11.2 17 7 12.8 0 12 C7 11.2 11.2 7 12 0 Z"
SPOTS = [(15, 0), (100, 34), (68, 100)]
STARS = [FIVE[1], FIVE[0], FIVE[3]]
FACETS = [("2,30 30,8 18,30", 0.5), ("30,8 34,30 18,30", 0.9), ("30,8 43.3,8 34,30", 0.35), ("43.3,8 50,30 34,30", 0.75),
          ("43.3,8 56.7,8 50,30", 0.95), ("56.7,8 66,30 50,30", 0.4), ("56.7,8 70,8 66,30", 0.8), ("70,8 82,30 66,30", 0.3),
          ("70,8 98,30 82,30", 0.6), ("2,30 18,30 50,78", 0.3), ("18,30 34,30 50,78", 0.7), ("34,30 50,30 50,78", 0.95),
          ("50,30 66,30 50,78", 0.5), ("66,30 82,30 50,78", 0.85), ("82,30 98,30 50,78", 0.4)]


def diamond(opacity):
    facets = "".join(f'<polygon points="{p}" fill="#fff" fill-opacity="{o}" stroke="#fff" stroke-opacity="0.75" stroke-width="0.7" stroke-linejoin="round"/>'
                     for p, o in FACETS)
    return f'<i class="gem" style="opacity:{opacity}"><svg width="46" height="36.8" viewBox="-8 -8 116 96">{facets}</svg></i>'


def shine(inner, r, ring, edge=FIVE, tones=None, swap=True, backdrop="", gloss=None, glint=None, band=0, part=40, corner=False,
          delay=0, sparkles=0, face="", cls="", glow="", extra=""):
    """One piece wrapped in the Shine: the exact markup shine.css expects."""
    v = f"--r:{r}px;--ring:{ring}px;"
    if ring and edge is not FIVE:
        v += f"--edge:{','.join(edge)};"
    if tones:
        v += f"--tone-a:{tones[0]};--tone-b:{tones[1]};"
    if gloss:
        v += f"--gloss:{gloss};"
    if glint:
        v += f"--glint:{glint};--band:{band}px;"
    if delay:
        v += f"--delay:{delay}ms;"
    if glow:
        v += f"box-shadow:{glow};"
    attrs = (f' data-part="{part}"' if glint else "") + (" data-corner" if corner else "")
    out = f'<div class="jl-shine{" " + cls if cls else ""}"{attrs} style="{v}{extra}"><div class="jl-ring">'
    out += '<i class="jl-edge"></i>' if ring else ""
    out += f'<div class="jl-face{" " + face if face else ""}">'
    if tones:
        out += '<i class="jl-tones"></i>' + ('<i class="jl-swap"></i>' if swap else "")
    out += backdrop
    out += '<i class="jl-gloss"></i>' if gloss else ""
    out += '<i class="jl-glint"></i>' if glint else ""
    out += inner + "</div></div>"
    for i in range(sparkles):
        x, y = SPOTS[i]
        out += (f'<svg class="jl-spark" style="left:{x}%;top:{y}%;animation-delay:{500 + i * 1733}ms" viewBox="0 0 24 24">'
                f'<path d="{STAR}" fill="{STARS[i]}"/></svg>')
    return out + "</div>"


def code(text, long=False):
    return f'<pre class="code{" long" if long else ""}">{esc(text.strip(chr(10)))}</pre>'


def figure(body, caption, kind="WEB"):
    return f"<figure>{body}<figcaption><b>{kind}</b> &nbsp;{caption}</figcaption></figure>"


def crop(name, width):
    return f'<img class="crop" src="shots/{name}.jpg" width="{width}">'


def phone(name, caption="App screen", short=False):
    return f'<figure class="phone{" short" if short else ""}"><img src="shots/{name}.jpg"><figcaption><b>APP</b> &nbsp;{caption}</figcaption></figure>'


# ---------------------------------------------------------------- the example pieces
def ex_pills():
    pills = '<div class="x-pill-on"><span class="mono">1</span><span>Overview</span></div>'
    for i, name in enumerate(SECTIONS[1:5], start=1):
        pills += shine(f'<span class="mono">{i + 1}</span><span>{name}</span>', 999, 2, tones=("#A8DCFF", "#8CEBD6"),
                       gloss="rgba(255,255,255,0.78)", glint="rgba(255,255,255,0.95)", band=22, part=32, delay=i * 160, face="x-navface")
    return (f'<div class="x x-bar"><div class="x-mode"><div class="on">{ico("person", 15)}Personal</div><div>{ico("people", 15)}Comparative</div></div>'
            f'<div class="x-nav">{pills}</div></div>')


def ex_report():
    pdf = ('<svg width="32" height="32" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3" fill="#0F0F12"/>'
           '<text x="12" y="14.6" text-anchor="middle" font-family="Figtree" font-weight="800" font-size="6.6" fill="#fff">PDF</text></svg>')
    inner = (f'<i class="c1"></i><i class="c2"></i><div class="x-badge">{pdf}</div>'
             '<div class="x-words"><span class="t">Report download</span><span class="s">Poora analysis ek PDF mein</span></div>'
             f'<div class="x-go">{ico("download", 22)}</div>')
    return '<div class="x">' + shine(inner, 22, 3, tones=("#86CFFB", "#66E0CC"), gloss="rgba(255,255,255,0.46)", glint="rgba(255,255,255,0.92)",
                                     band=72, part=46, sparkles=3, face="x-reportface", cls="x-report",
                                     glow="0 8px 16px rgba(56,189,248,0.34)", extra="background:#86CFFB;") + "</div>"


def rgba(hex_colour, alpha):
    h = hex_colour.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def ex_tabs(open_key):
    out = ""
    for i, (key, t) in enumerate(TABS.items()):
        on = key == open_key
        inner = f'<span>{t["label"]}</span><span class="n">{t["count"]}</span>'
        out += shine(inner, 999, 3 if on else 2, edge=t["edge"], tones=t["on"] if on else t["rest"], gloss="rgba(255,255,255,0.62)",
                     glint="rgba(255,255,255,0.95)", band=26, part=34, delay=i * 220, face="x-tabface on" if on else "x-tabface",
                     glow=f'0 4px 9px {rgba(t["glow"], 0.45)}' if on else "", extra=f'background:{t["on"][1]};' if on else "")
    return f'<div class="x x-tabs">{out}</div>'


def ex_home():
    inner = (
        '<div class="x-top"><div class="x-live">ALL INDIA SERIES</div><span style="flex:1"></span>'
        '<span class="x-a70" style="font-size:11px;font-weight:700;letter-spacing:2px">50 DAYS</span></div>'
        '<div class="x-body"><div style="flex:1;display:flex;flex-direction:column;gap:6px">'
        '<span style="font-size:10.5px;font-weight:700;letter-spacing:2px;color:#C7F2EC">STARTS 9 DEC</span>'
        '<span style="font-size:23px;font-weight:800;letter-spacing:-0.3px">50 daily full mocks</span></div>'
        '<div class="x-pring"><span style="font-size:18px;font-weight:800">0</span><span class="x-a70" style="font-size:9.5px;font-weight:700">of 50</span></div></div>'
        '<div class="x-facts"><div><b>75</b><span>questions</span></div><div><b>180</b><span>minutes</span></div><div><b>+4 / &minus;1</b><span>marking</span></div></div>'
        '<div class="x-rule"></div>'
        '<div class="x-streakrow"><span class="x-a70">9 Dec &ndash; 27 Jan &middot; one mock a day</span><span class="x-ai">100% AI</span></div>'
        f'<div class="x-redcta">Opens 9 Dec {ico("calendar", 18)}</div>')
    return '<div class="x">' + shine(inner, 28, 2, edge=SERIES_EDGE, backdrop='<i class="bg"></i><i class="sheen"></i>', gloss="rgba(255,255,255,0.11)",
                                     glint="rgba(255,255,255,0.26)", band=96, part=46, corner=True, face="x-aitsface", cls="x-aits") + "</div>"


def ex_streak():
    def fact(icon, colour, bg, value, label):
        return (f'<div class="x-fact"><div class="ic" style="background:{bg}">{ico(icon, 15, colour)}</div>'
                f'<div><div class="v">{value}</div><div class="l">{label}</div></div></div>')
    cups = "".join(f'<div class="x-cup" style="left:{d * 2}%"><div class="dot">{ico("lock", 11)}</div>{d}d</div>' for d in (7, 15, 30, 45, 50))
    inner = (
        '<div class="x-row"><div class="x-ring"><span style="font-size:24px;font-weight:800">0</span>'
        '<span class="x-rose" style="font-size:10px;font-weight:700">/50 days</span></div><div class="x-factcol">'
        + fact("fire", "#EA580C", "#FFF0E6", "0-day streak", "current") + fact("star", "#B7791F", "#FFF6DB", "Best 0", "longest run")
        + fact("cancel", "#7A4A3C", "#FBEFF1", "0 skipped", "days missed") + "</div></div>"
        '<span class="x-rose" style="font-size:11.5px">Starts 9 Dec. No early points, no pretend progress.</span>'
        f'<div class="x-track"><div class="line"></div>{cups}</div>')
    return '<div class="x">' + shine(inner, 24, 2, edge=TABS["completed"]["edge"], tones=("#FFDCE8", "#FFB5CE"), gloss=PASTEL_GLOSS, glint=PASTEL_GLINT,
                                     band=84, part=46, corner=True, face="x-streakface", cls="x-streak") + "</div>"


def ex_daycards():
    words = {
        "today": ("DAY 3 &middot; TODAY", "11 DEC", "All India JEE Mains &middot; Test 03", "cta", "Start today&rsquo;s test"),
        "done": ("DAY 2 &middot; COMPLETED", "10 DEC", "All India JEE Mains &middot; Test 02", "cta", "View result"),
        "upcoming": ("DAY 4 &middot; UPCOMING", "12 DEC", "All India JEE Mains &middot; Test 04", "note", "Opens 12 Dec &middot; 12:01 AM IST"),
        "missed": ("DAY 1 &middot; MISSED", "9 DEC", "All India JEE Mains &middot; Test 01", "cta", "Practise this paper"),
    }
    out = ""
    for key, p in PASTEL.items():
        left, right, title, kind, action = words[key]
        foot = (f'<span class="x-cta" style="color:{p["cta"]}">{action}</span>' if kind == "cta"
                else f'<span class="x-note" style="color:{p["body"]}">{action}</span>')
        inner = (f'<div class="x-between"><span class="x-caps" style="color:{p["ink"]}">{left}</span><span class="x-caps" style="color:{p["ink"]}">{right}</span></div>'
                 f'<span class="x-daytitle">{title}</span>{foot}')
        out += shine(inner, 22, 2, edge=p["edge"], tones=(p["frm"], p["to"]), gloss=PASTEL_GLOSS, glint=PASTEL_GLINT, band=72, part=46, corner=True,
                     face="x-dayface")
    return f'<div class="x x-days">{out}</div>'


def chip(i, day, kind, chosen=False, word="DAY"):
    c = CHIPS[kind]
    inner = f'<span class="s" style="color:{c["soft"]}">{word}</span><span class="d" style="color:{c["ink"]}">{day}</span>'
    piece = shine(inner, 16, 3 if chosen else 2, edge=CHOSEN_EDGE if chosen else c["edge"], tones=(c["frm"], c["to"]), swap=False, gloss=c["gloss"],
                  glint=c["glint"], band=18, part=38, corner=True, delay=(i % 8) * 140, face="x-chipface on" if chosen else "x-chipface")
    return f'<div class="x-chipwrap">{piece}<div class="x-dot" style="background:{INK if chosen else "transparent"}"></div></div>'


def ex_chips():
    row = [chip(0, 1, "over"), chip(1, 2, "over"), chip(2, 3, "today", word="TODAY"), chip(3, 4, "upcoming"), chip(4, 5, "upcoming", chosen=True),
           chip(5, 6, "upcoming"), chip(6, 7, "upcoming")]
    return f'<div class="x x-chips">{"".join(row)}</div>'


def ex_map():
    cols = ""
    for c in range(8):
        cells = ""
        for d in range(c * 7 + 1, min(50, c * 7 + 7) + 1):
            kind = "over" if d < 13 else "today" if d == 13 else "upcoming"
            k = CHIPS[kind]
            marked = d in (13, 24)
            cells += (f'<div class="x-cell" style="background-image:linear-gradient(135deg,{k["frm"]},{k["to"]});color:{k["ink"]};'
                      f'{"border-color:#0F0F12" if marked else ""}">{d if marked else ""}</div>')
        cols += f'<div class="x-col">{cells}</div>'
    legend = "".join(f'<span><i style="background:linear-gradient(135deg,{CHIPS[k]["frm"]},{CHIPS[k]["to"]})"></i>{CHIPS[k]["label"]}</span>'
                     for k in ("over", "today", "upcoming"))
    return f'<div class="x x-map"><div class="x-grid">{cols}</div><div class="x-legend">{legend}</div></div>'


def ex_tiles(chosen="rank"):
    keys, rows = list(TILES), ""
    for r in range(3):
        row = ""
        for c in range(2):
            key = keys[r * 2 + c]
            t, on = TILES[key], keys[r * 2 + c] == chosen
            accent = FORMS[key]["text"]
            badge = f'<span class="x-new" style="color:{t["badge"]}">NEW</span>' if t["new"] and not on else ""
            inner = (f'<div class="ic" style="background:{t["chip"]};border-color:{t["line"]}">{ico(t["icon"], 17, t["ink"], 1.4)}{badge}</div>'
                     f'<div class="tx"><span class="tt" style="color:{t["ink"]}">{t["title"]}</span><span class="vv" style="color:{t["soft"]}">{t["value"]}</span></div>')
            row += shine(inner, 18, 3 if on else 2, edge=[accent, "#FFFFFF", accent, "#FFFFFF", accent] if on else t["edge"], tones=(t["frm"], t["to"]),
                         swap=False, backdrop=diamond(0.75 if on else 0.45), gloss=t["gloss"], glint=t["glint"], band=30, part=40, corner=True,
                         delay=(r * 2 + c) * 200, face="x-tileface on" if on else "x-tileface",
                         glow=f"0 4px 18px {rgba(accent, 0.7)}" if on else "", extra=f'background:{t["to"]};')
        rows += f'<div class="r">{row}</div>'
    return f'<div class="x x-rank">{rows}</div>'


def form_head(key, title=None):
    f = FORMS[key]
    band = LIGHT_BAND if f["band"] == "light" else DEEP_BAND
    inner = (f'<div class="ic" style="background:{f["on"]}">{ico(f["icon"], 16, f["ink"], 1.6)}</div>'
             f'<div style="flex:1;min-width:0;color:{f["on"]}"><div class="nm">{f["name"].upper()}</div><div class="ti">{title or f["title"]}</div></div>')
    return (f'<div class="x-headbleed" style="background:{f["ink"]}">'
            + shine(inner, 0, 0, gloss=band["gloss"], glint=band["glint"], band=34, part=36, face="x-headface") + "</div>")


def ex_form(key, body):
    f = FORMS[key]
    return '<div class="x">' + shine(form_head(key) + body, 22, 2, edge=f["edge"], backdrop='<i class="wash"></i>', face="x-formface", cls="x-form",
                                     glow=f'0 0 18px {rgba(f["text"], 0.45)}', extra=f'--soft:{f["soft"]};background:#121218;') + "</div>"


def form_body(key, label, placeholder, button):
    f = FORMS[key]
    toggles = "".join(f'<div class="x-toggle"{style}>{name}</div>' for name, style in
                      [("General", f' style="background:{f["ink"]};border-color:{f["ink"]};color:{f["on"]}"'), ("EWS", ""), ("OBC-NCL", ""), ("SC", "")])
    return (f'<div class="x-label">{label}</div><div class="x-input" style="border-color:{f["line"]}">{placeholder}</div>'
            f'<div class="x-toggles">{toggles}</div>'
            f'<div class="x-btn" style="background:{f["ink"]};color:{f["on"]}">{button} {ico("arrow", 18)}</div>')


def ex_switch(key):
    f = FORMS[key]
    return (f'<div class="x x-switch"><div style="border-color:{f["line"]};background:{f["soft"]};color:{f["text"]};font-weight:700">JEE Main</div>'
            "<div>COMEDK</div></div>")


def ex_heads():
    out = ""
    for key in ("rank", "pct", "target", "college", "compare"):
        f = FORMS[key]
        out += '<div class="x">' + shine(form_head(key), 22, 2, edge=f["edge"], backdrop='<i class="wash"></i>', face="x-formface", cls="x-form",
                                         glow=f'0 0 18px {rgba(f["text"], 0.45)}', extra=f'--soft:{f["soft"]};background:#121218;padding-bottom:0;') + "</div>"
    return f'<div class="x-heads">{out}</div>'


def ex_layers():
    """The Shine taken apart: the same small card with one more layer each time."""
    tones, base = ("#86CFFB", "#66E0CC"), dict(r=18, ring=3, face="x-layer")
    steps = [
        ("1 &middot; Running edge", "Colours slide round all four sides.", shine("", **{**base, "face": "x-layer white"})),
        ("2 &middot; Face colours", "Two colours, corner to corner. They slowly change places.", shine("", **base, tones=tones)),
        ("3 &middot; Gloss", "Soft white light on the upper 56 %.", shine("", **base, tones=tones, gloss="rgba(255,255,255,0.6)")),
        ("4 &middot; Glint", "A band of glass light crosses, then waits.", shine("", **base, tones=tones, gloss="rgba(255,255,255,0.6)",
                                                                              glint="rgba(255,255,255,0.95)", band=30, part=46)),
        ("5 &middot; Content", "Words and icons always stay above the light.", shine('<b style="font-size:13px">Report</b>', **base, tones=tones,
                                                                                    gloss="rgba(255,255,255,0.6)", glint="rgba(255,255,255,0.95)", band=30, part=46)),
    ]
    return '<div class="layers x">' + "".join(f'<div>{piece}<div class="cap"><b>{name}</b>{text}</div></div>' for name, text, piece in steps) + "</div>"


def snippet(note, r, ring, edge=None, tones=None, swap=True, gloss=None, glint=None, band=0, part=40, corner=False, delay="", content="... your content ...",
            backdrop="", extra=""):
    """The copy-and-paste markup of one piece, printed as text."""
    v = [f"--r:{r}px", f"--ring:{ring}px"]
    if edge:
        v.append("--edge:" + ", ".join(edge))
    if tones:
        v += [f"--tone-a:{tones[0]}", f"--tone-b:{tones[1]}"]
    if gloss:
        v.append(f"--gloss:{gloss}")
    if glint:
        v += [f"--glint:{glint}", f"--band:{band}px"]
    if delay:
        v.append(f"--delay:{delay}")
    if extra:
        v.append(extra)
    attrs = (f' data-part="{part}"' if glint else "") + (" data-corner" if corner else "")
    layers = ('<i class="jl-tones"></i>' if tones else "") + ('<i class="jl-swap"></i>' if tones and swap else "") + backdrop \
        + ('<i class="jl-gloss"></i>' if gloss else "") + ('<i class="jl-glint"></i>' if glint else "")
    lines, line = [], ""
    for item in v:                                   # settings wrapped so that no line is cut in print
        if line and len(line) + len(item) > 88:
            lines.append(line)
            line = ""
        line += ("; " if line else "") + item
    lines.append(line)
    style = (";" + chr(10) + "            ").join(lines)
    ring_open = '<div class="jl-ring">' + ('<i class="jl-edge"></i>' if ring else "")
    return (f"<!-- {note} -->" + chr(10)
            + f'<div class="jl-shine"{attrs}' + chr(10) + f'     style="{style}">' + chr(10)
            + f"  {ring_open}" + chr(10)
            + '    <div class="jl-face">' + chr(10) + (f"      {layers}" + chr(10) if layers else "")
            + f"      {content}" + chr(10) + "    </div>" + chr(10) + "  </div>" + chr(10) + "</div>")


# ---------------------------------------------------------------- the document

def fmt(template, scope):
    """An f-string that may hold '#' and backslashes in its {expressions} (Python 3.11 f-strings may not)."""
    out, i, n = [], 0, len(template)
    while i < n:
        if template[i] != "{":
            out.append(template[i])
            i += 1
            continue
        depth, j, quote = 1, i + 1, None
        while j < n and depth:
            c = template[j]
            if quote:
                if template.startswith(quote, j):
                    j += len(quote) - 1
                    quote = None
                elif c == "\\":
                    j += 1
            elif template.startswith(("'''", '"""'), j):
                quote = template[j:j + 3]
                j += 2
            elif c in "'\"":
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        out.append(str(eval(template[i + 1:j - 1], {**globals(), **scope})))
        i = j
    return "".join(out)

def h2(num, title):
    return f'<h2><span class="n">{num}</span>{title}</h2>'


def cover():
    toc = [("1", "What changed (before &rarr; after)"), ("2", "The Shine effect: how it is built"), ("2.4", "Web code: how to use it"),
           ("3.1", "Analysis &middot; section pills"), ("3.2", "Analysis &middot; Report download card"), ("3.3", "My Tests &middot; three tabs"),
           ("3.4", "Home &middot; All India Series card"), ("3.5", "Series page &middot; streak card"), ("3.6", "Series page &middot; day cards"),
           ("3.7", "Series page &middot; day chips"), ("3.8", "Series page &middot; 50-day map"), ("3.9", "Rank &middot; six tool tiles"),
           ("3.10", "Rank &middot; form panels"), ("4", "Rules: motion, speed, sizes, contrast"), ("5", "Checklist for the website"),
           ("A", "shine.css (full file)"), ("B", "shine.js (full file)")]
    rules = [
        ("Baby pink", grad("#FFAFC9", "#FF82AB"), "My Tests &rarr; <b>Completed</b> tab. Series page &rarr; streak card (softer: " + grad("#FFDCE8", "#FFB5CE") + ")"),
        ("Yellow", grad("#FFEE5C", "#FFD60A"), "My Tests &rarr; <b>In progress</b> tab. Rank &rarr; Rank predictor form (" + sw("#FFD60A") + ")"),
        ("Sky blue", grad("#9BDCFF", "#52BDFF"), "My Tests &rarr; <b>Saved</b> tab. Rank &rarr; College compare form (" + sw("#4CC3FF") + ")"),
        ("Sky blue + light teal", grad("#A8DCFF", "#8CEBD6"), "Analysis &rarr; section pills and Report download card. Series &rarr; <b>Upcoming</b> day card (" + grad("#C7F2EC", "#96D2FF") + ")"),
        ("Blood red", grad("#C1121F", "#8A0B15"), "Series &rarr; every day <b>still to come</b> (day chips and 50-day map). Rank &rarr; College predictor (" + sw("#D10F2A") + ")"),
        ("Parrot green", grad("#96EA3A", "#46BE1B"), "Series &rarr; every day that is <b>over</b> (day chips and 50-day map), whether its paper was taken or missed"),
        ("Five-colour edge", edge(FIVE), "Running edge of the Analysis pills and the Report card: pink, gold, aqua, blue, violet"),
    ]
    return f"""
<section class="first cover">
  <div class="brand">JEELIVE.AI</div>
  <div class="eyebrow">App &rarr; Website hand-off &middot; glossy theme</div>
  <h1>Every colour and shine change in the app, ready for the website</h1>
  <p class="lead">The app's Analysis, My Tests, Home, All India Series and Rank screens now wear one look: a glossy face, a band of light that
  crosses it, and a coloured edge that keeps running round it. This document lists every place it was applied, the exact colours, sizes and
  timings, and gives a tested web version (CSS + a small script) so the mobile website can look the same as the app.</p>
  <div class="stage" style="margin:14px 0 4px">{ex_tabs("completed")}{ex_chips()}</div>
  <p class="muted" style="font-size:11px">Above: My Tests tabs and series day chips, drawn by the web code in this document (one still frame; on a page they move).</p>

  <div class="box sky"><h3>Owner ke liye (short)</h3>
  <ul><li>Is PDF mein app ke saare naye rang aur glossy / lighting / daudti kinaari wale badlav likhe hain: kahan, kaun sa rang, kitna size, kitni speed.</li>
  <li>Har jagah ke saath app ka screenshot aur usi cheez ka web example hai.</li>
  <li>Website agent ko bas yeh PDF dena hai. Section 2 mein effect ka ready web code hai, Section 3 mein har screen ke exact rang.</li></ul></div>

  <div class="box red"><h3>Website agent: read this first</h3>
  <ol><li><b>One effect does everything.</b> It is called <b>Shine</b>. Build it once from Appendix A (CSS) and Appendix B (script), then reuse it with different colours.</li>
  <li><b>Section 3 has ten pieces.</b> Each gives the app screenshot, the same piece drawn with the web code, every colour, and the Shine settings.</li>
  <li><b>All sizes are CSS px at 1 : 1 with the app.</b> The app is designed at 390 px wide; cards are 358 px (16 px page margin on each side). On the mobile website use the same numbers.</li>
  <li><b>Use the colours exactly as written.</b> Text colours were chosen for contrast on each face. Do not swap families between pieces: each colour has a meaning (table below).</li>
  <li><b>Nothing else changes.</b> Layout, wording, data and behaviour stay as they are; this hand-off is only about colour and shine.</li></ol></div>

  <h3>The colour rules at a glance</h3>
  {table(["Colour", "Value", "Where it is used, and what it means"], rules)}
  <h3>Contents</h3>
  <ul class="toc">{"".join(f'<li><span class="m">{n}</span>{t}</li>' for n, t in toc)}</ul>
</section>"""


def changes():
    rows = [
        ("1", "Analysis &middot; 8 section pills<br><span class='muted'>bar fixed at the bottom of a result</span>",
         "Resting pills were plain text on the grey bar: number " + sw("#74747E") + " name " + sw("#3C3C44") + ". Open pill solid red.",
         "Resting pills are glossy <b>light sky blue &harr; light teal</b> " + grad("#A8DCFF", "#8CEBD6") + " with near-black words, a 2 px five-colour running edge and a glint that travels along the row like a wave. Open pill unchanged (solid red " + sw("#D91222") + ")."),
        ("2", "Analysis &middot; Report download",
         "A small outlined button among the action buttons (white, 1 px line " + sw("#DEDEE4") + ").",
         "One big glossy card, 358 &times; 152, at the top of every Analysis section: <b>sky &harr; aqua</b> " + grad("#86CFFB", "#66E0CC") + ", 3 px five-colour edge, glint, three twinkling stars, soft sky glow under it."),
        ("3", "My Tests &middot; tabs",
         "One grey segmented control; the chosen segment was black with white words. Order: In progress, Saved, Completed. Opened on In progress.",
         "Three separate glossy pills, each in its own colour. <b>Order: Completed, In progress, Saved. Opens on Completed.</b> Completed = baby pink, In progress = yellow, Saved = sky blue. The open tab wears the full colour, a thicker edge, a glow and its count on a white chip."),
        ("4", "Home &middot; All India Series card",
         "Onyx-to-ruby card with a still 1 px glass line " + sw("#FFFFFF1A") + " round it.",
         "Same face. The line became a 2 px <b>running edge</b> (ruby, gold, rose); a soft gloss and a corner-to-corner glint were added."),
        ("5", "Series page &middot; streak card (top)",
         "White card " + sw("#FFFFFF") + ", 1 px line " + sw("#ECECF0") + ", grey small words " + sw("#74747E") + ".",
         "Glossy <b>baby pink</b> " + grad("#FFDCE8", "#FFB5CE") + ", running edge (rose, orchid, coral), corner glint. Small words in rose ink " + sw("#5B3A46") + "."),
        ("6", "Series page &middot; big day cards<br><span class='muted'>Today card and the selected-day card</span>",
         "Flat pastel cards. Upcoming was teal to teal " + grad("#C7F2EC", "#8FDDD3") + ".",
         "Same pastels, now glossy with a running edge in each card's own family and a corner glint. <b>Upcoming is teal to sky blue</b> " + grad("#C7F2EC", "#96D2FF") + "."),
        ("7", "Series page &middot; day chips (DAY 1, 2, 3 ...)",
         "Pastel chips by status (peach today, green done, teal upcoming, sand missed). Chosen day: 2 px black line.",
         "<b>Day still to come = blood red</b> " + grad("#C1121F", "#8A0B15") + " with white words. <b>Day that is over = parrot green</b> " + grad("#96EA3A", "#46BE1B") + " with black words. Today keeps peach to pink. All glossy with running edge and glint. Chosen day: 3 px black edge with one gold light running round it."),
        ("8", "Series page &middot; 50-day map",
         "Pastel cells; far-away days faded to 35 %. Legend: Done, Today, Upcoming, Missed.",
         "Cells use the chip colours: blood red to come, parrot green over, peach-pink today. No fading. Legend: Completed, Today, Upcoming."),
        ("9", "Rank &middot; six tool tiles",
         "Black brushed-metal tiles, each only tinted with its colour (for example " + grad("#25252A", "#4A1122") + ").",
         "<b>No black in the tile.</b> Each tile is its own full colour: maroon, indigo, teal, blood red, gold, violet. Gloss, corner glint, three-colour running edge. The chosen tile glows in its form's colour."),
        ("10", "Rank &middot; form panel under the tiles",
         "Dark panel with a still 1.5 px coloured line and a flat coloured header band.",
         "The line became a 2 px <b>running edge</b> in three colours of the form's own family; the header band is glossy with a glint. The body stays dark."),
    ]
    out = "<table><tr><th>#</th><th>Where</th><th>Before</th><th>Now</th></tr>"
    for n, where, was, now in rows:
        out += f"<tr><td class=k>{n}</td><td class=k style='white-space:normal;width:150px'>{where}</td><td class=was style='width:190px'>{was}</td><td>{now}</td></tr>"
    out += "</table>"
    return f"""
<section>
  {h2("1", "What changed (before &rarr; after)")}
  <p class="where">Ten pieces on five screens changed. Everything not listed here looks as it did before.</p>
  {out}
  <div class="box"><h3>Not touched in this round</h3>
  <ul><li><b>Rapid Fire</b> (the game) has its own blood-red world and its own glitter border. Nothing in this document applies to it.</li>
  <li>The black metal <b>Rank Card</b> (result card) and the purple <b>Dream College Meter</b> keep their existing look.</li>
  <li>Page backgrounds, fonts (Figtree; Roboto Mono for numbers), buttons, spacing and all wording.</li></ul></div>
</section>"""


def effect():
    layers = [
        ("Running edge", "A strip <code>ring</code> px thick round the piece (2 px; 3 px on an open or chosen piece and on the Report card). Its colours slide round all four sides. "
         "Built as a square as wide as the piece's diagonal + 4 px, filled corner to corner with the edge colours, turning behind the face.", "One full turn every <b>4200 ms</b>, linear, for ever."),
        ("Face colours", "Two colours from the top-left corner to the bottom-right corner (<code>tones</code>). A piece that already has its own picture (Home card, Rank tiles, day chips) keeps it instead.", "Still."),
        ("Colour swap", "The same two colours the other way round, laid over the face. Fading it in and out makes the two colours keep changing places. Only for faces with two <code>tones</code>.",
         "<b>5600 ms</b> per cycle, ease-in-out: clear, full at the half, clear again."),
        ("Gloss", "White light on the <b>upper 56 %</b> of the face: strongest at the top edge, fading to nothing. A plain gradient, no blur.", "Still."),
        ("Glint", "A soft band of white light, <code>band</code> px wide (clear, white, clear across its width). It crosses the face and then waits outside it. "
         "<b>Line path</b> (pills, tabs, header bands, Report card): the band is tilted 20&deg; and slides left to right. "
         "<b>Corner path</b> (cards, tiles, chips): the band lies across the card and travels from the top-left corner to the bottom-right corner.",
         "<b>3600 ms</b> per cycle. It crosses in the first <code>part</code> % of the cycle with ease-in-out and waits for the rest."),
        ("Content", "Words, icons and buttons. Always above every light layer, so text stays crisp.", "&ndash;"),
        ("Stars", "Report card only: three 16 px four-point stars on the edge, twinkling one after another.", "<b>5200 ms</b> per star cycle, ease-out; each visible for about 0.9 s."),
        ("Glow", "A soft coloured shadow under an open tab, a chosen tile, the Report card and a Rank form. It is a normal <code>box-shadow</code>; it does not move.", "Still."),
    ]
    timing = [
        ("Edge turn", "4200 ms", "linear", "rotate 0&deg; &rarr; 360&deg;"),
        ("Glint cycle", "3600 ms", "ease-in-out", "crosses in the first 32 to 46 % (per piece), then waits"),
        ("Colour swap", "5600 ms", "ease-in-out", "opacity 0 &rarr; 1 &rarr; 0; starts at 3 &times; the piece's delay"),
        ("Star twinkle", "5200 ms", "ease-out", "0 to 9 %: grow, turn 45&deg;, appear &middot; 9 to 18 %: shrink, turn to 90&deg;, vanish &middot; rest: hidden. Stars start at 500, 2233, 3967 ms"),
    ]
    return f"""
<section>
  {h2("2", "The Shine effect: how it is built")}
  <p class="where">Every piece in this document is the same stack of simple layers. Only two things ever move or fade: <b>position (transform)</b> and
  <b>opacity</b>. That is what keeps it light on a phone.</p>
  <div class="stage tight">{ex_layers()}</div>
  <h3>2.1 &nbsp;The layers, bottom to top</h3>
  {table(["Layer", "What it is", "Motion"], layers)}
  <h3>2.2 &nbsp;Timings (same for every piece)</h3>
  {table(["Motion", "Length", "Easing", "What happens"], timing)}
  <div class="box"><h3>2.3 &nbsp;Two habits that make it feel alive, and one that keeps it calm</h3>
  <ul><li><b>Stagger.</b> Neighbours start a little apart (<code>delay</code>), so the glint travels along a row like a wave: pills 160 ms apart, tabs 220 ms, tiles 200 ms, day chips 140 ms.</li>
  <li><b>Thicker edge when chosen.</b> An open tab, a chosen tile and a chosen day use a 3 px edge and the face shrinks by 1 px on each side, so the piece never changes size.</li>
  <li><b>Rest.</b> A piece rests when it is off screen, inside a hidden tab pane, under another screen or sheet, or when the phone has Reduce Motion on.
  Resting means: the edge stands still as a coloured slope, the gloss stays, and the swap, glint and stars are not drawn.</li></ul></div>
</section>"""


def web_code():
    settings = [
        ("radius", "<code>--r</code>", "Corner radius of the whole piece. 999px = pill."),
        ("ring", "<code>--ring</code>", "Thickness of the running edge. For no edge use 0px and leave out <code>&lt;i class=\"jl-edge\"&gt;</code>."),
        ("edge", "<code>--edge</code>", "The colours that run round, comma separated. Repeat the first colour at the end so there is no seam. Leave out for the five colours."),
        ("tones", "<code>--tone-a</code>, <code>--tone-b</code><br>+ <code>&lt;i class=\"jl-tones\"&gt;</code> <code>&lt;i class=\"jl-swap\"&gt;</code>", "Face colours, corner to corner. Leave out <code>jl-swap</code> when the two colours must not change places (chips, tiles)."),
        ("backdrop", "your own <code>&lt;i&gt;</code> layers, first in the face", "A face with its own picture (Home card, diamond on a tile). Every direct <code>&lt;i&gt;</code> in the face is a light or picture layer; everything else is content."),
        ("gloss", "<code>--gloss</code> + <code>&lt;i class=\"jl-gloss\"&gt;</code>", "The white of the top light."),
        ("glint", "<code>--glint</code> + <code>&lt;i class=\"jl-glint\"&gt;</code>", "The white of the crossing band."),
        ("band", "<code>--band</code>", "Width of the glint band."),
        ("part", "<code>data-part=\"32 | 34 | 36 | 38 | 40 | 46\"</code>", "Share of the 3.6 s cycle in which the glint crosses. 40 when left out."),
        ("corner", "<code>data-corner</code>", "Glint travels corner to corner (cards, tiles, chips). Without it: tilted band, left to right."),
        ("delay", "<code>--delay</code>", "Start later than the neighbour, for the wave."),
        ("sparkles", "<code>&lt;svg class=\"jl-spark\"&gt;</code> &times; 3", "Stars on the edge (Report card only). Put them after <code>.jl-ring</code>."),
        ("rest", "<code>data-rest</code>", "Hold this piece still (hidden pane, under a sheet). <code>shine.js</code> sets <code>data-off</code> by itself for pieces off screen."),
    ]
    skeleton = snippet("Example: one resting Analysis pill", 999, 2, tones=("#A8DCFF", "#8CEBD6"), gloss="rgba(255,255,255,0.78)",
                       glint="rgba(255,255,255,0.95)", band=22, part=32, delay="160ms",
                       content='<span class="num">2</span> <span>Performance</span>')
    return f"""
<section>
  {h2("2.4", "Web code: how to use it")}
  <p class="where">Add <code>shine.css</code> (Appendix A) and <code>shine.js</code> (Appendix B) once. Then every piece is the same small block of markup with different
  settings. The examples in this document are drawn by exactly these two files.</p>
  {code(skeleton)}
  <ul><li><code>.jl-shine</code> = the piece. <code>.jl-ring</code> = the edge (it clips). <code>.jl-face</code> = the face; put your own layout class on it (flex row, padding ...).</li>
  <li>Order inside the face: picture or colours, swap, gloss, glint, then your content. The content is lifted above the light by the CSS.</li>
  <li><code>shine.js</code> measures each piece (size of the turning square, slope of the colours, path of the glint) and measures again when its size changes.
  After adding pieces to the page later (a list that loads), call <code>JLShine.watch()</code>.</li>
  <li>The total size never changes: the edge is <b>inside</b> the piece. Example: a tab row is 52 px high = 48 px face + 2 px edge on each side.</li></ul>
  <h3>Settings: app name &rarr; web name</h3>
  {table(["App (Shine.tsx)", "Web", "Meaning"], settings)}
  <div class="box"><h3>Browser support</h3>
  <p>Needs CSS <code>aspect-ratio</code>, the <code>translate</code> property and <code>ResizeObserver</code>: Chrome 104+, Safari 15+ (iOS 15+), Firefox 89+.
  Without the script the edge, colours, swap and gloss still show; only the glint stays hidden.</p></div>
</section>"""


def piece(num, title, where, body):
    return f'<section>{h2(num, title)}<p class="where"><b>Where:</b> {where}</p>{body}</section>'


def p_pills():
    rows = [
        ("Resting pill face", grad("#A8DCFF", "#8CEBD6") + "<br>light sky blue and light teal; they keep changing places"),
        ("Running edge, 2 px", edge(FIVE, "pink, gold, aqua, blue, violet")),
        ("Gloss", sw("rgba(255,255,255,0.78)")),
        ("Glint", sw("rgba(255,255,255,0.95)") + " band 22 px"),
        ("Words on a resting pill", sw("#0F0F12") + " number: Roboto Mono 700, 10.5 px &middot; name: Figtree 700, 12.5 px"),
        ("Open pill (unchanged)", sw("#D91222") + " solid, no shine &middot; name white, Figtree 800, 12.5 px &middot; number " + sw("rgba(248,250,252,0.72)")),
        ("Bar behind the pills", sw("#F6F6F8") + " top line " + sw("#ECECF0") + " top corners 20 px"),
    ]
    body = fmt(r"""
  <div class="cols">{phone("analysis_screen", "Result &rarr; Analysis")}
    <div class="main">
      {figure(crop("analysis_pills_bar", 390), "the bar in the app", "APP")}
      {figure('<div class="stage tight">' + ex_pills() + "</div>", "the same bar drawn with shine.css")}
      {params(radius="999", ring="2", band="22", part="32", glint="line", delay="i &times; 160 ms")}
    </div></div>
  {table(["Part", "Colour and type"], rows)}
  <ul><li><b>Sizes.</b> Every pill is 44 px high. Resting: 40 px face + 2 px edge on each side, padding 0 12 px. Open: padding 0 14 px. 6 px between number and name, 6 px between pills.</li>
  <li><b>Wave.</b> Pill number <i>i</i> (0, 1, 2 ...) starts <i>i</i> &times; 160 ms late, so the glint and the colour change run along the bar.</li>
  <li>The bar scrolls sideways; the open pill is scrolled into view. The eight names: {", ".join(SECTIONS)}.</li></ul>
  {code(snippet("Resting section pill (pill number i)", 999, 2, tones=("#A8DCFF", "#8CEBD6"), gloss="rgba(255,255,255,0.78)", glint="rgba(255,255,255,0.95)", band=22, part=32, delay="calc(i * 160ms)", content='<span class="num">2</span> <span>Performance</span>'))}""", locals())
    return piece("3.1", "Analysis &middot; section pills", "Result screen &rarr; Analysis tab &rarr; the bar fixed at the bottom (under the Personal / Comparative switch).", body)


def p_report():
    rows = [
        ("Face", grad("#86CFFB", "#66E0CC") + "<br>sky blue and aqua; they keep changing places"),
        ("Running edge, 3 px", edge(FIVE, "pink, gold, aqua, blue, violet")),
        ("Gloss / glint", sw("rgba(255,255,255,0.46)") + sw("rgba(255,255,255,0.92)") + " band 72 px"),
        ("Three stars, 16 px", sw("#FFB020") + " at 15 % from the left, on the top edge &middot; " + sw("#FF3D9A") + " on the right edge, 34 % down &middot; " + sw("#3B82F6") + " at 68 % from the left, on the bottom edge"),
        ("Glow under the card", "<code>box-shadow: 0 8px 16px rgba(56,189,248,0.34)</code> " + sw("#38BDF8")),
        ("Two soft circles on the face", sw("rgba(255,255,255,0.22)") + " 190 px circle at right &minus;60, top &minus;84 &middot; 130 px circle at right 54, bottom &minus;84"),
        ("Icon badge", "60 &times; 60, radius 18 " + sw("rgba(255,255,255,0.55)") + " 1 px line " + sw("rgba(255,255,255,0.9)") + " PDF icon 32 px " + sw("#0F0F12")),
        ("Title", "&ldquo;Report download&rdquo; Figtree 800, 22 px, letter-spacing &minus;0.5 " + sw("#0F0F12")),
        ("Second line", "&ldquo;Poora analysis ek PDF mein&rdquo; Figtree 600, 13.5 px " + sw("#0B4A5C")),
        ("Round button", "46 px circle " + sw("#0F0F12") + " white download icon 22 px"),
    ]
    body = fmt(r"""
  <div class="cols"><div class="main">
      {figure(crop("analysis_report_card", 386), "the card in the app", "APP")}
      {figure('<div class="stage">' + ex_report() + "</div>", "the same card drawn with shine.css")}
    </div>
    <div style="width:250px;flex:none">{params(radius="22", ring="3", band="72", part="46", glint="line", stars="3")}
      <ul><li><b>Size.</b> 358 &times; 152 px: 146 px face + 3 px edge on each side. Padding 17 px, 14 px between badge, words and button.</li>
      <li><b>Place.</b> First thing in every Analysis section, above the section title. One tap downloads the report PDF.</li>
      <li><b>Narrow phones</b> (under 360 px): title 19 px, badge 48 px, side padding 11 px.</li>
      <li>While the file is being made the round button shows a spinner.</li></ul></div></div>
  {table(["Part", "Colour and type"], rows)}
  {code(snippet("Report download card", 22, 3, tones=("#86CFFB", "#66E0CC"), gloss="rgba(255,255,255,0.46)", glint="rgba(255,255,255,0.92)", band=72, part=46, extra="background:#86CFFB; box-shadow:0 8px 16px rgba(56,189,248,0.34)", content="... badge, words, round button ...") + chr(10) + "<!-- after .jl-ring, inside .jl-shine: three stars (path in Appendix A note) -->" + chr(10) + '<svg class="jl-spark" style="left:15%; top:0%;   animation-delay:500ms"  viewBox="0 0 24 24"><path d="..." fill="#FFB020"/></svg>' + chr(10) + '<svg class="jl-spark" style="left:100%; top:34%; animation-delay:2233ms" viewBox="0 0 24 24"><path d="..." fill="#FF3D9A"/></svg>' + chr(10) + '<svg class="jl-spark" style="left:68%; top:100%; animation-delay:3967ms" viewBox="0 0 24 24"><path d="..." fill="#3B82F6"/></svg>')}
  <p class="muted" style="font-size:11px">Star path (24 &times; 24 box): <code>{STAR}</code></p>""", locals())
    return piece("3.2", "Analysis &middot; Report download card", "Result screen &rarr; Analysis tab &rarr; top of every one of the eight sections.", body)


def p_tabs():
    rows = []
    for t in TABS.values():
        rows.append((f'{t["label"]}<br><span class="muted">{t["name"]}</span>', grad(*t["on"]), grad(*t["rest"]), edge(t["edge"], t["edge_name"]), sw(t["glow"])))
    body = fmt(r"""
  <div class="cols">{phone("tests_completed_screen", "My Tests, opened on Completed", short=True)}
    <div class="main">
      {figure(crop("tests_tabs_completed", 382) + crop("tests_tabs_progress", 382) + crop("tests_tabs_saved", 382), "the tabs in the app: Completed open, In progress open, Saved open", "APP")}
      {figure('<div class="stage">' + ex_tabs("completed") + ex_tabs("progress") + ex_tabs("saved") + "</div>", "the same three states drawn with shine.css")}
    </div></div>
  {params(radius="999", ring="2 (open: 3)", band="26", part="34", glint="line", delay="i &times; 220 ms")}
  {table(["Tab", "Open face", "Resting face", "Running edge (its own family)", "Glow when open"], rows)}
  <div class="keep">
  {table(["Part", "Value"], [
        ("Order and start", "<b>Completed, In progress, Saved.</b> The screen opens on <b>Completed</b>."),
        ("Gloss / glint (all three)", sw("rgba(255,255,255,0.62)") + sw("rgba(255,255,255,0.95)")),
        ("Words", "Open tab: " + sw("#0F0F12") + " Figtree 800, 13 px &middot; resting tab: " + sw("#3D3D47") + " Figtree 600, 13 px"),
        ("Count", "Figtree 700, 10.5 px, under the name. On the open tab it sits on a white chip " + sw("rgba(255,255,255,0.92)") + " (min-width 22, height 16, radius 8, padding 0 6 px)"),
        ("Glow of the open tab", "<code>box-shadow: 0 4px 9px</code> of the glow colour at 45 %"),
        ("Sizes", "Three equal tabs, 8 px apart, row 52 px high: resting 48 px face + 2 px edge; open 46 px face + 3 px edge"),
        ("Rule", "A colour never moves to another tab: pink is always Completed, yellow always In progress, sky blue always Saved. Resting tabs are not grey: they wear a softer wash of their own colour."),
    ])}
  {code(snippet("Completed tab, open (tab number 0). Resting: --ring:2px and the resting colours.", 999, 3, edge=TABS["completed"]["edge"], tones=TABS["completed"]["on"], gloss="rgba(255,255,255,0.62)", glint="rgba(255,255,255,0.95)", band=26, part=34, delay="0ms", extra="background:#FF82AB; box-shadow:0 4px 9px rgba(255,77,143,0.45)", content='<span>Completed</span> <span class="count">5</span>'))}
  </div>""", locals())
    return piece("3.3", "My Tests &middot; three tabs", "My Tests screen &rarr; the row of tabs under the title.", body)


def p_home():
    rows = [
        ("Running edge, 2 px (new)", edge(SERIES_EDGE, "ruby, gold, rose") + "<br>replaces the old still 1 px line " + sw("#FFFFFF1A")),
        ("Gloss (new)", sw("rgba(255,255,255,0.11)") + " very soft: the card is dark"),
        ("Glint (new)", sw("rgba(255,255,255,0.26)") + " band 96 px, corner to corner"),
        ("Face (unchanged)", "corner to corner: " + sw("#0B0B0D") + " 0 % " + sw("#17090D") + " 55 % " + sw("#3A0912") + " 100 %"),
        ("Red glow, top right (unchanged)", sw("#E11D2E") + " at 45 % fading to 0: an ellipse 75 % wide, 65 % high, centred at 96 % / 0 %"),
        ("Hairline on the top edge (unchanged)", "1 px high, 28 px in from each side: clear " + sw("rgba(255,255,255,0.24)") + " clear"),
        ("Words and button (unchanged)", "white " + sw("#FFFFFF") + " soft white " + sw("rgba(248,250,252,0.72)") + " button " + sw("#D91222") + " glass boxes " + sw("#FFFFFF09") + " with line " + sw("#FFFFFF1A")),
    ]
    body = fmt(r"""
  <div class="cols">{phone("home_aits_screen", "Home")}
    <div class="main">
      {figure('<div class="stage">' + ex_home() + "</div>", "the card drawn with shine.css (words are sample data)")}
      {params(radius="28", ring="2", band="96", part="46", glint="corner")}
    </div></div>
  {table(["Part", "Colour"], rows)}
  <ul><li><b>Size stays the same.</b> Padding went from 20 px (with the 1 px line) to 19 px inside the 2 px edge.</li>
  <li>The face is the card's own picture, so it is never recoloured: no colour swap on this card.</li>
  <li>This is the one dark card on the light Home screen. Keep the gloss and glint as soft as written; stronger whites make it look grey.</li></ul>
  {code(snippet("Home: All India Series card", 28, 2, edge=SERIES_EDGE, gloss="rgba(255,255,255,0.11)", glint="rgba(255,255,255,0.26)", band=96, part=46, corner=True, backdrop='<i class="bg"></i><i class="sheen"></i>', content="... the card's content ...") + chr(10) + ".bg    { inset:0; background: radial-gradient(ellipse 75% 65% at 96% 0%, rgba(225,29,46,.45), rgba(225,29,46,0))," + chr(10) + "                             linear-gradient(var(--ta,135deg), #0B0B0D 0%, #17090D 55%, #3A0912 100%); }" + chr(10) + ".sheen { top:0; left:28px; right:28px; height:1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.24), transparent); }")}""", locals())
    return piece("3.4", "Home &middot; All India Series card", "Home screen &rarr; the dark &ldquo;All India Series&rdquo; card.", body)


def p_streak():
    rows = [
        ("Face", grad("#FFDCE8", "#FFB5CE") + "<br>two baby pinks; they keep changing places"),
        ("Running edge, 2 px", edge(TABS["completed"]["edge"], "rose, orchid, coral") + "<br>the same family as the Completed tab"),
        ("Gloss / glint", sw(PASTEL_GLOSS) + sw(PASTEL_GLINT) + " band 84 px, corner to corner"),
        ("Big words and numbers", sw("#0F0F12")),
        ("Small words on the pink", sw("#5B3A46") + " rose ink (was grey " + sw("#74747E") + ")"),
        ("Progress ring", "track " + sw("#F1F1F4") + " filled part: teal to green " + grad("#0D9488", "#3A6B1F") + " 108 px, 9 px stroke"),
        ("Three facts (icon on a soft circle)", "streak " + sw("#EA580C") + " on " + sw("#FFF0E6") + " &middot; best " + sw("#B7791F") + " on " + sw("#FFF6DB") + " &middot; skipped " + sw("#7A4A3C") + " on " + sw("#FBEFF1")),
        ("Cup line", "line " + sw("#F1F1F4") + " filled " + sw("#3A6B1F") + " &middot; locked cup " + sw("#F6F6F8") + " line " + sw("#D9D9DF") + " &middot; earned cup " + sw("#B7791F")),
    ]
    body = fmt(r"""
  <div class="cols">{phone("series_top", "All India Series page")}
    <div class="main">
      {figure('<div class="stage">' + ex_streak() + "</div>", "the streak card drawn with shine.css")}
      {params(radius="24", ring="2", band="84", part="46", glint="corner")}
    </div></div>
  {table(["Part", "Colour"], rows)}
  <ul><li><b>Size stays the same</b> as the old white card: padding 19 px inside the 2 px edge (was 20 px with a 1 px line), 16 px between the rows.</li>
  <li>Baby pink is the &ldquo;my finished work&rdquo; colour: the same family as the Completed tab in My Tests.</li></ul>
  {code(snippet("Series page: streak card", 24, 2, edge=TABS["completed"]["edge"], tones=("#FFDCE8", "#FFB5CE"), gloss=PASTEL_GLOSS, glint=PASTEL_GLINT, band=84, part=46, corner=True, content="... ring, three facts, cup line ..."))}""", locals())
    return piece("3.5", "Series page &middot; streak card", "All India Series page &rarr; the first card (days done, streak, cups).", body)


def p_daycards():
    rows = []
    for key, p in PASTEL.items():
        was = " <span class='muted'>(second colour was " + sw("#8FDDD3") + ")</span>" if key == "upcoming" else ""
        rows.append((f'{p["label"]}<br><span class="muted">{p["name"]}</span>', grad(p["frm"], p["to"]) + was, sw(p["ink"]), sw(p["body"]), sw(p["cta"]), edge(p["edge"], p["edge_name"])))
    body = fmt(r"""
  <div class="cols">{phone("series_strip_screen", "an Upcoming day card under the chips")}
    <div class="main">
      {params(radius="24 / 22", ring="2", band="72", part="46", glint="corner")}
      <ul><li>Two cards use this look: the <b>Today</b> card (radius 24) and the <b>selected-day</b> card under the chips (radius 22).</li>
      <li>The card wears the colour of its day's status. Its two colours keep changing places.</li>
      <li><b>Only one colour changed:</b> Upcoming now ends in sky blue {sw("#96D2FF")}. Today, Done and Missed keep their pastels; they only gained the shine.</li>
      <li>Padding 18 px inside the 2 px edge, 8 px between lines. Title Figtree 800, 17 px (21 px on the Today card) {sw("#111114")}.</li>
      <li>Top line: Figtree 800, 10 px, letter-spacing 1.8, capitals, in the status ink.</li>
      <li>Button: dark pill {sw("#111114")} with the status's light colour for its words: 50 px high on the Today card, 44 px on the selected-day card.</li></ul>
    </div></div>
  {figure('<div class="stage">' + ex_daycards() + "</div>", "the four statuses drawn with shine.css (words are sample data)")}
  {table(["Status", "Face", "Ink (caps line)", "Body words", "Words on the dark button", "Running edge"], rows)}
  {table(["Shared by all four", "Value"], [("Gloss / glint", sw(PASTEL_GLOSS) + sw(PASTEL_GLINT) + " band 72 px, corner to corner")])}""", locals())
    return piece("3.6", "Series page &middot; day cards", "All India Series page &rarr; the &ldquo;Today&rdquo; card and the card of the day chosen in the chip row.", body)


def p_chips():
    rows = []
    for key in ("upcoming", "over", "today"):
        c = CHIPS[key]
        means = {"upcoming": "a day still to come", "over": "a day that is over: paper taken <b>or</b> missed", "today": "today"}[key]
        rows.append((f'{c["name"]}<br><span class="muted">{means}</span>', grad(c["frm"], c["to"]), sw(c["ink"]), sw(c["soft"]), edge(c["edge"], c["edge_name"]), sw(c["gloss"]) + "<br>" + sw(c["glint"])))
    body = fmt(r"""
  {figure(crop("series_day_strip", 390), "the chip row in the app (launch has not started, so every day is still to come; day 1 is chosen)", "APP")}
  {figure('<div class="stage">' + ex_chips() + "</div>", "all looks drawn with shine.css: days 1 and 2 over, day 3 today, days 4 to 7 to come, day 5 chosen")}
  {params(radius="16", ring="2 (chosen: 3)", band="18", part="38", glint="corner", delay="(i mod 8) &times; 140 ms")}
  {table(["Look", "Face", "Day number", "Small word", "Running edge", "Gloss / glint"], rows)}
  {table(["Part", "Value"], [
        ("Chosen day", "3 px edge: black with one gold light running round it " + edge(CHOSEN_EDGE) + " and a 6 px dot " + sw("#0F0F12") + " under the chip"),
        ("Sizes", "52 px wide, 68 px high (64 px face + 2 px edge; chosen 62 px + 3 px), radius 16, 8 px apart"),
        ("Words", "small word &ldquo;DAY&rdquo; or &ldquo;TODAY&rdquo;: Figtree 800, 8.5 px, letter-spacing 1.2 &middot; day number: Figtree 800, 19 px"),
    ])}
  <ul><li><b>Meaning.</b> Blood red = not yet happened. Parrot green = over. The chip no longer tells Completed from Missed; the big day card under it still does.</li>
  <li>The chip face is its own picture: the two reds (or greens) do <b>not</b> change places. Leave out <code>jl-swap</code>.</li>
  <li><b>There are 50 chips.</b> Only the chips on screen may move; the rest must rest. <code>shine.js</code> does this by itself.</li>
  <li>The row opens scrolled so that today (or the chosen day) is the third chip.</li></ul>
  {code(snippet("Day chip, still to come (chip number i)", 16, 2, edge=CHIPS["upcoming"]["edge"], tones=(CHIPS["upcoming"]["frm"], CHIPS["upcoming"]["to"]), swap=False, gloss=CHIPS["upcoming"]["gloss"], glint=CHIPS["upcoming"]["glint"], band=18, part=38, corner=True, delay="calc((i % 8) * 140ms)", content='<span class="word">DAY</span> <span class="num">4</span>'))}""", locals())
    return piece("3.7", "Series page &middot; day chips", "All India Series page &rarr; &ldquo;All days&rdquo; row (DAY 1, DAY 2, DAY 3 ... swipe sideways).", body)


def p_map():
    rows = [
        ("Day still to come", grad(CHIPS["upcoming"]["frm"], CHIPS["upcoming"]["to"]) + " blood red"),
        ("Day that is over", grad(CHIPS["over"]["frm"], CHIPS["over"]["to"]) + " parrot green"),
        ("Today", grad(CHIPS["today"]["frm"], CHIPS["today"]["to"]) + " peach to pink"),
        ("Today and the chosen day", "2 px line " + sw("#0F0F12") + " and the day number inside (Figtree 800, one third of the cell) in that look's number colour"),
        ("Card behind", sw("#FFFFFF") + " 1 px line " + sw("#ECECF0") + " radius 22, padding 16"),
        ("Legend", "Completed, Today, Upcoming: 12 px squares (radius 3) + Figtree 400, 11 px " + sw("#6B6B75")),
    ]
    body = fmt(r"""
  <div class="cols">{phone("series_map_screen", "50-day map (before launch: all days to come)")}
    <div class="main">
      {figure('<div class="stage">' + ex_map() + "</div>", "the map in web CSS with sample days: 1 to 12 over, 13 today, 24 chosen")}
    </div></div>
  {table(["Part", "Colour"], rows)}
  <ul><li><b>No shine here.</b> The cells are plain corner-to-corner gradients (50 small cells would be too busy and too heavy). Same colours as the day chips.</li>
  <li><b>No fading.</b> Far-away days used to be faded to 35 %; now every day to come is full blood red.</li>
  <li>Grid: 7 days per column, read top to bottom, then the next column. 6 px gaps. Cell = 34 px or smaller to fit, radius = a quarter of the cell.</li>
  <li>Tapping a cell chooses that day in the chip row.</li></ul>
  {code('''<!-- one cell of the map -->
<div style="width:34px; height:34px; border-radius:9px; border:2px solid transparent; background-origin:border-box;
            background-image: linear-gradient(135deg, #C1121F, #8A0B15)"></div>            <!-- to come  -->
... linear-gradient(135deg, #96EA3A, #46BE1B) ...                                          <!-- over     -->
... linear-gradient(135deg, #FFDDBF, #FFB9CC); border-color:#0F0F12 ...  13               <!-- today    -->''')}""", locals())
    return piece("3.8", "Series page &middot; 50-day map", "All India Series page &rarr; &ldquo;50-day map&rdquo; card near the bottom.", body)


def p_tiles():
    rows = []
    for key, t in TILES.items():
        f = FORMS[key]
        rows.append((f'{t["title"].title()}<br><span class="muted">{t["name"]}</span>', grad(t["frm"], t["to"]), sw(t["chip"]) + "<br>" + sw(t["line"]),
                     sw(t["ink"]) + "<br>" + sw(t["soft"]), edge(t["edge"], t["edge_name"]), sw(f["text"])))
    body = fmt(r"""
  <div class="cols">{phone("rank_rank", "Rank tab: tiles, then the open tool's form")}
    <div class="main">
      {figure(crop("rank_tiles", 374), "the six tiles in the app (Rank predictor chosen)", "APP")}
      {figure('<div class="stage dark">' + ex_tiles("rank") + "</div>", "the same six tiles drawn with shine.css")}
      {params(radius="18", ring="2 (chosen: 3)", band="30", part="40", glint="corner", delay="order &times; 200 ms")}
    </div></div>
  {table(["Tile", "Face", "Icon circle / its ring", "Title / small line", "Running edge", "Chosen: glow + edge colour"], rows)}
  {table(["Part", "Value"], [
        ("Gloss / glint", "five dark tiles: " + sw(TILE_GLOSS) + sw(TILE_GLINT) + " &middot; gold tile (light): " + sw("rgba(255,255,255,0.5)") + sw("rgba(255,255,255,0.9)")),
        ("Chosen tile", "3 px edge where the form's colour and white chase each other (colour, white, colour, white, colour) + glow <code>box-shadow: 0 4px 18px</code> of that colour at 70 %. Its diamond is brighter (75 % instead of 45 %)."),
        ("Sizes", "Two tiles per row, 8 px gaps, 64 px high (60 px face + 2 px edge; chosen 58 px + 3 px), radius 18, padding 9 px 11 px"),
        ("Icon", "34 px circle with a 1 px ring, icon 17 px in the title colour"),
        ("Words", "title: Figtree 600, 10.5 px, capitals, letter-spacing 1.2 &middot; small line: Figtree 400, 10.5 px"),
        ("NEW badge", "white pill " + sw("#FFFFFF") + " on the bottom edge of the icon circle; word Figtree 700, 8 px in the tile's deep colour. Hidden on the chosen tile."),
        ("Diamond", "46 px wide faceted diamond in white, in the bottom-right corner (right &minus;8, bottom &minus;9), under the gloss"),
        ("Page behind", sw("#000000") + " the Rank tab stays black; only tiles and forms carry colour"),
    ])}
  <ul><li><b>The rule the owner asked for:</b> no black inside a tile. Each tile is one full colour from corner to corner.</li>
  <li>The tile face is its own picture: no colour swap. Words are white on five tiles and near-black {sw("#1C1300")} on the gold tile.</li>
  <li>The chosen tile's glow and edge use the colour of the <b>form below</b> (next page), so the student sees which form belongs to the tile.</li></ul>""", locals())
    return piece("3.9", "Rank &middot; six tool tiles", "Rank tab &rarr; the six tiles at the top (two per row).", body)


FORM_SNIPPET = """<!-- Rank form panel (Rank predictor). The header band is a second Shine inside it, without an edge. -->
<div class="jl-shine"
     style="--r:22px; --ring:2px; --edge:#FFD60A, #FF8A00, #FFF3B0, #FFD60A;
            background:#121218; box-shadow:0 0 18px rgba(255,214,10,0.45)">
  <div class="jl-ring"><i class="jl-edge"></i>
    <div class="jl-face" style="padding:15.5px; background:#121218"><i class="wash"></i>
      <div style="margin:-15.5px -15.5px 0; background:#FFD60A">                      <!-- header band -->
        <div class="jl-shine" data-part="36"
             style="--r:0px; --ring:0px; --band:34px;
                    --gloss:rgba(255,255,255,0.46); --glint:rgba(255,255,255,0.9)">
          <div class="jl-ring">
            <div class="jl-face"><i class="jl-gloss"></i><i class="jl-glint"></i>
              ... icon circle, tool name, title ...
            </div>
          </div>
        </div>
      </div>
      ... fields, chips, main button ...
    </div>
  </div>
</div>
.wash { inset:0;
        background: linear-gradient(to bottom right, rgba(255,214,10,0.12), rgba(255,255,255,0) 62%); }"""


def p_forms():
    rows = []
    for key, f in FORMS.items():
        band = "light band: strong shine" if f["band"] == "light" else "deep band: soft shine"
        rows.append((f'{f["name"]}<br><span class="muted">{f["colour"]}</span>', sw(f["ink"]), sw(f["on"]), sw(f["text"]), sw(f["soft"]) + "<br>" + sw(f["line"]),
                     edge(f["edge"], f["edge_name"]), band))
    body = fmt(r"""
  <div class="shots"><img src="shots/rank_pct.jpg"><img src="shots/rank_target.jpg"><img src="shots/rank_college.jpg"><img src="shots/rank_compare.jpg"></div>
  <p class="muted" style="font-size:10.5px;margin-top:5px"><b style="color:#0F0F12;letter-spacing:1.2px;font-size:9.5px">APP</b> &nbsp;Percentile se rank (teal), Target marks (lime), College predictor (blood red), College compare (sky blue)</p>
  <div class="stage dark" style="margin:10px 0"><div class="pair">
    <div>{ex_switch("rank")}{ex_form("rank", form_body("rank", "Marks (out of 300)", "e.g. 180", "Predict rank"))}</div>
    <div>{ex_switch("college")}{ex_form("college", form_body("college", "Marks (out of 300)", "e.g. 180", "Colleges dekho"))}</div>
  </div></div>
  <p class="muted" style="font-size:10.5px"><b style="color:#0F0F12;letter-spacing:1.2px;font-size:9.5px">WEB</b> &nbsp;a light-band form (Rank predictor) and a deep-band form (College predictor) drawn with shine.css, with the exam switch above each (drawn 320 px wide to fit this page; 358 px in the app)</p>
  {params(form_edge="radius 22, ring 2, no gloss, no glint", header_band="radius 0, ring 0, band 34, part 36, glint line")}
  {table(["Form", "Form colour", "Words on it", "Its colour for words on black", "Soft wash / frame line", "Running edge", "Header band"], rows)}
  {table(["Part", "Value"], [
        ("Panel", "radius 22, body " + sw("#121218") + " (stays dark), padding 15.5 px, 12 px between rows. Top-left wash of the soft colour fading out towards the middle."),
        ("Glow round the panel", "<code>box-shadow: 0 0 18px</code> of the form's &ldquo;words on black&rdquo; colour at 45 %"),
        ("Running edge", "2 px, three colours of the form's own family. No gloss or glint on the body: the fields must stay calm."),
        ("Header band", "runs edge to edge at the top, filled with the form colour. Light bands (yellow, teal, lime, sky blue): gloss " + sw(LIGHT_BAND["gloss"]) + " glint " + sw(LIGHT_BAND["glint"]) + ". Deep bands (blood red, violet): gloss " + sw(DEEP_BAND["gloss"]) + " glint " + sw(DEEP_BAND["glint"]) + "."),
        ("In the band", "32 px circle in the &ldquo;words on it&rdquo; colour with the tool icon in the form colour &middot; tool name: Figtree 700, 10 px, capitals, letter-spacing 1.6, 72 % opacity &middot; title: Figtree 800, 15.5 px"),
        ("Inside the form", "text field: 52 px high, radius 14, " + sw("#1A1A23") + ", line = frame line &middot; chosen chip: form colour with &ldquo;words on it&rdquo; &middot; other chips " + sw("#1A1A23") + " line " + sw("#30303E") + " words " + sw("#C3C6D0") + " &middot; main button: 54 px pill in the form colour"),
        ("Exam switch above the form", "chosen side: frame line, soft wash, words in the &ldquo;words on black&rdquo; colour &middot; others " + sw("#8F92A3")),
    ])}
  <ul><li><b>One form at a time.</b> Only the open tool's form moves; forms in hidden panes rest (<code>data-rest</code>).</li>
  <li>The Dream college tile opens the purple Dream College Meter card, which keeps its existing look; the violet row above is used for its switch and chips.</li></ul>
  {code(FORM_SNIPPET)}""", locals())
    return piece("3.10", "Rank &middot; form panels", "Rank tab &rarr; the form that opens under the tiles (one per tool).", body)


def rules():
    base = [
        ("Light pages", "page " + sw("#FFFFFF") + " words " + sw("#0F0F12") + " soft words " + sw("#6B6B75") + " card line " + sw("#ECECF0") + " bar " + sw("#F6F6F8") + " brand red " + sw("#D91222")),
        ("Rank tab (dark)", "page " + sw("#000000") + " panel " + sw("#121218") + " raised " + sw("#1A1A23") + " line " + sw("#23232E") + " strong line " + sw("#30303E") + " words " + sw("#E6E8EE") + " soft words " + sw("#8F92A3")),
        ("Type", "Figtree 400 / 500 / 600 / 700 / 800 for words &middot; Roboto Mono 400 / 700 for numbers"),
        ("Shape", "radius: 6, 12, 20, pill 999 &middot; spacing steps: 4, 8, 12, 16, 24, 32, 48"),
    ]
    contrast = [
        ("Analysis pills and Report card", "near-black on every tone", "11 : 1 or more (card's second line 5.7 : 1)"),
        ("My Tests tabs", "open " + sw("#0F0F12") + " resting " + sw("#3D3D47"), "6.5 : 1 or more"),
        ("Streak card", "small words " + sw("#5B3A46"), "6 : 1 or more"),
        ("Blood-red chip", "white", "6 : 1 or more"),
        ("Parrot-green chip", "black", "7 : 1 or more"),
        ("Rank tiles", "white; near-black on gold", "5 : 1 or more; gold 6 : 1 or more"),
        ("Rank form header", "near-black on light bands; white on blood red and violet", "4.5 : 1 or more"),
    ]
    return f"""
<section>
  {h2("4", "Rules: motion, speed, sizes, contrast")}
  <h3>4.1 &nbsp;Keep it light on the phone</h3>
  <ul><li><b>Move and fade only.</b> Animate only <code>transform</code> and <code>opacity</code> (the supplied CSS does). Never animate gradient angles, background-position, box-shadow, filter, width or height.</li>
  <li><b>No blur.</b> Gloss and glint are plain gradients. Do not use <code>backdrop-filter</code> or <code>filter: blur()</code> for them.</li>
  <li><b>Rest what is not seen.</b> Off-screen pieces rest by themselves (<code>shine.js</code>). Add <code>data-rest</code> to pieces in a hidden tab pane or under an open sheet or dialog.</li>
  <li><b>Long rows.</b> In the 50-chip day row only the chips on screen may move.</li>
  <li><b>Reduce Motion.</b> With <code>prefers-reduced-motion: reduce</code> everything stands still: coloured edge, gloss, no glint, no swap, no stars. Already in the CSS.</li>
  <li>Use the Shine only on the ten pieces of this document. If everything shines, nothing does.</li></ul>
  <h3>4.2 &nbsp;Sizes</h3>
  <ul><li>The edge sits <b>inside</b> the piece. A piece with a 3 px edge has a face 1 px smaller on each side than the same piece with a 2 px edge.</li>
  <li>Everything that can be tapped is at least 44 px high.</li>
  <li><b>Press feel.</b> While a finger is on a piece it shrinks a little and springs back: pills and tiles to 97 %, tabs to 98 %, the big cards to 98.5 %.</li>
  <li>All numbers are CSS px for a phone-wide page (designed at 390 px; pieces stretch with the screen, edges and radii do not).</li></ul>
  <h3>4.3 &nbsp;Contrast that was checked in the app (keep these word colours)</h3>
  {table(["Piece", "Words", "Contrast"], contrast)}
  <h3>4.4 &nbsp;The base these pieces sit on (already shared by app and website)</h3>
  {table(["", "Values"], base)}
</section>"""


def checklist():
    items = [
        "shine.css and shine.js added once; <code>JLShine.watch()</code> called after lists load.",
        "Analysis: resting section pills are sky blue and light teal with the five-colour edge; the open pill is still solid red.",
        "Analysis: the Report download card (358 &times; 152, 3 px edge, three stars) is the first thing in every section.",
        "My Tests: tab order is Completed, In progress, Saved, and the screen opens on Completed.",
        "My Tests: pink = Completed, yellow = In progress, sky blue = Saved; the open tab has the glow, the 3 px edge and the white count chip.",
        "Home: the All India Series card has the ruby, gold, rose running edge, soft gloss and corner glint; its face is unchanged.",
        "Series page: the streak card is baby pink with rose-ink small words.",
        "Series page: day cards are glossy; the Upcoming card ends in sky blue.",
        "Series page: chips are blood red for days to come and parrot green for days that are over; the chosen chip has the black edge with a gold light and a dot under it.",
        "Series page: the 50-day map uses the chip colours, has no fading, and its legend reads Completed, Today, Upcoming.",
        "Rank: no black inside any of the six tiles; the chosen tile glows in its form's colour.",
        "Rank: the form has a 2 px running edge and a glossy header band; its body stays dark.",
        "Glint paths: left to right on pills, tabs, header bands and the Report card; corner to corner on cards, tiles and chips.",
        "Timings: edge 4.2 s, glint cycle 3.6 s, swap 5.6 s, stars 5.2 s.",
        "Pieces off screen, in hidden panes or under sheets rest; Reduce Motion stops all movement.",
        "Checked on a 360 px and a 390 px wide phone: no piece changed size, no text is cut.",
    ]
    return f"""
<section>
  {h2("5", "Checklist for the website")}
  <p class="where">Tick each line on the mobile website next to the app.</p>
  <ul class="check">{"".join(f"<li>{i}</li>" for i in items)}</ul>
  <div class="box sky"><h3>How to compare with the app</h3>
  <p>Open the app and the mobile website side by side on the same phone width. Each piece should match the &ldquo;APP&rdquo; pictures in Section 3: same colours,
  same size, the edge running at the same speed, and the glint crossing in the same direction.</p></div>
</section>"""


def appendix():
    return f"""
<section>
  {h2("A", "shine.css (full file)")}
  <p class="where">Copy as it is. The colours are not in this file: each piece passes its own through the <code>--</code> settings.</p>
  {code(SHINE_CSS, long=True)}
</section>
<section>
  {h2("B", "shine.js (full file)")}
  <p class="where">Load once, after the page's HTML (or with <code>defer</code>). No library needed.</p>
  {code(SHINE_JS, long=True)}
</section>"""


def document():
    count = check_against_theme()
    parts = [cover(), changes(), effect(), web_code(), p_pills(), p_report(), p_tabs(), p_home(), p_streak(), p_daycards(), p_chips(), p_map(),
             p_tiles(), p_forms(), rules(), checklist(), appendix()]
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>JEELIVE.AI app glossy theme: hand-off for the website</title>'
            '<link rel="stylesheet" href="shine.css"><link rel="stylesheet" href="guide.css"></head><body>'
            + "".join(parts) + '<script src="shine.js"></script></body></html>')
    return page, count


# One still frame for print: every piece as it looks 0.7 s after it starts (so rows show the wave), stars at their brightest.
FREEZE = """() => {
  document.getAnimations().forEach(a => {
    const delay = a.effect.getTiming().delay || 0;
    a.pause();
    a.currentTime = a.animationName === 'jl-spark' ? delay + 468 : a.animationName === 'jl-swap' ? 0 : 700;
  });
  return document.querySelectorAll('.jl-shine[data-ready]').length + ' of ' + document.querySelectorAll('.jl-shine').length;
}"""
FOOT = ('<div style="width:100%;font-family:Figtree,Arial,sans-serif;font-size:8px;color:#8C8C96;padding:0 48px;display:flex;justify-content:space-between">'
        '<span>JEELIVE.AI &middot; App glossy theme: hand-off for the website</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


async def build():
    from playwright.async_api import async_playwright
    page_html, count = document()
    (HERE / "guide.html").write_text(page_html)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 794, "height": 1123})
        # In print every piece must be drawn, wherever it is on the page.
        await page.add_init_script("delete window.IntersectionObserver;")
        await page.emulate_media(media="print")
        await page.goto((HERE / "guide.html").as_uri(), wait_until="load")
        await page.evaluate("document.fonts.ready")
        await page.evaluate("document.querySelectorAll('.jl-shine').forEach(JLShine.size)")
        await page.wait_for_timeout(300)
        ready = await page.evaluate(FREEZE)
        await page.pdf(path=str(PDF), width="210mm", height="297mm", print_background=True, display_header_footer=True,
                       header_template="<span></span>", footer_template=FOOT, margin={"top": "12mm", "bottom": "14mm", "left": "0", "right": "0"})
        await browser.close()
    print(f"{count} colours checked against theme.ts; pieces measured: {ready}; wrote {PDF} ({PDF.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    asyncio.run(build())
