"""Purpose-composed portrait/wide shots. Quiz/duel are feature illustrations."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw
from graphics import WHITE, MUTED, TEAL, BLUE, RUBY, text, text_sprite, place, panel, ring, avatar, ease

STARTS = [0, 3, 7, 13, 17, 22, 27, 29, 34, 39, 45]


def hook(f, t, u):
    out = f.background(t)
    f.title(out, ["Pen rakh do."] if f.portrait else ["Pen", "rakh do."], u, kicker="RAPID FIRE / NO-PEN CHALLENGE")
    ring(out, f.cx, f.cy, 270 if f.portrait else 290, t, amount=.91)
    text(out, "Sirf 20 seconds.", f.cx, f.cy + 360, 43, TEAL, center=True)
    f.footer(out, "JEELIVE.AI  /  RAPID FIRE")
    return out


def challenge(f, t, u):
    out = f.background(t)
    f.title(out, ["20 sec.", "No pen."], u, accent=TEAL, kicker="RAPID FIRE")
    ring(out, f.cx, f.cy + (85 if f.portrait else 0), 244 if f.portrait else 290, t, amount=.88 + .04 * math.sin(u))
    f.footer(out, "DIMAAG CHALAO. CHALLENGE LO.")
    return out


def question_card(u):
    p = panel(810, 610)
    text(p, "CONCEPT PREVIEW", 38, 31, 23, TEAL, weight=700)
    remaining = 20 - min(4, int(u))
    text(p, f"{remaining}s", 675, 27, 35, TEAL)
    text(p, "Force ka SI unit?", 38, 107, 57, width=730)
    text(p, "Socho. Phir ek option chuno.", 38, 187, 28, MUTED, weight=500)
    answered = u >= 4.65
    d = ImageDraw.Draw(p)
    for i, label in enumerate(["Newton", "Joule", "Watt", "Pascal"]):
        x, y = 38 + (i % 2) * 374, 270 + (i // 2) * 118
        active = answered and i == 0
        d.rounded_rectangle((x, y, x + 351, y + 96), 22, fill=(23, 66, 61) if active else (26, 34, 49), outline=TEAL if active else (51, 64, 87), width=3 if active else 1)
        text(p, label, x + 25, y + 24, 42, TEAL if active else WHITE, weight=700)
        if active:
            d.line((x + 288, y + 46, x + 301, y + 59, x + 325, y + 33), fill=TEAL, width=5)
    text(p, "Sahi jawab. Agla challenge?" if answered else "20-second concept challenge", 40, 539, 27, TEAL if answered else MUTED, weight=600)
    if 4.3 < u < 4.75:
        pulse = int(15 + (u - 4.3) * 90)
        d.ellipse((245 - pulse, 318 - pulse, 245 + pulse, 318 + pulse), outline=(255, 255, 255, 160), width=3)
    return p


def question(f, t, u):
    out = f.background(t)
    f.title(out, ["Socho.", "Tap karo."], u, accent=TEAL, kicker="RAPID FIRE", subtitle="Ek concept. Ek sahi jawab.")
    p = question_card(u)
    scale = (1 if f.portrait else .96) * (.93 + .07 * ease(u / .6))
    place(out, p, f.cx, 1040 if f.portrait else 560, scale, .65 * math.sin(u * .75), ease(u / .5))
    f.footer(out, "NO PEN. NO PAPER. SIRF TUM.")
    return out


@lru_cache(maxsize=6)
def concept_card(subject, accent, numeral):
    p = panel(580, 270, line=accent, radius=32)
    text(p, numeral, 35, 27, 27, accent, weight=600)
    text(p, subject, 35, 91, 63, width=500)
    text(p, "CONCEPTS  /  RAPID FIRE", 35, 195, 23, accent, weight=600)
    d = ImageDraw.Draw(p, "RGBA")
    d.ellipse((440, 24, 540, 124), outline=(*accent, 70), width=2)
    d.arc((417, 44, 553, 106), 10, 350, fill=(*accent, 160), width=3)
    return p


def subjects(f, t, u):
    out = f.background(t)
    f.title(out, ["Har card.", "Naya challenge."], u, kicker="RAPID FIRE", size=84 if f.portrait else 118)
    rows = [("Physics", TEAL), ("Chemistry", (142, 182, 255)), ("Maths", (185, 161, 255))]
    for i, (label, color) in enumerate(rows):
        p = concept_card(label, color, f"0{i + 1}")
        y = (835 + i * 205) if f.portrait else (337 + i * 203)
        x = f.cx + (i - 1) * (32 if f.portrait else 36)
        a = ease((u - i * .15) / .7)
        place(out, p, x + (1 - a) * 200, y + 8 * math.sin(t + i), 1 if f.portrait else .98, (1 - i) * 4, a)
    return out


def duel(f, t, u):
    out = f.background(t)
    f.title(out, ["Solo bhi.", "Dost ke saath bhi."], u, kicker="RAPID FIRE", size=79 if f.portrait else 112)
    size = 335 if f.portrait else 340
    center = f.cx if f.portrait else 1360
    cy = 1025 if f.portrait else 550
    separation = 207 if f.portrait else 223
    for i, name in enumerate(["av_rocket", "av_einstein"]):
        a = ease((u - i * .12) / .75)
        x = center + (2 * i - 1) * (separation + (1 - a) * 220)
        place(out, avatar(name, size), x, cy + 10 * math.sin(u * 1.2 + i), 1, (1 - i * 2) * 2.2, a)
        text(out, "TUM" if i == 0 else "DOST", x, cy + 205, 27, TEAL if i == 0 else (185, 161, 255), center=True)
    vs = text_sprite("VS", 78, WHITE)
    place(out, vs, center, cy, .92 + .04 * math.sin(t * 3))
    f.footer(out, "SOLO SPRINT  /  CHALLENGE FRIEND")
    return out


def dare(f, t, u):
    out = f.background(t)
    f.title(out, ["Kitna tez", "sochoge?"], u, accent=TEAL, kicker="20-SECOND NO-PEN CHALLENGE")
    ring(out, f.cx, 1060 if f.portrait else 540, 250 if f.portrait else 292, t, amount=.82 + .05 * math.sin(u))
    f.footer(out, "RAPID FIRE. CHALLENGE ACCEPTED?")
    return out


def bridge(f, t, u):
    progress = min(1, u / 1.9)
    mix = .5 - .5 * math.cos(progress * math.pi)
    out = Image.blend(f.background(t), f.background(t, True), mix)
    carry = Image.new("RGBA", out.size)
    color = tuple(int(a * (1 - mix) + b * mix) for a, b in zip(TEAL, (255, 130, 145)))
    ring(carry, f.cx, 1060 if f.portrait else 540, 250 if f.portrait else 292, t, amount=.82, accent=color)
    place(out, carry, f.w / 2, f.h / 2, alpha=math.cos(progress * math.pi / 2) ** 1.2)
    lines = ["Ab exam", "mode."]
    x = 78 if f.portrait else 124
    y = 710 if f.portrait else 350
    for i, line in enumerate(lines):
        a = ease((u - .1 * i) / .7)
        text(out, line, x + (1 - a) * 80, y + i * 125, 114 if f.portrait else 138, WHITE, 825 if f.portrait else 810, a)
    return out


@lru_cache(maxsize=1)
def series_card():
    p = panel(790, 470, (26, 7, 10), (152, 71, 85))
    gleam = Image.new("RGBA", p.size)
    d = ImageDraw.Draw(gleam, "RGBA")
    for i in range(80):
        d.line((i * 10, 0, max(0, i * 10 - 230), 465), fill=(255, 198, 204, int(17 * (1 - i / 80))), width=10)
    p = Image.alpha_composite(p, gleam)
    d = ImageDraw.Draw(p, "RGBA")
    text(p, "ALL INDIA", 45, 42, 24, (222, 208, 213), weight=600)
    text(p, "JEE Mains", 45, 106, 73, width=700)
    text(p, "Test Series", 45, 188, 73, width=700)
    d.rounded_rectangle((43, 319, 747, 415), 22, fill=RUBY, outline=(255, 198, 204), width=2)
    text(p, "Practice. Analysis. Review.", 395, 351, 32, center=True)
    return p


def series(f, t, u):
    out = f.background(t, True)
    f.title(out, ["All India.", "Bada challenge."], u, accent=(255, 120, 131), kicker="JEE MAINS TEST SERIES", size=89 if f.portrait else 121)
    a = ease((u - .15) / .85)
    place(out, series_card(), f.cx, 1030 if f.portrait else 575, .96 + .04 * a, .8 * math.sin(u * .55), a)
    f.footer(out, "ALL INDIA JEE MAINS TEST SERIES", (255, 158, 170))
    return out


def feature_icon(draw, x, y, kind):
    color = (255, 151, 168)
    if kind == 0:
        draw.rounded_rectangle((x, y + 7, x + 43, y + 46), 7, outline=color, width=3)
        draw.line((x, y + 19, x + 43, y + 19), fill=color, width=3)
        for dx in [11, 31]:
            draw.line((x + dx, y, x + dx, y + 13), fill=color, width=3)
    elif kind == 1:
        for i, h in enumerate([18, 31, 43]):
            draw.rounded_rectangle((x + i * 17, y + 46 - h, x + i * 17 + 10, y + 46), 3, fill=color)
    else:
        draw.ellipse((x + 4, y, x + 39, y + 33), outline=color, width=3)
        draw.line((x + 14, y + 35, x + 29, y + 35), fill=color, width=3)
        draw.line((x + 14, y + 43, x + 29, y + 43), fill=color, width=3)


@lru_cache(maxsize=3)
def feature_card(i, label):
    p = panel(790, 135, (27, 12, 20), (97, 40, 53), 26)
    feature_icon(ImageDraw.Draw(p), 35, 43, i)
    text(p, label, 116, 44, 42, width=615, weight=700)
    return p


def routine(f, t, u):
    out = f.background(t, True)
    f.title(out, ["Practice ko", "routine banao."], u, kicker="ALL INDIA TEST SERIES", accent=(255, 120, 131), size=89 if f.portrait else 119)
    for i, label in enumerate(["Full-length tests", "Detailed analysis", "Solutions & review"]):
        a = ease((u - .18 * i) / .75)
        y = 866 + i * 179 if f.portrait else 359 + i * 176
        place(out, feature_card(i, label), f.cx + (1 - a) * 100, y, .98, 0, a)
    return out


def finale(f, t, u):
    out = Image.blend(f.background(t), f.background(t, True), .5)
    a = ease(u / 1.05)
    width = 815 if f.portrait else 970
    logo = f.logo.resize((width, int(width * f.logo.height / f.logo.width)), Image.Resampling.LANCZOS)
    if f.portrait:
        text(out, "Ab tumhari", 78, 388, 111, width=830, alpha=a)
        text(out, "baari.", 78, 510, 111, TEAL, width=830, alpha=a)
        place(out, logo, 490, 950 + (1 - a) * 45, .97 + .03 * a, alpha=a)
        text(out, "20 SEC. NO PEN.", 490, 1215, 43, TEAL, center=True, alpha=ease((u - .5) / .7))
        text(out, "RAPID FIRE + ALL INDIA SERIES", 490, 1313, 28, WHITE, width=820, center=True, alpha=a, weight=600)
    else:
        place(out, logo, 960, 389 + (1 - a) * 35, .97 + .03 * a, alpha=a)
        text(out, "Ab tumhari baari.", 960, 643, 100, WHITE, width=1550, center=True, alpha=a)
        text(out, "20-SEC RAPID FIRE  +  ALL INDIA TEST SERIES", 960, 825, 35, TEAL, width=1620, center=True, alpha=ease((u - .5) / .7), weight=600)
    return out


SHOTS = [hook, challenge, question, subjects, duel, dare, bridge, series, routine, finale]


def frame(film, t):
    i = next(i for i in range(len(SHOTS)) if t < STARTS[i + 1])
    u = t - STARTS[i]
    current = SHOTS[i](film, t, u)
    if i > 0 and u < .32:
        previous = SHOTS[i - 1](film, t, STARTS[i] - STARTS[i - 1])
        current = Image.blend(previous, current, ease(u / .32))
    return current