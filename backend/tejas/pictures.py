"""Lighter, faster pictures for the app: "has it changed?" answers (ETag, 304, 206), asset_revision and a lossless WebP copy.
Switched on per student: PICTURE_PILOT_PHONES holds the mobile numbers ('*' = every student). Everyone else gets the old answers, byte for byte."""
import hashlib, io, json, os, re
from collections import OrderedDict
from threading import Lock
from fastapi import Response
from starlette.concurrency import run_in_threadpool
from .cache import ByteCache
from .db import files
from .derivatives import RENDER, render_crop

_setting = os.environ.get('PICTURE_PILOT_PHONES', '7004186276').strip()
EVERYONE = _setting == '*'
PHONES = {d[-10:] for d in (re.sub(r'\D', '', part) for part in _setting.split(',')) if len(d) >= 10}
PRIVATE = {'Cache-Control': 'private, no-store', 'Accept-Ranges': 'bytes'}
PNG_ONLY = b'-'
_light = ByteCache(48 * 1024 * 1024)
_light_locks = [Lock() for _ in range(16)]
_light_tags = OrderedDict()
_revisions = OrderedDict()


def pilot(u):
    if EVERYONE:
        return True
    digits = re.sub(r'\D', '', str((u or {}).get('phone') or ''))
    return len(digits) >= 10 and digits[-10:] in PHONES


def etag_of(body):
    """Strong ETag: a hash of exactly the bytes served."""
    return '"' + hashlib.sha256(body).hexdigest()[:32] + '"'


def _encode(png):
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(png))
        im.load()
        out = io.BytesIO()
        im.save(out, 'WEBP', lossless=True, quality=80, method=4, exact=True)
        raw = out.getvalue()
        back = Image.open(io.BytesIO(raw))
        same = back.size == im.size and back.convert('RGBA').tobytes() == im.convert('RGBA').tobytes()
        return raw if same and len(raw) < len(png) else PNG_ONLY
    except Exception:  # noqa: BLE001  any trouble keeps the PNG
        return PNG_ONLY


def webp_of(png):
    """The lossless WebP copy (same pixel size, every pixel compared), or None when the PNG stays."""
    key = hashlib.sha256(png).hexdigest()
    hit = _light.get(key)
    if hit is None:
        with _light_locks[int(key[:4], 16) % len(_light_locks)]:
            hit = _light.get(key)
            if hit is None:
                hit = _light.put(key, _encode(png))
                _light_tags[key] = etag_of(png if hit == PNG_ONLY else hit)
                while len(_light_tags) > 50000:
                    _light_tags.popitem(last=False)
    return None if hit == PNG_ONLY else hit


def picture(source, ref, webp=False):
    png = render_crop(source, ref)
    light = webp_of(png) if webp else None
    return (light, 'image/webp') if light else (png, 'image/png')


def saved_etag(source, webp):
    """A saved picture's ETag without reading it from storage: its recorded hash is the hash of the bytes served."""
    if source.get('kind') != 'rendered_png' or not source.get('sha256'):
        return None
    return _light_tags.get(source['sha256']) if webp else '"' + source['sha256'][:32] + '"'


def _same(header, tag):
    if not header:
        return False
    values = [v.strip() for v in header.split(',')]
    return '*' in values or any((v[2:] if v.startswith('W/') else v) == tag for v in values)


def _span(header, size):
    """(first, last) of one byte range; None = answer the whole picture; False = outside the picture."""
    m = re.fullmatch(r'bytes=(\d{0,12})-(\d{0,12})', header.strip())
    if not m or not (m[1] or m[2]):
        return None
    if not m[1]:
        return (max(0, size - int(m[2])), size - 1) if int(m[2]) else False
    first, last = int(m[1]), min(int(m[2]), size - 1) if m[2] else size - 1
    return (first, last) if first <= last and first < size else False


def conditional(request, body, media_type):
    tag = etag_of(body)
    headers = {**PRIVATE, 'ETag': tag}
    if _same(request.headers.get('if-none-match'), tag):
        return Response(status_code=304, headers=headers)
    wanted, guard = request.headers.get('range'), request.headers.get('if-range')
    span = _span(wanted, len(body)) if wanted and guard in (None, tag) else None
    if span is False:
        return Response(status_code=416, headers={**headers, 'Content-Range': f'bytes */{len(body)}'})
    if span:
        return Response(body[span[0]:span[1] + 1], status_code=206, media_type=media_type,
                        headers={**headers, 'Content-Range': f'bytes {span[0]}-{span[1]}/{len(body)}'})
    return Response(body, media_type=media_type, headers=headers)


async def answer(request, source, ref, webp):
    tag = saved_etag(source, webp)
    if tag and _same(request.headers.get('if-none-match'), tag):
        return Response(status_code=304, headers={**PRIVATE, 'ETag': tag})
    body, media_type = await run_in_threadpool(picture, source, ref, webp)
    return conditional(request, body, media_type)


async def revisions(questions, pack_id=None):
    """asset_revision per question: changes only when one of its pictures (question, piece or solution) is replaced."""
    hit = _revisions.get(pack_id) if pack_id else None
    if hit is not None:
        _revisions.move_to_end(pack_id)
        return hit
    kinds = ('q_refs', 'c_refs', 's_refs')
    ids = list({r['file_id'] for q in questions for k in kinds for r in q.get(k, []) if r.get('file_id')})
    saved = {}
    if ids:
        async for f in files.find({'id': {'$in': ids}}, {'_id': 0, 'id': 1, 'sha256': 1, 'path': 1}):
            saved[f['id']] = f.get('sha256') or f.get('path', '')
    out = {}
    for q in questions:
        identity = [RENDER, [[k, [[saved.get(r.get('file_id'), ''), r] for r in q.get(k, [])]] for k in kinds]]
        out[q['id']] = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()[:16]
    if pack_id:
        _revisions[pack_id] = out
        while len(_revisions) > 64:
            _revisions.popitem(last=False)
    return out


async def stamp(rows, a, corrected=False):
    found = await revisions(a['questions'], None if corrected else a.get('pack_id'))
    for row in rows:
        row['asset_revision'] = found.get(row['id'])
