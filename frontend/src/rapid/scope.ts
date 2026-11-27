import { useSyncExternalStore } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

/** What a round is played on: picks, each a whole subject (chapter null) or one chapter. Mirrors backend/scope.py. */
export type Pick = { subject: string; chapter?: string | null };
export type CatalogSubject = { name: string; total: number; chapters: { name: string; count: number }[] };

export const SUBJECTS = ["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning"] as const;
/** BITSAT's two extra sections live in the same arena (cards follow the BITSAT 2026 syllabus). */
export const BITSAT_SUBJECTS = ["English", "Logical Reasoning"] as const;
export const isBitsat = (s?: string) => (BITSAT_SUBJECTS as readonly string[]).includes(s || "");
/** Up to 5 picks a list is named and carried exactly as before chapters could be ticked freely (27 Nov 2026). */
export const CLASSIC_PICKS = 5;
/** A ceiling on one request (the bank has 110 chapters), not a rule of the game. The same number as the server's. */
export const MAX_PICKS = 150;
export const PCM: Pick[] = SUBJECTS.slice(0, 3).map((subject) => ({ subject, chapter: null }));
export const SHORT: Record<string, string> = { Physics: "Physics", Chemistry: "Chemistry", Mathematics: "Maths", English: "English", "Logical Reasoning": "Reasoning" };
const order = (s: string) => { const i = (SUBJECTS as readonly string[]).indexOf(s); return i < 0 ? 9 : i; };

export const pickKey = (p: Pick) => `${p.subject}:${p.chapter || "*"}`;
export const isWhole = (picks: Pick[], subject: string) => picks.some((p) => p.subject === subject && !p.chapter);
export const isPCM = (picks: Pick[]) => picks.length === 3 && PCM.every((s) => isWhole(picks, s.subject));

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

/** The same short name the server gives a round: "PCM Mixed", "Mixed Physics + Chemistry", "Optics +2 more", "33 chapters · Physics + Chemistry". */
export function scopeLabel(picks: Pick[]): string {
  const whole = picks.filter((p) => !p.chapter).map((p) => SHORT[p.subject] || p.subject);
  const chapters = picks.filter((p) => p.chapter).map((p) => p.chapter as string);
  if (!picks.length) return "Pick a subject";
  if (!chapters.length) return isPCM(picks) ? "PCM Mixed" : `Mixed ${whole.join(" + ")}`;
  if (!whole.length && chapters.length > CLASSIC_PICKS) {
    const names = [...new Set(normalise(picks).map((p) => SHORT[p.subject] || p.subject))];
    return `${chapters.length} chapters · ${names.join("+") === "Physics+Chemistry+Maths" ? "PCM" : names.join(" + ")}`;
  }
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

// ---- Ticking chapters in the picker. A subject whose every chapter is ticked is kept as one whole subject. ----
/** The chapters of a subject that have cards. */
const playable = (s?: CatalogSubject) => (s?.chapters || []).filter((c) => c.count > 0).map((c) => c.name);
/** The ticked chapters of one subject, by name. */
export const tickedOf = (picks: Pick[], s: CatalogSubject) =>
  isWhole(picks, s.name) ? playable(s) : picks.filter((p) => p.subject === s.name && p.chapter).map((p) => p.chapter as string);
/** Is every chapter of this subject ticked? */
export const allTicked = (picks: Pick[], s: CatalogSubject) => { const all = playable(s), on = tickedOf(picks, s); return all.length > 0 && all.every((c) => on.includes(c)); };

/** Ticks or unticks one chapter. Unticking one chapter of a whole subject leaves all its other chapters ticked. */
export function tickChapter(picks: Pick[], s: CatalogSubject, chapter: string): Pick[] {
  const now = tickedOf(picks, s), next = now.includes(chapter) ? now.filter((c) => c !== chapter) : [...now, chapter];
  const all = playable(s), whole = all.length > 0 && all.every((c) => next.includes(c));
  return normalise([...picks.filter((p) => p.subject !== s.name), ...(whole ? [{ subject: s.name, chapter: null }] : next.map((c) => ({ subject: s.name, chapter: c })))]);
}

/** Select all (`on`) or Clear for these subjects. The other subjects keep their ticks. */
export const tickAll = (picks: Pick[], subjects: CatalogSubject[], on: boolean): Pick[] =>
  normalise([...picks.filter((p) => !subjects.some((s) => s.name === p.subject)), ...(on ? subjects.filter((s) => playable(s).length).map((s) => ({ subject: s.name, chapter: null })) : [])]);

/**
 * The list a round is started on.
 * Whole subjects alone go as they are: each subject gets an even share ("PCM Mixed" is 10 + 10 + 10 of 30 cards).
 * Once any chapter is ticked on its own, every ticked chapter gets an even share, so a whole subject goes as its chapters.
 */
export function picksToPlay(picks: Pick[], subjects: CatalogSubject[]): Pick[] {
  const tidy = normalise(subjects.reduce((list, s) => (!isWhole(list, s.name) && allTicked(list, s) ? [...list.filter((p) => p.subject !== s.name), { subject: s.name, chapter: null }] : list), picks));
  if (!tidy.some((p) => p.chapter) || !tidy.some((p) => !p.chapter)) return tidy;
  return normalise(tidy.flatMap((p) => {
    const all = p.chapter ? [] : playable(subjects.find((s) => s.name === p.subject));
    return all.length ? all.map((chapter) => ({ subject: p.subject, chapter })) : [p];
  }));
}

/** Subjects that take part, short names, in order ("Physics · Maths"). */
export const scopeSubjects = (picks: Pick[]) => [...new Set(picks.map((p) => p.subject))].sort((a, b) => order(a) - order(b)).map((s) => SHORT[s] || s).join(" · ");

// Picks travel between screens as one route param. A long list (many chapters ticked one by one) travels grouped by subject,
// {"Physics":["Optics","Waves"],"Chemistry":0}, a third of the size; a list of up to 5 travels as it always did.
export const encodePicks = (picks: Pick[]) => {
  const list = normalise(picks);
  if (list.length <= CLASSIC_PICKS) return JSON.stringify(list);
  const by: Record<string, string[] | 0> = {};
  for (const p of list) { if (!p.chapter) by[p.subject] = 0; else ((by[p.subject] ||= []) as string[]).push(p.chapter); }
  return JSON.stringify(by);
};
export function decodePicks(raw?: string | string[] | null): Pick[] | null {
  try {
    const got = JSON.parse(Array.isArray(raw) ? raw[0] : raw || "");
    const v = Array.isArray(got) || !got || typeof got !== "object" ? got
      : Object.entries(got).flatMap(([subject, c]) => (Array.isArray(c) ? c.map((chapter) => ({ subject, chapter })) : [{ subject, chapter: null }]));
    const ok = Array.isArray(v) && v.length > 0 && v.length <= MAX_PICKS && v.every((p) => p && (SUBJECTS as readonly string[]).includes(p.subject));
    return ok ? normalise(v) : null;
  } catch { return null; }
}
/** Picks from route params: `picks` first, then the older subject + chapter pair. */
export const picksFrom = (p: { picks?: string; subject?: string; chapter?: string }): Pick[] =>
  decodePicks(p.picks) || [{ subject: p.subject || "Physics", chapter: p.chapter || null }];

// The lobby's choice, shared by every screen that starts a round (Play, Play Friends, Knockout Cup, Gang War).
// Nothing is picked until the student picks: every new app session starts with no subject.
let current: Pick[] = [];
const listeners = new Set<() => void>();
export function setScope(picks: Pick[]) { const next = normalise(picks); if (next.length) { current = next; listeners.forEach((f) => f()); } }
export const getScope = () => current;
export const useScope = () => useSyncExternalStore((f) => { listeners.add(f); return () => { listeners.delete(f); }; }, getScope, getScope);

// Cards in one round (rule R2: 30, 50 or 100). One choice for the lobby and the battleground sheet, kept on the phone.
export const CARD_COUNTS = [30, 50, 100] as const;
export type CardCount = (typeof CARD_COUNTS)[number];
export const CARD_SECONDS = 20;
const COUNT_KEY = "rf.cardCount.v1";
let count: CardCount = 30;
const countListeners = new Set<() => void>();
AsyncStorage.getItem(COUNT_KEY).then((v) => { const n = Number(v); if ((CARD_COUNTS as readonly number[]).includes(n) && n !== count) { count = n as CardCount; countListeners.forEach((f) => f()); } }).catch(() => {});
export function setCardCount(n: CardCount) { if (n === count) return; count = n; countListeners.forEach((f) => f()); AsyncStorage.setItem(COUNT_KEY, String(n)).catch(() => {}); }
export const getCardCount = () => count;
export const useCardCount = () => useSyncExternalStore((f) => { countListeners.add(f); return () => { countListeners.delete(f); }; }, getCardCount, getCardCount);
/** The round size actually dealt: the chosen count, or the largest one these picks have enough unique cards for (0 = not even 30). */
export const fitCount = (chosen: number, available: number) => [...CARD_COUNTS].reverse().find((n) => n <= chosen && n <= available) || 0;
/** "100 cards · 33 min" — how long a full round takes at 20 s a card. */
export const roundLength = (n: number) => `${Math.ceil((n * CARD_SECONDS) / 60)} min`;
