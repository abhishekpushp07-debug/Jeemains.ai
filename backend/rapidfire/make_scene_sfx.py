"""One-time: the five All India card scene sounds (roar, launch, arrow thud, cheer + war horn, gallop + neigh).
Sources: Mixkit free sound effects (Mixkit Sound Effects Free License: use in apps allowed, no resale of the raw files).
Run from /app/backend:  python rapidfire/make_scene_sfx.py   -> frontend/assets/sfx/scene_*.m4a (mono AAC 96 kbps)"""
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import requests

FF, SR = imageio_ffmpeg.get_ffmpeg_exe(), 44100
TMP, OUT = Path("/tmp/scene_sfx"), Path("/app/frontend/assets/sfx")
SRC = {  # mixkit id: what it is
    5: "big wild lion growl", 677: "big cinematic impact", 1721: "fast rocket whoosh", 1722: "rocket ignition flames",
    2769: "arrow shot through air", 498: "wood hard hit", 476: "huge crowd cheering victory", 1654: "warfare horn",
    7: "horse fast gallop in the dirt", 83: "intense horse stallion neigh",
}


def load(i: int) -> np.ndarray:
    mp3, wav = TMP / f"{i}.mp3", TMP / f"{i}.wav"
    if not mp3.exists():
        mp3.write_bytes(requests.get(f"https://assets.mixkit.co/active_storage/sfx/{i}/{i}-preview.mp3", headers={"User-Agent": "Mozilla/5.0"}, timeout=60).content)
    subprocess.run([FF, "-loglevel", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
    w = wave.open(str(wav))
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def cut(a, start, end, fade_in=0.02, fade_out=0.4):
    x = a[int(start * SR):int(end * SR)].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    x[:fi] *= np.linspace(0, 1, fi)
    x[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    return x


def mix(length, *parts):
    """parts: (clip, at_seconds, gain)"""
    out = np.zeros(int(length * SR), np.float32)
    for clip, at, gain in parts:
        s = int(at * SR)
        n = min(len(clip), len(out) - s)
        out[s:s + n] += clip[:n] * gain
    return out / max(1e-6, np.abs(out).max()) * 0.9


def save(name, a):
    wav = TMP / f"{name}.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    subprocess.run([FF, "-loglevel", "error", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "96k", str(OUT / f"{name}.m4a")], check=True)
    print("saved", name, f"{len(a) / SR:.1f}s")


TMP.mkdir(exist_ok=True)
s = {i: load(i) for i in SRC}
save("scene_space", mix(2.8, (cut(s[1722], 0.0, 0.9, fade_out=0.5), 0.0, 0.8), (cut(s[1721], 0.5, 3.0, fade_in=0.3, fade_out=0.7), 0.2, 1.0)))
save("scene_cup", mix(3.0, (cut(s[1654], 0.15, 2.3, fade_out=0.6), 0.0, 0.75), (cut(s[476], 1.2, 3.9, fade_in=0.25, fade_out=0.9), 0.5, 1.0)))
save("scene_lion", mix(2.7, (cut(s[677], 0.0, 1.6, fade_out=0.8), 0.0, 0.45), (cut(s[5], 0.05, 2.6, fade_out=0.6), 0.05, 1.0)))
save("scene_race", mix(2.8, (cut(s[83], 0.05, 0.95, fade_out=0.3), 0.0, 0.8), (cut(s[7], 38.0, 40.6, fade_in=0.2, fade_out=0.7), 0.2, 1.0)))
save("scene_arrow", mix(1.6, (cut(s[2769], 0.0, 1.0, fade_out=0.3), 0.0, 0.9), (cut(s[498], 0.0, 1.2, fade_out=0.6), 0.32, 1.0)))
