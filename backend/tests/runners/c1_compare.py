#!/usr/bin/env python3
"""TEST-ONLY: the re-run of the older suites after C1a + C1b (/root/p2/c1_reg_*.log) held against the same suites from before this work
(/root/p2/r2_reg_*.log = after S1b, before C1). Reads logs only. Says, suite by suite, whether the failing lines are the very same lines."""
import os, re

P = '/root/p2/'
TOTAL = re.compile(r'^TOTAL (\d+) PASS (\d+) FAIL (\d+)', re.M)
RANDOM = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')   # a request id is new on every run


def line(l):
    return RANDOM.sub('<id>', l)[:300]


def read(path):
    text = open(path, errors='replace').read() if os.path.exists(path) else None
    if text is None:
        return None
    fails = sorted(set(line(l) for l in text.split('\n') if l.startswith('FAIL')))
    m = TOTAL.findall(text)
    checks = (int(m[-1][0]), int(m[-1][1]), int(m[-1][2])) if m else (text.count('\nPASS ') + len(fails), text.count('\nPASS '), len(fails))
    return checks, fails, 'Traceback (most recent call last)' in text and not m


names = [l.split()[1] for l in open(P + 'c1_regress.log') if l.startswith('=== ')]
tot = [0, 0, 0]; new, same, clean, fresh = [], [], [], []
for n in names:
    now, was = read(f'{P}c1_reg_{n}.log'), read(f'{P}r2_reg_{n}.log')
    if now is None:
        new.append((n, 'no log')); continue
    (c, p, f), fails, broke = now
    tot = [tot[0] + c, tot[1] + p, tot[2] + f]
    if broke or not c:
        new.append((n, 'did not reach its total')); continue
    if not fails:
        (clean if was else fresh).append((n, c)); continue
    if was is None:
        new.append((n, f'{len(fails)} failing, no earlier log to hold it against: ' + ' | '.join(fails)[:400])); continue
    extra = [x for x in fails if x not in was[1]]
    (new if extra else same).append((n, f'{len(fails)} failing' + (': NEW: ' + ' | '.join(extra)[:500] if extra else ', the same lines as before')))
print(f'suites {len(names)} | checks {tot[0]} | pass {tot[1]} | fail {tot[2]}')
print(f'all pass, also run before: {len(clean)} | all pass, not in the earlier list: {len(fresh)} -> ' + ', '.join(f'{n} {c}/{c}' for n, c in fresh))
print('failing with the very same lines as before this work:'); [print('  ', n, '::', d) for n, d in same]
print('NEW or unexplained:' + ('' if new else ' none')); [print('  ', n, '::', d) for n, d in new]
print('DONE' if any(l.startswith('REGDONE') for l in open(P + 'c1_regress.log')) else 'NOT FINISHED YET')
