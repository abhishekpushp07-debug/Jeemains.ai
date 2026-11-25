// What the student has chosen in Student Choice so far: chapters (step 1), then questions from them (step 2).
// The ticked chapters are kept on the phone for each account, so the list is still there the next day; the ticked
// questions are kept while the app is open, so going back and forth between the two steps loses nothing.
import { useEffect, useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";
import { Bank, Counts, NONE, SUBJECTS, Subject } from "./api";

/** Where a chosen question is from: its chapter, its subject, and its number in the chapter. */
export type From = { chapter: string; subject: Subject; n: number };
let chapters: string[] = []; // in the order they were chosen
const picked = new Map<string, From>();
let version = 0;
const listeners = new Set<() => void>();
const changed = () => { version += 1; listeners.forEach(fn => fn()); };
const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };

let owner = ""; // the account these ticks belong to
let loaded = false; // the phone's copy of that account's chapters has been read
const key = (uid: string) => `choice.chapters.${uid}`;
const keep = () => { if (owner && loaded) void storage.setItem(key(owner), JSON.stringify(chapters)); };
function open(uid: string) {
  if (owner === uid) return;
  owner = uid; loaded = false; chapters = []; picked.clear(); changed();
  void storage.getItem<string | null>(key(uid), null).then(raw => {
    if (owner !== uid) return;
    let saved: unknown = null;
    try { saved = raw ? JSON.parse(raw) : null; } catch {}
    // Chapters ticked while the copy was being read stay, after the saved ones.
    const here = chapters.length;
    const all = [...(Array.isArray(saved) ? saved.filter((id): id is string => typeof id === "string") : []), ...chapters];
    chapters = [...new Set(all)].slice(0, 300);
    loaded = true;
    if (here) keep();
    changed();
  });
}

/** Redraws the screen whenever the choice changes. With the signed-in student's id it also brings back the chapters
 *  that account ticked on this phone before. */
export function useChoice(uid?: string) {
  useEffect(() => { if (uid) open(uid); }, [uid]);
  return useSyncExternalStore(subscribe, () => version, () => version);
}
/** False while the phone's copy is still being read: a screen must not decide "nothing is ticked" before it is true. */
export const choiceLoaded = () => loaded;

export const chosenChapters = () => chapters;
export const hasChapter = (id: string) => chapters.includes(id);
export function toggleChapter(id: string) {
  if (chapters.includes(id)) {
    chapters = chapters.filter(c => c !== id);
    for (const [qid, p] of picked) if (p.chapter === id) picked.delete(qid); // its questions go with it
  } else chapters = [...chapters, id];
  keep();
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
  keep();
  changed();
}
