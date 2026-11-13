"""One-off build tool: cleans the bundled arena artwork (stray white plates, dark halo around the glow). Nothing here runs inside the app."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parents[2] / "frontend" / "assets" / "arena"


def load(name):
    return np.asarray(Image.open(OUT / name).convert("RGBA")).astype(np.float32)


def save(a, name):
    Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA").save(OUT / name, "WEBP", quality=80, alpha_quality=88, method=6)


def touching_border(mask):
    lab, _ = ndimage.label(mask)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    return np.isin(lab, edge[edge > 0])


def strip_plate(name, dark_plate=False):
    """Remove a white card (and optionally the dark app-icon plate inside it) left behind by the cut-out."""
    a = load(name)
    rgb, al = a[..., :3], a[..., 3]
    peak, low = rgb.max(2), rgb.min(2)
    outside = touching_border(((low > 200) & (al > 120)) | (al < 25))
    if dark_plate:
        plate = touching_border(ndimage.binary_dilation(outside, iterations=3) | (peak < 70)) & ~outside
        a[..., 3] = np.where(plate, np.clip((peak - 24) / 110, 0, 1) * 255, al)
    a[..., 3] = np.where(outside, 0, a[..., 3])
    a[..., 3] = ndimage.gaussian_filter(a[..., 3], 0.7)
    save(a, name)


def soften(name, band, floor, span):
    """Dark pixels near the outer edge fade out, so only light (the glow) is left around the subject."""
    a = load(name)
    al = a[..., 3] / 255
    peak = a[..., :3].max(2)
    edge = np.clip(1 - ndimage.distance_transform_edt(al > 0.5) / band, 0, 1)
    key = np.clip((peak - floor) / span, 0, 1)
    a[..., 3] = al * (1 - edge * (1 - key)) * 255
    save(a, name)


if __name__ == "__main__":
    strip_plate("gem_gold.webp")
    strip_plate("ic_rival.webp", dark_plate=True)
    for f in sorted(OUT.glob("*.webp")):
        if not f.name.startswith(("phoenix_", "pgem_")):  # the Phoenix layers are finished by make_phoenix_layers.py
            soften(f.name, 8, 26, 90)
    print("total bytes", sum(f.stat().st_size for f in OUT.glob("*.webp")))
