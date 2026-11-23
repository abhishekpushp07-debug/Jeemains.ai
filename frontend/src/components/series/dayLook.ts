// How a day looks in the day strip and in the 50-day map. A day still to come is blood red; a day that is over is parrot
// green whether or not the student took its paper; today keeps its own colours. The big day card under the strip still
// says "Completed" or "Missed", and so does each day's spoken label.
import { chipEdges, colors, pastel, pastelEdges, SeriesTone } from "@/src/theme";

export type DayLook = "over" | "today" | "upcoming";
export const dayLook = (tone: SeriesTone): DayLook => tone === "upcoming" ? "upcoming" : tone === "today" ? "today" : "over";

/** `from` / `to` = the face, corner to corner; `ink` = the day number; `soft` = the small word above it; `edge`, `gloss`, `glint` = its shine. */
export const DAY_LOOKS: Record<DayLook, { from: string; to: string; ink: string; soft: string; edge: readonly [string, string, ...string[]]; gloss: string; glint: string; label: string }> = {
  over: { from: colors.custom_chipParrot, to: colors.custom_chipParrotDeep, ink: colors.custom_chipParrotInk, soft: colors.custom_chipParrotSoft,
    edge: chipEdges.parrot, gloss: colors.custom_chipParrotGloss, glint: colors.custom_chipParrotGlint, label: "Completed" },
  today: { from: pastel.today.from, to: pastel.today.to, ink: colors.custom_pastelInk, soft: pastel.today.ink,
    edge: pastelEdges.today, gloss: colors.custom_seriesPastelGloss, glint: colors.custom_seriesPastelGlint, label: "Today" },
  upcoming: { from: colors.custom_chipBlood, to: colors.custom_chipBloodDeep, ink: colors.custom_chipBloodInk, soft: colors.custom_chipBloodSoft,
    edge: chipEdges.blood, gloss: colors.custom_chipBloodGloss, glint: colors.custom_chipBloodGlint, label: "Upcoming" },
};
export const DAY_LOOK_ORDER: DayLook[] = ["over", "today", "upcoming"];
