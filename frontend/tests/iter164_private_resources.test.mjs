// TEST-ONLY iteration 164: Node fault-injection unit tests for frontend/src/lib/privateResources.js + api.js fetchWithSession.
// All fetch responses are MOCKED test data; the app source files are copied unmodified except the import path.
// Run: node /app/frontend/tests/iter164_private_resources.test.mjs
import fs from 'fs'; import path from 'path'; import assert from 'assert/strict';
const SRC = '/app/frontend/src/lib', TMP = '/tmp/fe164';
fs.mkdirSync(TMP, {recursive: true});
globalThis.process.env.REACT_APP_BACKEND_URL = 'https://x.test';
fs.writeFileSync(path.join(TMP, 'api.mjs'), fs.readFileSync(path.join(SRC, 'api.js'), 'utf8'));
fs.writeFileSync(path.join(TMP, 'pr.mjs'), fs.readFileSync(path.join(SRC, 'privateResources.js'), 'utf8').replace("from './api'", "from './api.mjs'"));
const listeners = {}; const events = [];
globalThis.window = {addEventListener: (n, f) => (listeners[n] ||= []).push(f), dispatchEvent: e => {events.push(e.type); (listeners[e.type] || []).forEach(f => f(e));}};
Object.defineProperty(globalThis, 'navigator', {value: {connection: {saveData: false}}, configurable: true, writable: true});
const live = new Set(), revoked = new Set(); let urlN = 0;
URL.createObjectURL = () => {const u = 'blob:' + (++urlN); live.add(u); return u;};
URL.revokeObjectURL = u => {live.delete(u); revoked.add(u);};
// ---- mocked fetch ----
let calls = [], pending = [], inflight = 0, peak = 0, handler;
globalThis.fetch = (url, opts = {}) => {
  calls.push({url, opts}); inflight++; peak = Math.max(peak, inflight);
  return new Promise((res, rej) => {
    const done = () => inflight--;
    const item = {url, opts, resolve: r => {done(); res(r);}, reject: e => {done(); rej(e);}};
    opts.signal?.addEventListener('abort', () => item.reject(new DOMException('aborted', 'AbortError')));
    if (handler) handler(item); else pending.push(item);
  });
};
const img = (size = 1000, status = 200, type = 'image/png') => new Response(status === 200 ? new Uint8Array(size) : 'x', {status, headers: {'Content-Type': status === 200 ? type : 'application/json', 'Retry-After': '2'}});
const tick = (n = 5) => new Promise(r => setTimeout(r, n));
const reset = () => {calls = []; pending = []; peak = 0; handler = null; events.length = 0;};
const api = await import(path.join(TMP, 'api.mjs'));
const P = await import(path.join(TMP, 'pr.mjs'));
const results = []; const t = async (name, fn) => {reset(); try {await fn(); results.push(['PASS', name]);} catch (e) {results.push(['FAIL', name, e.message]);}};

await t('signed-out acquire rejected, no fetch', async () => {P.resetPrivateResources(null); await assert.rejects(P.acquireSourceAsset('/a/0')); assert.equal(calls.length, 0);});
P.resetPrivateResources('A');
await t('same path coalesced, reuse w/o refetch, no-store+credentials', async () => {
  handler = i => i.resolve(img());
  const [a, b] = await Promise.all([P.acquireSourceAsset('/q/1'), P.acquireSourceAsset('/q/1')]);
  assert.equal(calls.length, 1); assert.equal(a.url, b.url); assert.equal(calls[0].opts.cache, 'no-store'); assert.equal(calls[0].opts.credentials, 'include');
  a.release(); b.release(); b.release();
  const c = await P.acquireSourceAsset('/q/1'); assert.equal(calls.length, 1); assert.equal(c.url, a.url); assert.ok(live.has(c.url)); c.release();
});
await t('max 4 in flight, queue drains', async () => {
  const ps = Array.from({length: 10}, (_, i) => P.acquireSourceAsset('/c/' + i)); await tick();
  assert.equal(pending.length, 4);
  while (pending.length || calls.length < 10) {const x = pending.splice(0); x.forEach(i => i.resolve(img(10))); await tick();}
  const out = await Promise.all(ps); assert.equal(calls.length, 10); assert.ok(peak <= 4, 'peak ' + peak); out.forEach(o => o.release());
});
await t('network failures + error responses release queue slots; error readable; manual retry refetches', async () => {
  let n = 0; handler = i => (n++ % 2 ? i.reject(new TypeError('net')) : i.resolve(img(0, 503)));
  const rs = await Promise.allSettled(Array.from({length: 8}, (_, i) => P.acquireSourceAsset('/e/' + i)));
  assert.ok(rs.every(r => r.status === 'rejected'));
  const busy = rs.map(r => r.reason).find(e => e.status === 503); assert.match(busy.message, /temporarily busy/); assert.equal(busy.retryAfterMs, 2000);
  handler = null; const ps = Array.from({length: 4}, (_, i) => P.acquireSourceAsset('/e2/' + i)); await tick();
  assert.equal(pending.length, 4, 'slots leaked: only ' + pending.length + ' started');
  pending.splice(0).forEach(i => i.resolve(img(10))); (await Promise.all(ps)).forEach(o => o.release());
  handler = i => i.resolve(img(10)); const before = calls.length; const r = await P.acquireSourceAsset('/e/0'); assert.equal(calls.length, before + 1); r.release();
});
await t('non-image content-type rejected and not cached', async () => {
  handler = i => i.resolve(new Response('{}', {status: 200, headers: {'Content-Type': 'application/json'}}));
  await assert.rejects(P.acquireSourceAsset('/ct'), /invalid/); handler = i => i.resolve(img()); const r = await P.acquireSourceAsset('/ct'); assert.equal(calls.length, 2); r.release();
});
await t('A->B switch with active+queued fetches: no stale A data for B, old urls revoked, latest epoch remains', async () => {
  const held = await (handler = i => i.resolve(img()), P.acquireSourceAsset('/held')); handler = null;
  const ps = Array.from({length: 7}, (_, i) => P.acquireSourceAsset('/sw/' + i)); await tick();
  const startedA = calls.length;
  P.resetPrivateResources('B');
  assert.ok(!live.has(held.url), 'active A url not revoked on switch');
  pending.splice(0).forEach(i => i.resolve(img()));  // aborted already; late resolves ignored
  const rs = await Promise.allSettled(ps); await tick();
  assert.ok(rs.every(r => r.status === 'rejected' && r.reason.name === 'AbortError'), JSON.stringify(rs.map(r => r.status)));
  assert.equal(calls.length, startedA, 'queued A fetches must not hit network after switch');
  held.release(); held.release();
  handler = i => i.resolve(img()); const b = await P.acquireSourceAsset('/sw/0'); assert.equal(calls.length, startedA + 1, 'B must refetch'); assert.ok(live.has(b.url)); b.release();
  const q = Array.from({length: 5}, (_, i) => P.acquireSourceAsset('/sw2/' + i)); (await Promise.all(q)).forEach(o => o.release()); // slots not leaked
});
await t('logout reset revokes all; acquire after logout rejected', async () => {
  handler = i => i.resolve(img()); const a = await P.acquireSourceAsset('/lo'); P.resetPrivateResources(null);
  assert.ok(!live.has(a.url)); await assert.rejects(P.acquireSourceAsset('/lo')); a.release(); P.resetPrivateResources('B');
});
await t('12MiB LRU: unpinned evicted oldest-first, pinned kept, oversized active entry revoked on release', async () => {
  P.resetPrivateResources('B'); handler = i => i.resolve(img(i.url.includes('big') ? 13 * 1024 * 1024 : 3 * 1024 * 1024));
  const pin = await P.acquireSourceAsset('/l/0'); const urls = [];
  for (let i = 1; i <= 4; i++) {const r = await P.acquireSourceAsset('/l/' + i); urls.push(r.url); r.release();}
  assert.ok(live.has(pin.url), 'pinned evicted'); assert.ok(!live.has(urls[0]), 'LRU oldest not evicted'); assert.ok(live.has(urls[3]));
  const big = await P.acquireSourceAsset('/big'); assert.ok(live.has(big.url) && live.has(pin.url), 'active oversize/pinned revoked while in use');
  big.release(); assert.ok(!live.has(big.url), 'oversized not evicted after release'); pin.release();
});
await t('reload:true retires and refetches', async () => {
  handler = i => i.resolve(img()); const a = await P.acquireSourceAsset('/rl'); a.release(); const n = calls.length;
  const b = await P.acquireSourceAsset('/rl', {reload: true}); assert.equal(calls.length, n + 1); assert.ok(!live.has(a.url)); b.release();
});
await t('prefetch max 2, SaveData skips', async () => {
  handler = i => i.resolve(img(10)); P.prefetchSourceAssets(['/p/1', '/p/2', '/p/3']); await tick(20); assert.equal(calls.length, 2);
  navigator.connection.saveData = true; P.prefetchSourceAssets(['/p/9']); await tick(); assert.equal(calls.length, 2); navigator.connection.saveData = false;
});
await t('startedAttempt handoff: one-use, same user+id, active, 5s TTL', async () => {
  P.resetPrivateResources('B'); const att = {id: 'x', status: 'active', server_now: 100};
  P.rememberStartedAttempt('B', att); assert.equal(P.takeStartedAttempt('B', 'y'), null); assert.equal(P.takeStartedAttempt('B', 'x'), null, 'mismatch must consume');
  P.rememberStartedAttempt('B', att); const got = P.takeStartedAttempt('B', 'x'); assert.equal(got.id, 'x'); assert.ok(got.server_now >= 100); assert.equal(P.takeStartedAttempt('B', 'x'), null);
  P.rememberStartedAttempt('A', att); assert.equal(P.takeStartedAttempt('A', 'x'), null);
  P.rememberStartedAttempt('B', {...att, status: 'completed'}); assert.equal(P.takeStartedAttempt('B', 'x'), null);
  P.rememberStartedAttempt('B', att); P.resetPrivateResources('A'); P.resetPrivateResources('B'); assert.equal(P.takeStartedAttempt('B', 'x'), null);
  const realNow = performance.now.bind(performance); P.rememberStartedAttempt('B', att); const t0 = realNow(); performance.now = () => t0 + 5001;
  assert.equal(P.takeStartedAttempt('B', 'x'), null); performance.now = realNow;
});
// ---- fetchWithSession ----
const refreshes = () => calls.filter(c => c.url.endsWith('/auth/refresh')).length;
await t('simultaneous 401 JSON/image/download: one refresh, one bounded retry each', async () => {
  let ok = false; handler = i => i.url.endsWith('/auth/refresh') ? setTimeout(() => {ok = true; i.resolve(new Response('{}', {status: 200}));}, 10) : i.resolve(ok ? img() : new Response('{}', {status: 401}));
  const rs = await Promise.all([api.fetchWithSession('/attempts/1'), api.fetchWithSession('/attempts/1/questions/q/asset/question/0'), api.fetchWithSession('/reports/x.pdf'), api.api('/sets').catch(e => e)]);
  assert.equal(refreshes(), 1); assert.equal(calls.length, 1 + 4 * 2); assert.ok(rs.slice(0, 3).every(r => r.status === 200));
});
await t('staggered 401 after refresh completed: no second refresh', async () => {
  let ok = false, gate; handler = i => {
    if (i.url.endsWith('/auth/refresh')) {ok = true; return i.resolve(new Response('{}', {status: 200}));}
    if (i.url.endsWith('/slow') && !gate) {gate = i; return;}
    i.resolve(ok ? img() : new Response('{}', {status: 401}));
  };
  const slow = api.fetchWithSession('/slow'); await tick();
  const r1 = await api.fetchWithSession('/fast'); assert.equal(r1.status, 200);
  gate.resolve(new Response('{}', {status: 401})); const r2 = await slow; assert.equal(r2.status, 200); assert.equal(refreshes(), 1);
});
await t('failed refresh: no loop, single retry bound, session-lost dispatched, resources reset', async () => {
  P.resetPrivateResources('B'); handler = i => i.resolve(img()); const held = await P.acquireSourceAsset('/sl'); calls = [];
  handler = i => i.resolve(new Response('{}', {status: 401}));
  const rs = await Promise.all([api.fetchWithSession('/a'), api.fetchWithSession('/b')]);
  assert.ok(rs.every(r => r.status === 401)); assert.equal(refreshes(), 1); assert.ok(calls.length <= 3, 'calls ' + calls.length);
  assert.ok(events.includes('tejas-session-lost')); assert.ok(!live.has(held.url)); held.release();
});
for (const st of [403, 429, 503]) await t(`${st} does NOT refresh`, async () => {handler = i => i.resolve(new Response('{}', {status: st})); const r = await api.fetchWithSession('/z'); assert.equal(r.status, st); assert.equal(refreshes(), 0); assert.equal(calls.length, 1);});
await t('image decode/invalid body does not refresh', async () => {P.resetPrivateResources('B'); handler = i => i.resolve(new Response('notpng', {status: 200, headers: {'Content-Type': 'text/html'}})); await assert.rejects(P.acquireSourceAsset('/dec')); assert.equal(refreshes(), 0);});
await t('abort preserved through api(); no refresh', async () => {
  handler = null; const c = new AbortController(); const p = api.api('/sets', {signal: c.signal}); await tick(); c.abort();
  await assert.rejects(p, e => e.name === 'AbortError'); assert.equal(refreshes(), 0);
});
await t('network failure via api() gives readable message', async () => {handler = i => i.reject(new TypeError('Failed to fetch')); await assert.rejects(api.api('/sets'), /Connection interrupted/);});
await t('studio GET limit 3 retained', async () => {
  handler = null; const ps = Array.from({length: 6}, (_, i) => api.fetchWithSession('/studio/x' + i)); await tick();
  assert.equal(pending.length, 3); while (calls.length < 6 || pending.length) {pending.splice(0).forEach(i => i.resolve(new Response('{}', {status: 200}))); await tick();} await Promise.all(ps);
});
results.forEach(r => console.log(r.join(' | ')));
const fails = results.filter(r => r[0] === 'FAIL').length; console.log(`TOTAL ${results.length} FAIL ${fails}`); process.exit(fails ? 1 : 0);
