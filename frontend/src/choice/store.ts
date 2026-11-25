// What the student has chosen for a Student Choice paper so far: chapters (step 1), then questions from them (step 2).
// Kept while the app is open, so going back and forth between the two steps loses nothing.
import { useSyncExternalStore } from "react";
import { Bank, Counts, NONE, SUBJECTS, Subject } from "./api";

/** Where a chosen question is from: its chapter, its subject, and its number in the chapter. */
export type From = { chapter: string; subject: Subject; n: number };
let chapters: string[] = []; // in the order they were chosen
const picked = new Map<string, From>();
let version = 0;
const listeners = new Set<() => void>();
const changed = () => { version += 1; listeners.forEach(fn => fn()); };
const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };

/** Redraws the screen whenever the choice changes. */
export const useChoice = () => useSyncExternalStore(subscribe, () => version, () => version);

export const chosenChapters = () => chapters;
export const hasChapter = (id: string) => chapters.includes(id);
export function toggleChapter(id: string) {
  if (chapters.includes(id)) {
    chapters = chapters.filter(c => c !== id);
    for (const [qid, p] of picked) if (p.chapter === id) picked.delete(qid); // its questions go with it
  } else chapters = [...chapters, id];
  changed();
}

export const hasQuestion = (id: string) => picked.has(id);
export const pickedCount = () => picked.size;
export const pickedIn = (chapter: string) => { let n = 0; for (const p of picked.values()) if (p.chapter === chapter) n += 1; return n; };
export function counts(): Counts {
  const c = { ...NONE };
  for (const p of picked.values()) c[p.subject] += 1;
  return c;
}
/** Ticks or unticks a question. "full" / "subject" = it was not ticked: the paper, or its subject, already has all it may. */
export function toggleQuestion(id: string, from: From, bank: Pick<Bank, "max_questions" | "max_per_subject">): "ok" | "full" | "subject" {
  if (picked.has(id)) picked.delete(id);
  else if (picked.size >= bank.max_questions) return "full";
  else if (bank.max_per_subject && counts()[from.subject] >= bank.max_per_subject) return "subject";
  else picked.set(id, from);
  changed();
  return "ok";
}
/** The chosen questions in the paper's order: Physics, Chemistry, Mathematics; inside a subject the bank's chapter order,
 *  then the question's number in its chapter. */
export function orderedIds(bank: Bank): string[] {
  const place = new Map<string, number>();
  bank.subjects.forEach(s => s.chapters.forEach((c, i) => place.set(c.id, i)));
  return [...picked.entries()].sort(([, a], [, b]) => SUBJECTS.indexOf(a.subject) - SUBJECTS.indexOf(b.subject)
    || (place.get(a.chapter) ?? 0) - (place.get(b.chapter) ?? 0) || a.n - b.n).map(([id]) => id);
}
export function clearChoice() {
  chapters = [];
  picked.clear();
  changed();
}
