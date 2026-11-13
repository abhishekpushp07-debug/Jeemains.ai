import { useSyncExternalStore } from "react";

/** What a round is played on: up to 5 picks, each a whole subject (chapter null) or one chapter. Mirrors backend/scope.py. */
export type Pick = { subject: string; chapter?: string | null };
export type CatalogSubject = { name: string; total: number; chapters: { name: string; count: number }[] };

export const SUBJECTS = ["Physics", "Chemistry", "Mathematics"] as const;
export const MAX_PICKS = 5;
export const PCM: Pick[] = SUBJECTS.map((subject) => ({ subject, chapter: null }));
const SHORT: Record<string, string> = { Physics: "Physics", Chemistry: "Chemistry", Mathematics: "Maths" };
const order = (s: string) => { const i = (SUBJECTS as readonly string[]).indexOf(s); return i < 0 ? 9 : i; };

export const pickKey = (p: Pick) => `${p.subject}:${p.chapter || "*"}`;
export const isWhole = (picks: Pick[], subject: string) => picks.some((p) => p.subject === subject && !p.chapter);
export const isPCM = (picks: Pick[]) => picks.length === 3 && SUBJECTS.every((s) => isWhole(picks, s));

/** One tidy list: no repeats, a whole subject swallows its own chapters, always in the same order. */
export function normalise(picks: Pick[]): Pick[] {
  const whole = new Set(picks.filter((p) => !p.chapter).map((p) => p.subject));
  const seen = new Set<string>(), out: Pick[] = [];
  for (const p of picks) {
    const row = { subject: p.subject, chapter: p.chapter || null };
    if ((row.chapter && whole.has(row.subject)) || seen.has(pickKey(row))) continue;
    seen.add(pickKey(row)); out.push(row);
  }
  return out.sort((a, b) => order(a.subject) - order(b.subject) || (a.chapter || "").localeCompare(b.chapter || ""));
}

/** The same short name the server gives a round: "PCM Mixed", "Mixed Physics + Chemistry", "Optics +2 more". */
export function scopeLabel(picks: Pick[]): string {
  const whole = picks.filter((p) => !p.chapter).map((p) => SHORT[p.subject] || p.subject);
  const chapters = picks.filter((p) => p.chapter).map((p) => p.chapter as string);
  if (!picks.length) return "Pick a subject";
  if (!chapters.length) return whole.length === 3 ? "PCM Mixed" : `Mixed ${whole.join(" + ")}`;
  if (!whole.length) return chapters.length === 1 ? chapters[0] : `${chapters[0]} +${chapters.length - 1} more`;
  return `Mixed ${whole[0]} +${picks.length - 1} more`;
}

/** Cards available for these picks (a whole subject counts all its cards once). */
export function cardCount(picks: Pick[], subjects?: CatalogSubject[]): number {
  return picks.reduce((n, p) => {
    const sub = subjects?.find((s) => s.name === p.subject);
    return n + (p.chapter ? sub?.chapters.find((c) => c.name === p.chapter)?.count || 0 : sub?.total || 0);
  }, 0);
}

/** Subjects that take part, short names, in order ("Physics · Maths"). */
export const scopeSubjects = (picks: Pick[]) => [...new Set(picks.map((p) => p.subject))].sort((a, b) => order(a) - order(b)).map((s) => SHORT[s] || s).join(" · ");

// Picks travel between screens as one route param.
export const encodePicks = (picks: Pick[]) => JSON.stringify(normalise(picks));
export function decodePicks(raw?: string | string[] | null): Pick[] | null {
  try {
    const v = JSON.parse(Array.isArray(raw) ? raw[0] : raw || "");
    const ok = Array.isArray(v) && v.length > 0 && v.length <= MAX_PICKS && v.every((p) => p && (SUBJECTS as readonly string[]).includes(p.subject));
    return ok ? normalise(v) : null;
  } catch { return null; }
}
/** Picks from route params: `picks` first, then the older subject + chapter pair. */
export const picksFrom = (p: { picks?: string; subject?: string; chapter?: string }): Pick[] =>
  decodePicks(p.picks) || [{ subject: p.subject || "Physics", chapter: p.chapter || null }];

// The lobby's choice, shared by every screen that starts a round (Play, Play Friends, Knockout Cup, Gang War).
let current: Pick[] = [{ subject: "Physics", chapter: null }];
const listeners = new Set<() => void>();
export function setScope(picks: Pick[]) { const next = normalise(picks); if (next.length) { current = next; listeners.forEach((f) => f()); } }
export const getScope = () => current;
export const useScope = () => useSyncExternalStore((f) => { listeners.add(f); return () => { listeners.delete(f); }; }, getScope, getScope);
