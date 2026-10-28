"""Add verified phone-compatible MP4s without changing masters or learner data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent
APP = ROOT.parents[1]
load_dotenv(APP / "backend/.env")


def verify(path, mode):
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
    video = next(row for row in info["streams"] if row["codec_type"] == "video")
    audio = next(row for row in info["streams"] if row["codec_type"] == "audio")
    expected = (720, 1280) if mode == "vertical" else (1280, 720)
    if (video["width"], video["height"]) != expected or float(info["format"]["duration"]) != 45:
        raise ValueError("Incorrect mobile film dimensions/duration")
    if (video["codec_name"], video["profile"], video["level"], video["pix_fmt"]) != ("h264", "Constrained Baseline", 31, "yuv420p"):
        raise ValueError("Incorrect mobile video profile")
    if (audio["codec_name"], audio["profile"], audio["sample_rate"]) != ("aac", "LC", "44100"):
        raise ValueError("Incorrect mobile audio profile")
    decoded = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, timeout=90)
    if decoded.returncode or decoded.stderr:
        raise ValueError("Mobile film decode failed")


def publish():
    manifest_file = APP / "backend/marketing_manifest.json"
    manifest = json.loads(manifest_file.read_text())
    storage = os.environ["BRANDING_STORAGE_URL"].rstrip("/")
    with httpx.Client(timeout=180, http2=True) as client:
        auth = None
        for mode in ("vertical", "landscape"):
            target = ROOT / "output" / f"JEELIVE-Mobile-{mode.title()}-45s.mp4"
            verify(target, mode)
            data = target.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            name = f"{mode}-mobile.mp4"
            if manifest["assets"].get(name, {}).get("sha256") == digest:
                continue
            if auth is None:
                init = client.post(storage + "/init", json={"emergent_key": os.environ["EMERGENT_LLM_KEY"]})
                if init.status_code != 200:
                    raise RuntimeError(f"Storage initialization failed HTTP{init.status_code}")
                auth = {"X-Storage-Key": init.json()["storage_key"]}
            path = f"jeelive-ai/uploads/marketing/{uuid.uuid4()}.mp4"
            put = client.put(storage + "/objects/" + path, content=data, headers={**auth, "Content-Type": "video/mp4"})
            if put.status_code not in (200, 201):
                raise RuntimeError(f"Mobile upload failed HTTP{put.status_code}; no retry")
            saved = put.json()["path"]
            get = client.get(storage + "/objects/" + saved, headers=auth)
            if get.status_code != 200 or hashlib.sha256(get.content).hexdigest() != digest:
                raise RuntimeError("Mobile file read-back failed")
            record = {"path": saved, "sha256": digest, "bytes": len(data), "content_type": "video/mp4", "filename": target.name}
            manifest["assets"][name] = record
            manifest_file.write_text(json.dumps(manifest, indent=2) + "\n")
            published_file = ROOT / "published.json"
            published = json.loads(published_file.read_text())
            published["assets"][name] = record
            published_file.write_text(json.dumps(published, indent=2) + "\n")
            print(json.dumps({"verified": name, "bytes": len(data), "sha256": digest}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", required=True)
    parser.parse_args()
    publish()