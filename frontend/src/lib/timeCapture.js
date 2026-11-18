import { post } from './api';

// Time capture for one attempt: on-screen stretches, answer changes and mark toggles.
// Kept in localStorage so a refresh or crash loses nothing; sent along with answer saves and submit.
const MAX = 200;
const keyOf = (user, attempt) => `tejas-time-${user}-${attempt}`;
const round = n => Math.round(n * 10) / 10;
const read = key => {
  try {
    const s = JSON.parse(localStorage.getItem(key) || 'null');
    return s && typeof s.sid === 'string' && Array.isArray(s.events) && Number.isInteger(s.n) ? s : null;
  } catch { return null; }
};

export function createRecorder(userId, attemptId, clock) {
  const key = keyOf(userId, attemptId);
  const s = read(key) || { sid: crypto.randomUUID(), n: 1, events: [], open: null };
  let sent = 0, dead = false;
  const save = () => { if (!dead) try { localStorage.setItem(key, JSON.stringify(s)); } catch {} };
  const push = e => s.events.push({ n: s.n++, ...e });
  const end = at => {
    if (s.open && at - s.open.a >= 0.5) push({ k: 'v', q: s.open.q, a: round(s.open.a), b: round(at) });
    s.open = null;
  };
  if (s.open) end(s.open.last || s.open.a); // after a refresh or crash the stretch ends where it was last seen alive
  const rec = {
    show(q) {
      if ((s.open?.q || null) === (q || null)) return;
      const t = clock();
      end(t);
      if (q) s.open = { q, a: t, last: t };
      save();
    },
    beat() { if (s.open) { s.open.last = clock(); save(); } },
    answer(q, value) {
      const t = round(clock()), v = String(value ?? '').slice(0, 30), last = s.events[s.events.length - 1];
      // Typing a number is one change, not one per key.
      if (last && last.k === 'a' && last.q === q && last.n > sent && t - last.a < 5) { last.v = v; last.a = t; } else push({ k: 'a', q, a: t, v });
      save();
    },
    mark(q, on) { push({ k: 'm', q, a: round(clock()), v: on ? '1' : '0' }); save(); },
    take() {
      if (!s.events.length) return undefined;
      const events = s.events.slice(0, MAX);
      sent = events[events.length - 1].n;
      return { sid: s.sid, events };
    },
    ack(cursor) { if (typeof cursor === 'number') { s.events = s.events.filter(e => e.n > cursor); save(); } },
    pending: () => s.events.length,
    async flush() {
      while (s.events.length) {
        const batch = rec.take();
        const r = await post(`/attempts/${attemptId}/timeline`, batch);
        rec.ack(r.cursor);
        if (!(r.cursor >= batch.events[batch.events.length - 1].n)) break;
      }
    },
    clear() { dead = true; try { localStorage.removeItem(key); } catch {} },
  };
  return rec;
}

// After an auto-submit or a lost connection: whatever time record is left on this device goes up once (the server takes it for 10 minutes).
export async function flushLeftover(userId, attemptId) {
  if (!read(keyOf(userId, attemptId))) return;
  const rec = createRecorder(userId, attemptId, () => 0);
  try { await rec.flush(); rec.clear(); } catch (e) { if (e.status) rec.clear(); }
}
