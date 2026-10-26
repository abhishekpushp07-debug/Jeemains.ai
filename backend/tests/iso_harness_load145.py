"""TEST-ONLY iteration 145 load harness. Local copy of iso_harness_iter134 pattern with EXCLUSIVE DB `tejas_isolated_load145`.
- Real FastAPI app (server.app incl. AdmissionGate + all middleware) WITHOUT lifespan (no seeding / worker / AI).
- Every server/tejas module-level Motor DB/collection handle is rebound to tejas_isolated_load145. MONGO_URL/DB_NAME unchanged.
- auth.current overridden by X-Test-User header -> synthetic in-memory users (TEST ONLY).
- Storage: GET -> original local PDFs in /app/data/jee_pyq/source_audit; any write raises + is recorded in PUTS.
- LLM: LlmChat.send_message raises + is recorded in LLM_CALLS (must stay empty).
"""
import gzip, importlib, json, os, pkgutil, sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env')
REAL_DB = os.environ['DB_NAME']
TEST_DB = 'tejas_isolated_load145'
assert TEST_DB != REAL_DB and TEST_DB not in ('tejas_isolated_iter134', 'tejas_isolated_reset144')

import server  # noqa: E402
import tejas  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # noqa: E402
from fastapi import Request, HTTPException  # noqa: E402

for m in pkgutil.iter_modules(tejas.__path__):
    try:
        importlib.import_module('tejas.' + m.name)
    except Exception as e:  # pragma: no cover
        print('import skipped', m.name, e)

import tejas_storage, tejas_core  # noqa: E402,F401
from tejas import db as tdbmod  # noqa: E402
TDB = tdbmod.client.get_database(TEST_DB, write_concern=tdbmod.db.write_concern)

PATCHED = []
for name, mod in list(sys.modules.items()):
    if not (name == 'server' or name.startswith('tejas')) or mod is None:
        continue
    for attr, val in list(vars(mod).items()):
        if isinstance(val, AsyncIOMotorDatabase) and val.name == REAL_DB:
            setattr(mod, attr, TDB); PATCHED.append(f'{name}.{attr}')
        elif isinstance(val, AsyncIOMotorCollection) and val.database.name == REAL_DB:
            setattr(mod, attr, TDB[val.name]); PATCHED.append(f'{name}.{attr}')


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
                    if dbn != TEST_DB:
                        bad.append(f'{name}.{attr}->{dbn}')
    return bad


# ---- storage boundary (GET original PDFs; writes forbidden) ----
RES = BACKEND / 'resources'
AUDIT = Path('/app/data/jee_pyq/source_audit')
DATA = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))
SETS = DATA['collections']['tejas_sets']
FILES = DATA['collections']['tejas_files']
PATHS = {f['path']: AUDIT / (f['source_drive_id'] + '.pdf') for f in FILES}
PUTS, GETS, LLM_CALLS = [], [], []


class _Resp:
    def __init__(self, c): self.content = c


def _bytes(path):
    GETS.append(path)
    if path not in PATHS:
        raise tejas_storage.StorageError('TEST: unknown object ' + path)
    return PATHS[path].read_bytes()


def fake_request(method, path, data=None, content_type=None):
    if method != 'GET':
        PUTS.append(path); raise RuntimeError('TEST: storage writes forbidden')
    return _Resp(_bytes(path))


def fake_get(path): return _bytes(path)
def fake_put(*a, **k): PUTS.append(a[:1]); raise RuntimeError('TEST: storage writes forbidden')


REAL = (tejas_storage.request, tejas_storage.get_object, tejas_storage.put_object)
for name, mod in list(sys.modules.items()):
    if mod is None or not (name.startswith('tejas') or name == 'server'):
        continue
    for attr, val in list(vars(mod).items()):
        if val is REAL[0]: setattr(mod, attr, fake_request)
        elif val is REAL[1]: setattr(mod, attr, fake_get)
        elif val is REAL[2]: setattr(mod, attr, fake_put)

# ---- LLM must never be called ----
from emergentintegrations.llm.chat import LlmChat  # noqa: E402


async def _no_llm(self, *a, **k):
    LLM_CALLS.append(type(self).__name__); raise RuntimeError('TEST: LLM forbidden')
LlmChat.send_message = _no_llm

# ---- synthetic auth ----
USERS = {}


async def fake_current(request: Request):
    u = USERS.get(request.headers.get('x-test-user', ''))
    if not u:
        raise HTTPException(401, 'TEST: unknown synthetic user')
    return dict(u)


app = server.app
from tejas import auth  # noqa: E402
app.dependency_overrides[auth.current] = fake_current
