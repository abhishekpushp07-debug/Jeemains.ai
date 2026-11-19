// Analysis 2.0: the same words, tags and number formats as jeelive.ai, in the app's own colours.
import type React from "react";
import { colors } from "@/src/theme";
import type { IconName } from "@/src/components/ui";

export type An = any; // the versioned analysis JSON from GET /attempts/{id}/analysis
export type Q = any;
export type Drill = (title: string, ids: string[]) => void;
export type Open = (questionId: string) => void;
export type SectionProps = { an: An; id: string; onDrill: Drill; onOpen: Open; go: (section: string) => void; slot?: React.ReactNode };

export const mmss = (s?: number | null) => (s == null ? "—" : `${Math.floor(Math.round(s) / 60)}m ${String(Math.round(s) % 60).padStart(2, "0")}s`);
export const pc = (v?: number | null) => (v == null ? "—" : v + "%");
export const r1 = (v?: number | null) => Math.round((v || 0) * 10) / 10;
export const slug = (v: unknown) => String(v).toLowerCase().replace(/[^a-z0-9]+/g, "-");
export const pick = (an: An, test: (q: Q) => boolean): string[] => an.questions.filter(test).map((q: Q) => q.id);

const byId = new WeakMap<object, Record<string, Q>>();
export function index(an: An): Record<string, Q> {
  let map = byId.get(an.questions);
  if (!map) { map = Object.fromEntries(an.questions.map((q: Q) => [q.id, q])); byId.set(an.questions, map!); }
  return map!;
}

export type Tone = "good" | "bad" | "warn" | "info" | "teal" | "mute" | "brand" | "plain";
// ink = text and icons, soft = quiet background, line = border, fill = chart bars.
export const TONE: Record<Tone, { ink: string; soft: string; line: string; fill: string }> = {
  good: { ink: colors.success, soft: colors.custom_successSoft, line: colors.custom_doneTo, fill: colors.custom_qAnswered },
  bad: { ink: colors.error, soft: colors.custom_errorSoft, line: colors.brandLine, fill: colors.custom_qNotAnswered },
  warn: { ink: colors.warning, soft: colors.custom_warningSoft, line: colors.custom_todayFrom, fill: colors.custom_webLearningActive },
  info: { ink: colors.custom_savedBlue, soft: colors.custom_webSavedSoft, line: colors.custom_royalTintLine, fill: colors.custom_savedBlue },
  teal: { ink: colors.custom_qMarkedInk, soft: colors.custom_qMarkedSoft, line: colors.custom_upTo, fill: colors.custom_qMarked },
  mute: { ink: colors.muted, soft: colors.custom_cardRaised, line: colors.custom_cardLineStrong, fill: colors.custom_dim },
  brand: { ink: colors.brandText, soft: colors.brandTertiary, line: colors.brandLine, fill: colors.brandPrimary },
  plain: { ink: colors.onSurface, soft: colors.custom_card, line: colors.custom_cardLine, fill: colors.onSurface },
};

export const RESULT: Record<string, string> = { correct: "Sahi", incorrect: "Galat", skipped: "Chhoda", dropped: "Dropped", bonus: "Bonus" };
export const OUT_TONE: Record<string, Tone> = { correct: "good", incorrect: "bad", skipped: "mute", dropped: "mute", bonus: "good" };
export const OUT_ICON: Record<string, IconName> = { correct: "check", incorrect: "close", skipped: "minus", dropped: "cancel", bonus: "star" };
export const TAG: Record<string, [Tone, IconName]> = {
  perfect: ["good", "check-circle"], slow_correct: ["warn", "timer-sand"], wasted: ["bad", "lightning-bolt"], concept_gap: ["bad", "brain"],
  costly_overtime: ["bad", "clock-alert-outline"], confused: ["warn", "help-circle-outline"], smart_skip: ["info", "skip-next"],
  not_seen: ["mute", "eye-off-outline"], no_score: ["mute", "cancel"],
};
export const LEVEL_TONE: Record<string, Tone> = { easy: "good", moderate: "warn", tough: "bad", unrated: "mute" };

export const RANK_NOTE: Record<string, string> = {
  sealed: "Rank sabka time khatam hone par aayega", preparing: "Class ka data ban raha hai…", staff: "Staff attempt par Rank nahi banta",
  original_only: "Rank sirf original Score par banta hai", none: "Is test par Rank nahi banta", ready: "Rank jald aayega",
};
