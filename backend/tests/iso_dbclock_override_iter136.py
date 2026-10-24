"""TEST-ONLY pytest plugin (iteration 136) for fixed-calendar isolated suites (iter105/106) built on iso_harness.
Since iter136, series/MyTests/competition gates read the Mongo clock (canonical.database_now via hello.localTime,
canonical.clocked_one via $$NOW). Those suites simulate future calendar days with H.CLOCK, so this plugin overrides the
SEPARATE database-clock authority explicitly (database_now + clocked_one's _database_now) to H.CLOCK[0].
It does NOT restore app-clock trust in production code; it only redirects the DB authority inside the isolated run.
Pipeline $$NOW literals (EPOCH_NOW in finalize/expiry/$expr) remain real Mongo time.
Usage: cd /app/backend && PYTHONPATH=tests python -m pytest -p iso_dbclock_override_iter136 tests/test_iter105_live_series_isolated.py ... -n0
"""
import sys
import iso_harness as H
from tejas import canonical as CN

_real_clocked_one = CN.clocked_one
_real_database_now = CN.database_now


async def _fake_database_now():
    return H.CLOCK[0]


async def _fake_clocked_one(collection, query, projection):
    row = await _real_clocked_one(collection, query, projection)
    if row is not None:
        row['_database_now'] = H.CLOCK[0]
    return row


PATCHED = []
for name, mod in list(sys.modules.items()):
    if mod is None or not name.startswith('tejas'):
        continue
    for attr, val in list(vars(mod).items()):
        if val is _real_database_now:
            setattr(mod, attr, _fake_database_now); PATCHED.append(f'{name}.{attr}')
        elif val is _real_clocked_one:
            setattr(mod, attr, _fake_clocked_one); PATCHED.append(f'{name}.{attr}')
CN.database_now = _fake_database_now
CN.clocked_one = _fake_clocked_one
print('DBCLOCK_OVERRIDE', sorted(PATCHED))
