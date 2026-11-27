// The face of each Rank tool tile: the tool's own colour from corner to corner (maroon, indigo, teal, blood red, gold or
// violet) with a faceted diamond in its corner. There is no black in it; the page behind stays black. ToolGrid lays the
// gloss, the glass glint and the running edge over it.
import React from "react";
import { StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { rankColors as colors, toolEdges } from "@/src/theme";
import { Diamond } from "./Diamond";

export type Jewel = "maroon" | "indigo" | "teal" | "champ" | "blood" | "violet";
/** from / to = the tile, corner to corner; ink = title and icon; soft = the small line; chip / line = the icon circle and its
 *  ring; badge = the word on the white NEW badge; edge = the colours that run round the tile; gloss / glint = its shine. */
type Tone = { from: string; to: string; ink: string; soft: string; chip: string; line: string; badge: string;
  edge: readonly [string, string, ...string[]]; gloss: string; glint: string };
const deep = { ink: colors.custom_tileInk, gloss: colors.custom_tileGloss, glint: colors.custom_tileGlint };
export const JEWELS: Record<Jewel, Tone> = {
  maroon: { ...deep, from: colors.custom_tileMaroon, to: colors.custom_tileMaroonDeep, soft: colors.custom_tileMaroonSoft, chip: colors.custom_tileMaroonChip,
    line: colors.custom_tileMaroonLine, badge: colors.custom_tileMaroonDeep, edge: toolEdges.maroon },
  indigo: { ...deep, from: colors.custom_tileIndigo, to: colors.custom_tileIndigoDeep, soft: colors.custom_tileIndigoSoft, chip: colors.custom_tileIndigoChip,
    line: colors.custom_tileIndigoLine, badge: colors.custom_tileIndigoDeep, edge: toolEdges.indigo },
  teal: { ...deep, from: colors.custom_tileTeal, to: colors.custom_tileTealDeep, soft: colors.custom_tileTealSoft, chip: colors.custom_tileTealChip,
    line: colors.custom_tileTealLine, badge: colors.custom_tileTealDeep, edge: toolEdges.teal },
  blood: { ...deep, from: colors.custom_tileBlood, to: colors.custom_tileBloodDeep, soft: colors.custom_tileBloodSoft, chip: colors.custom_tileBloodChip,
    line: colors.custom_tileBloodLine, badge: colors.custom_tileBloodDeep, edge: toolEdges.blood },
  // Gold is a light colour, so its words are near-black and its shine is stronger.
  champ: { from: colors.custom_tileGold, to: colors.custom_tileGoldDeep, ink: colors.custom_tileGoldInk, soft: colors.custom_tileGoldSoft, chip: colors.custom_tileGoldChip,
    line: colors.custom_tileGoldLine, badge: colors.custom_tileGoldInk, edge: toolEdges.champ, gloss: colors.custom_tileGoldGloss, glint: colors.custom_tileGoldGlint },
  violet: { ...deep, from: colors.custom_tileViolet, to: colors.custom_tileVioletDeep, soft: colors.custom_tileVioletSoft, chip: colors.custom_tileVioletChip,
    line: colors.custom_tileVioletLine, badge: colors.custom_tileVioletDeep, edge: toolEdges.violet },
};

/** The chosen tile's diamond is brighter and carries two sparkles. */
export function JewelFace({ jewel, on }: { jewel: Jewel; on?: boolean }) {
  const j = JEWELS[jewel];
  return <>
    <LinearGradient pointerEvents="none" colors={[j.from, j.to]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <Diamond width={46} tint={colors.custom_tileInk} sparkle={on} opacity={on ? 0.75 : 0.45} style={styles.gem} />
  </>;
}

const styles = StyleSheet.create({
  gem: { position: "absolute", right: -8, bottom: -9 },
});
