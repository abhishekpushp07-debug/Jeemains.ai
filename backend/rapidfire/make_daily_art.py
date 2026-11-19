"""One-time: the All India Rapid trophy artwork (original design) for the lobby card. Run from /app/backend.
Generated on pure black, then the black is turned into transparency (bright glow stays, like the other arena art)."""
import asyncio
import io
import os
import sys

from dotenv import load_dotenv
from PIL import Image

load_dotenv("/app/backend/.env")
import base64  # noqa: E402

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

OUT = "/app/frontend/assets/arena/"
PROMPTS = {
    "daily_trophy": "A majestic original golden championship trophy, tall world-cup style: two flowing golden flame ribbons spiral up "
                    "from a jewelled base with ruby and emerald gems and hold a glowing golden globe of the Earth with India lit "
                    "brightly in warm light. Polished 24k gold, sparkling highlights, soft golden glow around it, game art style, "
                    "front view, the whole trophy visible and centred, on a pure solid black background, no text, no logo, no people.",
}


def key_black(raw: bytes, size: int) -> Image.Image:
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    px = im.load()
    out = Image.new("RGBA", im.size)
    po = out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b = px[x, y]
            a = max(r, g, b)
            a = 0 if a < 14 else min(255, int((a - 14) * 1.6))
            if a:  # un-premultiply so the glow keeps its colour over any background
                k = 255 / max(a, 1)
                po[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), a)
    box = out.getbbox()
    if box:
        out = out.crop(box)
    w, h = out.size
    side = max(w, h)
    sq = Image.new("RGBA", (side, side))
    sq.paste(out, ((side - w) // 2, (side - h) // 2))
    return sq.resize((size, size), Image.LANCZOS)


async def main(names):
    for name in names:
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"daily-art-{name}", system_message="You create game artwork.")
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPTS[name]))
        raw = base64.b64decode(images[0]["data"])
        open(f"/tmp/{name}_raw.png", "wb").write(raw)
        key_black(raw, 640).save(OUT + name + ".webp", "WEBP", quality=88, method=6)
        print("saved", name)


asyncio.run(main(sys.argv[1:] or list(PROMPTS)))
