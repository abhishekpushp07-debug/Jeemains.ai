"""TEST-ONLY iteration 182 browser bridge: the real app on 127.0.0.1:8770 with a disposable isolated DB (storage + AI mocked).
Seeds BITSAT › Chapter-wise with: a real 30-chapter physics PDF (read by headings) and a PDF with no headings (waiting for marked starts).
Writes /tmp/uibridge/bridge.json (owner + reviewer cookies, 0600) and sample PDFs for upload. Stop with SIGTERM; it drops its own DB.
Run: cd /app/backend && python tests/chapters_bridge182.py 2400 &
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, upload, complete, drain  # noqa: E402
from chapters_iso182 import headless, layout_b, SRC  # noqa: E402
from tejas import structure  # noqa: E402
import uvicorn  # noqa: E402

OUT = '/tmp/uibridge'


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    files = {'chapters_physics.pdf': Path(SRC).read_bytes(), 'chapters_no_headings.pdf': headless((5, 20)), 'chapters_layout_b.pdf': layout_b()}
    for name, raw in files.items():
        Path(OUT, name).write_bytes(raw)
    own, _ = await mkstaff('owner', 'ui'); rev, _ = await mkstaff('reviewer', 'ui')
    ids = {}
    for name, title in (('chapters_physics.pdf', 'Physics chapter book'), ('chapters_no_headings.pdf', 'Chapters without headings')):
        b = await upload(own, files[name], title, section_id='bitsat:chapters')
        await complete(own, b['id']); await drain(3000); ids[title] = b['id']
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'books': ids}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, ids, flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8770, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ['bridge.json', *files]:
            try: os.unlink(OUT + '/' + name)
            except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
