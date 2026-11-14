"""TEST-ONLY iteration 176 isolated harness: real FastAPI app (all middleware) without lifespan, every Motor handle
rebound to a disposable DB (TEJAS_ISO_DB). REAL auth is kept (no dependency override). Storage GET -> local original
PDFs, storage writes and LLM calls forbidden. MONGO_URL/DB_NAME unchanged; customer DB never written.
"""
import gzip, importlib, json, os, pkgutil, sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env')
REAL_DB = os.environ['DB_NAME']
TEST_DB = os.environ['TEJAS_ISO_DB']
assert TEST_DB != REAL_DB and TEST_DB.startswith('tejas_isolated_')

import server  # noqa: E402
import tejas  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # noqa: E402
for m in pkgutil.iter_modules(tejas.__path__):
    try:
        importlib.import_module('tejas.' + m.name)
    except Exception as e:  # pragma: no cover
        print('import skipped', m.name, e)
import tejas_storage  # noqa: E402
from tejas import db as tdbmod  # noqa: E402
TDB = tdbmod.client.get_database(TEST_DB, write_concern=tdbmod.db.write_concern)
for name, mod in list(sys.modules.items()):
    if not (name == 'server' or name.startswith('tejas')) or mod is None:
        continue
    for attr, val in list(vars(mod).items()):
        if isinstance(val, AsyncIOMotorDatabase) and val.name == REAL_DB:
            setattr(mod, attr, TDB)
        elif isinstance(val, AsyncIOMotorCollection) and val.database.name == REAL_DB:
            setattr(mod, attr, TDB[val.name])


def leftover_real_handles():
    bad = []
    for name, mod in list(sys.modules.items()):
        if not (name == 'server' or name.startswith('tejas')) or mod is None:
            continue
        for attr, val in vars(mod).items():
            vals = val.values() if isinstance(val, dict) else val if isinstance(val, (list, tuple)) else [val]
            for v in vals:
                if isinstance(v, (AsyncIOMotorDatabase, AsyncIOMotorCollection)):
                    if (v.name if isinstance(v, AsyncIOMotorDatabase) else v.database.name) != TEST_DB:
                        bad.append(f'{name}.{attr}')
    return bad


RES = BACKEND / 'resources'
AUDIT = Path('/app/data/jee_pyq/source_audit')
DATA = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))
PATHS = {f['path']: AUDIT / (f['source_drive_id'] + '.pdf') for f in DATA['collections']['tejas_files']}
PUTS, LLM_CALLS = [], []


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


REAL = (tejas_storage.request, tejas_storage.get_object, tejas_storage.put_object)
for name, mod in list(sys.modules.items()):
    if mod is None or not (name.startswith('tejas') or name == 'server'):
        continue
    for attr, val in list(vars(mod).items()):
        if val is REAL[0]: setattr(mod, attr, fake_request)
        elif val is REAL[1]: setattr(mod, attr, _bytes)
        elif val is REAL[2]: setattr(mod, attr, fake_put)

from emergentintegrations.llm.chat import LlmChat  # noqa: E402


async def _no_llm(self, *a, **k):
    LLM_CALLS.append(type(self).__name__); raise RuntimeError('TEST: LLM forbidden')
LlmChat.send_message = _no_llm
app = server.app
