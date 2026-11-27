// Each Rank tool's form colour: Rank predictor maroon, Cut off teal, Target marks lime, College predictor
// blood red, College compare sky blue. The chosen tile glows in it and the form below wears it (running edge, glossy header band,
// chosen chips, fields and the main button), so the student sees at once which form belongs to the tile they tapped.
import React, { createContext, useContext } from "react";
import type { IconName } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { formEdges, rankColors as colors } from "@/src/theme";
import type { Tool } from "./ToolGrid";

/** ink = the colour (fills), on = text on it, text = the colour for words, icons and tile glow on black.
 *  edge = the colours that run round the form; gloss / glint = the shine on its header band.
 *  bar = the score bar after Show in its own look (College predictor: shining purple), with the Edit button in `ink`. */
export type Accent = { ink: string; soft: string; line: string; on: string; text: string; name: string; icon: IconName;
  edge: readonly [string, string, ...string[]]; gloss: string; glint: string;
  bar?: { from: string; to: string; glow: string; hint: string; chip: string } };
// A light header band carries dark words and the strong shine; a deep one (maroon, blood red, violet) white words and the soft shine.
const light = { on: colors.custom_fOn, gloss: colors.custom_formGloss, glint: colors.custom_formGlint };
const deep = { on: colors.onBrandPrimary, gloss: colors.custom_formDeepGloss, glint: colors.custom_formDeepGlint };
export const ACCENTS: Record<Tool, Accent> = {
  rank: { ink: colors.custom_fMaroon, soft: colors.custom_fMaroonSoft, line: colors.custom_fMaroonLine, ...deep, edge: formEdges.rank, text: colors.custom_fMaroonText, name: "Rank predictor", icon: "podium" },
  cutoff: { ink: colors.custom_fTeal, soft: colors.custom_fTealSoft, line: colors.custom_fTealLine, ...light, edge: formEdges.cutoff, text: colors.custom_fTeal, name: "Cut off", icon: "format-list-checks" },
  target: { ink: colors.custom_fLime, soft: colors.custom_fLimeSoft, line: colors.custom_fLimeLine, ...light, edge: formEdges.target, text: colors.custom_fLime, name: "Target marks", icon: "bullseye-arrow" },
  college: { ink: colors.custom_fBlood, soft: colors.custom_fBloodSoft, line: colors.custom_fBloodLine, ...deep, edge: formEdges.college, text: colors.custom_fBloodText,
    name: "College predictor", icon: "school-outline",
    bar: { from: colors.custom_fPurpleFrom, to: colors.custom_fPurpleTo, glow: colors.custom_fPurpleGlow, hint: colors.custom_fPurpleHint, chip: colors.custom_fPurpleChip } },
  compare: { ink: colors.custom_fSky, soft: colors.custom_fSkySoft, line: colors.custom_fSkyLine, ...light, edge: formEdges.compare, text: colors.custom_fSky, name: "College compare", icon: "compare-horizontal" },
  dream: { ink: colors.custom_fViolet, soft: colors.custom_fVioletSoft, line: colors.custom_fVioletLine, ...deep, edge: formEdges.dream, text: colors.custom_fVioletText,
    name: "Dream college", icon: "bullseye-arrow" },
};

/** The open tool's colour (set around each tool pane). */
export const AccentContext = createContext<Accent | null>(null);
/** True inside a form panel (Strip with `form`). */
export const InForm = createContext(false);
export const useAccent = () => useContext(AccentContext);
/** The tool's colour, but only inside its form panel. */
export function useFormAccent() {
  const a = useContext(AccentContext);
  return useContext(InForm) ? a : null;
}

/** The form's main button in the tool's colour. */
export function FormButton({ testID, label, busy, onPress }: { testID: string; label: string; busy?: boolean; onPress: () => void }) {
  const a = useAccent();
  return <Pill testID={testID} size="lg" label={label} iconRight="arrow-right" busy={busy} onPress={onPress}
    bg={a?.ink ?? colors.brandPrimary} ink={a?.on ?? colors.onBrandPrimary} />;
}

/** Text field frame and cursor in the tool's colour. */
export function useField() {
  const a = useAccent();
  return { style: a ? { borderColor: a.line } : null, selectionColor: a?.ink ?? colors.custom_rankBloodInk };
}
