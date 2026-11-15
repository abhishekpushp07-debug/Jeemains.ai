"""TEST-ONLY iteration 181 browser bridge: the real app on 127.0.0.1:8770 bound to a disposable isolated DB (storage + AI mocked).
Writes /tmp/uibridge/bridge.json (owner + reviewer cookies, 0600) and sample PDFs. No job pump: the app continues uploads by itself.
Run: cd /app/backend && python tests/master_bridge181.py 1800 &   (stop with SIGTERM; it drops its own DB)
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, build_pdf, q3  # noqa: E402
from master_iso181 import single_pdf  # noqa: E402
from tejas import structure  # noqa: E402
import uvicorn  # noqa: E402

OUT = '/tmp/uibridge'


def split_pdfs():
    q = fitz.open(); p = q.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13); y = 100
    for num, text, opts in q3('SPLIT'):
        p.insert_text((40, y), f'Q{num}. {text}', fontsize=11); y += 20
        for lab, o in zip('ABCD', opts): p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
        y += 22
    k = fitz.open(); p = k.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
    for num, ans in [(1, 'B'), (2, 'B'), (3, 'C')]: p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
    return q.tobytes(), k.tobytes()


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    qonly, konly = split_pdfs()
    files = {'single_paper.pdf': single_pdf(), 'questions_only.pdf': qonly, 'answer_key_only.pdf': konly,
             'two_mocks.pdf': build_pdf([{'n': 1, 'qs': q3('B1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('B2'), 'keys': [(1, 'A'), (2, 'B'), (3, 'C')]}])}
    for name, raw in files.items():
        Path(OUT, name).write_bytes(raw)
    own, _ = await mkstaff('owner', 'ui'); rev, _ = await mkstaff('reviewer', 'ui')
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies)}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, flush=True)
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
