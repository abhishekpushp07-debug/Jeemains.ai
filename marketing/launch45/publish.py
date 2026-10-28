"""Explicit owner operator: new UUID objects, verified read-back, public allowlist."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

import httpx
from dotenv import load_dotenv
from PIL import Image
from download_pack import make_pack

ROOT = Path(__file__).parent
APP = ROOT.parents[1]
load_dotenv(APP / "backend/.env")


def verify_media(path):
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
    duration = float(info.get("format", {}).get("duration", 0))
    video = next(row for row in info["streams"] if row["codec_type"] == "video")
    audio = next(row for row in info["streams"] if row["codec_type"] == "audio")
    expected = (1080, 1920) if "vertical" in path.name else (1920, 1080)
    codecs = ("h264", "aac") if path.suffix == ".mp4" else ("vp9", "opus")
    if abs(duration - 45) > .1 or (video["width"], video["height"]) != expected:
        raise ValueError("Incomplete or incorrect video; refusing publication")
    if (video["codec_name"], audio["codec_name"]) != codecs or video["r_frame_rate"] != "30/1":
        raise ValueError("Unsupported campaign encoding")


def publish():
    storage = os.environ["BRANDING_STORAGE_URL"].rstrip("/")
    output = ROOT / "output"
    items = {}
    for mode in ["vertical", "landscape"]:
        video = output / f"JEELIVE-launch-45s-{mode}.mp4"
        verify_media(video)
        verify_media(video.with_suffix(".webm"))
        poster = output / f"JEELIVE-launch-poster-{mode}.jpg"
        Image.open(output / f"{mode}-04.8.jpg").save(poster, quality=93)
        items[f"{mode}.mp4"] = (video, "video/mp4")
        items[f"{mode}.webm"] = (video.with_suffix(".webm"), "video/webm")
        items[f"poster-{mode}.jpg"] = (poster, "image/jpeg")
    items["launch-pack.zip"] = (make_pack(output), "application/zip")
    for name in ["rapid-stage", "series-stage"]:
        items[f"source-{name}.jpg"] = (ROOT / "assets" / f"{name}.jpg", "image/jpeg")
    previous_file = ROOT / "published.json"
    previous = json.loads(previous_file.read_text()).get("assets", {}) if previous_file.exists() else {}
    result = {}
    with httpx.Client(timeout=180, http2=True) as client:
        init = client.post(storage + "/init", json={"emergent_key": os.environ["EMERGENT_LLM_KEY"]})
        if init.status_code != 200:
            raise RuntimeError(f"Storage init failed HTTP{init.status_code}; no retries")
        auth = {"X-Storage-Key": init.json()["storage_key"]}
        for name, (local, content_type) in items.items():
            data = local.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if previous.get(name, {}).get("sha256") == digest:
                result[name] = previous[name]
                continue
            path = f"jeelive-ai/uploads/marketing/{uuid.uuid4()}{local.suffix}"
            put = client.put(storage + "/objects/" + path, content=data, headers={**auth, "Content-Type": content_type})
            if put.status_code not in (200, 201):
                raise RuntimeError(f"Upload failed HTTP{put.status_code}; no retries")
            saved = put.json()["path"]
            get = client.get(storage + "/objects/" + saved, headers=auth)
            if get.status_code != 200 or hashlib.sha256(get.content).hexdigest() != digest:
                raise RuntimeError("Object read-back verification failed")
            result[name] = {"path": saved, "sha256": digest, "bytes": len(data), "content_type": content_type, "filename": local.name}
            previous[name] = result[name]
            previous_file.write_text(json.dumps({"assets": previous}, indent=2) + "\n")
            print(json.dumps({"verified": name, "bytes": len(data)}), flush=True)
    public = {key: value for key, value in result.items() if not key.startswith("source-")}
    for name in ("vertical-mobile.mp4", "landscape-mobile.mp4", "launch-mobile-pack.zip"):
        if name in previous:
            public[name] = previous[name]
    (APP / "backend/marketing_manifest.json").write_text(json.dumps({"campaign": "launch45-v1", "assets": public}, indent=2) + "\n")
    print("Published allowlist: 2 MP4 masters + 2 WebM previews + 2 posters + download ZIP; no secrets or learner data")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", required=True)
    parser.parse_args()
    publish()