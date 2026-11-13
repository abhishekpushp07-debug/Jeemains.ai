"""One-off build tool: the Phoenix Diamond as layers, so it is always upright and perfectly symmetrical.

    phoenix_wing.webp   the LEFT fire wing (the app mirrors it for the right wing)
    pgem_<colour>.webp  the upright centre diamond in the five streak colours (recoloured from one ruby)

    python tools/make_phoenix_layers.py generate   # needs EMERGENT_LLM_KEY, skips pictures already in RAW
    python tools/make_phoenix_layers.py build
Nothing here runs inside the app.
"""
import asyncio
import base64
import os
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image
from scipy import ndimage

from make_arena_art import cut_out

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
RAW = Path(os.environ.get("ARENA_RAW", "/tmp/arena_raw2"))
OUT = ROOT.parent / "frontend" / "assets" / "arena"
TAIL = (" Flat straight-on front view like a heraldic emblem: no tilt, no rotation, no perspective, no three-quarter angle. Centred with a small margin. "
        "Ultra glossy premium mobile-game art, vivid saturated colours. Isolated on a pure solid black (#000000) background and nothing else: "
        "no floor, no scenery, no frame, no card, no text, no letters, no watermark. Square image.")
PROMPTS = {
    "pwings": ("A majestic pair of phoenix wings made of blazing fire, perfectly mirror-symmetrical, spread wide open to the left and to the right and sweeping upward, "
               "both wings joined at one small point in the exact centre of the image. Long layered flame feathers in clear rows, white-hot gold near the centre, "
               "bright orange in the middle and deep red at the feather tips, a few flying embers. ONLY the two wings: no bird, no body, no head, no tail, no gem, no jewel." + TAIL),
    "pruby": ("One huge faceted crimson-red ruby diamond, classic brilliant cut seen exactly from the front, perfectly upright and perfectly mirror-symmetrical: "
              "a flat table edge on top, widest near the top, tapering to a sharp point straight down at the bottom centre. Crisp facets, bright white specular highlights, "
              "light blazing inside it, a thin golden rim light on its edges. ONLY the gem: no wings, no fire, no sparkles, no rays around it." + TAIL),
}
# hue (0-1), saturation gain, brightness gain
COLOURS = {"red": None, "blue": (0.61, 1.0, 1.05), "emerald": (0.39, 1.0, 1.0), "gold": (0.125, 0.95, 1.25), "kohinoor": (None, 0.16, 1.5)}


async def generate():
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    RAW.mkdir(parents=True, exist_ok=True)

    async def one(name):
        for attempt in range(3):
            target = RAW / f"{name}.png"
            if target.exists():
                return
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"phoenix-{name}-{attempt}", system_message="You are a game icon artist.")
                chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
                _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPTS[name]))
                if images:
                    target.write_bytes(base64.b64decode(images[0]["data"]))
                    print("ok", name, flush=True)
                    return
            except Exception as e:  # noqa: BLE001
                print("retry", name, type(e).__name__, str(e)[:160], flush=True)
                await asyncio.sleep(3)
        print("FAILED", name, flush=True)

    await asyncio.gather(*(one(n) for n in PROMPTS))


def emissive(img):
    """Fire on black: brightness becomes transparency, so only light is left and it glows on any dark background."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    # The model sometimes paints the black on a white rounded card: clear whatever white touches the border.
    labels, _ = ndimage.label(a.min(axis=2) > 170)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    a[ndimage.binary_dilation(np.isin(labels, edge[edge > 0]), iterations=16)] = 0
    peak = a.max(axis=2)
    alpha = np.clip((peak - 14) / 150, 0, 1) ** 0.85
    rgb = a / np.maximum(alpha[..., None], 0.1)
    return np.dstack([rgb, alpha * 255]).clip(0, 255)


def bbox(alpha, floor=24):
    ys, xs = np.where(alpha > floor)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def save(arr, name, width):
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    img = img.resize((width, round(width * img.height / img.width)), Image.LANCZOS)
    path = OUT / f"{name}.webp"
    img.save(path, "WEBP", quality=80, alpha_quality=88, method=6)
    print(f"{name:14s} {img.size} {path.stat().st_size:6d} bytes")


def recolour(arr, hue, sat, val):
    rgb, alpha = arr[..., :3] / 255, arr[..., 3:]
    hsv = np.array(Image.fromarray((rgb * 255).astype(np.uint8), "RGB").convert("HSV")).astype(np.float32) / 255
    # Only the red body changes colour; white highlights and the golden rim keep their own light.
    body = np.clip(hsv[..., 1] * 1.6, 0, 1)
    if hue is None:  # Kohinoor: clear white with a soft rainbow running across the facets
        h, w = hsv.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        hsv[..., 0] = ((xx / w) * 0.9 + (yy / h) * 0.5) % 1
        hsv[..., 1] = np.clip(hsv[..., 1] * sat + 0.1 * body, 0, 1)
    else:
        hsv[..., 0] = hue
        hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 1)
    hsv[..., 2] = np.clip(hsv[..., 2] * val, 0, 1)
    out = np.array(Image.fromarray((hsv * 255).astype(np.uint8), "HSV").convert("RGB")).astype(np.float32)
    return np.dstack([out, alpha])


def build():
    wings = emissive(Image.open(RAW / "pwings.png"))
    x0, y0, x1, y1 = bbox(ndimage.binary_opening(wings[..., 3] > 40, iterations=3) * 255.0)
    reach = max(wings.shape[1] // 2 - x0, x1 - wings.shape[1] // 2) + 10  # keep the picture's own centre line as the mirror line
    half = wings[max(0, y0 - 10):y1 + 10, wings.shape[1] // 2 - reach: wings.shape[1] // 2]  # left wing; the centre line is its right edge
    save(half, "phoenix_wing", 330)
    print("wing ratio h/w", round(half.shape[0] / half.shape[1], 3))

    ruby = np.asarray(cut_out(Image.open(RAW / "pruby.png"))).astype(np.float32)
    x0, y0, x1, y1 = bbox(ruby[..., 3], 60)
    ruby = ruby[y0:y1, x0:x1]
    left = ruby[:, : ruby.shape[1] // 2]
    ruby = np.concatenate([left, left[:, ::-1]], axis=1)  # exact mirror symmetry about the centre line
    ruby[..., 3] = ndimage.gaussian_filter(ruby[..., 3], 0.6)
    print("gem ratio h/w", round(ruby.shape[0] / ruby.shape[1], 3))
    for name, shift in COLOURS.items():
        save(ruby if shift is None else recolour(ruby, *shift), f"pgem_{name}", 250)


if __name__ == "__main__":
    asyncio.run(generate()) if sys.argv[1] == "generate" else build()
