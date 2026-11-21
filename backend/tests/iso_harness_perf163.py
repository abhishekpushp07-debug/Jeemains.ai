"""TEST-ONLY performance baseline harness (iteration 163). Reusable for AFTER-fix comparison runs.
- Real FastAPI app (no lifespan / workers / AI), REAL auth (no dependency overrides).
- Every tejas/server Motor handle re-bound to a disposable DB on a *command-monitored* Motor client
  (MONGO_URL / DB_NAME untouched; customer DB never written).
- Storage boundary: ONLY tejas_storage.request is replaced -> reads ORIGINAL LOCAL source PDFs from disk
  (LOCAL DISK BYTES, NOT object-storage network latency). Real get_object + its 32MB source cache are kept so
  production cache semantics are exercised. Any PUT raises.
- Counters: storage GETs/bytes/seconds, fitz PDF opens/seconds, crop renders/seconds, Mongo commands by name.
"""
import importlib, os, pkgutil, sys, time, json, gzip, secrets, threading
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env')
os.environ.pop('SUPABASE_URL', None)  # tests stay offline: every file goes to the in-memory store below
REAL_DB = os.environ['DB_NAME']
TEST_DB = 'tejas_isolated_perf163_' + secrets.token_hex(4)
assert TEST_DB != REAL_DB

import server  # noqa: E402
import tejas  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase  # noqa: E402
from pymongo import monitoring  # noqa: E402

for m in pkgutil.iter_modules(tejas.__path__):
    try:
        importlib.import_module('tejas.' + m.name)
    except Exception as e:  # pragma: no cover
        print('import skipped', m.name, e)

from tejas import db as tdbmod  # noqa: E402
import tejas_storage, tejas_core  # noqa: E402

LOCK = threading.Lock()
STATS = Counter()       # numeric counters
CMDS = Counter()        # mongo command counts by name
CMD_MS = Counter()


class _Cmd(monitoring.CommandListener):
    def started(self, e):
        if e.database_name == TEST_DB:
            with LOCK:
                CMDS[e.command_name] += 1

    def succeeded(self, e):
        if e.database_name == TEST_DB:
            with LOCK:
                CMD_MS['ms'] += e.duration_micros / 1000

    def failed(self, e):
        pass


from tejas.runtime import DB_POOL, DB_WAIT_MS  # noqa: E402
MCLIENT = AsyncIOMotorClient(os.environ['MONGO_URL'], maxPoolSize=DB_POOL, minPoolSize=0, maxConnecting=2,
                             waitQueueTimeoutMS=DB_WAIT_MS, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000,
                             socketTimeoutMS=15000, tz_aware=True, event_listeners=[_Cmd()])
TDB = MCLIENT.get_database(TEST_DB, write_concern=tdbmod.db.write_concern)

RES = Path('/app/backend/resources')
AUDIT = Path('/app/data/jee_pyq/source_audit')
_FILES = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))['collections']['tejas_files']
PATHS = {f['path']: AUDIT / (f['source_drive_id'] + '.pdf') for f in _FILES}
PUTS = []


class _Resp:
    def __init__(self, c): self.content = c


def fake_request(method, path, data=None, content_type=None):
    if method != 'GET':
        PUTS.append(path); raise RuntimeError('TEST: storage writes forbidden')
    if path not in PATHS:
        raise tejas_storage.StorageError('TEST: unknown object ' + path)
    t = time.perf_counter()
    b = PATHS[path].read_bytes()
    with LOCK:
        STATS['storage_get'] += 1; STATS['storage_bytes'] += len(b); STATS['storage_s'] += time.perf_counter() - t
    return _Resp(b)


_real_validate, _real_render = tejas_core.validate_pdf, tejas_core._render_crop_png


def counted_validate(data, **k):
    t = time.perf_counter()
    try:
        return _real_validate(data, **k)
    finally:
        with LOCK:
            STATS['pdf_open'] += 1; STATS['pdf_open_s'] += time.perf_counter() - t


def counted_render(data, ref, scale=2, **k):
    t = time.perf_counter()
    try:
        return _real_render(data, ref, scale, **k)
    finally:
        with LOCK:
            STATS['crop_render'] += 1; STATS['crop_render_s'] += time.perf_counter() - t
            STATS['crop_render_lowres' if scale < 1 else 'crop_render_full'] += 1


tejas_core.validate_pdf = counted_validate
tejas_core._render_crop_png = counted_render

# iter166 TEST-ONLY instrumentation: per-ref geometry checks and Page.get_pixmap calls (scale-bucketed), guards untouched
import fitz as _fitz  # noqa: E402
_real_geom, _real_pixmap = tejas_core._crop_geometry, _fitz.Page.get_pixmap
GEOM_LOG = []      # (page) per geometry check
PIXMAP_LOG = []    # (page_number, scale, clip is None)


def counted_geometry(doc, ref):
    with LOCK:
        STATS['crop_geometry'] += 1; GEOM_LOG.append(ref.get('page'))
    return _real_geom(doc, ref)


def counted_pixmap(self, *a, **k):
    m = k.get('matrix'); sc = round(m.a, 3) if m is not None else 1
    t = time.perf_counter()
    try:
        return _real_pixmap(self, *a, **k)
    finally:
        with LOCK:
            whole = k.get('clip') is None
            STATS['pixmap_calls'] += 1; STATS['pixmap_s'] += time.perf_counter() - t
            STATS['pixmap_wholepage_lowres' if whole and sc < 1 else 'pixmap_clip_lowres' if sc < 1 else 'pixmap_full'] += 1
            PIXMAP_LOG.append((self.number, sc, whole))


tejas_core._crop_geometry = counted_geometry
_fitz.Page.get_pixmap = counted_pixmap
tejas_storage.request = fake_request

PATCHED = []
for name, mod in list(sys.modules.items()):
    if not (name == 'server' or name.startswith('tejas')) or mod is None:
        continue
    for attr, val in list(vars(mod).items()):
        if isinstance(val, AsyncIOMotorDatabase) and val.name == REAL_DB:
            setattr(mod, attr, TDB); PATCHED.append(f'{name}.{attr}')
        elif isinstance(val, AsyncIOMotorCollection) and val.database.name == REAL_DB:
            setattr(mod, attr, TDB[val.name]); PATCHED.append(f'{name}.{attr}')
        elif isinstance(val, AsyncIOMotorClient) and val is tdbmod.client:
            setattr(mod, attr, MCLIENT); PATCHED.append(f'{name}.{attr}')


def leftover_real_handles():
    bad = []
    for name, mod in list(sys.modules.items()):
        if not (name == 'server' or name.startswith('tejas')) or mod is None:
            continue
        for attr, val in vars(mod).items():
            vals = val.values() if isinstance(val, dict) else val if isinstance(val, (list, tuple)) else [val]
            for v in vals:
                if isinstance(v, (AsyncIOMotorDatabase, AsyncIOMotorCollection)):
                    dbn = v.name if isinstance(v, AsyncIOMotorDatabase) else v.database.name
                    if dbn == REAL_DB:
                        bad.append(f'{name}.{attr}')
    return bad


def snap():
    with LOCK:
        return {**{k: round(v, 4) if isinstance(v, float) else v for k, v in STATS.items()},
                'db_cmds': sum(CMDS.values()), 'db_by_cmd': dict(CMDS), 'db_ms': round(CMD_MS['ms'], 2)}


def diff(a, b):
    out = {}
    for k in set(a) | set(b):
        if k == 'db_by_cmd':
            d = {c: b[k].get(c, 0) - a[k].get(c, 0) for c in set(a[k]) | set(b[k])}
            out[k] = {c: v for c, v in d.items() if v}
        else:
            v = b.get(k, 0) - a.get(k, 0)
            if v:
                out[k] = round(v, 4) if isinstance(v, float) else v
    return out


def reset_process_caches():
    """Cold = empty process-local derivative/source/pack caches (simulates fresh pod). Auth state untouched."""
    from tejas import derivatives, packs
    for c in (tejas_storage._source_cache, tejas_core._crop_cache, derivatives._cache, derivatives._validation_cache):
        with c.lock:
            c.data.clear(); c.size = 0
    packs._cache.clear(); packs._cache_bytes = 0


def rss_mb():
    for line in open('/proc/self/status'):
        if line.startswith(('VmRSS', 'VmHWM')):
            pass
    d = {l.split(':')[0]: l.split(':')[1].strip() for l in open('/proc/self/status') if l.startswith(('VmRSS', 'VmHWM'))}
    return {k: round(int(v.split()[0]) / 1024, 1) for k, v in d.items()}


app = server.app
app.dependency_overrides.clear()
ORIGIN = os.environ['FRONTEND_URL'].rstrip('/')
