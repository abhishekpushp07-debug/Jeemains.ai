"""OPERATIONAL (owner-approved, 2026-11-21): upload the owner's boxed chemistry book to the PREVIEW app as the owner, exactly as Master does,
and time upload -> Draft. Nothing goes Live. Reads ADMIN_EMAIL / ADMIN_PASSWORD from backend/.env; never prints them.
Run: cd /app/backend && python tests/preview_upload211.py list
     cd /app/backend && python tests/preview_upload211.py upload <chapter_section_id>
     cd /app/backend && python tests/preview_upload211.py status <book_id>
"""
import hashlib, json, math, os, sys, time
from pathlib import Path
import httpx
from dotenv import dotenv_values

ENV = dotenv_values(Path(__file__).resolve().parents[1] / '.env')
BASE = 'http://127.0.0.1:8001'
PDF = '/root/pdfengine/chemistry_chapterwise.pdf'


def data(r):
    d = r.json()
    return d['data'] if isinstance(d, dict) and 'data' in d and 'meta' in d else d


def owner():
    c = httpx.Client(base_url=BASE, timeout=300, headers={'Origin': ENV['FRONTEND_URL'].rstrip('/')})
    r = c.post('/api/auth/login', json={'email': ENV['ADMIN_EMAIL'], 'password': ENV['ADMIN_PASSWORD']})
    assert r.status_code == 200, (r.status_code, r.text[:200])
    # The session cookies are marked secure; on the server's own address they are sent by hand.
    c.headers['Cookie'] = '; '.join(f'{k}={v}' for k, v in c.cookies.items()); c.cookies.clear()
    return c


def summary(c, bid):
    b = data(c.get(f'/api/admin/books/{bid}'))
    rows = [(m['label'], (m.get('chapter') or {}).get('title', '')[:30], m['state'], m.get('cut_summary'), len(m.get('issues') or [])) for m in b.get('mocks', [])]
    return b['state'], b.get('read_pages'), b.get('pages'), b.get('message'), rows


def main():
    c = owner()
    try:
        run(c)
    finally:
        c.post('/api/auth/logout')


def run(c):
    if sys.argv[1] == 'list':
        for e in data(c.get('/api/admin/catalog'))['items']:
            print(e['slug'], e['name'], [(s['id'], s['name'], s['layout'], s.get('kind')) for s in e['sections']])
    elif sys.argv[1] == 'upload':
        raw = open(PDF, 'rb').read(); sha = hashlib.sha256(raw).hexdigest(); t0 = time.time()
        r = c.post('/api/admin/books', json={'filename': 'chemistry_chapterwise.pdf', 'title': 'Chemistry chapter-wise (boxed) — engine test', 'sha256': sha,
                                             'size': len(raw), 'rights_confirmed': True, 'section_id': sys.argv[2], 'subject': 'Chemistry'})
        assert r.status_code == 200, r.text[:400]
        b = data(r); ch = b['chunk_size']
        for n in range(math.ceil(len(raw) / ch)):
            part = raw[n * ch:(n + 1) * ch]
            pr = c.put(f"/api/admin/books/{b['id']}/parts/{n}", params={'sha256': hashlib.sha256(part).hexdigest()}, content=part, headers={'content-type': 'application/octet-stream'})
            assert pr.status_code == 200, pr.text[:300]
        t1 = time.time(); r = c.post(f"/api/admin/books/{b['id']}/complete"); print('BOOK', b['id'], 'upload', round(t1 - t0, 1), 's complete', r.status_code, flush=True)
        last = None
        while True:
            state, read, pages, msg, rows = summary(c, b['id'])
            if (state, read) != last:
                print(f'{time.time() - t1:7.1f}s {state} {read}/{pages} {msg}', flush=True); last = (state, read)
            if state not in ('received', 'reading', 'matching', 'uploading'):
                break
            time.sleep(3)
        print('DRAFT after', round(time.time() - t1, 1), 's')
        for row in rows:
            print('  ', row)
    else:
        state, read, pages, msg, rows = summary(c, sys.argv[2]); print(state, read, pages, msg)
        for row in rows:
            print('  ', row)


if __name__ == '__main__':
    main()
