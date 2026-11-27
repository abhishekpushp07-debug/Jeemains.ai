// Which class a chapter belongs to: Class 11 or Class 12.
// The list (exam -> subject -> chapter name -> 11 or 12) comes with the app (classLevels.json), so a screen groups its
// chapters without waiting for anything. Our server keeps the same list (backend/class_levels.json) and says its number
// in /api/app/switches: only when the server's list is newer than the app's is it fetched, once, and used from then on.
// So a chapter can be moved to the other class, or an exam added, without a new app build.
// A chapter is looked up by its name written plainly (`classKey`), so "01 Units, Dimensions and Errors" (the website's
// chapter-wise test) and "Units & Measurements" (Rapid Fire) are both found. A chapter the list does not know has no
// class: screens show it after the others, never hide it.
import { useSyncExternalStore } from "react";
import { BACKEND, appSwitches, onAppSwitches } from "@/src/api/client";
import builtIn from "./classLevels.json";

export type ClassLevel = 11 | 12;
type Book = { version: number; exams: Record<string, Record<string, Record<string, number>>> };
let book: Book = builtIn;
let asked = 0; // the newest version already asked for
const listeners = new Set<() => void>();

/** A chapter's name as the list knows it: small letters, no number in front, "&" as "and", no punctuation.
 *  The server's `key` (backend/class_levels.py) does the same. */
export const classKey = (title: string) => String(title).toLowerCase().replace(/^\s*\d+[.)]?\s+/, "").replace(/&/g, " and ").replace(/[^a-z0-9]+/g, " ").trim();
/** Whether this exam's subject is split into classes at all (JEE Physics is; BITSAT Reasoning is not). */
export const hasClasses = (exam: string, subject: string) => !!book.exams[exam]?.[subject];
export function classOf(exam: string, subject: string, title: string): ClassLevel | null {
  const level = book.exams[exam]?.[subject]?.[classKey(title)];
  return level === 11 || level === 12 ? level : null;
}

function newer() {
  const version = Number(appSwitches()?.classes);
  if (!Number.isInteger(version) || version <= book.version || version <= asked || !BACKEND) return;
  asked = version;
  fetch(`${BACKEND}/api/app/classes?v=${version}`).then(r => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((next: Book) => {
      if (!Number.isInteger(next?.version) || next.version <= book.version || !next.exams || typeof next.exams !== "object") return;
      book = next; listeners.forEach(listener => listener());
    }, () => { asked = 0; }); // not answered: asked again with the next switches answer
}
onAppSwitches(newer);
newer();

const subscribe = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };
const version = () => book.version;
/** For a screen that groups by class: it is drawn again if a newer list arrives. Gives the list's version. */
export const useClassBook = () => useSyncExternalStore(subscribe, version, version);
