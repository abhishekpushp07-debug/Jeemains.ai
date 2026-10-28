"""Package exactly the two finished MP4s; public download, no app/learner changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import uuid
import zipfile

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent
APP = ROOT.parents[1]
load_dotenv(APP / "backend/.env")


def make_pack(output, expected=None):
    target = output / "JEELIVE-Launch-Videos-45s.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
        for mode in ("vertical", "landscape"):
            name = f"JEELIVE-launch-45s-{mode}.mp4"
            data = (output / name).read_bytes()
            if expected:
                record = expected[f"{mode}.mp4"]
                if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
                    raise ValueError("MP4 differs from verified published master")
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != 2:
            raise ValueError("Archive verification failed")
    return target


def publish_pack():
    manifest_file = APP / "backend/marketing_manifest.json"
    manifest = json.loads(manifest_file.read_text())
    target = make_pack(ROOT / "output", manifest["assets"])
    data = target.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    previous = manifest["assets"].get("launch-pack.zip")
    if previous and previous["sha256"] == digest:
        print(json.dumps({"already_published": True, "bytes": len(data), "sha256": digest}))
        return
    storage = os.environ["BRANDING_STORAGE_URL"].rstrip("/")
    with httpx.Client(timeout=180, http2=True) as client:
        init = client.post(storage + "/init", json={"emergent_key": os.environ["EMERGENT_LLM_KEY"]})
        if init.status_code != 200:
            raise RuntimeError(f"Storage init failed HTTP{init.status_code}")
        auth = {"X-Storage-Key": init.json()["storage_key"]}
        path = f"jeelive-ai/uploads/marketing/{uuid.uuid4()}.zip"
        uploaded = client.put(storage + "/objects/" + path, content=data, headers={**auth, "Content-Type": "application/zip"})
        if uploaded.status_code not in (200, 201):
            raise RuntimeError(f"Archive upload failed HTTP{uploaded.status_code}; no retry")
        path = uploaded.json()["path"]
        verified = client.get(storage + "/objects/" + path, headers=auth)
        if verified.status_code != 200 or hashlib.sha256(verified.content).hexdigest() != digest:
            raise RuntimeError("Archive read-back verification failed")
    record = {"path": path, "sha256": digest, "bytes": len(data), "content_type": "application/zip", "filename": target.name}
    manifest["assets"]["launch-pack.zip"] = record
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n")
    published_file = ROOT / "published.json"
    published = json.loads(published_file.read_text())
    published["assets"]["launch-pack.zip"] = record
    published_file.write_text(json.dumps(published, indent=2) + "\n")
    print(json.dumps({"verified_zip": target.name, "bytes": len(data), "sha256": digest, "members": 2}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", required=True)
    parser.parse_args()
    publish_pack()