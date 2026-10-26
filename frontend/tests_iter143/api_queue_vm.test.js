// iter143: Node VM controlled-fetch unit tests for src/lib/api.js studio GET gate (max 3), release on error/abort, non-gated paths
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const SRC = fs.readFileSync(__dirname + '/../src/lib/api.js', 'utf8')
  .replace(/process\.env\.REACT_APP_BACKEND_URL/g, '"http://x"')
  .replace(/^export (const|async function|function)/gm, '$1');
function load(fetchImpl) {
  const ctx = { fetch: fetchImpl, setTimeout, console, URL, Response, Headers, FormData, Date, Promise, Error, Number, Array, Object };
  vm.createContext(ctx);
  vm.runInContext(SRC + '\n;globalThis.__api={api,post,put};', ctx);
  return ctx.__api;
}
function controlled() {
  const st = { active: 0, max: 0, calls: [], pending: [] };
  const f = (url, opts) => {
    st.active++; st.max = Math.max(st.max, st.active); st.calls.push({ url, method: (opts && opts.method) || 'GET' });
    return new Promise((res, rej) => {
      let settled = false; const done = (fn) => { if (settled) return; settled = true; st.active--; fn(); };
      if (opts && opts.signal) {
        if (opts.signal.aborted) return done(() => rej(new DOMException('aborted', 'AbortError')));
        opts.signal.addEventListener('abort', () => done(() => rej(new DOMException('aborted', 'AbortError'))));
      }
      st.pending.push({ url, ok: (status = 200, body = { ok: 1 }) => done(() => res(new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } }))), fail: () => done(() => rej(new TypeError('net'))) });
    });
  };
  return { st, f };
}
const tick = () => new Promise(r => setTimeout(r, 5));
const results = [];
async function t(name, fn) { try { await fn(); results.push(['PASS', name]); } catch (e) { results.push(['FAIL', name, e.message]); } }
const STUDIO = ['/studio/sets', '/studio/imports', '/studio/chapter-books', '/studio/mock-books', '/studio/ai-review', '/studio/solve-tests', '/studio/question-report-priorities'];

(async () => {
  await t('7 studio GETs: max inflight 3, all resolve, FIFO drain', async () => {
    const { st, f } = controlled(); const { api } = load(f);
    const ps = STUDIO.map(p => api(p));
    await tick(); assert.strictEqual(st.active, 3); assert.strictEqual(st.calls.length, 3);
    for (let i = 0; i < 7; i++) { await tick(); st.pending.shift().ok(); }
    const r = await Promise.all(ps); assert.strictEqual(r.length, 7); assert.strictEqual(st.max, 3);
    assert.deepStrictEqual(st.calls.map(c => c.url.replace('http://x/api', '')), STUDIO);
  });
  await t('network error releases slot; error message standard; queue drains', async () => {
    const { st, f } = controlled(); const { api } = load(f);
    const ps = STUDIO.map(p => api(p).then(() => 'ok', e => e.message));
    await tick(); st.pending.shift().fail(); st.pending.shift().fail();
    for (let i = 0; i < 5; i++) { await tick(); st.pending.shift().ok(); }
    const r = await Promise.all(ps); assert.strictEqual(st.max, 3);
    assert.ok(r[0].startsWith('Connection interrupted')); assert.strictEqual(r.filter(x => x === 'ok').length, 5);
  });
  await t('503 HTTP response releases slot and carries status/retryAfter', async () => {
    const { st, f } = controlled(); const { api } = load(f);
    const ps = STUDIO.slice(0, 4).map(p => api(p).then(() => 'ok', e => e));
    await tick(); st.pending.shift().ok(503, { error: { message: 'busy', code: 'capacity_busy' } });
    for (let i = 0; i < 3; i++) { await tick(); st.pending.shift().ok(); }
    const r = await Promise.all(ps); assert.strictEqual(r[0].status, 503); assert.strictEqual(r[0].message, 'busy'); assert.strictEqual(st.active, 0);
  });
  await t('abort of queued (not dequeued) request rejects and releases; abort of active request releases', async () => {
    const { st, f } = controlled(); const { api } = load(f);
    const acs = STUDIO.map(() => new AbortController());
    const ps = STUDIO.map((p, i) => api(p, { signal: acs[i].signal }).then(() => 'ok', e => e.message));
    await tick(); acs[5].abort(); acs[0].abort(); // 0 active, 5 queued
    await tick(); assert.ok(st.active <= 3);
    let guard = 0; while (st.pending.length && guard++ < 20) { await tick(); const p = st.pending.shift(); if (p) p.ok(); }
    const r = await Promise.race([Promise.all(ps), new Promise((_, rj) => setTimeout(() => rj(new Error('HUNG queue')), 1000))]);
    assert.ok(r[0].startsWith('Connection interrupted')); assert.ok(r[5].startsWith('Connection interrupted'));
    assert.strictEqual(r.filter(x => x === 'ok').length, 5); assert.strictEqual(st.max, 3);
    // new batch after drain still gets 3 fresh slots (no leak)
    const ps2 = STUDIO.slice(0, 3).map(p => api(p)); await tick(); assert.strictEqual(st.active, 3);
    st.pending.splice(0).forEach(p => p.ok()); await Promise.all(ps2);
  });
  await t('non-studio GET, studio POST/PUT and /auth/refresh not gated while gate full', async () => {
    const { st, f } = controlled(); const { api, post, put } = load(f);
    const ps = STUDIO.map(p => api(p)); await tick(); assert.strictEqual(st.active, 3);
    const extra = [api('/auth/session'), post('/studio/sets', { a: 1 }), put('/studio/sets/1', { a: 1 }), api('/catalog/x'), api('/studio/x', { method: 'DELETE' })];
    await tick(); assert.strictEqual(st.active, 8, 'expected 3 gated + 5 ungated active, got ' + st.active);
    st.pending.splice(3).forEach(p => p.ok()); await Promise.all(extra);
    for (let i = 0; i < 7; i++) { await tick(); st.pending.shift().ok(); } await Promise.all(ps);
  });
  await t('401 on studio GET -> refresh (ungated) -> retry; no deadlock with gate full', async () => {
    const { st, f } = controlled(); const { api } = load(f);
    const ps = STUDIO.map(p => api(p).then(() => 'ok', e => 'E:' + e.message));
    await tick();
    // all three active get 401
    for (let i = 0; i < 3; i++) st.pending.shift().ok(401, { detail: 'expired' });
    let guard = 0;
    while (guard++ < 60) {
      await tick();
      const p = st.pending.shift(); if (!p) { if (st.active === 0) break; continue; }
      p.ok();
    }
    const r = await Promise.race([Promise.all(ps), new Promise((_, rj) => setTimeout(() => rj(new Error('DEADLOCK')), 1500))]);
    assert.strictEqual(r.filter(x => x === 'ok').length, 7, JSON.stringify(r));
    const refreshes = st.calls.filter(c => c.url.endsWith('/auth/refresh')).length;
    assert.ok(refreshes >= 1 && refreshes <= 3, 'refreshes=' + refreshes);
    assert.ok(st.max <= 4, 'max=' + st.max + ' (3 gated + at most 1 refresh)');
  });
  results.forEach(r => console.log(r.join(' | ')));
  const fails = results.filter(r => r[0] === 'FAIL').length;
  console.log(`TOTAL ${results.length - fails}/${results.length}`); process.exit(fails ? 1 : 0);
})();
