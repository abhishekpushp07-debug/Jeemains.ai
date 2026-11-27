// Finished papers kept on the phone: the result (questions, the student's answers, the key, the written solutions) and
// its pictures. A kept paper opens at once on a weak line, and without a line through the offline door (./door.tsx).
//
// What the app can do by itself, and no more: only papers the student has FINISHED are kept. A paper not yet attempted
// is given by the website only after Start (which starts its clock), so it is never fetched here.
//
// Where it is kept: beside the pictures, in the account's own encrypted store (src/assets/deviceCache): at most 512 MB
// in all, the oldest-used copy gives way first, and signing out removes everything.
//
// How it is fetched (`keepResults`): after a confirmed session, quietly, a few papers per run (the owner's switch
// `keep`, backend/app_switches.py; 0 = off), one paper every few seconds, JEE Main first, then BITSAT, then the rest,
// newest first. Pictures come only in the website's parts of 12 (src/assets/paperPack.ts `keepResultPictures`), never
// one by one. A paper already kept is not fetched again; papers are kept only while they fit in 80 % of the room, so
// an old paper is never thrown out and fetched back in turns.
import { useSyncExternalStore } from "react";
import { api, apiRaw, appSwitches, getAssetAccount, onAssetScopeReset } from "@/src/api/client";
import { ARENA } from "@/src/arenaMode";
import { pictureKeys } from "@/src/assets/assetGrants";
import { keptTexts, readKeptText, saveKeptText, savedImages } from "@/src/assets/deviceCache/cache";
import { DISK_BUDGET } from "@/src/assets/deviceCache/types";
import { keepResultPictures } from "@/src/assets/paperPack";
import { originalLook } from "@/src/assets/pieces";

export type KeptRow = {
  id: string; set_id?: string; title: string; exam: string; kind?: string; submitted_at?: number; version?: number;
  score?: number; maximum?: number; correct?: number; incorrect?: number; skipped?: number; count?: number;
  /** Pictures of the paper, how many of them are on the phone, and about how much room the paper takes. */
  pictures: number; kept: number; bytes: number; at: number;
  /** The keys of a few of its pictures (the first ones: the first to give way when the phone is full). A run looks
   *  whether they are still here, and counts the paper again when one is not. */
  probe?: string[];
  /** The website's AI step-by-step solutions of this paper: how many are ready of all, when they were last asked for,
   *  and the room their copy takes. They are made over time, so a paper with some not ready is asked again later. */
  ai?: { ready: number; total: number; at: number; bytes: number };
};
const probeOf = (keys: { contentKey: string }[]) => [...new Set([0, 1, Math.floor(keys.length / 2), keys.length - 1].filter((i) => i >= 0 && i < keys.length))].map((i) => keys[i].contentKey);
type Index = { v: 1; rows: KeptRow[]; listed: number };
type Listed = { id: string; set_id?: string; title?: string; exam?: string; status?: string; submitted_at?: number; version?: number; result_available?: boolean; resumable?: boolean };

const INDEX = "results.index", docOf = (id: string) => `result.${id}`, aiOf = (id: string) => `ai.${id}`;
const ROOM = DISK_BUDGET * 0.8;      // the rest stays free for the paper being read or written right now
const ESTIMATE = 12 * 1024 * 1024;   // a paper not fetched yet is counted as this much
const PER_PICTURE = 50 * 1024;       // a picture that was already on the phone is counted as this much
const RUN_GAP = 15 * 60 * 1000, PAPER_GAP = 4000, PAGE_GAP = 800, MAX_PAGES = 6, TRY_AGAIN = 6 * 3600 * 1000, AI_AGAIN = 12 * 3600 * 1000;
const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const rank = (exam?: string) => (/jee/i.test(exam || "") ? 0 : /bitsat/i.test(exam || "") ? 1 : 2);
/** Nothing more to fetch for this paper now: every picture is here, or what is missing was tried within the last 6 hours. */
const settled = (row?: KeptRow) => !!row && (row.kept >= row.pictures || Date.now() - row.at < TRY_AGAIN);
/** Its AI solutions are worth asking for again: never asked, or some were not ready (or not answered) 12 hours ago. */
const aiDue = (row: KeptRow) => !row.ai || (row.ai.ready < row.ai.total && Date.now() - row.ai.at > AI_AGAIN);

let running: Promise<void> | null = null, lastRun = 0, held = false, stop: (() => void) | null = null;
let rows: KeptRow[] | null = null, owner: string | null = null;
const listeners = new Set<() => void>();
const publish = (next: KeptRow[] | null, uid: string | null) => { rows = next; owner = uid; listeners.forEach((f) => f()); };
// Another account, or signed out: nothing of the last one is shown. The store of the account that follows is opened a
// moment later; whoever is showing the list then gets that account's.
onAssetScopeReset(() => { publish(null, null); setTimeout(() => { if (listeners.size) void keptResults(); }, 0); });

async function readIndex(): Promise<Index> {
  try {
    const got = JSON.parse((await readKeptText(INDEX)) || "null");
    if (got?.v === 1 && Array.isArray(got.rows)) return { v: 1, rows: got.rows.filter((r: any) => r && typeof r.id === "string" && typeof r.title === "string"), listed: Number(got.listed) || 0 };
  } catch { /* an unreadable list is an empty list: it is built again */ }
  return { v: 1, rows: [], listed: 0 };
}
async function writeIndex(next: KeptRow[], uid: string) {
  if (getAssetAccount() !== uid) return;
  await saveKeptText(INDEX, JSON.stringify({ v: 1, rows: next, listed: Date.now() }));
  publish(next, uid);
}

/** The papers this phone keeps for the account whose store is open (signed in, or let in by the offline door). */
export async function keptResults(): Promise<KeptRow[]> {
  const uid = getAssetAccount();
  if (!uid) return [];
  if (rows && owner === uid) return rows;
  const index = await readIndex();
  if (getAssetAccount() === uid) publish(index.rows, uid);
  return index.rows;
}
const none: KeptRow[] = [];
export const useKeptResults = () => useSyncExternalStore((f) => { listeners.add(f); void keptResults(); return () => { listeners.delete(f); }; }, () => rows || none, () => none);

/** A kept paper's result, as the website gave it (PYQ papers in their original look). Null: not on this phone. */
export async function keptResult(id: string): Promise<any | null> {
  try {
    const got = JSON.parse((await readKeptText(docOf(id))) || "null");
    return got?.v === 1 && got.data?.summary && Array.isArray(got.data.questions) ? originalLook(got.data) : null;
  } catch { return null; }
}

/** While a paper is being attempted, or a Rapid Fire round is being played, nothing is fetched in the background: the
 *  line and the phone belong to it. Checked before every paper and before every part of 12 pictures. */
export const holdKeeping = (on: boolean) => { held = on; };
export const keepingHeld = () => held;
/** Ends the run now (the phone's background time is over): what came is kept, the rest waits for the next run. */
export const stopKeeping = () => { stop?.(); };

// ---- The website's AI step-by-step solutions (GET /attempts/{id}/ai-solutions, the call the result screen makes) ----
const aiItems = (data: any): any[] | null => (data && Array.isArray(data.items) ? data.items.filter((x: any) => x && typeof x.question_id === "string") : null);
const readyOf = (items: any[]) => items.filter((x) => x.state === "ready" && x.solution).length;
type AiKept = NonNullable<KeptRow["ai"]>;
/** Keeps the copy when at least one solution is ready (pending ones are nothing to read). */
async function saveAi(id: string, data: any, before?: AiKept): Promise<AiKept | undefined> {
  const items = aiItems(data);
  if (!items) return before ? { ...before, at: Date.now() } : undefined;
  const ready = readyOf(items), text = ready ? JSON.stringify({ v: 1, at: Date.now(), data: { items, disclosure: data.disclosure } }) : "";
  if (ready && !(await saveKeptText(aiOf(id), text))) return before ? { ...before, at: Date.now() } : undefined;
  // The website's own count of the paper's solutions when it gives one (it may send fewer items than that).
  return { ready, total: Math.max(items.length, Number(data.total) || 0), at: Date.now(), bytes: ready ? text.length : before?.bytes || 0 };
}
async function keepAi(id: string, signal: AbortSignal, before?: AiKept): Promise<AiKept> {
  const data = await api<any>(`/attempts/${encodeURIComponent(id)}/ai-solutions`, { signal }).catch(() => null);
  // Not answered: asked again after 12 hours (counted as one not ready).
  return (data && (await saveAi(id, data, before))) || (before ? { ...before, at: Date.now() } : { ready: 0, total: 1, at: Date.now(), bytes: 0 });
}
/** A kept paper's AI solutions that were ready when they were kept: `items` by question, as the website gave them. */
export async function keptAi(id: string): Promise<{ items: any[]; disclosure?: string } | null> {
  try {
    const got = JSON.parse((await readKeptText(aiOf(id))) || "null");
    const items = got?.v === 1 ? aiItems(got.data) : null;
    return items ? { items, disclosure: typeof got.data.disclosure === "string" ? got.data.disclosure : undefined } : null;
  } catch { return null; }
}
/** The result screen has just read a kept paper's AI solutions: the phone's copy follows, with no call of its own. */
export async function keepAiCopy(id: string, data: any): Promise<void> {
  try {
    const uid = getAssetAccount();
    if (ARENA || !uid || running || !aiItems(data)) return;
    const have = await keptResults(), row = have.find((r) => r.id === id);
    if (!row || getAssetAccount() !== uid || running || (row.ai && row.ai.ready >= readyOf(aiItems(data)!) && row.ai.total === Math.max(aiItems(data)!.length, Number(data.total) || 0))) return;
    const ai = await saveAi(id, data, row.ai);
    if (!ai || getAssetAccount() !== uid || running) return;
    await writeIndex(have.map((r) => (r.id === id ? { ...r, ai, bytes: r.bytes - (r.ai?.bytes || 0) + ai.bytes } : r)), uid);
  } catch { /* keeping a copy is never the result screen's trouble */ }
}

async function finished(signal: AbortSignal): Promise<Listed[] | null> {
  const out: Listed[] = [];
  for (let page = 1, pages = 1; page <= pages && page <= MAX_PAGES; page++) {
    // per_page=100: one page when the website honours it (asked in our note of 27 Nov); 12 a page as before when not.
    const d = await api<{ items?: Listed[]; pages?: number }>("/my/tests?" + new URLSearchParams({ tab: "completed", page: String(page), q: "", status: "all", exam: "", per_page: "100" }), { signal });
    if (!d || !Array.isArray(d.items)) return null;
    pages = Number(d.pages) || 1;
    // Finished only (the same reading as the Tests tab and PYQ): never a paper that can still be resumed.
    out.push(...d.items.filter((t) => t && typeof t.id === "string" && t.id && !t.resumable && t.result_available !== false
      && (t.status === "completed" || t.status === "expired" || t.result_available === true)));
    if (page < pages) await pause(PAGE_GAP);
  }
  return out.sort((a, b) => rank(a.exam) - rank(b.exam) || (Number(b.submitted_at) || 0) - (Number(a.submitted_at) || 0));
}

async function keepOne(t: Listed, signal: AbortSignal, hold: () => Promise<void>): Promise<KeptRow | null> {
  const res = await apiRaw<any>(`/attempts/${encodeURIComponent(t.id)}/results?score_version=original`, { signal });
  const data = res.data;
  if (res.status !== 200 || !data?.summary || data.status === "embargoed" || !Array.isArray(data.questions)) return null;
  const text = JSON.stringify({ v: 1, at: Date.now(), data });
  if (!(await saveKeptText(docOf(t.id), text))) return null;
  const ai = await keepAi(t.id, signal);
  const questions = originalLook(data).questions as any[], step = Number((appSwitches() as any)?.pictures) || 0;
  const keys = questions.flatMap((q) => pictureKeys(t.id, q, true));
  let kept = 0, bytes = 0;
  // The website's parts only (never one by one): every row must carry its asset_revision, and the owner's switch must allow solution parts.
  if (keys.length && step >= 4 && questions.every((q) => typeof q.asset_revision === "string" && q.asset_revision)) {
    const got = await keepResultPictures(t.id, questions, step >= 5, signal, hold);
    kept = got?.kept || 0; bytes = got?.bytes || 0;
  } else if (keys.length) kept = (await savedImages(keys.map((k) => k.contentKey)))?.filter(Boolean).length || 0;
  const s = data.summary;
  return { id: t.id, set_id: data.set_id || t.set_id, title: String(data.title || t.title || "Result"), exam: String(data.exam || t.exam || ""), kind: data.test_kind || undefined,
    submitted_at: Number(data.submitted_at ?? t.submitted_at) || undefined, version: t.version, score: s.score, maximum: s.maximum, correct: s.correct, incorrect: s.incorrect, skipped: s.skipped,
    count: Number(data.count) || questions.length, pictures: keys.length, kept, bytes: text.length + Math.max(bytes, kept * PER_PICTURE) + ai.bytes,
    // Some pictures came and then it stopped (the app was put away, the line dropped): the next run goes on. Nothing came
    // at all (the website is not giving this paper's pictures just now): tried again after 6 hours.
    at: kept < keys.length && bytes > 0 ? 0 : Date.now(), probe: probeOf(keys), ai };
}

/** A paper whose pictures were not all here: counted again from the phone (a result opened on screen brings its own
 *  pictures, under the same keys). Nothing is asked of the server. */
async function recount(row: KeptRow): Promise<KeptRow> {
  const data = await keptResult(row.id);
  if (!data) return row;
  const keys = (data.questions as any[]).flatMap((q) => pictureKeys(row.id, q, true));
  const have = await savedImages(keys.map((k) => k.contentKey));
  return have ? { ...row, pictures: keys.length, kept: have.filter(Boolean).length, probe: probeOf(keys) } : row;
}

/**
 * Brings the phone's kept papers up to date. Safe to call often: one run at a time, at most once in 15 minutes
 * (`force` runs now). Trouble of any kind is left for the next run; what is already kept stays.
 */
export function keepResults(uid: string, force = false): Promise<void> {
  if (running) return running;
  const limit = Number((appSwitches() as any)?.keep) || 0;
  if (ARENA || !uid || !limit || getAssetAccount() !== uid || (!force && Date.now() - lastRun < RUN_GAP)) return Promise.resolve();
  lastRun = Date.now();
  const ctl = new AbortController(), forget = onAssetScopeReset(() => ctl.abort());
  stop = () => ctl.abort();
  const mine = () => !ctl.signal.aborted && getAssetAccount() === uid;
  const hold = async () => { while (held && mine()) await pause(5000); };
  running = (async () => {
    const old = new Map((await readIndex()).rows.map((r) => [r.id, r]));
    // A kept result that gave way to newer things (the 512 MB limit) is not counted as kept: it is fetched again in its turn.
    const names = [...old.keys()], here = await keptTexts(names.map(docOf));
    if (here) names.forEach((id, i) => { if (!here[i]) old.delete(id); });
    // The same for pictures: a paper said to be whole whose first pictures are no longer here is counted again below.
    const whole = [...old.values()].filter((r) => r.kept >= r.pictures && r.probe?.length);
    const there = await savedImages(whole.flatMap((r) => r.probe!));
    const doubt = new Set<string>();
    if (there) { let k = 0; for (const r of whole) { const n = r.probe!.length; if (there.slice(k, k + n).some((ok) => !ok)) doubt.add(r.id); k += n; } }
    const listed = await finished(ctl.signal);
    if (!listed || !mine()) return;
    const next: KeptRow[] = [];
    let room = ROOM, fetched = 0, asked = 0;
    for (let i = 0; i < listed.length && mine(); i++) {
      const t = listed[i], was = old.get(t.id);
      const cost = was?.bytes || ESTIMATE;
      if (cost > room) break; // no room for this one or anything older: nothing is thrown out to make it
      // A copy made when the student opened the result (keepOpened) does not know the list's version yet: it is that version.
      let row: KeptRow | undefined = was && (was.version === undefined || was.version === t.version) ? { ...was, version: t.version } : undefined;
      if (row && (row.kept < row.pictures || doubt.has(row.id))) row = await recount(row);
      if (!mine()) return;
      if (!settled(row) && fetched < limit) {
        await hold();
        if (!mine()) return;
        fetched++;
        row = (await keepOne(t, ctl.signal, hold).catch(() => null)) || row;
        if (!mine()) return;
        if (row) await writeIndex([...next, row, ...listed.slice(i + 1).map((x) => old.get(x.id)).filter((r): r is KeptRow => !!r)], uid); // kept so far, should the app be closed now
        await pause(PAPER_GAP);
      } else if (row && aiDue(row) && asked < limit) {
        // A paper already kept: only its AI solutions are asked for again (one small answer, no pictures).
        await hold();
        if (!mine()) return;
        asked++;
        const ai = await keepAi(row.id, ctl.signal, row.ai);
        if (!mine()) return;
        row = { ...row, ai, bytes: row.bytes - (row.ai?.bytes || 0) + ai.bytes };
        await pause(PAGE_GAP);
      }
      if (row) { next.push(row); room -= row.bytes || ESTIMATE; }
    }
    if (mine()) await writeIndex(next, uid);
  })().catch(() => {}).finally(() => { forget(); running = null; stop = null; });
  return running;
}
/**
 * A result the student has just opened (src/api/paperOpening.ts) is kept too: no call is made for it. Its pictures are
 * arriving for the screen itself; the next run counts them and brings whatever is still missing (`at: 0`).
 */
export async function keepOpened(id: string, data: any): Promise<void> {
  try {
    const uid = getAssetAccount();
    if (ARENA || !uid || running || !Number((appSwitches() as any)?.keep) || !data?.summary || !Array.isArray(data.questions)) return;
    const have = await keptResults();
    if (getAssetAccount() !== uid || running || have.some((r) => r.id === id)) return;
    const text = JSON.stringify({ v: 1, at: Date.now(), data });
    if (text.length + have.reduce((n, r) => n + (r.bytes || ESTIMATE), 0) > ROOM) return; // no room: nothing is thrown out for it
    if (!(await saveKeptText(docOf(id), text)) || getAssetAccount() !== uid || running) return;
    const s = data.summary, pictures = (data.questions as any[]).reduce((n, q) => n + pictureKeys(id, q, true).length, 0);
    const row: KeptRow = { id, set_id: data.set_id || undefined, title: String(data.title || "Result"), exam: String(data.exam || ""), kind: data.test_kind || undefined,
      submitted_at: Number(data.submitted_at) || undefined, score: s.score, maximum: s.maximum, correct: s.correct, incorrect: s.incorrect, skipped: s.skipped,
      count: Number(data.count) || data.questions.length, pictures, kept: 0, bytes: text.length + pictures * PER_PICTURE, at: 0 };
    await writeIndex([row, ...(rows && owner === uid ? rows : have).filter((r) => r.id !== id)], uid);
  } catch { /* keeping a copy is never the result screen's trouble */ }
}
