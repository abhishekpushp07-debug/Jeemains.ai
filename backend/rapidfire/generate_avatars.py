"""Offline: generate game-style 3D avatar portraits (Nano Banana) into frontend/assets/avatars/*.webp.
Run: python rapidfire/generate_avatars.py   (skips avatars already generated)
"""
import asyncio, base64, io, os, sys, uuid
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / ".env")
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
sys.path.insert(0, str(ROOT.parent))
from shop import AVATAR_ITEMS  # noqa: E402

OUT = ROOT.parent.parent / "frontend" / "assets" / "avatars"
OUT.mkdir(parents=True, exist_ok=True)
STYLE = ("Premium 3D stylized mobile battle-game hero portrait (Free Fire / Clash Royale / Fortnite quality render). "
         "Head and shoulders bust, centered, facing camera slightly turned, confident expressive face, vibrant cinematic lighting with coloured rim light, "
         "glossy high-detail materials, soft glow. Plain solid deep navy background (#0B1020). Square 1:1 composition, character fills the frame. "
         "No text, no letters, no logo, no border, no watermark. Character: ")


async def one(sem, a):
    path = OUT / f"{a['id']}.webp"
    if path.exists():
        return
    for attempt in range(3):
        async with sem:
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=str(uuid.uuid4()), system_message="You create game art.")
                chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
                _, images = await chat.send_message_multimodal_response(UserMessage(text=STYLE + a["prompt"]))
            except Exception as e:  # noqa: BLE001
                print("ERR", a["id"], str(e)[:120], flush=True)
                continue
        if images:
            img = Image.open(io.BytesIO(base64.b64decode(images[0]["data"]))).convert("RGB")
            w, h = img.size
            s = min(w, h)
            img = img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((320, 320), Image.LANCZOS)
            img.save(path, "WEBP", quality=82)
            print("OK", a["id"], flush=True)
            return
    print("FAIL", a["id"], flush=True)


async def main():
    sem = asyncio.Semaphore(4)
    await asyncio.gather(*[one(sem, a) for a in AVATAR_ITEMS])


if __name__ == "__main__":
    asyncio.run(main())
