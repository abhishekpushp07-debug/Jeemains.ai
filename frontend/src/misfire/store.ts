// What Misfire remembers while the app is open: the questions being solved one after another, and what the student just
// did to them (tried, "Samajh gaya", put back). Every Misfire list shows that at once, without asking the website again
// and without losing its place.
import { useSyncExternalStore } from "react";
import type { MisfireItem } from "./api";

type Patch = Partial<Pick<MisfireItem, "status" | "tries" | "answer" | "solution_text" | "last_correct" | "solution_count">>;
let owner = "", version = 0;
const patches = new Map<string, Patch>();
const listeners = new Set<() => void>();
const queue = { items: [] as MisfireItem[], index: 0 };

const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };
const read = () => version;

/** Another account on this phone starts clean. */
export function misfireAccount(uid: string) {
  if (uid === owner) return;
  owner = uid; patches.clear(); queue.items = []; queue.index = 0; version++;
}
export function patchMisfire(id: string, patch: Patch) {
  patches.set(id, { ...patches.get(id), ...patch });
  version++;
  listeners.forEach(fn => fn());
}
/** The question as the student left it a moment ago. */
export const applied = (item: MisfireItem): MisfireItem => { const p = patches.get(item.id); return p ? { ...item, ...p } : item; };
/** Redraws a screen whenever a question changes. */
export const usePatches = () => useSyncExternalStore(subscribe, read, read);

/** The list the solve screen walks through, opened at one of its questions. */
export function openQueue(items: MisfireItem[], index: number) { queue.items = items; queue.index = Math.max(0, index); }
export const solveQueue = () => queue;
