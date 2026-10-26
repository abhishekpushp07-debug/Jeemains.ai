"""TEST-ONLY isolated harness (iteration 154): REAL auth (NO auth.current override), isolated DB.
- Imports the real FastAPI app WITHOUT lifespan (no owner seeding / workers / AI).
- Re-binds EVERY tejas/server Motor DB/collection handle to `tejas_isolated_iter154` (MONGO_URL/DB_NAME untouched).
- `now` replaced by OFFSET-able clock (real + OFFSET[0]) so rate-limit windows are controlled without customer records.
- Storage boundary: GET -> original local source PDFs; any PUT raises (for PYQ bundle import only).
"""
import importlib, os, pkgutil, sys, time, json, gzip
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env')
REAL_DB = os.environ['DB_NAME']
TEST_DB = 'tejas_isolated_iter154'
assert TEST_DB != REAL_DB

import server  # noqa: E402
import tejas  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # noqa: E402

for m in pkgutil.iter_modules(tejas.__path__):
    try:
        importlib.import_module('tejas.' + m.name)
    except Exception as e:  # pragma: no cover
        print('import skipped', m.name, e)

from tejas import db as tdbmod  # noqa: E402
import tejas_storage  # noqa: E402
TDB = tdbmod.client.get_database(TEST_DB, write_concern=tdbmod.db.write_concern)
REAL_NOW = tdbmod.now
OFFSET = [0.0]


def fake_now():
    return time.time() + OFFSET[0]


RES = Path('/app/backend/resources')
AUDIT = Path('/app/data/jee_pyq/source_audit')
_FILES = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))['collections']['tejas_files']
PATHS = {f['path']: AUDIT / (f['source_drive_id'] + '.pdf') for f in _FILES}
PUTS = []


class _Resp:
    def __init__(self, c): self.content = c


def _bytes(path):
    if path not in PATHS:
        raise tejas_storage.StorageError('TEST: unknown object ' + path)
    return PATHS[path].read_bytes()


def fake_request(method, path, data=None, content_type=None):
    if method != 'GET':
        PUTS.append(path); raise RuntimeError('TEST: storage writes forbidden')
    return _Resp(_bytes(path))


def fake_put(*a, **k):
    PUTS.append(a[:1]); raise RuntimeError('TEST: storage writes forbidden')


REAL_ST = (tejas_storage.request, tejas_storage.get_object, tejas_storage.put_object)
PATCHED = []
for name, mod in list(sys.modules.items()):
    if not (name == 'server' or name.startswith('tejas')) or mod is None:
        continue
    for attr, val in list(vars(mod).items()):
        if isinstance(val, AsyncIOMotorDatabase) and val.name == REAL_DB:
            setattr(mod, attr, TDB); PATCHED.append(f'{name}.{attr}')
        elif isinstance(val, AsyncIOMotorCollection) and val.database.name == REAL_DB:
            setattr(mod, attr, TDB[val.name]); PATCHED.append(f'{name}.{attr}')
        elif val is REAL_NOW:
            setattr(mod, attr, fake_now)
        elif val is REAL_ST[0]:
            setattr(mod, attr, fake_request)
        elif val is REAL_ST[1]:
            setattr(mod, attr, _bytes)
        elif val is REAL_ST[2]:
            setattr(mod, attr, fake_put)


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


app = server.app
app.dependency_overrides.clear()  # REAL auth.current/staff/owner
from tejas import auth  # noqa: E402
assert auth.current not in app.dependency_overrides
ORIGIN = os.environ['FRONTEND_URL'].rstrip('/')
