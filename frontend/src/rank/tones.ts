// Colour coding for the Rank tab: chance tags, college types, paper level and the three section strips.
import { Platform } from "react-native";
import { rankColors as colors } from "@/src/theme";
import type { Level, Segment, Tag } from "./api";

export const TAG: Record<Tag, { label: string; ink: string; soft: string }> = {
  safe: { label: "Safe", ink: colors.success, soft: colors.custom_successSoft },
  likely: { label: "Likely", ink: colors.custom_savedBlue, soft: colors.custom_webSavedSoft },
  borderline: { label: "Borderline", ink: colors.custom_flame, soft: colors.custom_flameSoft },
};

export const KIND: Record<Exclude<Segment, "all">, { label: string; ink: string; soft: string }> = {
  NIT: { label: "NIT", ink: colors.custom_royalMaroon, soft: colors.custom_webMaroonSoft },
  IIIT: { label: "IIIT", ink: colors.custom_qMarked, soft: colors.custom_qMarkedSoft },
  GFTI: { label: "GFTI", ink: colors.custom_gold, soft: colors.custom_goldSoft },
  DELHI: { label: "Delhi", ink: colors.custom_webLearningCompleted, soft: colors.custom_webCompletedSoft },
};

export const LEVEL: Record<Level, { label: string; ink: string; soft: string }> = {
  tough: { label: "Tough", ink: colors.error, soft: colors.custom_errorSoft },
  normal: { label: "Normal", ink: colors.onSurface, soft: colors.custom_cardRaised },
  easy: { label: "Easy", ink: colors.success, soft: colors.custom_successSoft },
};

export const CATEGORY_LABEL: Record<string, string> = { GEN: "General", EWS: "EWS", "OBC-NCL": "OBC-NCL", SC: "SC", ST: "ST" };

// The Rank Card's serif comes from the phone itself (no font file in the app).
export const SERIF = Platform.select({ ios: "Georgia", android: "serif", default: "Georgia, 'Times New Roman', serif" });

export const CAMPUS: Record<"Pilani" | "Goa" | "Hyderabad", { label: string; ink: string; soft: string }> = {
  Pilani: { label: "Pilani", ink: colors.custom_royalMaroon, soft: colors.custom_webMaroonSoft },
  Goa: { label: "Goa", ink: colors.custom_qMarked, soft: colors.custom_qMarkedSoft },
  Hyderabad: { label: "Hyderabad", ink: colors.custom_gold, soft: colors.custom_goldSoft },
};

export const EXAM: Record<"jee" | "bitsat", { label: string; ink: string; soft: string }> = {
  jee: { label: "JEE", ink: colors.custom_savedBlue, soft: colors.custom_webSavedSoft },
  bitsat: { label: "BITSAT", ink: colors.custom_royalMaroon, soft: colors.custom_webMaroonSoft },
};
