// The student's Mission share stats: their own link (goes in the caption) and how many friends opened it.
// A friend counts once, the first time their browser opens the link (counted on our server, robots excluded).
import { useFocusEffect } from "expo-router";
import { useCallback } from "react";
import { BACKEND, rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { caption } from "./copy";

export type MissionStats = { code: string; helped: number; week: number };

/** First name only, so it fits on the card ("Rahul Kumar" → "Rahul"). Empty for phone-only accounts. */
const firstName = (name?: string) => {
  const w = (name || "").trim().split(/\s+/)[0] || "";
  return /\d/.test(w) ? "" : w.slice(0, 14);
};

export function useMissionStats() {
  const { user } = useAuth();
  const uid = user?.id;
  const s = useCached<MissionStats>(uid ? `u.${uid}.mission` : null, () => rf<MissionStats>("/mission/me", uid!));
  useFocusEffect(useCallback(() => { s.revalidate(); }, [s.revalidate])); // eslint-disable-line react-hooks/exhaustive-deps
  const link = s.data?.code ? `${BACKEND}/api/j/${s.data.code}` : "https://jeelive.ai";
  return { stats: s.data, loading: s.loading && !s.data, error: s.error, reload: s.reload, refreshing: s.refreshing,
    name: firstName(user?.name), caption: caption(link) };
}

/** Milestones on the way: the next one above the current count. */
const STEPS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
export const nextStep = (n: number) => STEPS.find(x => x > n) ?? Math.ceil((n + 1) / 10000) * 10000;

/** 12 → "12", 1234 → "1,234", 25300 → "25k+" (fits the gold seal on the card). */
export const shortCount = (n: number) => n < 10000 ? n.toLocaleString("en-IN") : `${Math.floor(n / 1000)}k+`;
