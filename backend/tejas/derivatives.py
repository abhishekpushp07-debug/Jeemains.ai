"""Authorized immutable crop cache. Callers MUST authorize before invoking this helper.
Byte bound + striped locks coalesce duplicate cold requests without unbounded lock tables.
This is a pilot CPU optimization, not a CDN or physical vault isolation.
"""
import json, time
from hashlib import sha256
from pathlib import Path
from threading import Lock
from .cache import ByteCache
from .canonical import CanonicalIntegrityError

_cache = ByteCache(48 * 1024 * 1024)
_locks = [Lock() for _ in range(32)]
RENDER = 5
# The 30 verified JEE Main PYQ originals are also kept in the repository; used only when storage cannot give them back.
PYQ_COPIES = Path(__file__).resolve().parents[2] / 'data' / 'jee_pyq' / 'source_audit'
_away = {}  # path -> when storage last failed for it; for 30 minutes the kept copy is read at once


def source_bytes(source):
    """A source PDF's bytes: from storage, or for a PYQ original from its kept copy when its fingerprint matches the record."""
    from tejas_storage import get_object, StorageError, _source_cache
    path, sha = source['path'], source.get('sha256')
    copy = PYQ_COPIES / f"{source.get('source_drive_id')}.pdf" if source.get('source_collection') == 'jee-pyq-written' and sha and source.get('source_drive_id') else None
    if copy is None or time.time() - _away.get(path, 0) > 1800:
        try:
            return get_object(path)
        except StorageError:
            if copy is None or not copy.is_file():
                raise
            _away[path] = time.time()
    cached = _source_cache.get(path)
    if cached is not None:
        return cached
    raw = copy.read_bytes() if copy.is_file() else b''
    if sha256(raw).hexdigest() != sha:
        raise StorageError('The kept copy of this source is missing or differs from its record.')
    return _source_cache.put(path, raw)


def render_crop(source, ref, scale=2):
    from tejas_core import _render_crop_png
    from tejas_storage import get_object
    if source.get('kind') == 'rendered_png':
        raw = get_object(source['path'])
        if sha256(raw).hexdigest() != source['sha256']:
            raise CanonicalIntegrityError('Frozen image integrity check failed')
        return raw
    reviewed = source.get('source_collection') == 'jee-pyq-written' and bool(source.get('sha256'))
    identity = json.dumps({'source': source.get('sha256') or source['path'], 'ref': ref, 'scale': scale, 'reviewed_large_pages': reviewed, 'render': RENDER}, sort_keys=True, separators=(',', ':'))
    key = sha256(identity.encode()).hexdigest()
    found = _cache.get(key)
    if found is not None:
        return found
    with _locks[int(key[:8], 16) % len(_locks)]:
        found = _cache.get(key)
        if found is not None:
            return found
        raw = source_bytes(source)
        if source.get('sha256') and sha256(raw).hexdigest() != source['sha256']:
            raise CanonicalIntegrityError('Frozen source PDF integrity check failed')
        return _cache.put(key, _render_crop_png(raw, ref, scale, reviewed_large_pages=reviewed))


_validation_cache = ByteCache(8 * 1024)
_validation_locks = [Lock() for _ in range(32)]


def validate_source_crops(source, refs):
    from tejas_core import validate_pdf, validate_crop_pages
    from .canonical import CanonicalIntegrityError
    reviewed = source.get('source_collection') == 'jee-pyq-written' and bool(source.get('sha256'))
    unique = {json.dumps(ref, sort_keys=True, separators=(',', ':')): ref for ref in refs}
    identity = json.dumps({'source': source.get('sha256') or source['path'], 'refs': sorted(unique), 'reviewed': reviewed, 'validation': 2}, sort_keys=True)
    key = sha256(identity.encode()).hexdigest()
    cacheable = bool(source.get('sha256'))
    with _validation_locks[int(key[:8], 16) % len(_validation_locks)]:
        if cacheable and _validation_cache.get(key) is not None:
            return
        raw = source_bytes(source)
        if source.get('sha256') and sha256(raw).hexdigest() != source['sha256']:
            raise CanonicalIntegrityError('Source PDF failed its recorded integrity check.')
        with validate_pdf(raw, reviewed_large_pages=reviewed) as doc:
            validate_crop_pages(doc, unique.values())
        if cacheable:
            _validation_cache.put(key, bytes.fromhex(key))

