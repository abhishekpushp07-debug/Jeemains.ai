// Each Rank tool's form colour: Rank predictor bright yellow, Percentile se rank teal, Target marks lime, College predictor
// blood red, College compare sky blue. The chosen tile glows in it and the form below wears it (frame, header band, chosen chips,
// fields and the main button), so the student sees at once which form belongs to the tile they tapped.
import React, { createContext, useContext } from "react";
import type { IconName } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { rankColors as colors } from "@/src/theme";
import type { Tool } from "./ToolGrid";

/** ink = the colour (fills), on = text on it, text = the colour for words, icons and tile glow on black.
 *  bar = the score bar after Show in its own look (College predictor: shining purple), with the Edit button in `ink`. */
export type Accent = { ink: string; soft: string; line: string; on: string; text: string; name: string; icon: IconName;
  bar?: { from: string; to: string; glow: string; hint: string; chip: string } };
const on = colors.custom_fOn;
export const ACCENTS: Record<Tool, Accent> = {
  rank: { ink: colors.custom_fYellow, soft: colors.custom_fYellowSoft, line: colors.custom_fYellowLine, on, text: colors.custom_fYellow, name: "Rank predictor", icon: "podium" },
  pct: { ink: colors.custom_fTeal, soft: colors.custom_fTealSoft, line: colors.custom_fTealLine, on, text: colors.custom_fTeal, name: "Percentile se rank", icon: "chart-line-variant" },
  target: { ink: colors.custom_fLime, soft: colors.custom_fLimeSoft, line: colors.custom_fLimeLine, on, text: colors.custom_fLime, name: "Target marks", icon: "bullseye-arrow" },
  college: { ink: colors.custom_fBlood, soft: colors.custom_fBloodSoft, line: colors.custom_fBloodLine, on: colors.onBrandPrimary, text: colors.custom_fBloodText,
    name: "College predictor", icon: "school-outline",
    bar: { from: colors.custom_fPurpleFrom, to: colors.custom_fPurpleTo, glow: colors.custom_fPurpleGlow, hint: colors.custom_fPurpleHint, chip: colors.custom_fPurpleChip } },
  compare: { ink: colors.custom_fSky, soft: colors.custom_fSkySoft, line: colors.custom_fSkyLine, on, text: colors.custom_fSky, name: "College compare", icon: "compare-horizontal" },
  dream: { ink: colors.custom_fViolet, soft: colors.custom_fVioletSoft, line: colors.custom_fVioletLine, on: colors.onBrandPrimary, text: colors.custom_fVioletText,
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
