import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { storage } from "@/src/utils/storage";
import type { Crown } from "./social";

// All India Rapid: the same 30 cards for every JEE student each day, one try, one All India board.
export type DailyRow = { rank: number; name: string; pid?: string | null; avatar?: string | null; frame?: string | null; level: number; crown?: Crown | null; correct: number; ms: number; you: boolean };
export type DailyYou = { status: "new" | "playing" | "done"; i?: number; correct?: number; ms?: number; rank?: number | null };
export type DailyStatus = { exam: string; day: string; total: number; seconds: number; ends_in: number; players: number; top: DailyRow[]; yesterday: DailyRow[]; you: DailyYou };
export type DailyBoard = { day: string; total: number; players: number; items: DailyRow[]; you: DailyYou };
export type DailyResult = { correct: number; total: number; ms: number; rank: number | null; players: number; reward?: any; day: string };

export const useDaily = (uid?: string) => useCached<DailyStatus>(uid ? `u.${uid}.rfdaily.JEE` : null, () => rf("/daily?exam=JEE", uid!), false);
export const useDailyBoard = (uid?: string) => useCached<DailyBoard>(uid ? `u.${uid}.rfdailyboard.JEE` : null, () => rf("/daily/board?exam=JEE", uid!), false);

export const secs = (ms: number) => `${(ms / 1000).toFixed(1)} s`;
export const hms = (s: number) => [Math.floor(s / 3600), Math.floor((s % 3600) / 60), Math.floor(s % 60)].map((n) => String(n).padStart(2, "0")).join(":");
export const grouped = (n: number) => n.toLocaleString("en-IN");

/** Seconds left in today's round (midnight IST), ticking every second from the server's answer. */
export function useEndsIn(endsIn?: number) {
  const base = useMemo(() => ({ at: Date.now(), left: endsIn ?? 0 }), [endsIn]);
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const iv = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(iv);
  }, []);
  return Math.max(0, Math.round(base.left - (now - base.at) / 1000));
}

// The look of the All India card: five living scenes in one fire world. World Cup for everyone; "Change style" under the
// card (or a long press on it) opens the five to compare. The pick is kept on this phone only.
export const DAILY_STYLES = [
  { id: 1, name: "Space Race", line: "A rocket blasts out of the fire and into the stars" },
  { id: 2, name: "World Cup", line: "The golden cup held high over the army" },
  { id: 3, name: "Lion Clash", line: "Two lions leap and crash in a white-hot burst" },
  { id: 4, name: "Cavalry Race", line: "Three riders race along the burning ridge" },
  { id: 5, name: "Bullseye", line: "One arrow across the fire, dead centre: +10" },
] as const;
export type DailyLook = 1 | 2 | 3 | 4 | 5;
export const dailyStyleName = (n: DailyLook) => DAILY_STYLES[n - 1].name;
const KEY = "rf.dailyStyle.v2";
let look: DailyLook = 2;
const subs = new Set<() => void>();
storage.getItem<string | null>(KEY, null).then((v) => { const n = Number(v); if (n >= 1 && n <= 5) { look = n as DailyLook; subs.forEach((f) => f()); } }).catch(() => {});
export function setDailyLook(n: DailyLook) {
  look = n;
  subs.forEach((f) => f());
  void Promise.resolve(storage.setItem(KEY, String(n))).catch(() => {});
}
export const useDailyLook = () => useSyncExternalStore((f) => { subs.add(f); return () => { subs.delete(f); }; }, () => look, () => look);
