// Dream colleges: up to 5 college + branch per exam (JEE Main, BITSAT, COMEDK), each with the marks it needs, and the
// student's recent full mock scores, so every screen can say "X marks door". Kept with the student's account on our
// server (any phone shows the same list), with a copy per account on the phone for offline use. A phone sends only
// its own changes (merged into the account's list), so it never wipes dreams saved on another device. Signing out
// removes the phone copy (kept only while it holds changes the account does not have yet).
import { useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";
import { api, ApiError, rf } from "@/src/api/client";

export type DreamExam = "jee" | "bitsat" | "comedk";
export const EXAMS: DreamExam[] = ["jee", "bitsat", "comedk"];
export const FULL: Record<DreamExam, number> = { jee: 300, bitsat: 390, comedk: 180 };
/** Questions in a full paper. A test with fewer (a chapter or part test) is not a full mock, whatever its marks. */
export const FULL_QUESTIONS: Record<DreamExam, number> = { jee: 75, bitsat: 130, comedk: 180 };
export const EXAM_NAME: Record<DreamExam, string> = { jee: "JEE Main", bitsat: "BITSAT", comedk: "COMEDK" };
export const MAX_DREAMS = 5;

/** need = marks (out of FULL) for this seat on a normal paper; range = [easy-paper .. tough-paper] where known. */
export type Dream = { id: string; exam: DreamExam; college: string; branch: string; need: number; range?: [number, number]; note: string; at: number };
/** A full mock, its score scaled to the exam's full marks. */
export type Mock = { id: string; exam: DreamExam; score: number; max: number; raw: number; rawMax: number; title: string; at: number };
/** cheered = dreams whose "Dream Unlocked" celebration has played (once per dream college, on any device). */
type State = { dreams: Dream[]; mocks: Mock[]; cheered: string[] };
/** The phone's copy. `dirty` = the dream list was changed here and the account does not have that change yet;
 *  `base` = ids of the account's list those changes were made on; `unsent` = mocks not uploaded yet; `cheerSend` = celebrations not uploaded yet. */
type Saved = State & { dirty?: boolean; base?: string[]; unsent?: string[]; cheerSend?: string[] };

const LEGACY = "dream.v1"; // before dreams moved to the account: one list per phone
const key = (uid: string) => `dream.v2.${uid}`;
const EMPTY: State = { dreams: [], mocks: [], cheered: [] };
const REFRESH_MS = 60000; // coming back to the app reads the account's list again at most once a minute
let state: State = EMPTY;
let owner: string | null = null;
let dirty = false, base: string[] = [], unsent = new Set<string>(), cheerSend = new Set<string>();
let fetchedAt = 0; // when the account's list was last read (0 = not yet since sign-in)
let notice = ""; // set when the account refused a change
let ready: Promise<void> = Promise.resolve();
let queue: Promise<void> = Promise.resolve();
const listeners = new Set<() => void>();
const emit = () => listeners.forEach(f => f());
const subscribe = (f: () => void) => { listeners.add(f); return () => { listeners.delete(f); }; };
const read = () => state;
const readNotice = () => notice;
const byNewest = (a: Mock, b: Mock) => b.at - a.at;
const ids = (list: Dream[]) => list.map(d => d.id);
const sameIds = (a: Dream[], b: Dream[]) => a.length === b.length && a.every(d => b.some(x => x.id === d.id));
/** 400/409/413/422: the server will never accept this as it is, so it is not retried. */
const refused = (e: any) => e instanceof ApiError && [400, 409, 413, 422].includes(e.status);
/** Score on the exam's full-marks scale. A paper worth more than full marks (BITSAT with its 12 bonus questions = 426)
 *  keeps the real score, as cutoffs are absolute marks; a shorter paper is scaled up. */
const scaled = (exam: DreamExam, raw: number, rawMax: number) => Math.round(rawMax >= FULL[exam] ? raw : (raw / rawMax) * FULL[exam]);

function parse(raw: string | null): Saved | null {
  try {
    const got = raw ? JSON.parse(raw) : null;
    return got && Array.isArray(got.dreams) && Array.isArray(got.mocks) ? got : null;
  } catch { return null; }
}
const unionMocks = (...lists: Mock[][]) => {
  const out = new Map<string, Mock>();
  for (const list of lists) for (const m of list) if (!out.has(m.id)) out.set(m.id, { ...m, score: scaled(m.exam, m.raw, m.rawMax) });
  return [...out.values()].sort(byNewest).slice(0, 30);
};
/** `list` plus the dreams of `extra` it does not have yet, within the 5-per-exam limit. */
function addDreams(list: Dream[], extra: Dream[]) {
  const out = [...list];
  for (const d of extra) if (!out.some(x => x.id === d.id) && out.filter(x => x.exam === d.exam).length < MAX_DREAMS) out.push(d);
  return out;
}
/** This phone's changes (made on the account's list `seen`) applied to the account's current list: dreams removed
 *  here go, dreams added here join in free slots, dreams added on other devices stay. Same rule as the server's. */
function mergeDreams(server: Dream[], seen: string[], mine: Dream[]) {
  const had = new Set(seen), here = new Map(mine.map(d => [d.id, d]));
  return addDreams(server.filter(d => !had.has(d.id) || here.has(d.id)).map(d => here.get(d.id) || d), mine.filter(d => !had.has(d.id)));
}
/** Says which dreams added here found no room (that exam already had 5 on the account, from another device). */
function noRoom(seen: string[], mine: Dream[], merged: Dream[]) {
  const had = new Set(seen), lost = mine.filter(d => !had.has(d.id) && !merged.some(x => x.id === d.id));
  return lost.length ? `${lost.map(d => d.college).join(", ")} nahi juda: account mein ${EXAM_NAME[lost[0].exam]} ke ${MAX_DREAMS} dream college pehle se hain. Ek hatao, phir jodo.` : "";
}

function persist() {
  if (!owner) return Promise.resolve();
  const saved: Saved = { ...state, dirty, base, unsent: [...unsent], cheerSend: [...cheerSend] };
  return Promise.resolve(storage.setItem(key(owner), JSON.stringify(saved))).catch(() => {});
}

/** One sync at a time, in order: reads the account's list (first time, or `fresh`), then uploads what changed here.
 *  Never fails: offline or busy, the changes stay on the phone and go up on the next change or when the app opens. */
function sync(uid: string, fresh = false) {
  const run = queue.then(async () => {
    if (owner !== uid) return;
    try {
      if (!fetchedAt || fresh) await pull(uid);
      if (owner === uid && fetchedAt) await send(uid);
    } catch { /* kept for the next try */ }
    if (owner === uid) await persist();
  });
  queue = run;
  return run;
}

/** The account's list, with this phone's pending changes merged on top; mocks from every device are kept. */
async function pull(uid: string) {
  const server = await rf<State>("/dream", uid);
  const filled = !fetchedAt && !server.mocks.length && !state.mocks.length ? await backfill(uid) : [];
  if (owner !== uid) return;
  fetchedAt = Date.now();
  const dreams = dirty ? mergeDreams(server.dreams, base, state.dreams) : server.dreams;
  if (dirty) notice = noRoom(base, state.dreams, dreams) || notice;
  base = ids(server.dreams);
  dirty = !sameIds(dreams, server.dreams);
  const mocks = unionMocks(state.mocks, server.mocks, filled);
  const onServer = new Map(server.mocks.map(m => [m.id, m.score]));
  mocks.forEach(m => { if (onServer.get(m.id) !== m.score) unsent.add(m.id); });
  const cheeredThere = new Set(server.cheered || []);
  state.cheered.forEach(id => { if (!cheeredThere.has(id)) cheerSend.add(id); });
  state = { dreams, mocks, cheered: [...new Set([...cheeredThere, ...state.cheered])] };
  emit();
}

async function send(uid: string) {
  if (dirty) {
    const sent = state.dreams, seen = base;
    try {
      const res = await rf<{ dreams: Dream[] }>("/dream/dreams", uid, { method: "PUT", body: { dreams: sent, base: seen } });
      if (owner !== uid) return;
      // Changes made while this was on its way stay pending on top of the account's new list.
      const dreams = mergeDreams(res.dreams, ids(sent), state.dreams);
      base = ids(res.dreams);
      dirty = !sameIds(dreams, res.dreams);
      notice = noRoom(seen, sent, res.dreams);
      state = { ...state, dreams };
      emit();
    } catch (e) {
      if (!refused(e) || owner !== uid) throw e;
      // Refused (it would be every time): show the account's list again and say so, instead of retrying forever.
      dirty = false; fetchedAt = 0; // offline now? the account's list is read again first thing next time
      notice = "Ye badlav account mein save nahi hua, isliye account wali list wapas dikh rahi hai. Dobara try karo.";
      emit();
      await pull(uid);
    }
  }
  const mocks = state.mocks.filter(m => unsent.has(m.id));
  if (mocks.length) {
    try { await rf("/dream/mocks", uid, { method: "POST", body: { mocks } }); }
    catch (e) { if (!refused(e)) throw e; /* never accepted: stays on this phone only */ }
    if (owner === uid) mocks.forEach(m => unsent.delete(m.id));
  }
  const cheers = [...cheerSend].slice(0, MAX_DREAMS * 3);
  if (cheers.length) {
    try { await rf("/dream/cheered", uid, { method: "POST", body: { ids: cheers } }); }
    catch (e) { if (!refused(e)) throw e; }
    if (owner === uid) cheers.forEach(id => cheerSend.delete(id));
  }
}

/** Full mocks from the student's completed tests list (newest page), for a phone that never opened those results. */
async function backfill(uid: string): Promise<Mock[]> {
  try {
    const d = await api<{ items: any[] }>("/my/tests?" + new URLSearchParams({ tab: "completed", page: "1", q: "", status: "all", exam: "" }).toString());
    return (d?.items || []).flatMap(t => {
      const m = t.result_available && t.summary ? mockOf({ id: t.id, exam: t.exam, score: t.summary.score, maximum: t.summary.maximum, questions: t.count, title: t.title,
        at: typeof t.submitted_at === "number" ? t.submitted_at * 1000 : undefined }) : null;
      return m ? [m] : [];
    });
  } catch { return []; }
}

/** Called by sign-in / sign-out and each time the session is confirmed (app opened again): shows this account's dreams
 *  (phone copy at once, then the account's). `forget` (signing out) also removes the phone copy. */
export function setDreamAccount(uid: string | null, forget = false) {
  if (uid === owner) {
    // Back in the app: pick up changes made on other devices and send what failed before.
    if (uid && Date.now() - fetchedAt > REFRESH_MS) void ready.then(() => sync(uid, true));
    return;
  }
  const gone = owner, pending = dirty || unsent.size > 0 || cheerSend.size > 0;
  owner = uid; state = EMPTY; dirty = false; base = []; unsent = new Set(); cheerSend = new Set(); fetchedAt = 0; notice = ""; emit();
  if (gone && forget && !pending) void storage.removeItem(key(gone));
  if (!uid) { ready = Promise.resolve(); return; }
  ready = (async () => {
    const local = parse(await storage.getItem<string | null>(key(uid), null));
    const legacy = parse(await storage.getItem<string | null>(LEGACY, null));
    if (owner !== uid) return;
    // The old one-list-per-phone dreams join the first account signed in here after the update. They count as added
    // on this phone, so they only fill free slots: the account's own dreams always stay.
    state = { dreams: addDreams(local?.dreams || [], legacy?.dreams || []), mocks: unionMocks(local?.mocks || [], legacy?.mocks || []), cheered: local?.cheered || [] };
    base = local?.base || [];
    dirty = !!local?.dirty || !!legacy?.dreams.length;
    unsent = new Set([...(local?.unsent || []), ...(legacy?.mocks || []).map(m => m.id)]);
    cheerSend = new Set(local?.cheerSend || []);
    emit();
    await persist(); // saved under the account before the old key goes
    if (legacy) await storage.removeItem(LEGACY);
  })();
  void ready.then(() => sync(uid));
}

/** Before signing out: the last changes go up (waits at most 4 s). */
export const flushDreams = () => owner ? Promise.race([sync(owner), new Promise<void>(r => setTimeout(r, 4000))]) : Promise.resolve();

export function useDreams() {
  return useSyncExternalStore(subscribe, read, read);
}

/** A short note when the account refused the last change ("" otherwise). */
export function useDreamNotice() {
  return useSyncExternalStore(subscribe, readNotice, readNotice);
}

function save(next: State, dreamsChanged: boolean) {
  state = next;
  if (dreamsChanged) { dirty = true; notice = ""; }
  emit(); void persist();
  if (owner) void sync(owner);
}

export const dreamsOf = (s: State, exam: DreamExam) => s.dreams.filter(d => d.exam === exam);
/** Newest first. */
export const mocksOf = (s: State, exam: DreamExam) => s.mocks.filter(m => m.exam === exam);

/** Adds the dream (or removes it if already pinned). "full" when that exam already has 5. */
export async function toggleDream(d: Dream): Promise<"added" | "removed" | "full"> {
  await ready;
  if (state.dreams.some(x => x.id === d.id)) { save({ ...state, dreams: state.dreams.filter(x => x.id !== d.id) }, true); return "removed"; }
  if (dreamsOf(state, d.exam).length >= MAX_DREAMS) return "full";
  save({ ...state, dreams: [...state.dreams, d] }, true);
  return "added";
}

export const removeDream = async (id: string) => { await ready; save({ ...state, dreams: state.dreams.filter(x => x.id !== id) }, true); };

/** How long after a mock its celebration can still play: an old result opened much later stays quiet. */
const CHEER_MS = 7 * 86400000;
export type CheerWin = { mock: Mock; dreams: Dream[] };
/** The dreams the newest full mock of `exam` crossed for the first time (a mock taken after the dream was picked),
 *  hardest first. They are marked as celebrated at once, for the account on every device, so the show plays once per
 *  dream college. `mockId`: only when that mock is the newest. Waits for the account's list, so a show already played
 *  on another phone is known. */
export function claimCheer(exam: DreamExam, mockId?: string): CheerWin | null {
  if (!owner || !fetchedAt) return null;
  const m = mocksOf(state, exam)[0];
  if (!m || (mockId && m.id !== mockId) || Date.now() - m.at > CHEER_MS) return null;
  const done = new Set(state.cheered);
  const dreams = dreamsOf(state, exam).filter(d => !done.has(d.id) && d.at <= m.at && m.score >= d.need).sort((a, b) => b.need - a.need);
  if (!dreams.length) return null;
  dreams.forEach(d => cheerSend.add(d.id));
  save({ ...state, cheered: [...state.cheered, ...dreams.map(d => d.id)] }, false);
  return { mock: m, dreams };
}

/** Which dream exam a test belongs to, from the website's exam name ("JEE Main", "BITSAT", "COMEDK"). */
export function examOf(name?: string | null): DreamExam | null {
  const n = (name || "").toLowerCase();
  if (n.includes("bitsat")) return "bitsat";
  if (n.includes("comedk")) return "comedk";
  if (n.includes("jee") && !n.includes("adv")) return "jee";
  return null;
}

type MockIn = { id: string; exam?: string | null; score: number; maximum: number; questions?: number | null; title?: string; at?: number };
/** A full-length paper: the full paper's question count (90% or more) and at least half its marks. Chapter tests never count. */
export function isFullMock(m: { exam?: string | null; maximum: number; questions?: number | null }) {
  const exam = examOf(m.exam);
  return !!exam && !!m.maximum && m.maximum >= FULL[exam] / 2 && Number(m.questions) >= FULL_QUESTIONS[exam] * 0.9;
}
function mockOf(m: MockIn): Mock | null {
  const exam = examOf(m.exam);
  if (!exam || !isFullMock(m)) return null;
  return { id: m.id, exam, score: scaled(exam, m.score, m.maximum), max: FULL[exam], raw: m.score, rawMax: m.maximum, title: m.title || "Mock", at: m.at || Date.now() };
}

/** Remembers a released full mock (see isFullMock), for this account on every device. */
export async function recordMock(m: MockIn) {
  const mock = mockOf(m);
  if (!mock) return;
  await ready;
  if (!owner) return;
  const old = state.mocks.find(x => x.id === m.id);
  if (old && old.score === mock.score && old.raw === mock.raw && old.rawMax === mock.rawMax) return;
  unsent.add(mock.id);
  save({ ...state, mocks: [mock, ...state.mocks.filter(x => x.id !== m.id)].sort(byNewest).slice(0, 30) }, false);
}
