// "Meri details" for the website (NEW): the student's score and category, typed once, every field optional.
// Kept in the browser only and used as the starting values of all six Rank tools. Nothing here goes to a server.
// A web port of the app's src/rank/profile.ts: the same keys, the same shapes, the same rules (docs/12).
//
//   import { loadProfile, saveProfile, clearProfile, readForm, writeForm, SAVED } from "./rankProfile";
//   const profile = loadProfile();                              // EMPTY_PROFILE when the student never saved one
//   saveProfile({ ...profile, jee: { ...profile.jee, marks: "200", category: "OBC-NCL" } });
//   const form = readForm<CutoffForm>(SAVED.cutoff);            // a tool reads its own saved form when it opens
//   writeForm(SAVED.cutoff, { ...form, category: "SC" });       // a tool saves its own edits under its own key
//
// THE RULE. Saving the profile writes its values into every tool's saved form: they are that tool's starting values.
// After that each tool is edited on its own: the edit is saved under that tool's key only. It never changes the
// profile and never changes another tool. Saving the profile again fills the tools again.
import type { Category, CutoffBy, CutoffExam, CutoffScore, Level, ScoreKind } from "./jeeliveApp";

/** Every number is kept as the text the student typed ("" = not given). at = when it was last saved; 0 = never. */
export type RankProfile = {
  at: number;
  jee: { marks: string; pct: string; rank: string; level: Level; category: Category; female: boolean; pwd: boolean; state: string | null };
  comedk: { marks: string; rank: string };
  bitsat: { score: string };
};
export const EMPTY_PROFILE: RankProfile = {
  at: 0, jee: { marks: "", pct: "", rank: "", level: "normal", category: "GEN", female: false, pwd: false, state: null },
  comedk: { marks: "", rank: "" }, bitsat: { score: "" },
};

/** Where the profile and each Rank tool's form live in the browser. */
export const SAVED = {
  profile: "rank.profile.v1", estimate: "rank.estimate.v1", cutoff: "rank.cutoff.v1", target: "rank.target.v1",
  college: "rank.form.v1", bitsat: "rank.bitsat.v1", comedk: "rank.comedk.v1",
} as const;

// ------------------------------------------------------------------ each tool's saved form (what the profile fills)
/** Rank predictor. jee / comedk = the marks typed for that exam. */
export type EstimateForm = { exam: "jee" | "comedk"; jee: string; comedk: string; level: Level; category: Category; pwd: boolean };
/** Cut off: one choice per exam. text = what is typed in the score box; score = the one the list is filtered by
 *  (null = every cut-off is shown). The profile fills kind + text and leaves score null: the student taps "Eligible dikhao". */
export type CutoffPick = { by: CutoffBy; college: string | null; branch: string | null; kind: ScoreKind; text: string; score: CutoffScore | null };
export type CutoffForm = { exam: CutoffExam; level: Level; category: Category; female: boolean; pwd: boolean; state: string | null } & Record<CutoffExam, CutoffPick>;
/** Target marks. inst / code / campus = the chosen JEE college, COMEDK college and BITS campus. */
export type TargetForm = { exam: "jee" | "bitsat" | "comedk"; category: Category; female: boolean; pwd: boolean; state: string | null;
  inst: number | null; code: string | null; campus: "all" | "Pilani" | "Goa" | "Hyderabad" };
/** College predictor, JEE Main. College compare and Dream college read category, female, pwd and state from this form. */
export type CollegeForm = { marks: string; pct: string; rank: string; level: Level; category: Category; female: boolean; pwd: boolean; state: string | null; branches: string[] };
/** College predictor, COMEDK. (College predictor, BITSAT keeps only the typed score, as plain text.) */
export type ComedkForm = { marks: string; rank: string; branches: string[] };

// ------------------------------------------------------------------ the limits of every score
type Rule = { min: number; max: number; label: string; hint: string; bad: string; len: number; decimal?: boolean; signed?: boolean };
/** Every score a Rank tool accepts, per exam: its limits, field label, placeholder and the line shown when it is wrong. */
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

/** Typed text -> the number, null when the box is empty, or the sentence saying what to fix. */
export function readScore(exam: CutoffExam, kind: ScoreKind, text: string): number | string | null {
  const rule = SCORE[exam][kind], v = text.trim();
  if (!rule || !v) return null;
  const n = Number(v);
  return (rule.decimal ? Number.isFinite(n) : Number.isInteger(n)) && n >= rule.min && n <= rule.max ? n : rule.bad;
}

/** The first wrong number of a profile and the exam whose page shows it, or null when every box is fine or empty. */
export function problemOf(p: Omit<RankProfile, "at">): { exam: CutoffExam; text: string } | null {
  const boxes: [CutoffExam, ScoreKind, string][] = [["jee", "marks", p.jee.marks], ["jee", "percentile", p.jee.pct], ["jee", "rank", p.jee.rank],
    ["comedk", "marks", p.comedk.marks], ["comedk", "rank", p.comedk.rank], ["bitsat", "marks", p.bitsat.score]];
  for (const [exam, kind, text] of boxes) {
    const v = readScore(exam, kind, text);
    if (typeof v === "string") return { exam, text: v };
  }
  return null;
}

// ------------------------------------------------------------------ storage
/** Where the values are kept. Default: the browser's localStorage. Pass your own to test, or to use another store. */
export type Store = { getItem(key: string): string | null; setItem(key: string, value: string): void };
const browser = (): Store => window.localStorage;

function read(store: Store, key: string): Record<string, any> | null {
  try {
    const v = JSON.parse(store.getItem(key) ?? "null");
    return v && typeof v === "object" && !Array.isArray(v) ? v : null;
  } catch { return null; }
}

export function loadProfile(store: Store = browser()): RankProfile {
  const p = read(store, SAVED.profile);
  if (!p) return EMPTY_PROFILE;
  return { at: Number(p.at) || 0, jee: { ...EMPTY_PROFILE.jee, ...p.jee }, comedk: { ...EMPTY_PROFILE.comedk, ...p.comedk }, bitsat: { ...EMPTY_PROFILE.bitsat, ...p.bitsat } };
}

/** A tool's saved form, or null when it has none yet (use the tool's own defaults then, spread under what is read). */
export const readForm = <T = Record<string, any>>(key: string, store: Store = browser()) => read(store, key) as T | null;
/** A tool saves its own form: on Show, and on every chip or picker change. This never touches the profile. */
export const writeForm = (key: string, form: object, store: Store = browser()) => store.setItem(key, JSON.stringify(form));
/** College predictor, BITSAT: the typed score as plain text ("" = none). */
export const readBitsatScore = (store: Store = browser()) => store.getItem(SAVED.bitsat) ?? "";

/** Saves the profile and fills every tool's saved form with it. Check it with problemOf() first.
 *  - A score the profile leaves empty does not wipe the tool's own score.
 *  - JEE Main, when several scores are given: the College predictor gets all of them (the server picks the most exact);
 *    Cut off starts from the most exact one: rank, then percentile, then marks.
 *  - Cut off gets the score typed in its box but not applied: the list still shows every cut-off until the student taps
 *    "Eligible dikhao".
 *  After calling it, every open Rank tool must read its saved form again and show its form open. */
export function saveProfile(p: Omit<RankProfile, "at">, store: Store = browser()): RankProfile {
  const profile: RankProfile = { ...p, at: Date.now() };
  const j = p.jee, c = p.comedk, b = p.bitsat.score;
  const who = { category: j.category, female: j.female, pwd: j.pwd, state: j.state };
  const jee = !!(j.marks || j.pct || j.rank), comedk = !!(c.marks || c.rank);
  const patch = (key: string, change: (old: Record<string, any>) => Record<string, any>) => writeForm(key, change(read(store, key) ?? {}), store);
  const start = (old: object | undefined, kind: ScoreKind, text: string) => ({ ...old, kind, text, score: null });

  writeForm(SAVED.profile, profile, store);
  patch(SAVED.estimate, o => ({ ...o, level: j.level, category: j.category, pwd: j.pwd, ...(j.marks ? { jee: j.marks } : {}), ...(c.marks ? { comedk: c.marks } : {}) }));
  patch(SAVED.cutoff, o => ({
    ...o, ...who, level: j.level,
    ...(jee ? { jee: start(o.jee, j.rank ? "rank" : j.pct ? "percentile" : "marks", j.rank || j.pct || j.marks) } : {}),
    ...(comedk ? { comedk: start(o.comedk, c.rank ? "rank" : "marks", c.rank || c.marks) } : {}),
    ...(b ? { bitsat: start(o.bitsat, "marks", b) } : {}),
  }));
  patch(SAVED.target, o => ({ ...o, ...who }));
  patch(SAVED.college, o => ({ ...o, ...who, level: j.level, ...(jee ? { marks: j.marks, pct: j.pct, rank: j.rank } : {}) }));
  if (comedk) patch(SAVED.comedk, o => ({ ...o, marks: c.marks, rank: c.rank }));
  if (b) store.setItem(SAVED.bitsat, b);
  return profile;
}

/** Forgets the profile. The tools keep whatever they hold. */
export function clearProfile(store: Store = browser()): RankProfile {
  writeForm(SAVED.profile, EMPTY_PROFILE, store);
  return EMPTY_PROFILE;
}

/** The closed bar's line, e.g. "JEE Main: 200 marks, rank 7,500 · General  |  COMEDK: rank 30,000  |  BITSAT: 280". */
export function profileLine(p: RankProfile): string {
  const n = (v: string) => Number(v).toLocaleString("en-IN");
  const label: Record<Category, string> = { GEN: "General", EWS: "EWS", "OBC-NCL": "OBC-NCL", SC: "SC", ST: "ST" };
  const j = p.jee;
  const jee = [[j.marks && `${j.marks} marks`, j.pct && `${j.pct} percentile`, j.rank && `rank ${n(j.rank)}`].filter(Boolean).join(", ") || null,
    label[j.category], j.female ? "Female" : null, j.pwd ? "PwD" : null, j.state].filter(Boolean).join(" · ");
  const comedk = [p.comedk.marks && `${p.comedk.marks} marks`, p.comedk.rank && `rank ${n(p.comedk.rank)}`].filter(Boolean).join(", ");
  return [`JEE Main: ${jee}`, comedk ? `COMEDK: ${comedk}` : null, p.bitsat.score ? `BITSAT: ${p.bitsat.score}` : null].filter(Boolean).join("  |  ");
}
