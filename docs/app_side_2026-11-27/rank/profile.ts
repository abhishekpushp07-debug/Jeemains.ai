// "Meri details" (top of the Rank tab): the student's score and category, typed once. Saving it writes those values into
// every Rank tool's saved form as that tool's starting values. After that each tool is edited on its own: the edit stays
// in that tool and the profile is not touched, until the student saves the profile again.
import { useEffect, useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";
import type { Category, CutoffExam, Level, ScoreKind } from "./api";

export type RankProfile = {
  at: number; // when it was last saved; 0 = never
  jee: { marks: string; pct: string; rank: string; level: Level; category: Category; female: boolean; pwd: boolean; state: string | null };
  comedk: { marks: string; rank: string };
  bitsat: { score: string };
};
export const EMPTY_PROFILE: RankProfile = {
  at: 0, jee: { marks: "", pct: "", rank: "", level: "normal", category: "GEN", female: false, pwd: false, state: null },
  comedk: { marks: "", rank: "" }, bitsat: { score: "" },
};

/** Where the profile and each Rank tool's form live on the phone. */
export const SAVED = {
  profile: "rank.profile.v1", estimate: "rank.estimate.v1", cutoff: "rank.cutoff.v1", target: "rank.target.v1",
  college: "rank.form.v1", bitsat: "rank.bitsat.v1", comedk: "rank.comedk.v1",
} as const;

type Rule = { min: number; max: number; label: string; hint: string; bad: string; len: number; decimal?: boolean; signed?: boolean };
/** Every score a Rank tool accepts, per exam: its limits, field label and the line shown when it is wrong. */
export const SCORE: Record<CutoffExam, Partial<Record<ScoreKind, Rule>>> = {
  jee: {
    marks: { min: -75, max: 300, label: "Marks / 300", hint: "e.g. 180", len: 4, signed: true, bad: "JEE Main marks −75 se 300 ke beech poore ank mein daalo." },
    percentile: { min: 0, max: 100, label: "Percentile", hint: "e.g. 97.4", len: 10, decimal: true, bad: "Percentile 0 se 100 ke beech daalo." },
    rank: { min: 1, max: 2000000, label: "Rank (CRL)", hint: "e.g. 12000", len: 7, bad: "JEE Main rank 1 se 20,00,000 ke beech poore ank mein daalo." },
  },
  comedk: {
    marks: { min: 0, max: 180, label: "Marks / 180", hint: "e.g. 110", len: 3, bad: "COMEDK marks 0 se 180 ke beech poore ank mein daalo." },
    rank: { min: 1, max: 200000, label: "COMEDK rank", hint: "e.g. 4500", len: 6, bad: "COMEDK rank 1 se 2,00,000 ke beech poore ank mein daalo." },
  },
  bitsat: {
    marks: { min: -130, max: 390, label: "Score / 390", hint: "e.g. 280", len: 4, signed: true, bad: "BITSAT score −130 se 390 ke beech poore ank mein daalo." },
  },
};

/** Typed text -> the number, null when the box is empty, or the line saying what to fix. */
export function readScore(exam: CutoffExam, kind: ScoreKind, text: string): number | string | null {
  const rule = SCORE[exam][kind], v = text.trim();
  if (!rule || !v) return null;
  const n = Number(v);
  return (rule.decimal ? Number.isFinite(n) : Number.isInteger(n)) && n >= rule.min && n <= rule.max ? n : rule.bad;
}

// `saves` counts profile saves since the app opened: a tool re-reads its saved form each time it goes up.
let state: { profile: RankProfile; saves: number } = { profile: EMPTY_PROFILE, saves: 0 };
let loaded = false;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach(f => f());
const subscribe = (f: () => void) => { listeners.add(f); return () => { listeners.delete(f); }; };
const read = () => state;

async function load() {
  loaded = true;
  const raw = await storage.getItem<string | null>(SAVED.profile, null);
  if (!raw || state.saves) return;
  try {
    const p = JSON.parse(raw);
    state = { ...state, profile: { at: Number(p.at) || 0, jee: { ...EMPTY_PROFILE.jee, ...p.jee }, comedk: { ...EMPTY_PROFILE.comedk, ...p.comedk }, bitsat: { ...EMPTY_PROFILE.bitsat, ...p.bitsat } } };
    emit();
  } catch { /* start empty */ }
}

export function useRankProfile() {
  useEffect(() => { if (!loaded) load(); }, []);
  return useSyncExternalStore(subscribe, read, read).profile;
}
export const useProfileSaves = () => useSyncExternalStore(subscribe, read, read).saves;

async function patch(key: string, change: (old: Record<string, any>) => Record<string, any>) {
  const raw = await storage.getItem<string | null>(key, null);
  let old: Record<string, any> = {};
  try { const v = raw ? JSON.parse(raw) : null; if (v && typeof v === "object") old = v; } catch { /* start fresh */ }
  await storage.setItem(key, JSON.stringify(change(old)));
}

/** Saves the profile and fills every tool's saved form with it. A score the profile leaves empty does not wipe the
 *  tool's own; when several JEE scores are given the Cut off tool starts from the most exact (rank, percentile, marks). */
export async function saveProfile(p: Omit<RankProfile, "at">) {
  const profile: RankProfile = { ...p, at: Date.now() };
  const j = p.jee, c = p.comedk, b = p.bitsat.score;
  const who = { category: j.category, female: j.female, pwd: j.pwd, state: j.state };
  const jee = !!(j.marks || j.pct || j.rank), comedk = !!(c.marks || c.rank);
  const start = (old: object | undefined, kind: ScoreKind, text: string) => ({ ...old, kind, text, score: null });
  await Promise.all([
    storage.setItem(SAVED.profile, JSON.stringify(profile)),
    patch(SAVED.estimate, o => ({ ...o, level: j.level, category: j.category, pwd: j.pwd, ...(j.marks ? { jee: j.marks } : {}), ...(c.marks ? { comedk: c.marks } : {}) })),
    patch(SAVED.cutoff, o => ({
      ...o, ...who, level: j.level,
      ...(jee ? { jee: start(o.jee, j.rank ? "rank" : j.pct ? "percentile" : "marks", j.rank || j.pct || j.marks) } : {}),
      ...(comedk ? { comedk: start(o.comedk, c.rank ? "rank" : "marks", c.rank || c.marks) } : {}),
      ...(b ? { bitsat: start(o.bitsat, "marks", b) } : {}),
    })),
    patch(SAVED.target, o => ({ ...o, ...who })),
    patch(SAVED.college, o => ({ ...o, ...who, level: j.level, ...(jee ? { marks: j.marks, pct: j.pct, rank: j.rank } : {}) })),
    comedk ? patch(SAVED.comedk, o => ({ ...o, marks: c.marks, rank: c.rank })) : null,
    b ? storage.setItem(SAVED.bitsat, b) : null,
  ]);
  state = { profile, saves: state.saves + 1 };
  emit();
}

/** Forgets the profile. The tools keep whatever they hold. */
export async function clearProfile() {
  await storage.setItem(SAVED.profile, JSON.stringify(EMPTY_PROFILE));
  state = { ...state, profile: EMPTY_PROFILE };
  emit();
}
