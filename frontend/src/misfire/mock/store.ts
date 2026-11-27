// Misfire Mocks: a JEE Main-style mock made on the phone from the student's own open Misfire questions (the wrong or
// left ones of papers already finished and marked). Everything a mock needs came with those papers' results: the
// question, its key and its solution. So it is made, taken and marked on the phone, and only the right answers go to
// the website, to move those questions to "Samajh gaya" (./marking.ts).
//
// Where it is kept: in the account's own encrypted store beside the kept papers (src/assets/deviceCache), so signing
// out removes it. A mock is two documents: its questions (written once) and its state (answers, clock, result), which
// is small and is what every answer rewrites. The list of mocks is a third document.
import { useEffect, useState, useSyncExternalStore } from "react";
import { getAssetAccount, onAssetScopeReset } from "@/src/api/client";
import { readKeptText, saveKeptText } from "@/src/assets/deviceCache/cache";
import type { Counts, Subject } from "@/src/choice/api";

export type MockQ = {
  /** The question's own id (a mock never holds the same question twice). */
  id: string;
  misfire_id: string; attempt_id: string; number: number; subject: Subject; chapter: string; exam: string;
  /** The paper it came from and its number there. */
  source: string; source_number: number;
  type: string; text?: string; options?: Record<string, string>; typed_options?: Record<string, string> | null; pieces?: any[] | null;
  render_mode?: string; source_option_labels?: Record<string, string> | null; accessible_text?: string; asset_count?: number;
  /** The picture's revision, so a copy the phone already keeps for that paper is used (src/assets/assetGrants.ts). */
  asset_revision?: unknown; source_revision?: unknown; source_ref?: unknown;
  solution?: string; solution_kind?: string; solution_asset_count?: number;
  answer: string; accepted: string[]; numeric: string;
};
export type Answer = { value: string; marked?: boolean };
export type Outcome = "correct" | "incorrect" | "skipped";
export type SubjectScore = { name: Subject; count: number; score: number; maximum: number; correct: number; incorrect: number; skipped: number };
export type Marked = {
  score: number; maximum: number; correct: number; incorrect: number; skipped: number; accuracy: number | null; used: number;
  subjects: SubjectScore[]; outcomes: Record<string, Outcome>;
};
/** The right answers on their way to the website: `todo` still to go, `moved` now "Samajh gaya", `refused` the
 *  website did not take as right (they count as wrong), `gone` no longer in Misfire. Question ids. */
export type Sync = { todo: string[]; moved: string[]; refused: string[]; gone: string[] };
export type MockState = {
  status: "ready" | "active" | "done"; started_at?: number; deadline?: number; submitted_at?: number;
  answers: Record<string, Answer>; visited: string[]; result?: Marked; sync?: Sync;
};
export type MockPaper = { v: 1; id: string; uid: string; n: number; title: string; made_at: number; exam: string; counts: Counts; asked?: Counts; minutes: number; questions: MockQ[] };
export type Mock = MockPaper & MockState;
export type MockRow = {
  id: string; n: number; title: string; exam: string; made_at: number; count: number; minutes: number; counts: Counts;
  status: MockState["status"]; started_at?: number; deadline?: number; submitted_at?: number;
  score?: number; maximum?: number; correct?: number; incorrect?: number; skipped?: number; accuracy?: number | null; waiting?: number;
};

export const MARKS = { correct: 4, wrong: -1 };
/** A mock is over when it is submitted or its clock has run out (it is then marked the next time it is opened). */
export const mockOver = (m: { status: MockState["status"]; deadline?: number }) => m.status === "done" || (m.status === "active" && !!m.deadline && m.deadline <= Date.now());
const MAX_KEPT = 40;
const INDEX = "mf.mocks", paperDoc = (id: string) => `mf.mock.${id}`, stateDoc = (id: string) => `mf.mock.${id}.state`;

let owner: string | null = null, rows: MockRow[] | null = null, loading: Promise<MockRow[]> | null = null, version = 0;
const mocks = new Map<string, Mock>();
const listeners = new Set<() => void>();
const changed = () => { version++; listeners.forEach((f) => f()); };
onAssetScopeReset(() => { owner = null; rows = null; loading = null; mocks.clear(); changed(); });

// One write after another: a later answer never lands before an earlier one.
let chain: Promise<unknown> = Promise.resolve();
const queued = (work: () => Promise<unknown>) => { chain = chain.then(work, work); return chain; };

const read = async <T>(name: string): Promise<T | null> => { try { return JSON.parse((await readKeptText(name)) || "null"); } catch { return null; } };

export function rowOf(m: Mock): MockRow {
  const r = m.result;
  return {
    id: m.id, n: m.n, title: m.title, exam: m.exam, made_at: m.made_at, count: m.questions.length, minutes: m.minutes, counts: m.counts,
    status: m.status, started_at: m.started_at, deadline: m.deadline, submitted_at: m.submitted_at,
    ...(r ? { score: r.score, maximum: r.maximum, correct: r.correct, incorrect: r.incorrect, skipped: r.skipped, accuracy: r.accuracy } : {}),
    waiting: m.sync?.todo.length || 0,
  };
}
const stateOf = (m: Mock): MockState => ({ status: m.status, started_at: m.started_at, deadline: m.deadline, submitted_at: m.submitted_at, answers: m.answers, visited: m.visited, result: m.result, sync: m.sync });

/** This account's mocks, newest first (an empty list until its store is open). */
export function loadMocks(): Promise<MockRow[]> {
  const uid = getAssetAccount();
  if (!uid) return Promise.resolve([]);
  if (rows && owner === uid) return Promise.resolve(rows);
  if (loading && owner === uid) return loading;
  owner = uid;
  loading = (async () => {
    const got = await read<{ v: 1; rows: MockRow[] }>(INDEX);
    const list = got?.v === 1 && Array.isArray(got.rows) ? got.rows.filter((r) => r && typeof r.id === "string") : [];
    if (getAssetAccount() === uid) { rows = list; changed(); }
    return list;
  })().finally(() => { loading = null; });
  return loading;
}

/** The mocks list, redrawn whenever a mock changes. */
export function useMocks(): MockRow[] {
  useSyncExternalStore((f) => { listeners.add(f); void loadMocks(); return () => { listeners.delete(f); }; }, () => version, () => version);
  return (owner === getAssetAccount() && rows) || NONE;
}
const NONE: MockRow[] = [];

export async function getMock(id: string): Promise<Mock | null> {
  const uid = getAssetAccount();
  if (!uid) return null;
  const known = mocks.get(id);
  if (known && known.uid === uid) return known;
  const [paper, state] = await Promise.all([read<MockPaper>(paperDoc(id)), read<MockState>(stateDoc(id))]);
  if (!paper || paper.v !== 1 || paper.uid !== uid || !Array.isArray(paper.questions) || !state?.status || getAssetAccount() !== uid) return null;
  const mock: Mock = { ...paper, ...state, answers: state.answers || {}, visited: state.visited || [] };
  mocks.set(id, mock);
  return mock;
}

/** One mock, redrawn whenever it changes. `missing`: not on this phone (any more). */
export function useMock(id?: string): { mock: Mock | null; missing: boolean } {
  const v = useSyncExternalStore((f) => { listeners.add(f); return () => { listeners.delete(f); }; }, () => version, () => version);
  const [got, setGot] = useState<{ id?: string; mock: Mock | null; missing: boolean }>({ mock: null, missing: false });
  useEffect(() => {
    let live = true;
    if (id) void getMock(id).then((m) => { if (live) setGot({ id, mock: m, missing: !m }); });
    return () => { live = false; };
  }, [id, v]);
  return got.id === id ? { mock: got.mock, missing: got.missing } : { mock: null, missing: false };
}

async function writeIndex(uid: string) {
  if (getAssetAccount() !== uid || !rows) return;
  await saveKeptText(INDEX, JSON.stringify({ v: 1, rows }));
}

/** A new mock: its questions once, its state, and its row at the top of the list (the oldest beyond 40 give way). */
export async function addMock(m: Mock): Promise<void> {
  await loadMocks();
  mocks.set(m.id, m);
  rows = [rowOf(m), ...(rows || []).filter((r) => r.id !== m.id)];
  const dropped = rows.slice(MAX_KEPT);
  rows = rows.slice(0, MAX_KEPT);
  dropped.forEach((r) => mocks.delete(r.id));
  changed();
  const { status, started_at, deadline, submitted_at, answers, visited, result, sync, ...paper } = m;
  await queued(async () => {
    await saveKeptText(paperDoc(m.id), JSON.stringify(paper));
    await saveKeptText(stateDoc(m.id), JSON.stringify(stateOf(m)));
    for (const r of dropped) { await saveKeptText(paperDoc(r.id), "null"); await saveKeptText(stateDoc(r.id), "null"); }
    await writeIndex(m.uid);
  });
}

/** Changes a mock's state (answers, clock, result): kept in memory at once, written right after. */
export function saveState(m: Mock, patch: Partial<MockState>): Mock {
  const next: Mock = { ...m, ...patch };
  mocks.set(m.id, next);
  if (rows) rows = rows.map((r) => (r.id === m.id ? rowOf(next) : r));
  changed();
  void queued(async () => {
    await saveKeptText(stateDoc(m.id), JSON.stringify(stateOf(next)));
    if (patch.status || patch.result || patch.sync || patch.started_at) await writeIndex(m.uid);
  });
  return next;
}

/** The newest state of a mock this session knows (a screen's copy may be a moment old). */
export const latest = (m: Mock) => mocks.get(m.id) || m;

export async function removeMock(id: string): Promise<void> {
  const uid = getAssetAccount();
  await loadMocks();
  if (!uid || !rows) return;
  rows = rows.filter((r) => r.id !== id);
  mocks.delete(id);
  changed();
  await queued(async () => { await saveKeptText(paperDoc(id), "null"); await saveKeptText(stateDoc(id), "null"); await writeIndex(uid); });
}

/** The next mock's serial number for this account. */
export const nextNumber = () => Math.max(0, ...(rows || []).map((r) => r.n || 0)) + 1;
