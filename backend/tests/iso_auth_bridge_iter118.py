"""TEST-ONLY iteration 118 ISOLATED bridge with REAL auth (no X-Test-User override). Port 8766, lifespan off.
Config only from this process env (FRONTEND_URL / CORS_ORIGINS); .env untouched. Synthetic staff creds written to
/tmp/iter118_bridge_creds.json (0600, synthetic test-only, deleted at cleanup). Run: cd /app/backend/tests && python iso_auth_bridge_iter118.py &
"""
import asyncio, json, os
import uvicorn
import iso_auth_harness_iter118 as A
import server

if __name__ == '__main__':
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(A.seed())
    path = '/tmp/iter118_bridge_creds.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump({'owner_email': A.OWNER_EMAIL, 'owner_pw': A.OWNER_PW}, f)
    print('BRIDGE118 origins=', server.origins, flush=True)
    loop.run_until_complete(uvicorn.Server(uvicorn.Config(A.H.app, host='127.0.0.1', port=8766, log_level='warning', lifespan='off')).serve())
