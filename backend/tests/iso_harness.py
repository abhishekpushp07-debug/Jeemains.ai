"""TEST-ONLY isolated harness (iteration 105).
Imports the real FastAPI app, then re-binds every tejas module-level Mongo handle to a DEDICATED
test database (never the configured customer DB). Env vars are NOT changed. Clock (`now`) is
monkeypatched for IST date-boundary tests. Auth `current` is overridden by an X-Test-User header that
resolves synthetic fixture users only (TEST-ONLY MOCKED auth). No lifespan -> no seed/worker/AI.
"""
import importlib, os, pkgutil, sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env')
REAL_DB = os.environ['DB_NAME']
TEST_DB = 'tejas_isolated_iter105_test'
assert TEST_DB != REAL_DB

import server  # noqa: E402  (builds app + install_contracts -> fails if a route lacks a contract)
import tejas  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # noqa: E402
from fastapi import Request, HTTPException  # noqa: E402

for m in pkgutil.iter_modules(tejas.__path__):
    try:
        importlib.import_module('tejas.' + m.name)
    except Exception as e:  # pragma: no cover
        print('import skipped', m.name, e)

from tejas import db as tdbmod  # noqa: E402
TDB = tdbmod.client.get_database(TEST_DB, write_concern=tdbmod.db.write_concern)
CLOCK = [tdbmod.now()]
REAL_NOW = tdbmod.now


def fake_now():
    return CLOCK[0]


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


USERS = {}


async def fake_current(request: Request):
    u = USERS.get(request.headers.get('x-test-user', ''))
    if not u:
        raise HTTPException(401, 'Enter your number again to continue. Saved work is retained.')
    return dict(u)


app = server.app
from tejas import auth  # noqa: E402
app.dependency_overrides[auth.current] = fake_current
