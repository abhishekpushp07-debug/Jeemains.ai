"""TEST-ONLY isolated harness (iteration 169) for source-first book publishing.
- Real FastAPI app via httpx ASGITransport (no uvicorn, no lifespan), REAL JWT auth (login/phone signup) in a
  disposable DB `tejas_isolated_book169_<hex>`; MONGO_URL/DB_NAME untouched; customer DB never written.
- Storage MOCKED: tejas_storage.request -> in-memory dict (PUT/GET). Real get_object/put_object kept.
- AI MOCKED: tejas.book_ai.ask / solve_and_check replaced by scripted fakes (call counters). No paid calls.
- Real sealed book_pdf_worker subprocess parser (NOT mocked).
"""
import importlib, os, pkgutil, sys, secrets, threading
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env')
REAL_DB = os.environ['DB_NAME']
TEST_DB = 'tejas_isolated_book169_' + secrets.token_hex(4)
assert TEST_DB != REAL_DB

import server  # noqa
import tejas  # noqa
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # noqa
for m in pkgutil.iter_modules(tejas.__path__):
    try: importlib.import_module('tejas.' + m.name)
    except Exception as e: print('import skipped', m.name, e)
from tejas import db as tdbmod  # noqa
import tejas_storage  # noqa
TDB = tdbmod.client.get_database(TEST_DB, write_concern=tdbmod.db.write_concern)
PATCHED = []
for name, mod in list(sys.modules.items()):
    if not (name == 'server' or name.startswith('tejas')) or mod is None: continue
    for attr, val in list(vars(mod).items()):
        if isinstance(val, AsyncIOMotorDatabase) and val.name == REAL_DB:
            setattr(mod, attr, TDB); PATCHED.append(f'{name}.{attr}')
        elif isinstance(val, AsyncIOMotorCollection) and val.database.name == REAL_DB:
            setattr(mod, attr, TDB[val.name]); PATCHED.append(f'{name}.{attr}')


def leftover_real_handles():
    bad = []
    for name, mod in list(sys.modules.items()):
        if not (name == 'server' or name.startswith('tejas')) or mod is None: continue
        for attr, val in vars(mod).items():
            vals = val.values() if isinstance(val, dict) else val if isinstance(val, (list, tuple)) else [val]
            for v in vals:
                if isinstance(v, (AsyncIOMotorDatabase, AsyncIOMotorCollection)):
                    if (v.name if isinstance(v, AsyncIOMotorDatabase) else v.database.name) == REAL_DB: bad.append(f'{name}.{attr}')
    return bad


STORE, LOCK = {}, threading.Lock()


class _Resp:
    def __init__(self, c=b'', j=None): self.content = c; self._j = j; self.ok = True; self.status_code = 200
    def json(self): return self._j


def fake_request(method, path, data=None, content_type=None):
    with LOCK:
        if method == 'PUT':
            STORE[path] = bytes(data); return _Resp(j={'path': path})
        if path not in STORE: raise tejas_storage.StorageError('TEST: missing ' + path)
        return _Resp(STORE[path])


tejas_storage.request = fake_request
tejas_storage.init_storage = lambda force=False: 'TEST'

AI_CALLS = {'ask': 0, 'solve': 0}
AI_SCRIPT = {'ask': None, 'solve': None}


async def fake_ask(system, user, images, model, budget):
    AI_CALLS['ask'] += 1
    return AI_SCRIPT['ask'](user), {'usage': {'input_tokens': 1, 'output_tokens': 1}}


async def fake_solve(q, images):
    AI_CALLS['solve'] += 1
    return AI_SCRIPT['solve'](q)


from tejas import book_ai  # noqa
book_ai.ask = fake_ask
book_ai.solve_and_check = fake_solve
app = server.app
