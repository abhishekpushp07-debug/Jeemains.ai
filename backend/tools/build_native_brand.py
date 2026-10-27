"""Owner-only build tool: original public emblem -> bundled + managed PNG assets.

No learner uploads, no private images, no public write endpoint. Requires an
explicit --publish for new UUID objects; never overwrites original brand objects.
"""
import argparse
import copy
import hashlib
import io
import json
import os
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import httpx
from dotenv import load_dotenv
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = "4cec3778c23c429e1be0186c71db65da8ceece01ba736a14ed560623560faff2"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
load_dotenv(ROOT / "backend/.env")


def emblem_svg(source, background=False, monochrome=False):
    original = ET.fromstring(source)
    emblem = copy.deepcopy(original.find(f"{{{NS}}}g"))
    if emblem is None:
        raise ValueError("Original emblem group not found")
    if monochrome:
        for node in emblem.iter():
            if "fill" in node.attrib:
                node.set("fill", "#FFFFFF")
    svg = ET.Element(f"{{{NS}}}svg", {"viewBox": "0 0 1024 1024"})
    if background:
        ET.SubElement(svg, f"{{{NS}}}rect", {"width": "1024", "height": "1024", "fill": "#08080A"})
    # 62.5% height fits Android's adaptive safe zone, including circular masks.
    scale = 640 / 565
    holder = ET.SubElement(svg, f"{{{NS}}}g", {"transform": f"translate({(1024 - 430 * scale) / 2} 192) scale({scale})"})
    holder.append(emblem)
    return ET.tostring(svg)


def render(source):
    output = {}
    for name, background, monochrome in (("icon", True, False), ("adaptive", False, False), ("monochrome", False, True)):
        output[name] = cairosvg.svg2png(bytestring=emblem_svg(source, background, monochrome), output_width=1024, output_height=1024)
    output["splash"] = cairosvg.svg2png(bytestring=source, output_width=1132, output_height=452)
    favicon = Image.open(io.BytesIO(output["icon"])).resize((64, 64), Image.Resampling.LANCZOS)
    stream = io.BytesIO()
    favicon.save(stream, format="PNG", optimize=True)
    output["favicon"] = stream.getvalue()
    return output


def publish(images):
    base = os.environ["BRANDING_STORAGE_URL"].rstrip("/")
    previous_path = ROOT / "backend/native_brand_manifest.json"
    previous = json.loads(previous_path.read_text()).get("assets", {}) if previous_path.exists() else {}
    result = {}
    with httpx.Client(timeout=60, http2=True) as client:
        response = client.post(base + "/init", json={"emergent_key": os.environ["EMERGENT_LLM_KEY"]})
        if response.status_code != 200:
            raise RuntimeError(f"Storage initialization failed (HTTP {response.status_code})")
        auth = {"X-Storage-Key": response.json()["storage_key"]}
        for name, data in images.items():
            digest = hashlib.sha256(data).hexdigest()
            if previous.get(name, {}).get("sha256") == digest:
                result[name] = previous[name]
                continue
            path = f"jeelive-ai/uploads/brand/{uuid.uuid4()}.png"
            saved = client.put(base + "/objects/" + path, content=data, headers={**auth, "Content-Type": "image/png"})
            if saved.status_code not in (200, 201):
                raise RuntimeError(f"Public asset write failed (HTTP {saved.status_code}); no retry loop")
            actual_path = saved.json()["path"]
            verified = client.get(base + "/objects/" + actual_path, headers=auth)
            if verified.status_code != 200 or hashlib.sha256(verified.content).hexdigest() != digest:
                raise RuntimeError("Public asset read-back integrity check failed")
            result[name] = {"path": actual_path, "sha256": digest, "bytes": len(data)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--publish", action="store_true", required=True)
    args = parser.parse_args()
    source = Path(args.source).read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA:
        raise ValueError("Only the approved original public JEELIVE logo is accepted")
    images = render(source)
    manifest = publish(images)
    destination = ROOT / "frontend/assets/images"
    for name, data in images.items():
        (destination / f"jeelive-{name}.png").write_bytes(data)
    (ROOT / "backend/native_brand_manifest.json").write_text(json.dumps({"source_sha256": SOURCE_SHA, "assets": manifest}, indent=2) + "\n")
    print(json.dumps({"public_brand_assets_verified": len(images), "total_bytes": sum(map(len, images.values())), "original_home_artworks_changed": False}))


if __name__ == "__main__":
    main()