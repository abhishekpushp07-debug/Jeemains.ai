// Misfire Mock made by jeelive.ai (Pocket 2, 28 Nov 2026). Open only while the website's Student Choice switch (door A,
// GET /api/choice/bank, read by our server) says "misfire": true. The website picks the questions from the student's own
// open Misfire and makes an ordinary paper (door C, POST /choice/papers, mode "misfire"); from there it is a paper like
// any other: its page, timer, autosave, result and Analysis, in the app and on jeelive.ai alike, and in My Tests.
// Switch off (or not said): nothing of this is shown anywhere. Offline Misfire (./mock) is a different thing, the phone's.
// The shapes are the contract the website agreed on 28 Nov 2026 (memory/WEBSITE_MISFIRE_MOCK_NOTE.md, part 6).
import { api } from "@/src/api/client";
import { useBank } from "@/src/choice/parts";
import { Counts, SUBJECTS, Subject, askPaper } from "@/src/choice/api";
import { Paper, misfireKey } from "./api";

/** `on`: true / false once the switch is known, undefined while it is read. `minutes`: what a question of each subject
 *  brings on the website (door A), for the time shown before the paper is made. */
export function useWebMisfire(uid?: string): { on: boolean | undefined; minutes?: Record<Subject, number> } {
  const bank = useBank(uid);
  if (!uid) return { on: false };
  if (bank.data) return { on: bank.data.misfire === true, minutes: bank.data.ready ? bank.data.minutes : undefined };
  return { on: bank.error ? false : undefined };
}

const count = (n: unknown) => (typeof n === "number" && Number.isInteger(n) && n >= 0 ? n : null);
/** How many questions: the website says it per subject ({"Physics": 5, "Chemistry": 3, "Mathematics": 0}); a plain
 *  number is read as it is. null when it says neither. */
const many = (n: unknown) => {
  if (n && typeof n === "object" && !Array.isArray(n)) {
    const each = SUBJECTS.map((s) => count((n as Record<string, unknown>)[s]));
    return each.some((v) => v != null) ? each.reduce<number>((sum, v) => sum + (v || 0), 0) : null;
  }
  return count(n);
};
const unix = (n: unknown) => (typeof n === "number" && Number.isFinite(n) && n > 0 ? n : undefined);

/** One Misfire Mock of the student's (GET /my/misfire/mocks): made, maybe started (`attempt` = its newest attempt). */
export type WebMock = {
  set_id: string; title: string; created_at?: number; given: number | null; minutes: number | null;
  attempt: { id: string; resumable: boolean; started_at?: number; submitted_at?: number; summary: Paper["summary"] | null } | null;
};
export const webMocksKey = (uid: string) => `${misfireKey(uid)}.web`;
const mockName = (n: unknown) => (typeof n === "number" && Number.isInteger(n) && n > 0 ? `Misfire Mock #${n}` : typeof n === "string" && n.trim() ? n.trim().slice(0, 60) : "Misfire Mock");
/** The student's Misfire Mocks, newest first, 20 a page, those not started too. */
export async function loadWebMocks(page: number, signal?: AbortSignal): Promise<{ items: WebMock[]; pages: number }> {
  const d = await api<any>(`/my/misfire/mocks?page=${page}`, { signal });
  const items: WebMock[] = [];
  for (const m of d?.items || []) {
    if (typeof m?.set_id !== "string" || !/^[A-Za-z0-9_-]{6,80}$/.test(m.set_id)) continue;
    const a = m.attempt && typeof m.attempt.id === "string" && m.attempt.id ? m.attempt : null;
    items.push({
      set_id: m.set_id, title: typeof m.title === "string" && m.title.trim() ? m.title.trim().slice(0, 120) : mockName(m.number),
      created_at: unix(m.created_at), given: many(m.given) ?? many(m.asked), minutes: count(m.minutes),
      attempt: a && { id: a.id, resumable: a.resumable === true, started_at: unix(a.started_at), submitted_at: unix(a.submitted_at), summary: a.summary && typeof a.summary === "object" ? a.summary : null },
    });
  }
  return { items, pages: count(d?.pages) || 1 };
}
/** Where a Misfire Mock opens: not started, its page; being taken, the paper; else its result. */
export const webMockPath = (m: WebMock) => (!m.attempt ? `/set/${m.set_id}` : m.attempt.resumable && !m.attempt.summary ? `/attempt/${m.attempt.id}` : `/result/${m.attempt.id}`);

/** Asks jeelive.ai for the paper: how many of each subject, and the chapters (by their Misfire names) where the student
 *  ticked only some. `key`: the same for every retry of this one ask, so it is never made twice. Gives the set id, and
 *  how many questions were asked and given (null when the website does not say). */
export async function askWebMock(counts: Counts, picked: Record<Subject, string[] | null>, key: string): Promise<{ setId: string; asked: number | null; given: number | null }> {
  const chapters = Object.fromEntries(SUBJECTS.filter((s) => counts[s] > 0 && picked[s] !== null).map((s) => [s, picked[s]!]));
  const made = await askPaper({ mode: "misfire", counts: { Physics: counts.Physics, Chemistry: counts.Chemistry, Mathematics: counts.Mathematics },
    ...(Object.keys(chapters).length ? { chapters } : {}) }, key);
  return { setId: made.set_id, asked: many(made.asked), given: many(made.given) };
}

/** How many of a finished Misfire Mock's questions went to "Samajh gaya", as its result says; null when it does not say
 *  (a retry of wrong questions changes nothing in Misfire, and its result has no `misfire`). */
export function understoodOf(r: any): { understood: number; total: number | null } | null {
  const m = r?.misfire, n = m?.understood;
  if (typeof n !== "number" || !Number.isInteger(n) || n < 0) return null;
  const total = typeof m.total === "number" && Number.isInteger(m.total) && m.total >= n ? m.total : null;
  return { understood: n, total };
}
