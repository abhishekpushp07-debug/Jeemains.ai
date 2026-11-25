"""Private object storage on two stores. All authorization is performed by API callers.

With Supabase set up, every new file goes only to Supabase. When Supabase cannot take it (down, slow to answer, any error),
StorageWaiting is raised and the work waits and carries on by itself: files of one paper are never split between stores.
Without Supabase set up, Emergent storage takes new files. The reference a write returns names its store:
"sb://<bucket>/<path>" lives in Supabase, a plain path lives in Emergent storage (every file saved before Supabase too).
A read therefore goes straight to the one store that holds the file, never searching both.
"""

import base64, hashlib, logging, os, random, re, threading, time
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
    code = None    # Supabase's own answer code, when it answered at all
    moved = False  # a big file got at least one more piece across in this try
    stalls = 0     # tries in a row in which a big file did not move
    scope = None   # set when the code alone does not say whose trouble it is
    said = ''      # a plain reason of its own, when the code has none


def _error(text, code=None, moved=False, scope=None, said=''):
    exc = StorageError(text)
    exc.code, exc.moved, exc.scope, exc.said = code, moved, scope, said
    return exc


def _answer(r):
    """Supabase's own code and words for an answer (its storage API often wraps the real code inside a 400)."""
    code, said = r.status_code, r.text[:200]
    try:
        body = r.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        inner = str(body.get('statusCode') or '')
        code = int(inner) if inner.isdigit() else code
        said = str(body.get('message') or body.get('error') or said)[:200]
    return code, said


class StorageWaiting(StorageError):
    """Supabase cannot take or give a file right now. Nothing went to Emergent: the work waits and carries on by itself.
    scope says whose trouble it is: 'away' Supabase does not answer, 'blocked' the project itself is restricted,
    'file' Supabase answers and only this file did not go yet (Supabase is not rested for the others)."""
    scope = 'away'
    reason = ''   # one plain line for the owner, Supabase's code in brackets
    step = ''     # what to do next
    raw = ''      # the technical line, for the error list


class StorageStuck(StorageWaiting):
    """Supabase answers but keeps returning this one file. Only this file stops ("Atki hai"): Supabase is not rested, other work
    carries on, and the file is tried again every 15 minutes or when the owner presses Dobara chalao."""
    scope = 'stuck'


class SupabaseRefused(StorageError):
    """Supabase answers but will never take this file (too big for its limit): waiting would not help, so the work stops with this reason."""


TOO_BIG = 'Yeh file Supabase ki size limit se badi hai, isliye save nahi hui (Emergent mein bhi nahi gayi). Supabase dashboard mein bucket ki file size limit badhaiye ya chhoti PDF chuniye.'
NOT_ALLOWED = 'Supabase ne yeh file lene se mana kiya (file ka type ya naam allowed nahi). Isliye save nahi hui (Emergent mein bhi nahi gayi).'


def _refused(r):
    """Supabase is up but will never take THIS file: stop with the reason instead of waiting (and do not mark Supabase down)."""
    text = r.text.lower() if r.status_code in (400, 413, 415, 422) else ''
    if r.status_code == 413 or 'maximum allowed size' in text:
        raise SupabaseRefused(TOO_BIG)
    if r.status_code == 415 or any(s in text for s in ('mime type', 'invalid key', 'invalidkey')):
        raise SupabaseRefused(NOT_ALLOWED)


WAIT_TEXT = 'Supabase abhi file nahi le raha. Kaam ruka hai, file surakshit hai; Supabase lautte hi apne aap aage chalega.'
FILE_TEXT = 'Yeh file abhi Supabase mein nahi gayi. Machine khud phir koshish kar rahi hai; baaki kaam chal raha hai.'
STUCK_TEXT = 'Yeh file Supabase mein nahi ja rahi (atki hai). File surakshit hai aur baaki kitaabein chal rahi hain.'
BLOCKED = (401, 402, 403, 540)   # the project itself is restricted: billing or usage, a wrong key, a paused project
STUCK_RETRY = 900                # a stuck file is tried again by itself every 15 minutes


def scope_of(exc):
    """Whose trouble a failure is: 'away' (no answer, or Supabase's own fault), 'blocked' (the project is restricted) or 'file'."""
    if getattr(exc, 'scope', None):
        return exc.scope
    code = getattr(exc, 'code', None)
    if code is None or code in (408, 429) or (code >= 500 and code not in BLOCKED):
        return 'away'
    return 'blocked' if code in BLOCKED else 'file'


def explain(code, scope):
    """One plain line for the owner (Supabase's code in brackets) and what to do next."""
    tail = f' ({code})' if code else ''
    if code == 402:
        why, step = 'Supabase project par billing ya usage ki rok hai', 'Supabase dashboard me Billing aur Usage dekhiye. Rok hatte hi kaam apne aap aage chalega.'
    elif code == 540:
        why, step = 'Supabase project paused hai', 'Supabase dashboard me project ko Resume kijiye. Uske baad kaam apne aap aage chalega.'
    elif code in (401, 403):
        why, step = 'Supabase ne secret key nahi maani', 'Supabase dashboard › Project Settings › API keys me secret key dekhiye aur wahi key app ke Secrets me rakhiye.'
    elif scope == 'away':
        why = 'Supabase se jawab nahi aaya' if code is None else 'Supabase ki apni galti ya bheed'
        step = 'Kuch nahi karna: Supabase lautte hi kaam apne aap aage chalega.'
    else:
        why = ('Is file ke tukde Supabase tak nahi pahunch rahe, jabki Supabase chhoti files le raha hai' if code is None or code >= 500 else
               {409: 'Supabase ke mutabik yeh file us pate par pehle se hai', 423: 'Supabase me isi file ka ek aur upload abhi khula hai',
                404: 'Supabase ko is upload ka pata nahi mila'}.get(code, 'Supabase ne yeh file lautayi'))
        step = ('Har 15 minute me apne aap phir koshish hogi. Abhi koshish ke liye "Dobara chalao" dabaiye.' if scope == 'stuck'
                else 'Kuch nahi karna: machine khud phir koshish kar rahi hai.')
    return why + tail, step
RESUME_SECONDS = 20 * 3600   # Supabase keeps a half-sent big file for 24 hours


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
                code, said = _answer(r)
                raise _error(f'Supabase bucket could not be made ({code}): {said[:160]}', code)
        elif r.json().get('public'):
            raise _error(f'Supabase bucket {name} is public. Make it private first.', scope='blocked')
        STATE['bucket'] = name
        return name


def _tus_endpoint():
    base = project_url()
    host = urlparse(base).hostname or ''
    # Supabase's own storage address is the fast lane for big files.
    if host.endswith('.supabase.co') and host.count('.') == 2:
        return f"https://{host.split('.')[0]}.storage.supabase.co/storage/v1/upload/resumable"
    return base + '/storage/v1/upload/resumable'


def _carry_on(resume, path, size, tus):
    """The address of an earlier, half-sent copy of this same file, and how much of it Supabase already has."""
    if not resume or resume.get('path') != path or resume.get('size') != size or not resume.get('url') or time.time() - resume.get('started', 0) > RESUME_SECONDS:
        return None, 0
    try:
        h = _call('HEAD', resume['url'], tus)
    except StorageError:
        return None, 0
    if h.status_code == 200 and h.headers.get('Upload-Offset') is not None:
        there = int(h.headers['Upload-Offset'])
        if there < size:  # a finished upload has nothing left to carry on: the file is sent afresh
            return resume['url'], there
    return None, 0


def _tus(bucket, path, data, content_type, resume=None, on_progress=None):
    """A big file in 6 MB pieces. A piece that does not arrive is sent again from where Supabase says it stands;
    a later try carries on from the saved upload address (resume) instead of starting at 0. on_progress hears every piece."""
    tus = {'Tus-Resumable': '1.0.0'}
    where, offset = _carry_on(resume, path, len(data), tus)
    if where:
        info = {k: resume[k] for k in ('url', 'path', 'size', 'started')}
    else:
        meta = ','.join(f"{k} {base64.b64encode(v.encode()).decode()}" for k, v in (('bucketName', bucket), ('objectName', path), ('contentType', content_type), ('cacheControl', '3600')))
        r = _call('POST', _tus_endpoint(), {**tus, 'Upload-Length': str(len(data)), 'Upload-Metadata': meta, 'x-upsert': 'true'})
        _refused(r)
        if r.status_code != 201 or not r.headers.get('Location'):
            code, said = _answer(r)
            raise _error(f'Supabase big-file upload could not start ({code}): {said[:160]}', code)
        where = r.headers['Location']
        info = {'url': where, 'path': path, 'size': len(data), 'started': time.time()}
    misses, moved = 0, False
    if on_progress:
        on_progress({**info, 'sent': offset})
    while offset < len(data):
        try:
            # Permission to overwrite goes with every piece: Supabase asks for it when a piece arrives, not only when the upload starts.
            r = _call('PATCH', where, {**tus, 'Upload-Offset': str(offset), 'Content-Type': 'application/offset+octet-stream', 'x-upsert': 'true'}, tries=1, content=data[offset:offset + TUS_CHUNK])
        except StorageError:
            r = None
        if r is not None and r.status_code == 204:
            offset, misses, moved = int(r.headers.get('Upload-Offset', offset + TUS_CHUNK)), 0, True
            if on_progress:
                on_progress({**info, 'sent': offset})
            continue
        misses += 1
        code = r.status_code if r is not None else None
        if r is not None:
            _refused(r)
        # 409 = Supabase stands at another place, 423 = its lock on this file is held for a moment: both are asked again.
        stop = misses > 5 or (code is not None and code not in TRANSIENT + (409, 423))
        if not stop:
            time.sleep((2 if code == 423 else .5) * misses)
            try:
                h = _call('HEAD', where, tus)
            except StorageError:
                h = None
            there = int(h.headers['Upload-Offset']) if h is not None and h.status_code == 200 and h.headers.get('Upload-Offset') else None
            if there is not None and there != offset:
                if there > offset:  # the piece did arrive, only its answer was lost: that is progress, not a miss
                    misses, moved = 0, True
                offset = there
                if on_progress:
                    on_progress({**info, 'sent': offset})
            elif code == 409:
                stop = True  # Supabase agrees on the place and still returns the piece: sending it again cannot help
        if stop:
            raise _error(f'Supabase big-file upload stopped at {offset} of {len(data)} bytes ({code if code is not None else "no answer"}).', code, moved)


def sb_size(bucket, path):
    """How many bytes Supabase holds at this path; None when nothing is there. Any other answer raises (Supabase cannot say)."""
    r = _call('GET', f"{project_url()}/storage/v1/object/info/{quote(bucket, safe='')}/{quote(path, safe='/')}")
    if r.status_code == 200:
        return int(r.json().get('size') or 0)
    code, said = _answer(r)
    if code == 404:
        return None
    raise _error(f'Supabase file check failed ({code}): {said[:120]}', code)


def _same_there(bucket, path, data):
    """True when Supabase already holds exactly this file at this path: the size first, then every byte read back and fingerprinted."""
    if sb_size(bucket, path) != len(data):
        return False
    got = hashlib.sha256()
    try:
        with _client().stream('GET', _object_url(bucket, path, 'authenticated'), headers=_headers()) as r:
            if r.status_code != 200:
                return False
            for piece in r.iter_bytes(1024 * 1024):
                got.update(piece)
    except httpx.HTTPError as exc:
        raise StorageError(f'Supabase connection failed: {type(exc).__name__}') from None
    return got.hexdigest() == hashlib.sha256(data).hexdigest()


def _sized(bucket, path, want):
    """After every big save Supabase is asked how many bytes it holds; any other number is not accepted as saved."""
    size = sb_size(bucket, path)
    if size != want:
        said = 'Supabase me file save hone ke baad nahi mili' if size is None else f'Supabase me file ka size alag nikla ({size} bytes; hone chahiye {want})'
        raise _error(f'Supabase stored {size} bytes of {want}.', scope='file', said=said)


STALL_LIMIT = 2   # tries in a row without one more piece across: then a fresh upload and the one-request route
ONE_REQUEST = httpx.Timeout(connect=5.0, read=180.0, write=120.0, pool=10.0)


def _one_request(bucket, path, data, content_type):
    """The second route for a big file: the whole file in a single request (Supabase takes up to 5 GB this way)."""
    r = _call('POST', _object_url(bucket, path), {'Content-Type': content_type, 'x-upsert': 'true', 'Cache-Control': '3600'}, tries=1, content=data, timeout=ONE_REQUEST)
    _refused(r)
    if r.status_code not in (200, 201):
        code, said = _answer(r)
        raise _error(f'Supabase did not save the file in one request ({code}): {said[:160]}', code)


def _big(bucket, path, data, content_type, resume=None, on_progress=None):
    """A big file (an original PDF). It is never sent again when Supabase already holds exactly it; a half upload that does not
    move is dropped for a fresh one; when the piece route keeps failing while Supabase answers, the file goes in one request.
    resume/on_progress let the caller keep the place between tries; without them both tries happen in this one call."""
    if _same_there(bucket, path, data):
        return
    stalls, tries, last = int((resume or {}).get('stalls') or 0), 0, {}

    def tell(info):
        # The caller notes the place in its own database; a failure there is not Supabase's: the upload carries on, Supabase is not rested.
        if on_progress:
            try:
                on_progress(info)
            except Exception:  # noqa: BLE001
                logging.getLogger(__name__).warning('The place of a big upload could not be noted (%s); the upload carries on.', path, exc_info=True)

    def heard(info):
        first = not last
        last.update(info)
        tell({**info, 'stalls': stalls} if first and stalls else info)

    while True:
        tries += 1
        try:
            _tus(bucket, path, data, content_type, None if stalls >= STALL_LIMIT else resume, heard)
            _sized(bucket, path, len(data))  # a wrong size is a failed try like any other: next a fresh upload, then the one-request route
            return
        except SupabaseRefused:
            raise
        except StorageError as exc:
            try:
                if _same_there(bucket, path, data):  # every piece arrived; only the answer to the last one was lost
                    return
            except StorageError:
                raise exc from None  # Supabase itself is away: the file waits, this is not counted against it
            if exc.code == 423:
                raise  # another upload of this same file holds Supabase's lock: it waits
            stalls = 0 if exc.moved else stalls + 1
            place = {'url': '', 'path': path, 'size': len(data), 'started': time.time(), 'sent': 0, **last}
            tell({**place, 'stalls': stalls})
            if stalls >= STALL_LIMIT:
                try:
                    _one_request(bucket, path, data, content_type)
                    _sized(bucket, path, len(data))
                except SupabaseRefused:
                    raise
                except StorageError as second:
                    # A caller that keeps no place between tries has now had both routes return the file in this one call: it is stuck, not waiting.
                    second.stalls = stalls if on_progress or scope_of(second) != 'file' else STALL_LIMIT + 1
                    raise second from None
                return
            if on_progress or tries >= 2:
                exc.stalls = stalls
                raise
            resume, last = (place if exc.moved else None), {}


def sb_put(path, data, content_type, resume=None, on_progress=None):
    bucket = _bucket()
    if len(data) > TUS_CHUNK:
        _big(bucket, path, data, content_type, resume, on_progress)
    else:
        r = _call('POST', _object_url(bucket, path), {'Content-Type': content_type, 'x-upsert': 'true', 'Cache-Control': '3600'}, content=data)
        _refused(r)
        if r.status_code not in (200, 201):
            code, said = _answer(r)
            raise _error(f'Supabase did not save the file ({code}): {said[:160]}', code)
    return SB + bucket + '/' + path


def sb_get(bucket, path, tries=4):
    try:
        r = _call('GET', _object_url(bucket, path, 'authenticated'), tries=tries)
    except StorageError as exc:
        raise StorageWaiting(f'Supabase abhi file nahi de raha ({exc}). Thodi der mein apne aap phir koshish hogi.') from None
    if r.status_code in TRANSIENT:
        raise StorageWaiting(f'Supabase abhi file nahi de raha ({r.status_code}). Thodi der mein apne aap phir koshish hogi.')
    if r.status_code != 200:
        raise StorageError(f'Supabase file unavailable ({r.status_code}). Retry later.')
    return r.content


# ---------- Removing files from Supabase: only the files of one upload's own folder. Any other path is refused here, whoever asks. ----------
_OWN_FOLDER = re.compile(r'^jeelive/books/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/$')


def _removable(folder, names=()):
    if not _OWN_FOLDER.match(folder) or any(not n.startswith(folder) or n.endswith('/') or '..' in n or '//' in n for n in names):
        raise ValueError("Refused: only the files of one upload's own folder can be removed from Supabase.")


def sb_list(folder):
    """One level of a folder in Supabase: ([(file name, size)], [sub-folder names])."""
    bucket, rows, offset = _bucket(), [], 0
    while True:
        r = _call('POST', f"{project_url()}/storage/v1/object/list/{quote(bucket, safe='')}", {'Content-Type': 'application/json'},
                  json={'prefix': folder.rstrip('/'), 'limit': 1000, 'offset': offset, 'sortBy': {'column': 'name', 'order': 'asc'}})
        if r.status_code != 200:
            code, said = _answer(r)
            raise _error(f'Supabase could not list a folder ({code}): {said[:120]}', code)
        page = r.json()
        rows += page
        if len(page) < 1000:
            break
        offset += 1000
    return [(x['name'], (x.get('metadata') or {}).get('size')) for x in rows if x.get('id')], [x['name'] for x in rows if not x.get('id')]


def sb_remove(folder, names):
    """Removes these files of one upload's own folder (full paths). Returns how many were asked for."""
    _removable(folder, names)
    bucket = _bucket()
    for i in range(0, len(names), 100):
        r = _call('DELETE', f"{project_url()}/storage/v1/object/{quote(bucket, safe='')}", {'Content-Type': 'application/json'}, json={'prefixes': names[i:i + 100]})
        if r.status_code != 200:
            code, said = _answer(r)
            raise _error(f'Supabase could not remove files ({code}): {said[:120]}', code)
    for n in names:
        _source_cache.remove(SB + bucket + '/' + n)
    return len(names)


def sb_empty(folder):
    """Empties one upload's own folder: lists it, removes exactly those names, then lists it again. It must be empty, or this raises."""
    _removable(folder)
    removed = 0

    def clear(prefix, depth):
        nonlocal removed
        for _ in range(200):
            found, inner = sb_list(prefix)
            for sub in inner if depth < 3 else []:
                clear(prefix + sub + '/', depth + 1)
            if not found:
                return
            removed += sb_remove(folder, [prefix + name for name, _ in found])
    clear(folder, 0)
    left, inner = sb_list(folder)
    if left or inner:
        raise _error(f'Supabase still lists {len(left)} files and {len(inner)} folders there after removing.', scope='file')
    return removed


def sb_end_upload(url):
    """Ends a half-sent big upload, so Supabase drops its pieces. Only an upload address of this project's own big-file route is accepted."""
    u, own = urlparse(url or ''), {urlparse(_tus_endpoint()).hostname, urlparse(project_url()).hostname}
    if u.scheme != 'https' or u.hostname not in own or not u.path.startswith('/storage/v1/upload/resumable/'):
        return False
    return _call('DELETE', url, {'Tus-Resumable': '1.0.0'}).status_code in (200, 204)


def _ok():
    STATE.update(strikes=0, down_until=0.0, last_ok=time.time(), backup_since=None, backup_writes=0)


_count_lock = threading.Lock()


def _count(store):
    with _count_lock:
        STATE['writes'][store] += 1
        if store == 'emergent' and configured():  # a file Supabase should have taken
            STATE['backup_writes'] += 1


def _strike(exc, handed=True, scope='away'):
    # Supabase rests a little longer after every miss in a row (15 s, 30 s, ... 5 min); new files wait meanwhile (never Emergent).
    logging.getLogger(__name__).warning('Supabase miss (%s): %s', 'file waits' if handed else 'health check', str(exc)[:240])
    with _count_lock:
        STATE['strikes'] += 1
        STATE['down_until'] = time.time() + min(300, 15 * 2 ** (STATE['strikes'] - 1))
        STATE['last_error'] = str(exc)[:240]
        STATE['last_scope'], STATE['last_code'] = scope, getattr(exc, 'code', None)
        STATE['backup_since'] = STATE['backup_since'] or time.time()
        if handed:  # a real file had to wait (a failed health check alone does not count)
            STATE['failovers'] += 1
            STATE['last_failover'] = {'at': time.time(), 'reason': STATE['last_error']}


def supabase_on():
    return configured() and time.time() >= STATE['down_until']


def _wait(kind, text, code, scope, raw, said=''):
    why, step = explain(code, scope)
    out = kind(text)
    out.code, out.scope, out.reason, out.step, out.raw = code, scope, said or why, step, raw
    return out


def _waiting(exc, big):
    """The wait a caller sees for a Supabase failure. Supabase rests for everyone only when it does not answer or the project is
    blocked; a file that Supabase keeps returning stops alone (StorageStuck), and never for a lock (423)."""
    code, scope, raw = getattr(exc, 'code', None), scope_of(exc), str(exc)[:200]
    if code != 423 and scope != 'blocked' and (getattr(exc, 'stalls', 0) > STALL_LIMIT if big else scope == 'file'):
        scope = 'stuck'
    if scope in ('away', 'blocked'):
        _strike(exc, scope=scope)
        return _wait(StorageWaiting, f'{WAIT_TEXT} Wajah: {raw}', code, scope, raw)
    logging.getLogger(__name__).warning('Supabase returned one file (%s; Supabase is not rested): %s', scope, raw)
    return _wait(StorageStuck if scope == 'stuck' else StorageWaiting, f"{STUCK_TEXT if scope == 'stuck' else FILE_TEXT} Wajah: {raw}", code, scope, raw, getattr(exc, 'said', ''))


def put_object(path, data, content_type="application/pdf", resume=None, on_progress=None):
    """Saves a new file and returns its reference. With Supabase set up, new files go only to Supabase: when it cannot take one,
    StorageWaiting is raised and the caller waits for it (nothing is split into Emergent). Without Supabase, Emergent takes them."""
    with source_lock(path):
        if configured():
            if not supabase_on():
                raise _wait(StorageWaiting, f"{WAIT_TEXT} Wajah: {STATE['last_error'] or 'Supabase thodi der aaram par hai.'}", STATE.get('last_code'), STATE.get('last_scope') or 'away', STATE['last_error'])
            try:
                ref = sb_put(path, data, content_type, resume, on_progress)
            except SupabaseRefused:
                raise  # Supabase is fine, this one file is not allowed there: no rest, no wait
            except Exception as exc:  # noqa: BLE001  any Supabase trouble: the file waits
                raise _waiting(exc, len(data) > TUS_CHUNK) from None
            _ok()
            _count('supabase')
        else:
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
        out['supabase'] = {'ok': False, 'configured': False, 'error': 'Supabase set nahi hai (project URL ya secret key nahi mili).'}
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
