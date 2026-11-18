// Whole colleges added to College compare (college vs college), kept on the phone like the saved branches. Newest first.
import { useEffect, useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";

/** key = JEE institute number, COMEDK code or BITS campus (what the server's college compare needs). */
export type CompareCollege = { id: string; exam: "jee" | "bitsat" | "comedk"; key: string; title: string; sub: string };

const KEY = "rank.compare.colleges.v1";
const MAX = 20;
let items: CompareCollege[] = [];
let loaded = false;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach(f => f());
const subscribe = (f: () => void) => { listeners.add(f); return () => { listeners.delete(f); }; };
const read = () => items;

async function load() {
  loaded = true;
  const raw = await storage.getItem<string | null>(KEY, null);
  try {
    const got = raw ? JSON.parse(raw) : [];
    if (Array.isArray(got)) items = [...items, ...got.filter((g: CompareCollege) => !items.some(i => i.id === g.id))];
  } catch { /* start empty */ }
  emit();
}

export function useCompareColleges() {
  useEffect(() => { if (!loaded) load(); }, []);
  return useSyncExternalStore(subscribe, read, read);
}

/** Adds the college, or removes it if it is already there. */
export function toggleCollege(c: CompareCollege) {
  items = items.some(i => i.id === c.id) ? items.filter(i => i.id !== c.id) : [c, ...items].slice(0, MAX);
  emit();
  storage.setItem(KEY, JSON.stringify(items));
}
