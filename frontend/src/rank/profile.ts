// "Meri details" (top of the Rank tab): the student's score and category, typed once. Saving it writes those values into
// every Rank tool's saved form as that tool's starting values. After that each tool is edited on its own: the edit stays
// in that tool and the profile is not touched, until the student saves the profile again.
import { useEffect, useSyncExternalStore } from "react";
import { getAssetAccount } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import type { Category, CutoffExam, Level, ScoreKind } from "./api";

export type RankProfile = {
  at: number; // when it was last saved; 0 = never
  jee: { marks: string; pct: string; rank: string; level: Level; category: Category; female: boolean; pwd: boolean; state: string | null };
  comedk: { marks: string; rank: string };
  bitsat: { score: string };
  /** The account it belongs to, when it was saved signed in or came from the account's copy (./profileSync.ts). */
  uid?: string;
  /** When "Meri details hatao" was pressed (the profile is then empty): so the account's older copy does not bring it back. */
  clearedAt?: number;
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
let loading: Promise<void> | null = null;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach(f => f());
const subscribe = (f: () => void) => { listeners.add(f); return () => { listeners.delete(f); }; };
const read = () => state;

const text = (v: unknown, max = 12) => (typeof v === "string" ? v.slice(0, max) : typeof v === "number" && Number.isFinite(v) ? String(v) : "");
const LEVELS = ["tough", "normal", "easy"], CATEGORIES = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];
/** A profile as it is kept (on the phone, or the account's copy on the website), in the app's shape; null if it is not one. */
export function readProfile(p: any): RankProfile | null {
  if (!p || typeof p !== "object" || typeof p.jee !== "object" || !p.jee) return null;
  const j = p.jee, c = p.comedk && typeof p.comedk === "object" ? p.comedk : {}, b = p.bitsat && typeof p.bitsat === "object" ? p.bitsat : {};
  return {
    at: Number(p.at) || 0,
    jee: { marks: text(j.marks), pct: text(j.pct), rank: text(j.rank), level: LEVELS.includes(j.level) ? j.level : "normal",
      category: CATEGORIES.includes(j.category) ? j.category : "GEN", female: j.female === true, pwd: j.pwd === true,
      state: typeof j.state === "string" && j.state ? j.state.slice(0, 60) : null },
    comedk: { marks: text(c.marks), rank: text(c.rank) }, bitsat: { score: text(b.score) },
    ...(typeof p.uid === "string" && p.uid ? { uid: p.uid } : {}), ...(Number(p.clearedAt) > 0 ? { clearedAt: Number(p.clearedAt) } : {}),
  };
}

async function load() {
  const raw = await storage.getItem<string | null>(SAVED.profile, null);
  if (!raw || state.saves) return;
  try {
    const p = readProfile(JSON.parse(raw));
    if (p) { state = { ...state, profile: p }; emit(); }
  } catch { /* start empty */ }
}
/** Read from the phone once; later calls wait for the same read. */
export const profileReady = () => (loading ||= load());
export const currentProfile = () => state.profile;

export function useRankProfile() {
  useEffect(() => { void profileReady(); }, []);
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
 *  tool's own; when several JEE scores are given the Cut off tool starts from the most exact (rank, percentile, marks).
 *  Signed in, it belongs to that account (and goes to the account's copy: ./profileSync.ts). */
export async function saveProfile(p: Omit<RankProfile, "at">) {
  const uid = getAssetAccount();
  await keep({ jee: p.jee, comedk: p.comedk, bitsat: p.bitsat, at: Date.now(), ...(uid ? { uid } : {}) });
}

async function keep(profile: RankProfile) {
  const j = profile.jee, c = profile.comedk, b = profile.bitsat.score;
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

/** Forgets the profile. The tools keep whatever they hold. Signed in, the account's copy is emptied too. */
export async function clearProfile() {
  const uid = getAssetAccount();
  await forget({ ...EMPTY_PROFILE, clearedAt: Date.now(), ...(uid ? { uid } : {}) });
}

async function forget(profile: RankProfile) {
  await storage.setItem(SAVED.profile, JSON.stringify(profile));
  state = { ...state, profile };
  emit();
}

/** The account's copy (./profileSync.ts) is newer than the phone's: kept here as if it had been saved on this phone
 *  (every tool filled), or, when it was emptied on the other side, forgotten here too. */
export async function takeProfile(remote: RankProfile | null, at: number, uid: string) {
  if (remote) await keep({ jee: remote.jee, comedk: remote.comedk, bitsat: remote.bitsat, at, uid });
  else await forget({ ...EMPTY_PROFILE, clearedAt: at, uid });
}

/** A profile has just been sent up to the account (`at`: the time both sides now hold): only the owner (and that time)
 *  are noted on the phone; the tools are not touched. */
export async function stampProfile(uid: string, at?: number) {
  const p = state.profile;
  await forget({ ...p, uid, ...(at ? (p.at ? { at } : { clearedAt: at }) : {}) });
}
