"""Offline motion-design primitives; nothing is imported into the mobile app."""
from functools import lru_cache
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

ROOT = Path(__file__).parent
APP = ROOT.parents[1] / "frontend"
WHITE, MUTED = (247, 247, 250), (166, 178, 195)
TEAL, BLUE, RUBY = (101, 230, 212), (51, 112, 245), (182, 17, 42)


def ease(x):
    x = max(0, min(1, x))
    return 1 - (1 - x) ** 3


@lru_cache(maxsize=128)
def font(size, weight=800):
    return ImageFont.truetype(str(APP / f"assets/fonts/Figtree-{weight}.ttf"), max(8, int(size)))


@lru_cache(maxsize=512)
def text_sprite(text, size, color=WHITE, weight=800):
    f = font(size, weight)
    box = f.getbbox(text)
    out = Image.new("RGBA", (max(1, box[2] - box[0] + 6), max(1, box[3] - box[1] + 6)))
    ImageDraw.Draw(out).text((3 - box[0], 3 - box[1]), text, font=f, fill=color)
    return out


def text(canvas, words, x, y, size=80, color=WHITE, width=None, alpha=1, center=False, weight=800):
    if alpha <= 0:
        return
    size = int(size)
    if width:
        while font(size, weight).getlength(words) > width and size > 12:
            size -= 1
    sprite = text_sprite(words, size, color, weight)
    if alpha < .999:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.paste(sprite, (int(x - sprite.width / 2 if center else x), int(y)), sprite)


def panel(w, h, fill=(18, 24, 37), line=(52, 64, 86), radius=38):
    out = Image.new("RGBA", (int(w), int(h)))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((1, 1, w - 2, h - 2), radius, fill=(*fill, 250), outline=(*line, 255), width=2)
    d.rounded_rectangle((8, 8, w - 9, h - 9), max(1, radius - 7), outline=(255, 255, 255, 12), width=1)
    return out


def place(canvas, sprite, cx, cy, scale=1, angle=0, alpha=1):
    if alpha <= .002:
        return
    if abs(scale - 1) > .002:
        sprite = sprite.resize((max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))), Image.Resampling.BICUBIC)
    if abs(angle) > .02:
        sprite = sprite.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    if alpha < .999:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.paste(sprite, (int(cx - sprite.width / 2), int(cy - sprite.height / 2)), sprite)


@lru_cache(maxsize=32)
def halo(radius, color):
    s = int(radius * 2 + 120)
    out = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(out)
    d.ellipse((60, 60, s - 60, s - 60), outline=(*color, 160), width=10)
    return out.filter(ImageFilter.GaussianBlur(23))


def ring(canvas, cx, cy, radius, t, label="20", amount=.95, accent=TEAL):
    glow = halo(radius, accent)
    place(canvas, glow, cx, cy, alpha=.75 + .2 * math.sin(t * 2))
    d = ImageDraw.Draw(canvas, "RGBA")
    b = (cx - radius, cy - radius, cx + radius, cy + radius)
    d.ellipse(b, outline=(*accent, 35), width=3)
    d.arc(b, -90, -90 + max(.01, amount) * 360, fill=(*accent, 255), width=7)
    for i in range(60):
        a = i * math.tau / 60 - math.pi / 2
        r1, r2 = radius + 14, radius + (29 if i % 5 == 0 else 22)
        d.line((cx + math.cos(a) * r1, cy + math.sin(a) * r1, cx + math.cos(a) * r2, cy + math.sin(a) * r2), fill=(*accent, 95), width=2)
    size = int(radius * 1.18)
    sprite = text_sprite(str(label), size)
    place(canvas, sprite, cx, cy - 14)
    text(canvas, "SECONDS", cx, cy + radius * .47, 24, accent, center=True, weight=600)


@lru_cache(maxsize=12)
def avatar(name, size):
    im = Image.open(APP / f"assets/avatars/{name}.webp").convert("RGBA")
    im = ImageOps.fit(im, (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", im.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), 54, fill=255)
    im.putalpha(mask)
    return im


class Film:
    def __init__(self, portrait=True):
        self.portrait = portrait
        self.w, self.h = (1080, 1920) if portrait else (1920, 1080)
        self.cx, self.cy = (490, 975) if portrait else (1370, 535)
        self.bg = {}
        for key, asset in [("rapid", "rapid-stage.jpg"), ("series", "series-stage.jpg")]:
            im = Image.open(ROOT / "assets" / asset).convert("RGB")
            im = ImageOps.fit(im, (self.w + 100, self.h + 100), method=Image.Resampling.LANCZOS)
            if key == "rapid":
                shifted = Image.new("RGB", im.size)
                shifted.paste(im, (-50 if portrait else 410, 0))
                im = shifted
            arr = np.asarray(im).astype(float)
            xx = np.linspace(0, 1, im.width)[None, :, None]
            shade = .68 if portrait else .38 + .38 * xx
            self.bg[key] = Image.fromarray(np.clip(arr * shade, 0, 255).astype("uint8"))
        self.logo = Image.open(APP / "assets/images/jeelive-splash.png").convert("RGBA")
        rng = np.random.default_rng(7)
        self.dust = rng.random((45, 4))

    def background(self, t, ruby=False):
        bg = self.bg["series" if ruby else "rapid"]
        x = int(50 + 25 * math.sin(t * .11))
        y = int(50 + 19 * math.cos(t * .13))
        out = bg.crop((x, y, x + self.w, y + self.h))
        d = ImageDraw.Draw(out, "RGBA")
        color = (240, 100, 125) if ruby else TEAL
        for px, py, velocity, bright in self.dust:
            x = int(px * self.w + 12 * math.sin(t * .35 + py * 10))
            y = int((py * self.h - t * (8 + velocity * 16)) % self.h)
            r = 1 + int(bright * 2)
            d.ellipse((x, y, x + r, y + r), fill=(*color, int(20 + bright * 65)))
        return out

    def title(self, out, lines, u, accent=None, kicker=None, size=None, subtitle=None):
        portrait = self.portrait
        x, y, width = (78, 322, 825) if portrait else (124, 335, 810)
        size = size or (96 if portrait else 132)
        if kicker:
            text(out, kicker, x, y - 72, 28, accent or TEAL, width, ease(u / .45), weight=700)
        for i, line in enumerate(lines):
            a = ease((u - i * .08) / .55)
            text(out, line, x, y + i * size * 1.04 + (1 - a) * 48, size, accent if accent and i == len(lines) - 1 else WHITE, width, a)
        if subtitle:
            a = ease((u - .3) / .6)
            text(out, subtitle, x, y + len(lines) * size * 1.04 + 34, 34, MUTED, width, a, weight=500)

    def footer(self, out, label, color=TEAL):
        y = 1395 if self.portrait else 942
        text(out, label, 78 if self.portrait else 124, y, 25, color, 825 if self.portrait else 1650, weight=600)