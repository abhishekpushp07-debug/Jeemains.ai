// Saved college-branches (JEE) and BITS programs, kept on the phone so the shortlist opens instantly and offline.
import { useEffect, useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";
import { BitsatItem, fmt, Seat, Tag } from "./api";

export type Saved = { id: string; exam: "jee" | "bitsat"; title: string; sub: string; line: string; tag: Tag | null; seat?: Seat };

const KEY = "rank.shortlist.v1";
let items: Saved[] = [];
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
    if (Array.isArray(got)) items = [...items, ...got.filter((g: Saved) => !items.some(i => i.id === g.id))];
  } catch { /* start empty */ }
  emit();
}

export function useShortlist() {
  useEffect(() => { if (!loaded) load(); }, []);
  return useSyncExternalStore(subscribe, read, read);
}

export function toggleSaved(s: Saved) {
  items = items.some(i => i.id === s.id) ? items.filter(i => i.id !== s.id) : [s, ...items].slice(0, 50);
  emit();
  storage.setItem(KEY, JSON.stringify(items));
}

export const jeeSaved = (s: Seat): Saved => ({
  id: `jee-${s.prog}`, exam: "jee", title: s.college, sub: `${s.branch}${s.degree ? ` (${s.degree})` : ""}`,
  line: `Closing ${fmt(s.close)} ${s.rank_type} · ${s.round} · ${s.path}`, tag: s.tag ?? null, seat: s,
});

export const bitsatSaved = (b: BitsatItem): Saved => ({
  id: `bitsat-${b.id}`, exam: "bitsat", title: b.college, sub: b.program, line: `BITSAT 2026 cutoff ${b.cutoff} / 390`, tag: b.tag,
});
