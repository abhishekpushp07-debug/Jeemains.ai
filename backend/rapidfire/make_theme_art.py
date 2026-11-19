"""One-time: artwork for the five All India Rapid card themes (space, world cup, lions, horse race, archery).
Run from /app/backend:  python rapidfire/make_theme_art.py [name ...]
Backgrounds are full square scenes; sprites are drawn on black (glowing things) or green (solid things) and keyed out."""
import asyncio
import base64
import io
import os
import sys

import numpy as np
from dotenv import load_dotenv
from PIL import Image

load_dotenv("/app/backend/.env")
from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage  # noqa: E402

OUT = "/app/frontend/assets/arena/"
GREEN = "on a perfectly flat pure solid chroma-key green (#00FF00) background with no shadow, no ground, no text, no logo"
BLACK = "on a pure solid black background, no text, no logo"
WHITE = "as one solid pure black silhouette with crisp clean edges and no inner detail, on a plain pure white background, no ground, no text"
REF = "/app/backend/rapidfire/ref_battle.jpeg"  # the student's reference: riders on a ridge against blazing red smoke
BG = "square image, cinematic mobile game background art, rich colours, no text, no letters, no logo, no watermark"
ART = {
    # name: (prompt, mode, size)
    "th_space_bg": ("Deep outer space: a swirling violet and electric-blue nebula, a glowing ringed planet in the lower left corner, "
                    f"a bright golden galaxy far away, thousands of tiny sharp stars, {BG}, no spaceship", "bg", 720),
    "th_spaceship": ("One original sleek futuristic rocket spaceship, white and silver hull with gold and teal trim, glowing cyan cockpit window, "
                     "a long bright orange and electric blue engine flame blasting from the back, flying to the upper right at a 45 degree angle, "
                     f"3D game art, the whole ship visible and centred, {BLACK}", "black", 520),
    "th_stadium": ("A packed football stadium at night seen from pitch level, brilliant floodlights, a glowing green pitch in the lower third, "
                   f"huge crowd with thousands of camera flashes, golden confetti in the air, {BG}, no players, no ball", "bg", 720),
    "th_lion_bg": ("Wild African savannah at a dramatic sunset: a giant red-orange sun low behind a rocky ridge, golden dust in the air, "
                   f"silhouetted acacia trees, a flat dusty ground in the lower third, {BG}, no animals", "bg", 720),
    "th_lion": ("One original majestic male lion leaping forward to fight, roaring with its mouth wide open, thick golden mane flowing, front paws "
                f"raised with claws out, side view facing right, warm golden rim light, 3D game art, the whole lion visible, {GREEN}", "green", 560),
    "th_race_bg": ("A grand horse racing track on a sunny afternoon, side view down the home straight: lush green turf in the lower half, "
                   f"a big white grandstand full of cheering people, colourful flags, bright blue sky with soft clouds, {BG}, no horses", "bg", 720),
    "th_horse": ("One original racehorse galloping at full speed, side view facing right, legs fully stretched mid-stride, glossy dark bay coat, "
                 "a jockey in red and gold silks and a gold helmet crouched low on it, plain red saddle cloth with no number, "
                 f"3D game art, the whole horse and jockey visible, {GREEN}", "green", 560),
    "th_horse2": ("One original racehorse galloping at full speed, side view facing right, legs fully stretched mid-stride, shining dapple grey coat, "
                  "a jockey in royal blue and white silks and a white helmet crouched low on it, plain blue saddle cloth with no number, "
                  f"3D game art, the whole horse and jockey visible, {GREEN}", "green", 560),
    "th_horse3": ("One original racehorse galloping at full speed, side view facing right, legs fully stretched mid-stride, bright chestnut coat "
                  "with a white blaze, a jockey in saffron orange and purple silks and a purple helmet crouched low on it, plain purple saddle cloth "
                  f"with no number, 3D game art, the whole horse and jockey visible, {GREEN}", "green", 560),
    "th_range_bg": ("A royal archery range at golden hour: an ancient sandstone fort courtyard with tall saffron and gold banners, warm sun rays, "
                    f"distant purple hills, a soft blurred depth of field, {BG}, no people, no target", "bg", 720),
    "th_target": ("One original archery target seen perfectly face-on: a round straw boss with crisp scoring rings white, black, blue, red and a "
                  f"shining gold bullseye in the centre, a thin wooden rim, slight 3D depth, game art, perfectly centred and round, {GREEN}", "green", 520),
    # The fire world (the student's reference): blazing smoke behind a dark ridge, black silhouettes on it.
    "th_fire_bg": ("Using the attached picture only as the style and colour reference, paint a NEW square 1:1 image of the same scene but EMPTY: "
                   "thick blazing red-orange smoke and fire glow filling the middle, bright almost white-hot in the centre, fading to deep black at the "
                   "top corners, and a dark black rocky ridge across the lower third. NO riders, NO horses, NO people, NO animals, NO weapons, "
                   "nothing standing on the ridge, no text, cinematic and powerful", "bgref", 720),
    "sil_rider1": (f"A mounted warrior on a horse galloping to the right at full speed, raising a curved sword high, {WHITE}", "white", 480),
    "sil_rider2": (f"A mounted warrior on a horse galloping to the right at full speed, holding a long spear with a small flag forward, {WHITE}", "white", 480),
    "sil_rider3": (f"A mounted horse archer galloping to the right at full speed, drawing a bow and aiming ahead, {WHITE}", "white", 480),
    "sil_archer": (f"A standing archer seen from the side, facing right, drawing a long bow at full draw, aiming straight to the right, one foot forward, cape flowing, {WHITE}", "white", 480),
    "sil_lion": (f"A male lion leaping to the right to attack, roaring with mouth open, mane flowing, front paws stretched forward with claws out, {WHITE}", "white", 480),
    "sil_ship": (f"A sleek futuristic rocket spaceship flying to the right, side view, pointed nose, swept fins, {WHITE}", "white", 480),
    "sil_army": (f"A wide line of warriors standing on a ridge, raising swords, spears and banners high in victory, some on horses, wide panorama, {WHITE}", "white_wide", 720),
}


def key_white(im: Image.Image) -> Image.Image:
    a = np.asarray(im.convert("L")).astype(np.float32)
    alpha = np.clip((235 - a) * 1.25, 0, 255)
    z = np.zeros_like(a)
    return Image.fromarray(np.dstack([z + 8, z + 2, z + 4, alpha]).astype(np.uint8), "RGBA")


def square(im: Image.Image, size: int) -> Image.Image:
    box = im.getbbox() if im.mode == "RGBA" else None
    if box:
        im = im.crop(box)
    w, h = im.size
    side = max(w, h)
    sq = Image.new("RGBA", (side, side))
    sq.paste(im, ((side - w) // 2, (side - h) // 2))
    return sq.resize((size, size), Image.LANCZOS)


def key_black(im: Image.Image) -> Image.Image:
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    m = a.max(axis=2)
    alpha = np.clip((m - 14) * 1.6, 0, 255)
    k = 255 / np.maximum(alpha, 1)
    rgb = np.clip(a * k[..., None], 0, 255)  # un-premultiply so the glow keeps its colour on any background
    return Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")


def key_green(im: Image.Image) -> Image.Image:
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    spill = g - np.maximum(r, b)  # how much greener than the other two
    alpha = np.clip(255 - (spill - 30) * 4.5, 0, 255)
    alpha[g < 90] = 255
    g2 = np.where(spill > 0, np.maximum(r, b) + np.minimum(spill, 8), g)  # take the green fringe off the edges
    out = np.dstack([r, g2, b, alpha]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


async def make(name: str):
    prompt, mode, size = ART[name]
    chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"theme-art-{name}", system_message="You create game artwork.")
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    files = [ImageContent(base64.b64encode(open(REF, "rb").read()).decode())] if mode == "bgref" else None
    _, images = await chat.send_message_multimodal_response(UserMessage(text=prompt, file_contents=files))
    raw = base64.b64decode(images[0]["data"])
    open(f"/tmp/{name}_raw.png", "wb").write(raw)
    im = Image.open(io.BytesIO(raw))
    if mode == "white_wide":
        im = key_white(im)
        box = im.getbbox()
        im = im.crop(box) if box else im
        im = im.resize((size, round(size * im.size[1] / im.size[0])), Image.LANCZOS)
        im.save(OUT + name + ".webp", "WEBP", quality=86, method=6)
    elif mode in ("bg", "bgref"):
        w, h = im.size
        side = min(w, h)
        im = im.convert("RGB").crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2)).resize((size, size), Image.LANCZOS)
        im.save(OUT + name + ".webp", "WEBP", quality=80, method=6)
    else:
        im = square({"black": key_black, "green": key_green, "white": key_white}[mode](im), size)
        im.save(OUT + name + ".webp", "WEBP", quality=86, method=6)
    print("saved", name, flush=True)


async def main(names):
    res = await asyncio.gather(*(make(n) for n in names), return_exceptions=True)
    for n, r in zip(names, res):
        if isinstance(r, Exception):
            print("FAILED", n, repr(r), flush=True)


asyncio.run(main(sys.argv[1:] or list(ART)))
