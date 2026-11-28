// Misfire Mock made by jeelive.ai (Pocket 2, 28 Nov 2026). Open only while the website's Student Choice switch (door A,
// GET /api/choice/bank, read by our server) says "misfire": true. The website picks the questions from the student's own
// open Misfire and makes an ordinary paper (door C, POST /choice/papers, mode "misfire"); from there it is a paper like
// any other: its page, timer, autosave, result and Analysis, in the app and on jeelive.ai alike, and in My Tests.
// Switch off (or not said): nothing of this is shown anywhere. Offline Misfire (./mock) is a different thing, the phone's.
// The shapes below are the ones proposed to the website (Pocket 3 settles them with its reply).
import { api } from "@/src/api/client";
import { useBank } from "@/src/choice/parts";
import { Counts, SUBJECTS, Subject, makePaper } from "@/src/choice/api";
import { Paper, misfireKey } from "./api";

/** `on`: true / false once the switch is known, undefined while it is read. `minutes`: what a question of each subject
 *  brings on the website (door A), for the time shown before the paper is made. */
export function useWebMisfire(uid?: string): { on: boolean | undefined; minutes?: Record<Subject, number> } {
  const bank = useBank(uid);
  if (!uid) return { on: false };
  if (bank.data) return { on: bank.data.misfire === true, minutes: bank.data.ready ? bank.data.minutes : undefined };
  return { on: bank.error ? false : undefined };
}

/** A Misfire Mock as the website's paper history lists it. */
export type WebMock = Paper & { status?: string; resumable?: boolean; count?: number };
export const webMocksKey = (uid: string) => `${misfireKey(uid)}.web`;
/** The student's Misfire Mocks, newest first: the website's JEE Main paper history of kind "misfire". */
export async function loadWebMocks(page: number, signal?: AbortSignal): Promise<{ items: WebMock[]; pages: number }> {
  const d = await api<any>(`/exam-navigation/jee-main/history?kind=misfire&page=${page}`, { signal });
  return { items: (d?.items || []).filter((a: any) => typeof a?.id === "string" && a.id), pages: d?.pages || 1 };
}

/** Asks jeelive.ai for the paper: how many of each subject, and the chapters (by their Misfire names) where the student
 *  ticked only some. `key`: the same for every retry of this one ask, so it is never made twice. Gives the set id. */
export function askWebMock(counts: Counts, picked: Record<Subject, string[] | null>, key: string): Promise<string> {
  const chapters = Object.fromEntries(SUBJECTS.filter((s) => counts[s] > 0 && picked[s] !== null).map((s) => [s, picked[s]!]));
  return makePaper({ mode: "misfire", counts: { Physics: counts.Physics, Chemistry: counts.Chemistry, Mathematics: counts.Mathematics },
    ...(Object.keys(chapters).length ? { chapters } : {}) }, key);
}

/** How many of a finished Misfire Mock's questions went to "Samajh gaya", as its result says; null when it does not say. */
export function understoodOf(r: any): { understood: number; total: number | null } | null {
  const m = r?.misfire, n = m?.understood;
  if (typeof n !== "number" || !Number.isInteger(n) || n < 0) return null;
  const total = typeof m.total === "number" && Number.isInteger(m.total) && m.total >= n ? m.total : null;
  return { understood: n, total };
}
