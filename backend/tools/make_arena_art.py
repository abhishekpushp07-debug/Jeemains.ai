"""One-off build tool: original Rapid Fire arena artwork (gems, 3D icons, gang emblems). The Phoenix Diamond is built by make_phoenix_layers.py.

Each picture is generated once on pure black with its own glow and sparks, the black is turned into transparency
(the glow stays as light) and a small WebP is written into frontend/assets/arena. Nothing here runs inside the app.

    python tools/make_arena_art.py generate   # needs EMERGENT_LLM_KEY, skips pictures already in RAW
    python tools/make_arena_art.py build      # cut out + resize + write WebP
"""
import asyncio
import base64
import io
import os
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
RAW = Path(os.environ.get("ARENA_RAW", "/tmp/arena_raw2"))
OUT = ROOT.parent / "frontend" / "assets" / "arena"
STYLE = ("Epic legendary mobile-game icon: {what}. Dynamic three-quarter tilted hero angle, exaggerated chunky proportions, ultra glossy 3D render, "
         "vivid saturated colours, bright rim light and strong specular highlights, bursting with energy and motion, premium top-tier casual game art. "
         "Around it: {fx}. Centred, the whole subject and its effects inside the frame with a small margin. "
         "Isolated on a pure solid black (#000000) background and nothing else: no floor, no scenery, no frame, no border, no card, no tile, no rounded-square app-icon plate behind it, no text, no letters, no numbers, no watermark. Square image.")
GEM = "a huge faceted {colour} diamond gem, brilliant cut with a pointed bottom, tilted, light blazing inside it"
GEM_FX = "a glowing {glow} aura, sharp light rays, star-shaped sparkles and tiny flying shards"
EMBLEM = "a heraldic team crest: {what} bursting out of a rounded shield with a thick gold rim"
# name: (subject, effects, output size, model)
ART = {
    "gem_red": (GEM.format(colour="ruby-red"), GEM_FX.format(glow="red and orange"), 168, None),
    "gem_blue": (GEM.format(colour="royal-blue sapphire"), GEM_FX.format(glow="electric blue"), 168, None),
    "gem_emerald": (GEM.format(colour="deep-green emerald"), GEM_FX.format(glow="bright green"), 168, None),
    "gem_gold": (GEM.format(colour="golden-yellow"), GEM_FX.format(glow="warm golden"), 168, None),
    "gem_kohinoor": (GEM.format(colour="clear white, rainbow-iridescent"), GEM_FX.format(glow="white and rainbow"), 168, None),
    "ic_home": ("a cosy little hero house with a red roof, cream walls and a teal door, warm light pouring out of its windows", "golden sparkles and tiny stars swirling around it", 168, None),
    "ic_trophy": ("a mighty golden trophy cup with two handles and a big red gem on the front", "exploding golden light rays, confetti and sparkles", 168, None),
    "ic_gang": ("a squad of three round helmeted heroes in a power pose shoulder to shoulder, one teal, one gold, one red", "a fiery energy aura and crackling lightning sparks", 168, None),
    "ic_store": ("a magical market stall with a teal-and-white striped awning and a big gold coin sign", "glowing lanterns, gold coins and gems flying out, sparkles", 168, None),
    "ic_swords": ("two crossed steel swords with golden hilts clashing", "a bright spark explosion where the blades meet, flames licking along the blades", 168, None),
    "ic_friends": ("two friendly round hero characters, one teal and one gold, jumping into a high-five", "a burst of stars and sparkles at their hands, speed lines", 168, None),
    "ic_rival": ("a fierce robot head with blazing teal eyes and an antenna", "electric arcs crackling around it and glowing sparks", 168, None),
    "ic_bolt": ("a thick golden-yellow lightning bolt striking down", "crackling electric arcs, flying sparks and a bright yellow glow", 168, None),
    "ic_coin": ("a thick shiny gold coin with a star embossed on it, spinning", "a bright shine streak, sparkles and a few smaller coins flying behind it", 168, None),
    "ic_flame": ("a roaring orange and red flame with a white-hot core", "flying embers and sparks, heat glow", 168, None),
    "ic_chest": ("a wooden treasure chest with gold trim bursting open", "a beam of golden light, gold coins and red gems flying out, sparkles", 168, None),
    "ic_target": ("a red-and-white bullseye target with an arrow slamming into its centre", "an impact burst, flying splinters and sparks", 168, None),
    "ic_history": ("an hourglass with a golden frame and glowing golden sand", "a magic swirl of light and time sparkles circling it", 168, None),
    "ic_back": ("a chunky glossy white arrow pointing to the LEFT", "a short speed trail behind it on the right and a few sparkles", 132, None),
    "em_lion": (EMBLEM.format(what="a roaring golden lion head"), "flames and sparks flaring behind the shield", 168, None),
    "em_eagle": (EMBLEM.format(what="a fierce white eagle with spread wings"), "light rays and flying feathers behind the shield", 168, None),
    "em_thunder": (EMBLEM.format(what="a bright yellow lightning bolt"), "electric arcs crackling behind the shield", 168, None),
    "em_crown": (EMBLEM.format(what="a jewelled golden crown"), "golden light rays and sparkles behind the shield", 168, None),
    "em_shield": (EMBLEM.format(what="a steel knight helmet in front of two crossed swords"), "sparks and a blue energy glow behind the shield", 168, None),
    "em_dragon": (EMBLEM.format(what="a red dragon head breathing fire"), "flames and embers behind the shield", 168, None),
    "em_wolf": (EMBLEM.format(what="a howling silver-blue wolf head"), "icy mist, moonlight glow and frost sparkles behind the shield", 168, None),
    "em_rocket": (EMBLEM.format(what="a red-and-white rocket blasting upwards"), "a fiery exhaust trail and sparks behind the shield", 168, None),
}


async def one(name, sem):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    what, fx, _, model = ART[name]
    target = RAW / f"{name}.png"
    if target.exists():
        return
    async with sem:
        for attempt in range(3):
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"arena2-{name}-{attempt}", system_message="You are a game icon artist.")
                chat.with_model("gemini", model or "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
                _, images = await chat.send_message_multimodal_response(UserMessage(text=STYLE.format(what=what, fx=fx)))
                if images:
                    target.write_bytes(base64.b64decode(images[0]["data"]))
                    print("ok", name, flush=True)
                    return
            except Exception as e:  # noqa: BLE001
                print("retry", name, type(e).__name__, str(e)[:120], flush=True)
                await asyncio.sleep(3)
        print("FAILED", name, flush=True)


async def generate(names):
    RAW.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(6)
    await asyncio.gather(*(one(n, sem) for n in names))


def cut_out(img: Image.Image) -> Image.Image:
    """Black becomes transparent. The solid subject stays opaque (dark outlines included); the glow around it fades out as light."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    peak = a.max(axis=2)
    dark = peak < 34
    labels, _ = ndimage.label(dark)
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    outside = np.isin(labels, border[border > 0])
    light = np.clip((peak - 10) / 150, 0, 1)            # how much light a glow pixel carries
    depth = np.clip(ndimage.distance_transform_edt(~outside) / 7, 0, 1)  # 0 at the edge of the subject, 1 inside it
    alpha = np.where(outside, light, np.maximum(light, depth))
    rgb = np.where(alpha[..., None] < 0.999, a / np.maximum(alpha[..., None], 0.08), a)  # keep glow colours bright once the black is gone
    return Image.fromarray(np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8), "RGBA")


def build(names):
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for name in names:
        src = RAW / f"{name}.png"
        if not src.exists():
            print("missing", name)
            continue
        size = ART[name][2]
        img = cut_out(Image.open(src))
        box = Image.fromarray((np.asarray(img)[..., 3] > 20).astype(np.uint8) * 255).getbbox()
        img = img.crop(box)
        w, h = img.size
        side = max(w, h)
        sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        sq.paste(img, ((side - w) // 2, (side - h) // 2))
        img = sq.resize((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=78, alpha_quality=85, method=6)
        (OUT / f"{name}.webp").write_bytes(buf.getvalue())
        total += buf.tell()
        print(f"{name:14s} {img.size} {buf.tell():6d} bytes")
    print("total bytes", total)


if __name__ == "__main__":
    names = sys.argv[2:] or list(ART)
    if sys.argv[1] == "generate":
        asyncio.run(generate(names))
    else:
        build(names)
