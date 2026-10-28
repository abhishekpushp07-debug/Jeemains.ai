"""Render original45s marketing MP4s. Runtime app remains unchanged."""
import argparse
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from graphics import Film
from shots import frame

ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"


def stills():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    times = [1.7, 4.8, 9.6, 12.3, 15.1, 19.7, 24.3, 28.2, 31.5, 36.4, 42.5]
    for mode in ["vertical", "landscape"]:
        f = Film(mode == "vertical")
        thumbs = []
        for t in times:
            im = frame(f, t)
            im.save(OUTPUT / f"{mode}-{t:04.1f}.jpg", quality=90)
            thumb = im.copy()
            thumb.thumbnail((240, 420) if f.portrait else (400, 235))
            thumbs.append((t, thumb))
        tw, th = (250, 465) if f.portrait else (410, 265)
        sheet = Image.new("RGB", (tw * 4, th * 3), (17, 18, 24))
        d = ImageDraw.Draw(sheet)
        for i, (t, thumb) in enumerate(thumbs):
            x, y = (i % 4) * tw, (i // 4) * th
            sheet.paste(thumb, (x, y))
            d.text((x + 8, y + th - 28), f"{t:.1f}s", fill="white")
        sheet.save(OUTPUT / f"storyboard-{mode}.jpg", quality=92)
    print("Both-format storyboard stills generated")


def render(mode):
    f = Film(mode == "vertical")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"JEELIVE-launch-45s-{mode}.mp4"
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{f.w}x{f.h}", "-r", "30", "-i", "pipe:0", "-i", str(OUTPUT / "music-original.wav"), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-threads", "4", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-t", "45", "-movflags", "+faststart", "-metadata", "title=JEELIVE — Ab tumhari baari", str(target)]
    with subprocess.Popen(args, stdin=subprocess.PIPE) as encoder:
        try:
            for index in range(1350):
                encoder.stdin.write(frame(f, index / 30).tobytes())
                if index % 150 == 0:
                    print(json.dumps({"format": mode, "seconds_rendered": index / 30}), flush=True)
        finally:
            encoder.stdin.close()
        code = encoder.wait()
    if code:
        raise RuntimeError(f"Encoder failed with code {code}")
    print(json.dumps({"complete": mode, "bytes": target.stat().st_size}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["stills", "vertical", "landscape"])
    option = parser.parse_args().mode
    stills() if option == "stills" else render(option)