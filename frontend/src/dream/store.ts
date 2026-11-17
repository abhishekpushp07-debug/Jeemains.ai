// Dream colleges: up to 5 college + branch per exam (JEE Main, BITSAT, COMEDK), each with the marks it needs, and the
// student's recent full mock scores, so every screen can say "X marks door". Kept on the phone, like the shortlist.
import { useEffect, useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";

export type DreamExam = "jee" | "bitsat" | "comedk";
export const EXAMS: DreamExam[] = ["jee", "bitsat", "comedk"];
export const FULL: Record<DreamExam, number> = { jee: 300, bitsat: 390, comedk: 180 };
export const EXAM_NAME: Record<DreamExam, string> = { jee: "JEE Main", bitsat: "BITSAT", comedk: "COMEDK" };
export const MAX_DREAMS = 5;

/** need = marks (out of FULL) for this seat on a normal paper; range = [easy-paper .. tough-paper] where known. */
export type Dream = { id: string; exam: DreamExam; college: string; branch: string; need: number; range?: [number, number]; note: string; at: number };
/** A full mock, its score scaled to the exam's full marks. */
export type Mock = { id: string; exam: DreamExam; score: number; max: number; raw: number; rawMax: number; title: string; at: number };
type State = { dreams: Dream[]; mocks: Mock[] };

const KEY = "dream.v1";
let state: State = { dreams: [], mocks: [] };
let loaded = false;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach(f => f());
const subscribe = (f: () => void) => { listeners.add(f); return () => { listeners.delete(f); }; };
const read = () => state;
const save = (next: State) => { state = next; emit(); storage.setItem(KEY, JSON.stringify(state)); };

async function load() {
  loaded = true;
  const raw = await storage.getItem<string | null>(KEY, null);
  try {
    const got = raw ? JSON.parse(raw) : null;
    if (got && Array.isArray(got.dreams) && Array.isArray(got.mocks)) state = {
      dreams: [...state.dreams, ...got.dreams.filter((d: Dream) => !state.dreams.some(x => x.id === d.id))],
      mocks: [...state.mocks, ...got.mocks.filter((m: Mock) => !state.mocks.some(x => x.id === m.id))].sort((a, b) => b.at - a.at),
    };
  } catch { /* start empty */ }
  emit();
}

export function useDreams() {
  useEffect(() => { if (!loaded) load(); }, []);
  return useSyncExternalStore(subscribe, read, read);
}

export const dreamsOf = (s: State, exam: DreamExam) => s.dreams.filter(d => d.exam === exam);
/** Newest first. */
export const mocksOf = (s: State, exam: DreamExam) => s.mocks.filter(m => m.exam === exam);

/** Adds the dream (or removes it if already pinned). "full" when that exam already has 5. */
export function toggleDream(d: Dream): "added" | "removed" | "full" {
  if (state.dreams.some(x => x.id === d.id)) { save({ ...state, dreams: state.dreams.filter(x => x.id !== d.id) }); return "removed"; }
  if (dreamsOf(state, d.exam).length >= MAX_DREAMS) return "full";
  save({ ...state, dreams: [...state.dreams, d] });
  return "added";
}

export const removeDream = (id: string) => save({ ...state, dreams: state.dreams.filter(x => x.id !== id) });

/** Which dream exam a test belongs to, from the website's exam name ("JEE Main", "BITSAT", "COMEDK"). */
export function examOf(name?: string | null): DreamExam | null {
  const n = (name || "").toLowerCase();
  if (n.includes("bitsat")) return "bitsat";
  if (n.includes("comedk")) return "comedk";
  if (n.includes("jee") && !n.includes("adv")) return "jee";
  return null;
}

/** Remembers a released result as a mock. Only full-length papers count (at least half the exam's full marks). */
export function recordMock(m: { id: string; exam?: string | null; score: number; maximum: number; title?: string; at?: number }) {
  const exam = examOf(m.exam);
  if (!exam || !m.maximum || m.maximum < FULL[exam] / 2) return;
  const score = Math.round((m.score / m.maximum) * FULL[exam]);
  const mock: Mock = { id: m.id, exam, score, max: FULL[exam], raw: m.score, rawMax: m.maximum, title: m.title || "Mock", at: m.at || Date.now() };
  const old = state.mocks.find(x => x.id === m.id);
  if (old && old.raw === mock.raw && old.rawMax === mock.rawMax) return;
  save({ ...state, mocks: [mock, ...state.mocks.filter(x => x.id !== m.id)].sort((a, b) => b.at - a.at).slice(0, 30) });
}
