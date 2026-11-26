// Student Choice's chapter search: a chapter by its name, in all three subjects at once, while the student types.
// Everything is found on the phone (the bank is already there), so a result shows with each letter.
// What finds a chapter, best first:
//   its short name by first letters    "goc" General Organic Chemistry, "ktg" Kinetic Theory of Gases
//   a word of its name starts so       "therm" Thermodynamics, "p block" p-Block Elements
//   its first letters start so         "com" Centre of Mass, Momentum and Collisions
//   the letters are inside its name    "organic", "pblock"
// and, only when nothing is found as typed, a near spelling ("kinametics", "probablity", "matrix").
import { Chapter, Subject } from "./api";

export type Found = { c: Chapter; subject: Subject };
/** `close` = nothing has this name as typed: these are the chapters spelt nearly so. */
export type Search = { items: Found[]; close: boolean };
type Entry = Found & { words: string[]; joined: string; initials: string[] };

/** Short names students use that a chapter's own name does not hold: each stands for words of the name. */
const SHORT_NAMES: Record<string, string> = { "3d": "three dimensional", "3": "three", shm: "oscillations", emi: "electromagnetic induction", emw: "electromagnetic waves", nlm: "laws of motion", pnc: "permutations" };
const SMALL = new Set(["and", "of", "the", "in", "to", "under"]);

/** Small letters and digits only, one space between words ("d- and f-Block" -> "d and f block"). */
const plain = (s: string) => s.toLowerCase().replace(/&/g, " and ").replace(/[^a-z0-9\u0080-\uffff]+/g, " ").trim();

/** The chapters of every subject, made ready to be searched (once for a bank). */
export function searchIndex(subjects: { name: Subject; chapters: Chapter[] }[]): Entry[] {
  return subjects.flatMap(s => s.chapters.map(c => {
    const words = plain(c.title).split(" ").filter(Boolean);
    const big = words.filter(w => !SMALL.has(w));
    return { c, subject: s.name, words, joined: words.join(""), initials: [...new Set([big.map(w => w[0]).join(""), words.map(w => w[0]).join("")])] };
  }));
}

/** How many letters must be changed, added, dropped (or two neighbours swapped) to turn `a` into `b`. */
function distance(a: string, b: string) {
  let before: number[] = [], last = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const row = [i];
    for (let j = 1; j <= b.length; j++) {
      const same = a[i - 1] === b[j - 1];
      row[j] = Math.min(last[j] + 1, row[j - 1] + 1, last[j - 1] + (same ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) row[j] = Math.min(row[j], before[j - 2] + 1);
    }
    before = last; last = row;
  }
  return last[b.length];
}
/** A word typed nearly right: the same first letter, and one slip (two in a long word) from how the name's word starts.
 *  Gives the number of slips, or -1 when it is further off than that. */
function slips(typed: string, word: string) {
  if (typed.length < 4 || typed[0] !== word[0]) return -1;
  let best = typed.length >= 8 ? 3 : 2;
  for (let n = typed.length - 1; n <= typed.length + 1; n++) if (n >= 3 && n <= word.length) best = Math.min(best, distance(typed, word.slice(0, n)));
  return best <= (typed.length >= 8 ? 2 : 1) ? best : -1;
}
/** How far a chapter's name is from what is typed, in slips over all typed words; -1 = too far. */
function nearness(e: Entry, typed: string[]) {
  let sum = 0;
  for (const t of typed) {
    if (e.words.some(w => w.startsWith(t))) continue;
    const best = Math.min(...e.words.map(w => slips(t, w)).filter(n => n >= 0));
    if (!Number.isFinite(best)) return -1;
    sum += best;
  }
  return sum;
}

/** How well a chapter fits what is typed: 0 best … 3; -1 = it does not. Every typed word has to fit. */
function fit(e: Entry, typed: string[]) {
  let worst = 0;
  for (const t of typed) {
    const alone = typed.length === 1 && t.length >= 2;
    const score = alone && e.initials.includes(t) ? 0 : e.words.some(w => w.startsWith(t)) ? 1 : alone && e.initials.some(i => i.startsWith(t)) ? 2 : t.length >= 3 && e.joined.includes(t) ? 3 : -1;
    if (score < 0) return -1;
    worst = Math.max(worst, score);
  }
  return worst;
}

/** The chapters that fit `query`, best first; chapters that fit equally stay in the bank's order (Physics, Chemistry,
 *  Maths, each in its own order). Nothing typed = nothing found. */
export function findChapters(index: Entry[], query: string): Search {
  const typed = plain(query).split(" ").filter(Boolean).flatMap(t => (SHORT_NAMES[t] || t).split(" ")).slice(0, 8);
  if (!typed.length) return { items: [], close: false };
  const scored = index.map((e, at) => ({ e, at, score: fit(e, typed) })).filter(x => x.score >= 0).sort((a, b) => a.score - b.score || a.at - b.at);
  if (scored.length) return { items: scored.map(x => ({ c: x.e.c, subject: x.e.subject })), close: false };
  // Nothing as typed: a slip in the spelling is forgiven, in words long enough to tell. The nearest spelling first.
  const close = index.map((e, at) => ({ e, at, off: nearness(e, typed) })).filter(x => x.off >= 0).sort((a, b) => a.off - b.off || a.at - b.at);
  return { items: close.map(x => ({ c: x.e.c, subject: x.e.subject })), close: close.length > 0 };
}
