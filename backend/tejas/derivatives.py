"""Authorized immutable crop cache. Callers MUST authorize before invoking this helper.
Byte bound + striped locks coalesce duplicate cold requests without unbounded lock tables.
This is a pilot CPU optimization, not a CDN or physical vault isolation.
"""
import json
from hashlib import sha256
from threading import Lock
from .cache import ByteCache
from .canonical import CanonicalIntegrityError

_cache = ByteCache(48 * 1024 * 1024)
_locks = [Lock() for _ in range(32)]


def render_crop(source, ref, scale=2):
    from tejas_core import crop_png
    from tejas_storage import get_object
    if source.get('kind') == 'rendered_png':
        raw = get_object(source['path'])
        if sha256(raw).hexdigest() != source['sha256']:
            raise CanonicalIntegrityError('Frozen image integrity check failed')
        return raw
    reviewed = source.get('source_collection') == 'jee-pyq-written' and bool(source.get('sha256'))
    identity = json.dumps({'source': source.get('sha256') or source['path'], 'ref': ref, 'scale': scale, 'reviewed_large_pages': reviewed, 'render': 2}, sort_keys=True, separators=(',', ':'))
    key = sha256(identity.encode()).hexdigest()
    found = _cache.get(key)
    if found is not None:
        return found
    with _locks[int(key[:8], 16) % len(_locks)]:
        found = _cache.get(key)
        if found is not None:
            return found
        raw = get_object(source['path'])
        if source.get('sha256') and sha256(raw).hexdigest() != source['sha256']:
            raise CanonicalIntegrityError('Frozen source PDF integrity check failed')
        return _cache.put(key, crop_png(raw, ref, scale, reviewed_large_pages=reviewed))


_validation_cache = ByteCache(8 * 1024)


def validate_source_crops(source, refs):
    from tejas_storage import get_object
    from tejas_core import validate_pdf, _render_crop_png
    from .canonical import CanonicalIntegrityError
    reviewed = source.get('source_collection') == 'jee-pyq-written' and bool(source.get('sha256'))
    unique = {json.dumps(ref, sort_keys=True, separators=(',', ':')): ref for ref in refs}
    identity = json.dumps({'source': source.get('sha256') or source['path'], 'refs': sorted(unique), 'reviewed': reviewed, 'validation': 1}, sort_keys=True)
    key = sha256(identity.encode()).hexdigest()
    cacheable = bool(source.get('sha256'))
    with _locks[int(key[:8], 16) % len(_locks)]:
        if cacheable and _validation_cache.get(key) is not None:
            return
        raw = get_object(source['path'])
        if source.get('sha256') and sha256(raw).hexdigest() != source['sha256']:
            raise CanonicalIntegrityError('Source PDF failed its recorded integrity check.')
        with validate_pdf(raw, reviewed_large_pages=reviewed) as doc:
            for ref in unique.values():
                _render_crop_png(raw, ref, .3, reviewed_large_pages=reviewed, _document=doc)
        if cacheable:
            _validation_cache.put(key, bytes.fromhex(key))

