// The Matched paper of a shift: every one of OUR questions that matched a JEE Main question of that shift, to be solved
// like a paper. Everything happens on the phone (the answers came with the shift), so it works without sign-in and
// nothing is sent anywhere. Marking is JEE Main's: +4 for a right answer, -1 for a wrong one, 0 for one left.
import { storage } from "@/src/utils/storage";
import type { MatchedShift, Side } from "./api";

export type PaperQuestion = { id: string; n: number | null; subject: string; chapter: string; jee: Side; ours: Side };
export const RIGHT = 4, WRONG = -1;

/** A number as a student types it or as it was supplied ("8", "-2.5", "1,200"); null when it is not a number. */
const number = (s: string) => {
  const t = s.replace(/[−–]/g, "-").replace(/,/g, "").trim();
  return t && Number.isFinite(Number(t)) ? Number(t) : null;
};
/** One of ours can be checked: the place of its right option is known, or (without options) its answer is a number. */
const checkable = (s: Side) => (s.options.length ? s.correct != null : number(s.answer) != null);

/** In the JEE paper's order; a JEE question that matched two of ours gives two questions. */
export const paperOf = (shift: MatchedShift): PaperQuestion[] => shift.items.flatMap((it, k) =>
  it.ours.map((ours, j) => ({ id: `${k}.${j}`, n: it.n, subject: it.subject, chapter: it.chapter, jee: it.jee, ours })).filter(q => checkable(q.ours)));

/** An answer is the place of the chosen option ("1" = B), or the number typed. "" = left. */
export type Answers = Record<string, string>;
/** Something that can be marked was given: an option, or a whole number ("-" alone is not one). */
export const answered = (q: PaperQuestion, given?: string) => !!given && (q.ours.options.length > 0 || number(given) != null);
export function isRight(q: PaperQuestion, given: string) {
  if (q.ours.options.length) return given === String(q.ours.correct);
  const a = number(q.ours.answer), b = number(given);
  return a != null && b != null && Math.abs(a - b) < 1e-6;
}
export type Verdict = "right" | "wrong" | "left";
export const verdict = (q: PaperQuestion, answers: Answers): Verdict => (!answered(q, answers[q.id]) ? "left" : isRight(q, answers[q.id]) ? "right" : "wrong");

export type Tally = { right: number; wrong: number; left: number; marks: number; max: number };
export function tally(paper: PaperQuestion[], answers: Answers): Tally {
  const t = { right: 0, wrong: 0, left: 0 };
  for (const q of paper) t[verdict(q, answers)] += 1;
  return { ...t, marks: t.right * RIGHT + t.wrong * WRONG, max: paper.length * RIGHT };
}

/** A paper being attempted, or just submitted: kept while the app is open, so leaving the screen loses nothing.
 *  `stamp` = which writing of the shift it belongs to: a shift that was corrected meanwhile starts a fresh paper. */
export type Run = { stamp: number; answers: Answers; seconds: number; done: boolean };
const runs = new Map<string, Run>();
export const peekRun = (shift: string, stamp: number) => { const run = runs.get(shift); return run && run.stamp === stamp ? run : undefined; };
export function runOf(shift: string, stamp: number) {
  let run = peekRun(shift, stamp);
  if (!run) runs.set(shift, run = { stamp, answers: {}, seconds: 0, done: false });
  return run;
}

/** The last submitted paper of a shift, remembered on the phone for the shift's top card (kept as "right:wrong:left:seconds"). */
export type Last = Tally & { seconds: number };
const key = (shift: string) => `matched.paper.${shift}`;
export const saveLast = (shift: string, t: Tally, seconds: number) => storage.setItem(key(shift), [t.right, t.wrong, t.left, seconds].join(":"));
export async function readLast(shift: string): Promise<Last | null> {
  const [right, wrong, left, seconds] = String(await storage.getItem<string>(key(shift), "")).split(":").map(Number);
  if (![right, wrong, left, seconds].every(n => Number.isInteger(n) && n >= 0) || !(right + wrong + left)) return null;
  return { right, wrong, left, seconds, marks: right * RIGHT + wrong * WRONG, max: (right + wrong + left) * RIGHT };
}

export const clock = (seconds: number) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
