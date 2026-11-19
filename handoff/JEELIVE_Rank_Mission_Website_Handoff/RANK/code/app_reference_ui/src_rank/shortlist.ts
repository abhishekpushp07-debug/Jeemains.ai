// Saved college-branches (JEE, COMEDK, BITS programs) for College compare and the shortlist, kept on the phone so they open
// instantly and offline. Added from a College predictor card ("Add to Compare") or from a college's branch list in Compare.
import { useEffect, useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";
import { BitsatItem, BitsatTarget, ComedkItem, ComedkTargetRow, CompareItem, fmt, JeeTargetRow, Seat, Tag } from "./api";

/** `jee` = how the server finds a JEE seat added from a college's branch list (a predictor card carries the full `seat`). */
export type Saved = { id: string; exam: "jee" | "bitsat" | "comedk"; title: string; sub: string; line: string; tag: Tag | null; seat?: Seat;
  jee?: { prog: number; quota: string; gender: "N" | "F"; path: string } };

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

/** What the server needs to find a saved seat again (compare and the saved-list PDF). */
export function toCompareItem(s: Saved): CompareItem {
  const j = s.seat ?? s.jee;
  if (s.exam === "jee") return { exam: "jee", id: s.id, prog: j?.prog, quota: j?.quota, gender: j?.gender, path: j?.path };
  return { exam: s.exam, id: s.id.replace(/^(comedk|bitsat)-/, "") };
}

/** Branches from a college's list in College compare (no chance tag: no score is entered there). */
export const jeeRowSaved = (college: string, r: JeeTargetRow): Saved => ({
  id: `jee-${r.prog}`, exam: "jee", title: college, sub: `${r.branch}${r.degree ? ` (${r.degree})` : ""}`,
  line: `Closing ${fmt(r.final.close)} ${r.rank_type} · ${r.final.label} · ${r.path}`, tag: null,
  jee: { prog: r.prog, quota: r.quota, gender: r.gender, path: r.path },
});
export const comedkRowSaved = (code: string, college: string, r: ComedkTargetRow): Saved => ({
  id: `comedk-${code}|${r.cc}`, exam: "comedk", title: college, sub: r.course, line: `COMEDK 2026 closing ${fmt(r.final.close)} · ${r.final.label} · GM`, tag: null,
});
export const bitsatRowSaved = (r: BitsatTarget["rows"][number]): Saved => ({
  id: `bitsat-${r.id}`, exam: "bitsat", title: r.college, sub: r.program, line: `BITSAT 2026 cutoff ${r.cutoff} / 390`, tag: null,
});

/** Body of POST /api/rank/pdf/saved: every saved college, their chance tags, and which ones go side by side. */
export const savedPdfBody = (list: Saved[], pick: string[] = []) => ({
  items: list.map(toCompareItem), tags: list.map(s => s.tag), pick: pick.map(id => list.findIndex(s => s.id === id)).filter(i => i >= 0),
});

export const comedkSaved = (c: ComedkItem): Saved => ({
  id: `comedk-${c.id}`, exam: "comedk", title: c.college, sub: c.course, line: `COMEDK 2026 closing ${fmt(c.close)} · ${c.round} · GM`, tag: c.tag ?? null,
});
