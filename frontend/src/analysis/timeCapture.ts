// Time capture for one attempt, in the website's own format: on-screen stretches, answer changes and mark toggles.
// Kept on the phone so a crash or a closed app loses nothing; sent along with answer saves and with submit.
import { post, uuid } from "@/src/api/client";
import { storage } from "@/src/utils/storage";

type Event = { n: number; k: "v" | "a" | "m"; q: string; a: number; b?: number; v?: string };
type Stored = { sid: string; n: number; events: Event[]; open: { q: string; a: number; last: number } | null };
export type TimeBatch = { sid: string; events: Event[] };

const MAX = 200; // the server takes at most 200 events in one request
const keyOf = (user: string, attempt: string) => `time.${user}.${attempt}`;
const round = (n: number) => Math.round(n * 10) / 10;

async function read(key: string): Promise<Stored | null> {
  const raw = await storage.getItem<string | null>(key, null);
  if (!raw) return null;
  try {
    const s = JSON.parse(raw);
    return s && typeof s.sid === "string" && Array.isArray(s.events) && Number.isInteger(s.n) ? s : null;
  } catch { return null; }
}

/** `clock` gives the server's time in seconds (the same clock the paper's timer runs on). */
export async function createRecorder(userId: string, attemptId: string, clock: () => number) {
  const key = keyOf(userId, attemptId);
  const s: Stored = (await read(key)) || { sid: uuid(), n: 1, events: [], open: null };
  let sent = 0, dead = false;
  const save = () => { if (!dead) void storage.setItem(key, JSON.stringify(s)); };
  const push = (e: Omit<Event, "n">) => { s.events.push({ n: s.n++, ...e }); };
  const end = (at: number) => {
    if (s.open && at - s.open.a >= 0.5) push({ k: "v", q: s.open.q, a: round(s.open.a), b: round(at) });
    s.open = null;
  };
  if (s.open) end(s.open.last || s.open.a); // after a crash the stretch ends where it was last seen alive
  const rec = {
    /** The question now on screen; null when no question is visible (app in the background, paper closed). */
    show(q: string | null) {
      if ((s.open?.q || null) === (q || null)) return;
      const t = clock();
      end(t);
      if (q) s.open = { q, a: t, last: t };
      save();
    },
    beat() { if (s.open) { s.open.last = clock(); save(); } },
    answer(q: string, value: string) {
      const t = round(clock()), v = String(value ?? "").slice(0, 30), last = s.events[s.events.length - 1];
      // Typing a number is one change, not one per key.
      if (last && last.k === "a" && last.q === q && last.n > sent && t - last.a < 5) { last.v = v; last.a = t; } else push({ k: "a", q, a: t, v });
      save();
    },
    mark(q: string, on: boolean) { push({ k: "m", q, a: round(clock()), v: on ? "1" : "0" }); save(); },
    take(): TimeBatch | undefined {
      if (!s.events.length) return undefined;
      const events = s.events.slice(0, MAX);
      sent = events[events.length - 1].n;
      return { sid: s.sid, events };
    },
    ack(cursor?: number | null) { if (typeof cursor === "number") { s.events = s.events.filter(e => e.n > cursor); save(); } },
    pending: () => s.events.length,
    async flush() {
      while (s.events.length) {
        const batch = rec.take()!;
        const r = await post<{ cursor: number }>(`/attempts/${attemptId}/timeline`, batch);
        rec.ack(r?.cursor);
        if (!(r?.cursor >= batch.events[batch.events.length - 1].n)) break;
      }
    },
    clear() { dead = true; void storage.removeItem(key); },
  };
  return rec;
}
export type Recorder = Awaited<ReturnType<typeof createRecorder>>;

/** After an auto-submit or a lost connection: the time record still on this phone goes up once (the server takes it for 10 minutes). */
export async function flushLeftover(userId: string, attemptId: string) {
  if (!(await read(keyOf(userId, attemptId)))) return;
  const rec = await createRecorder(userId, attemptId, () => 0);
  try { await rec.flush(); rec.clear(); } catch (e: any) { if (e?.status) rec.clear(); }
}
