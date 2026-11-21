"""Private object storage on two stores. All authorization is performed by API callers.

Every new file goes to Supabase first. When Supabase cannot take it (not set up, down, slow to answer, any error), Emergent
storage takes it at once, so a file is always saved in one of the two. The reference a write returns names its store:
"sb://<bucket>/<path>" lives in Supabase, a plain path lives in Emergent storage (every file saved before Supabase too).
A read therefore goes straight to the one store that holds the file, never searching both.
"""

import base64, hashlib, os, random, re, threading, time
from urllib.parse import quote, urlparse
import httpx
import requests
from tejas.cache import ByteCache

_source_cache = ByteCache(64 * 1024 * 1024)
_source_locks = [threading.Lock() for _ in range(32)]
SB = 'sb://'
TUS_CHUNK = 6 * 1024 * 1024   # Supabase resumable uploads take exactly 6 MB per piece (the last one may be smaller)
TRANSIENT = (408, 429, 500, 502, 503, 504)


def source_lock(path):
    return _source_locks[int.from_bytes(hashlib.sha256(path.encode()).digest()[:4], 'big') % len(_source_locks)]


class StorageError(Exception):
    pass


# ---------- Emergent storage ----------
BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
URL = BASE.rstrip("/") + "/objstore/api/v1/storage"
_key = None
_lock = threading.Lock()
_local = threading.local()


def _session():
    # One kept-alive connection per worker thread instead of a new connection for every file.
    if getattr(_local, 'session', None) is None:
        _local.session = requests.Session()
    return _local.session


def init_storage(force=False):
    global _key
    with _lock:
        if _key and not force:
            return _key
        r = _session().post(URL + "/init", json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")}, timeout=30)
        if r.status_code != 200:
            raise StorageError(f"Private storage initialization unavailable ({r.status_code}). Check account storage access.")
        _key = r.json()["storage_key"]
        return _key


_quick = threading.local()


def request(method, path, data=None, content_type=None):
    """Emergent storage. A hiccup (5xx) is retried with growing waits instead of failing on the first try."""
    tries = 2 if getattr(_quick, 'on', False) else 4   # the health check gives up quickly
    for attempt in range(tries):
        last = attempt == tries - 1
        try:
            r = _session().request(method, URL + "/objects/" + path, headers={"X-Storage-Key": init_storage(), "Content-Type": content_type or "application/octet-stream"},
                                   data=data, timeout=120)
        except (requests.RequestException, StorageError):
            if last:
                raise StorageError("Private storage connection interrupted. Retry this operation.")
            time.sleep(attempt + 1)
            continue
        if r.ok:
            return r
        if r.status_code in (401, 403, 404) and attempt == 0 and not last:
            init_storage(force=True)
            continue
        if r.status_code in (500, 502, 503, 504) and not last:
            time.sleep(2 ** attempt)
            continue
        raise StorageError(f"Private storage unavailable ({r.status_code}). Retry later or check account storage permissions and quota.")
    raise StorageError("Private storage could not complete this request.")


# ---------- Supabase ----------
STATE = {'down_until': 0.0, 'strikes': 0, 'last_error': '', 'last_ok': 0.0, 'auth': None, 'bucket': None,
         'writes': {'supabase': 0, 'emergent': 0}, 'failovers': 0, 'last_failover': None, 'backup_since': None, 'backup_writes': 0}
_sb_lock = threading.Lock()


def project_url():
    raw = (os.environ.get('SUPABASE_URL') or '').strip().rstrip('/')
    # The dashboard address of a project also names it: https://supabase.com/dashboard/project/<ref>
    m = re.search(r'supabase\.com/dashboard/project/([a-z0-9]{20})', raw)
    return f'https://{m[1]}.supabase.co' if m else raw


def configured():
    key = (os.environ.get('SUPABASE_SECRET_KEY') or '').strip()
    return project_url().startswith('https://') and bool(key) and not key.startswith('http')


def bucket_name():
    """Preview and live never share files: the bucket is named after the app's own address unless SUPABASE_BUCKET says otherwise."""
    if os.environ.get('SUPABASE_BUCKET'):
        return os.environ['SUPABASE_BUCKET'].strip()
    host = urlparse(os.environ.get('FRONTEND_URL') or '').hostname or 'app'
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9-]+', '-', ('jeelive-' + host).lower())).strip('-')[:63].rstrip('-')


def _client():
    if getattr(_local, 'sb', None) is None:
        # A Supabase that accepts the connection and then hangs costs at most 20 s of silence before Emergent takes the file.
        _local.sb = httpx.Client(timeout=httpx.Timeout(connect=5.0, read=20.0, write=60.0, pool=10.0), limits=httpx.Limits(max_connections=16, max_keepalive_connections=8, keepalive_expiry=90.0))
    return _local.sb


def _headers(extra=None):
    key = os.environ['SUPABASE_SECRET_KEY'].strip()
    h = {'apikey': key}
    # Old JWT keys also go in Authorization; a new secret key goes there only if Supabase asks for it (found once, then kept).
    if key.startswith('eyJ') or STATE['auth'] == 'bearer':
        h['Authorization'] = 'Bearer ' + key
    return {**h, **(extra or {})}


def _call(method, url, headers=None, tries=3, **kw):
    """One Supabase request. Network trouble and 408/429/5xx are retried quickly; any other answer is returned as it is."""
    attempt, r = 0, None
    while attempt < tries:
        try:
            r = _client().request(method, url, headers=_headers(headers), **kw)
        except httpx.HTTPError as exc:
            attempt += 1
            if attempt >= tries or (isinstance(exc, httpx.TimeoutException) and method not in ('GET', 'HEAD')):
                raise StorageError(f'Supabase connection failed: {type(exc).__name__}')
            time.sleep(.2 * 3 ** (attempt - 1) + random.random() * .1)
            continue
        text = r.text.lower() if r.status_code in (400, 401, 403) else ''
        if text and STATE['auth'] is None and any(s in text for s in ('jwt', 'jws', 'authorization')):
            STATE['auth'] = 'bearer'
            continue
        attempt += 1
        if r.status_code in TRANSIENT and attempt < tries:
            time.sleep(.2 * 3 ** (attempt - 1) + random.random() * .1)
            continue
        return r
    return r


def _object_url(bucket, path, kind=''):
    return f"{project_url()}/storage/v1/object/{kind + '/' if kind else ''}{quote(bucket, safe='')}/{quote(path, safe='/')}"


def _bucket():
    """The private bucket of this app, made on first use."""
    name = bucket_name()
    if STATE['bucket'] == name:
        return name
    with _sb_lock:
        if STATE['bucket'] == name:
            return name
        r = _call('GET', f'{project_url()}/storage/v1/bucket/{quote(name, safe="")}')
        if r.status_code != 200:
            r = _call('POST', f'{project_url()}/storage/v1/bucket', {'Content-Type': 'application/json'}, json={'id': name, 'name': name, 'public': False})
            if r.status_code not in (200, 201) and 'already exists' not in r.text.lower():
                raise StorageError(f'Supabase bucket could not be made ({r.status_code}): {r.text[:160]}')
        elif r.json().get('public'):
            raise StorageError(f'Supabase bucket {name} is public. Make it private first.')
        STATE['bucket'] = name
        return name


def _tus_endpoint():
    base = project_url()
    host = urlparse(base).hostname or ''
    # Supabase's own storage address is the fast lane for big files.
    if host.endswith('.supabase.co') and host.count('.') == 2:
        return f"https://{host.split('.')[0]}.storage.supabase.co/storage/v1/upload/resumable"
    return base + '/storage/v1/upload/resumable'


def _tus(bucket, path, data, content_type):
    """A big file in 6 MB pieces. A piece that does not arrive is sent again from where Supabase says it stands."""
    meta = ','.join(f"{k} {base64.b64encode(v.encode()).decode()}" for k, v in (('bucketName', bucket), ('objectName', path), ('contentType', content_type), ('cacheControl', '3600')))
    tus = {'Tus-Resumable': '1.0.0'}
    r = _call('POST', _tus_endpoint(), {**tus, 'Upload-Length': str(len(data)), 'Upload-Metadata': meta, 'x-upsert': 'true'})
    if r.status_code != 201 or not r.headers.get('Location'):
        raise StorageError(f'Supabase big-file upload could not start ({r.status_code}): {r.text[:160]}')
    where, offset, misses = r.headers['Location'], 0, 0
    while offset < len(data):
        try:
            r = _call('PATCH', where, {**tus, 'Upload-Offset': str(offset), 'Content-Type': 'application/offset+octet-stream'}, tries=1, content=data[offset:offset + TUS_CHUNK])
        except StorageError:
            r = None
        if r is not None and r.status_code == 204:
            offset, misses = int(r.headers.get('Upload-Offset', offset + TUS_CHUNK)), 0
            continue
        misses += 1
        if misses > 5 or (r is not None and r.status_code not in TRANSIENT + (409,)):
            raise StorageError(f'Supabase big-file upload stopped at {offset} of {len(data)} bytes ({r.status_code if r is not None else "no answer"}).')
        time.sleep(.5 * misses)
        h = _call('HEAD', where, tus)
        if h.status_code == 200 and h.headers.get('Upload-Offset'):
            offset = int(h.headers['Upload-Offset'])


def sb_put(path, data, content_type):
    bucket = _bucket()
    if len(data) > TUS_CHUNK:
        _tus(bucket, path, data, content_type)
    else:
        r = _call('POST', _object_url(bucket, path), {'Content-Type': content_type, 'x-upsert': 'true', 'Cache-Control': '3600'}, content=data)
        if r.status_code not in (200, 201):
            raise StorageError(f'Supabase did not save the file ({r.status_code}): {r.text[:160]}')
    return SB + bucket + '/' + path


def sb_get(bucket, path, tries=4):
    r = _call('GET', _object_url(bucket, path, 'authenticated'), tries=tries)
    if r.status_code != 200:
        raise StorageError(f'Supabase file unavailable ({r.status_code}). Retry later.')
    return r.content


def _ok():
    STATE.update(strikes=0, down_until=0.0, last_ok=time.time(), backup_since=None, backup_writes=0)


_count_lock = threading.Lock()


def _count(store):
    with _count_lock:
        STATE['writes'][store] += 1
        if store == 'emergent' and configured():  # a file Supabase should have taken
            STATE['backup_writes'] += 1


def _strike(exc, handed=True):
    # Supabase rests a little longer after every miss in a row (15 s, 30 s, ... 5 min) and writes go straight to Emergent meanwhile.
    with _count_lock:
        STATE['strikes'] += 1
        STATE['down_until'] = time.time() + min(300, 15 * 2 ** (STATE['strikes'] - 1))
        STATE['last_error'] = str(exc)[:240]
        STATE['backup_since'] = STATE['backup_since'] or time.time()
        if handed:  # a file really went to Emergent (a failed health check alone does not count)
            STATE['failovers'] += 1
            STATE['last_failover'] = {'at': time.time(), 'reason': STATE['last_error']}


def supabase_on():
    return configured() and time.time() >= STATE['down_until']


def put_object(path, data, content_type="application/pdf"):
    """Saves a file and returns its reference: Supabase first, Emergent the moment Supabase cannot."""
    with source_lock(path):
        ref = None
        if supabase_on():
            try:
                ref = sb_put(path, data, content_type)
                _ok()
                _count('supabase')
            except Exception as exc:  # noqa: BLE001  any Supabase trouble hands the file to Emergent storage
                _strike(exc)
        if ref is None:
            ref = request('PUT', path, data, content_type).json()['path']
            _count('emergent')
        _source_cache.remove(ref)
        return ref


def get_object(ref):
    cached = _source_cache.get(ref)
    if cached is not None:
        return cached
    with source_lock(ref):
        cached = _source_cache.get(ref)
        if cached is not None:
            return cached
        if ref.startswith(SB):
            bucket, path = ref[len(SB):].split('/', 1)
            raw = sb_get(bucket, path)
        else:
            raw = request('GET', ref).content
        return _source_cache.put(ref, raw)


def probe():
    """Each store writes a tiny file, reads it back and compares it. Times in milliseconds."""
    payload = f'jeelive storage check {time.time():.3f}'.encode()
    out = {}
    if configured():
        t = time.time()
        try:
            ref = sb_put('health/check.bin', payload, 'application/octet-stream'); w = time.time()
            got = sb_get(ref[len(SB):].split('/', 1)[0], 'health/check.bin', tries=2)
            out['supabase'] = {'ok': got == payload, 'write_ms': round((w - t) * 1000), 'read_ms': round((time.time() - w) * 1000), 'error': '' if got == payload else 'Read back different bytes.'}
            if got == payload:
                _ok()
        except Exception as exc:  # noqa: BLE001
            out['supabase'] = {'ok': False, 'error': str(exc)[:240], 'took_ms': round((time.time() - t) * 1000)}
            if supabase_on():
                _strike(exc, handed=False)
    else:
        out['supabase'] = {'ok': False, 'configured': False, 'error': 'Supabase is not set up (project URL or secret key missing).'}
    t = time.time()
    _quick.on = True
    try:
        request('PUT', 'jeelive/health/check.bin', payload, 'application/octet-stream'); w = time.time()
        got = request('GET', 'jeelive/health/check.bin').content
        out['emergent'] = {'ok': got == payload, 'write_ms': round((w - t) * 1000), 'read_ms': round((time.time() - w) * 1000), 'error': '' if got == payload else 'Read back different bytes.'}
    except Exception as exc:  # noqa: BLE001
        out['emergent'] = {'ok': False, 'error': str(exc)[:240], 'took_ms': round((time.time() - t) * 1000)}
    finally:
        _quick.on = False
    return out
