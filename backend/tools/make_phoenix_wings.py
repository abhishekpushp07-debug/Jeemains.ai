"""One-off build tool: the Phoenix wing in each streak-diamond colour, recoloured from the original fire wing.

    python tools/make_phoenix_wings.py
Writes pwing_<colour>.webp next to phoenix_wing.webp (the red diamond keeps the original fire wing). Nothing here runs inside the app.
"""
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[2] / "frontend" / "assets" / "arena"
# hue turn (0-1), saturation gain, brightness gain; None hue = clear white light
COLOURS = {"blue": (0.56, 1.0, 1.0), "emerald": (0.33, 0.95, 0.95), "gold": (0.07, 0.8, 1.12), "kohinoor": (None, 0.14, 1.25)}


def main():
    src = np.asarray(Image.open(OUT / "phoenix_wing.webp").convert("RGBA")).astype(np.float32)
    rgb, alpha = src[..., :3], src[..., 3:]
    hsv = np.array(Image.fromarray(rgb.astype(np.uint8), "RGB").convert("HSV")).astype(np.float32) / 255
    for name, (turn, sat, val) in COLOURS.items():
        out = hsv.copy()
        if turn is None:
            out[..., 0] = 0.58
        else:
            out[..., 0] = (out[..., 0] + turn) % 1
        out[..., 1] = np.clip(out[..., 1] * sat, 0, 1)
        out[..., 2] = np.clip(out[..., 2] * val, 0, 1)
        img = Image.fromarray(np.dstack([np.array(Image.fromarray((out * 255).astype(np.uint8), "HSV").convert("RGB")), alpha[..., 0]]).astype(np.uint8), "RGBA")
        path = OUT / f"pwing_{name}.webp"
        img.save(path, "WEBP", quality=72, alpha_quality=85, method=6)
        print(name, img.size, path.stat().st_size)


if __name__ == "__main__":
    main()
