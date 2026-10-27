"""Publish original compressed public RF artwork through existing managed storage."""
import asyncio
import hashlib
import io
import json
import os
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
ART = {
    'spark': '7af1b3fc214f8ac1a8c762515ec003dcdfb9031d43d701acc41fcc5b0dc36ab8',
    'friends': '7cd80d4c8fae9dde99a55cb90b426f264b78b6ad2b865d89e33c79584fab247f',
    'trophy': '678b2224377db9a48796e0bb1f63d0cd103e362550caf5d7f2329d7f6914753d',
    'coins': '7223159f11a0a2c8aa102296e56cadae1d7cfaa94419dc2c11bb1a58d45e16e3',
}
SOURCE = 'https://static.prod-images.emergentagent.com/jobs/90d1afef-705b-4292-ab1d-cf3f3412335b/images/'


async def main():
    storage = os.environ['BRANDING_STORAGE_URL'].rstrip('/')
    out = ROOT / 'rapidfire' / 'art_manifest.json'
    if out.exists():
        print('Already published; no duplicate upload.')
        return
    manifest = {}
    async with httpx.AsyncClient(timeout=90) as client:
        res = await client.post(storage + '/init', json={'emergent_key': os.environ['EMERGENT_LLM_KEY']})
        res.raise_for_status()
        headers = {'X-Storage-Key': res.json()['storage_key'], 'Content-Type': 'image/webp'}
        for name, source in ART.items():
            res = await client.get(SOURCE + source + '.jpeg')
            res.raise_for_status()
            image = Image.open(io.BytesIO(res.content)).convert('RGB')
            image.thumbnail((640, 640) if name == 'spark' else (256, 256))
            buff = io.BytesIO()
            image.save(buff, 'WEBP', quality=82, method=6)
            data = buff.getvalue()
            path = f'jeelive-ai/uploads/brand/{uuid.uuid4()}.webp'
            res = await client.put(storage + '/objects/' + path, headers=headers, content=data)
            res.raise_for_status()
            path = res.json()['path']
            manifest[name] = {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
            print(name, len(data), flush=True)
    out.write_text(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    asyncio.run(main())