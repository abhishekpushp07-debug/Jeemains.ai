// The small parts of a matched question's card, shared by the shift's list (Pair.tsx) and the Matched paper (PaperQuestion.tsx).
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { GlossWord } from "@/src/components/GlossWord";
import type { TabLook } from "@/src/components/GlossTabs";
import { colors, space, tabEdges } from "@/src/theme";
import { MatchedItem, SHORT } from "./api";

const WHITE = colors.custom_chipBloodInk, YELLOW = colors.custom_glossYellow, INK = colors.custom_matchedInk;
export const PAD = 14, BOX = 12;

// Matched's two tab colours, from My Tests' glossy tabs: flame for JEE Main, sun yellow for ours.
export const FLAME: TabLook = { on: [colors.custom_tabOrange, colors.custom_tabOrangeDeep], rest: [colors.custom_tabOrangeSoft, colors.custom_tabOrangeSoftDeep], edge: tabEdges.orange, glow: colors.custom_tabOrangeGlow };
export const SUN: TabLook = { on: [colors.custom_tabSun, colors.custom_tabSunDeep], rest: [colors.custom_tabSunSoft, colors.custom_tabSunSoftDeep], edge: tabEdges.sun, glow: colors.custom_tabSunGlow };

// Which tab a card was showing, kept while its shift is open: a card that scrolls far away is taken down by the list, and
// comes back as the student left it.
export const kept = new Map<number, "question" | "solution">();

/** The card's glossy red top: a word in glossy yellow (the question's number), its subject and its chapter. */
export function Ribbon({ it, id, word }: { it: Pick<MatchedItem, "subject" | "chapter">; id: string; word?: string }) {
  return <LinearGradient colors={[colors.custom_matchedFrom, colors.custom_matchedMid, colors.custom_matchedTo]} locations={[0, 0.6, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.ribbon}>
    <LinearGradient pointerEvents="none" colors={[colors.custom_fireGloss, colors.custom_clear]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.gloss} />
    {word ? <GlossWord testID={`${id}-number`} size={19}>{word}</GlossWord> : null}
    {it.subject ? <View style={styles.subject}><T w="heavy" size={10.5} color={WHITE} style={styles.caps} numberOfLines={1}>{(SHORT[it.subject] || it.subject).toUpperCase()}</T></View> : null}
    <T w="semibold" size={12.5} color={WHITE} numberOfLines={1} style={styles.chapter}>{it.chapter}</T>
    <View style={styles.seal}><Glyph name="check" size={15} color={INK} stroke={2.6} /></View>
  </LinearGradient>;
}

/** Whose question follows ("JEE MAIN 2027", "HAMARA QUESTION"), where it was asked, and how close the match is. */
export function SideHead({ label, tint, detail, tag, testID }: { label: string; tint: string; detail?: string; tag?: string; testID?: string }) {
  return <View style={styles.head}>
    <View style={styles.label}>
      <View style={[styles.dot, { backgroundColor: tint }]} />
      <T w="heavy" size={10.5} color={tint} style={styles.caps}>{label}</T>
    </View>
    {detail ? <T testID={testID} w="bold" size={12} color={colors.custom_softText} numberOfLines={1} style={styles.detail}>{detail}</T> : null}
    {tag ? <View style={styles.tag}><T w="heavy" size={10} color={INK} style={styles.tagText} numberOfLines={1}>{tag.toUpperCase()}</T></View> : null}
  </View>;
}

/** Between the JEE question and ours when both are on the card together: how close the match is ("SAME CONCEPT"). */
export function Seal({ tag, testID }: { tag?: string; testID?: string }) {
  return <View style={styles.join}>
    <View style={styles.rule} />
    <View style={styles.joint}>
      <Glyph name="compare-horizontal" size={13} color={INK} stroke={2.2} />
      <T testID={testID} w="heavy" size={10} color={INK} style={styles.tagText} numberOfLines={1}>{(tag || "Matched").toUpperCase()}</T>
    </View>
    <View style={styles.rule} />
  </View>;
}

export const cardStyles = StyleSheet.create({
  card: { borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, overflow: "hidden" },
  body: { gap: space.md, padding: PAD },
  // Whose question it is can be told from its paper: the JEE Main one lies on soft red, ours on soft gold.
  panel: { gap: 10, padding: BOX, borderRadius: 16 },
  jee: { backgroundColor: colors.custom_chipBloodSoft },
  ours: { backgroundColor: colors.custom_goldSoft },
});

const styles = StyleSheet.create({
  ribbon: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 50, paddingVertical: 8, paddingLeft: PAD, paddingRight: 10 },
  gloss: { position: "absolute", left: 0, right: 0, top: 0, height: "56%" },
  subject: { height: 24, paddingHorizontal: 9, borderRadius: 12, justifyContent: "center", borderWidth: 1, borderColor: colors.custom_fireLine, backgroundColor: colors.custom_fireGlass },
  chapter: { flex: 1, minWidth: 0 },
  seal: { width: 30, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center", backgroundColor: YELLOW },
  caps: { letterSpacing: 1.4 },
  head: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 8 },
  label: { flexDirection: "row", alignItems: "center", gap: 6 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  detail: { flexShrink: 1 },
  tag: { height: 22, paddingHorizontal: 9, borderRadius: 11, justifyContent: "center", backgroundColor: YELLOW },
  tagText: { letterSpacing: 1 },
  join: { flexDirection: "row", alignItems: "center", gap: space.sm },
  rule: { flex: 1, minWidth: 12, height: 1, backgroundColor: colors.custom_cardLineStrong },
  joint: { flexDirection: "row", alignItems: "center", gap: 5, height: 24, paddingHorizontal: 10, borderRadius: 12, backgroundColor: YELLOW, flexShrink: 1 },
});
