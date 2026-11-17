"""Owner actions on the live site for QA runs: count or remove test accounts, run the data check. Credentials come from the environment and are never printed.
Usage: python tools/live_owner.py BASE count|remove|integrity [PREFIX CREATED_AFTER]
"""
import asyncio, json, os, sys
import aiohttp
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
BASE, ACTION = sys.argv[1].rstrip('/'), sys.argv[2]
H = {'Content-Type': 'application/json', 'Origin': BASE, 'User-Agent': 'Mozilla/5.0 (JEELIVE owner QA)'}


async def main():
    async with aiohttp.ClientSession() as s:
        async def call(method, path, body=None):
            async with s.request(method, BASE + '/api' + path, json=body, headers=H) as r:
                return r.status, await r.json(content_type=None)
        code, _ = await call('POST', '/auth/login', {'email': os.environ['ADMIN_EMAIL'], 'password': os.environ['ADMIN_PASSWORD']})
        if code != 200:
            print('owner sign-in failed', code); return
        try:
            if ACTION in ('count', 'remove'):
                body = {'prefix': sys.argv[3], 'created_after': float(sys.argv[4]), 'dry_run': ACTION == 'count',
                        'confirm': 'REMOVE TEST ACCOUNTS' if ACTION == 'remove' else ''}
                print(json.dumps(await call('POST', '/admin/qa/test-accounts/remove', body)))
            elif ACTION == 'integrity':
                print(await call('POST', '/admin/integrity/run', {}))
                for _ in range(30):
                    await asyncio.sleep(4)
                    code, r = await call('GET', '/admin/integrity')
                    d = (r or {}).get('data') or {}
                    if not d.get('running'):
                        rep = d.get('report') or {}
                        print(json.dumps({k: rep.get(k) for k in ('last_run', 'found', 'fixed', 'needs_attention', 'missing_safeguards', 'index_problems')}))
                        print(json.dumps([(c['key'] if 'key' in c else c.get('label'), c.get('found'), c.get('state')) for c in rep.get('checks', [])]))
                        break
        finally:
            await call('POST', '/auth/logout')


asyncio.run(main())
