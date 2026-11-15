import React from "react";
import { Share, View } from "react-native";
import { T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { DSheet, Pill } from "./design";

export type { Series, Slot } from "@/src/series";

export function SeriesExplainer({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <DSheet visible={open} onClose={onClose} testID="series-explainer" title="How it works">
      <T w="heavy" size={10} color={colors.brandText} style={{ letterSpacing: 1.8 }}>THE DAILY FULL-SYLLABUS CHALLENGE</T>
      <T w="heavy" size={22}>62 days. One focused mission.</T>
      <View style={{ flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        <T w="heavy" size={14} color={colors.brandText}>Score 200+ with AI</T>
        <T size={13} color={colors.muted}>· AI analysed PYQ based test series · Created by <T w="heavy" size={13}>AI Astra</T></T>
      </View>
      {[
        "One full mock each day · 75 questions · 300 marks · 180 minutes.",
        "Live window 12:01 AM–11:59 PM IST. Last start 8:59 PM IST.",
        "One live attempt per profile. Resume keeps the original deadline.",
        "Live results and solutions unlock at 11:59 PM IST for fairness.",
        "Previous days open in the practice archive at midnight.",
        "Your streak grows with each live day you finish. Archive practice doesn’t count.",
      ].map((x) => (
        <View key={x} style={{ flexDirection: "row", gap: space.sm, alignItems: "flex-start" }}>
          <Glyph name="check-circle-outline" size={18} color={colors.success} />
          <T size={13.5} color={colors.custom_softText} style={{ flex: 1 }}>{x}</T>
        </View>
      ))}
      <T size={11} color={colors.custom_eyebrow} testID="series-claims-disclaimer">
        Independent practice, not affiliated with NTA. The 80-factor PYQ analysis is the series’ stated design approach, not an AI prediction of the official paper. “AI Astra” and “100% AI” describe the creator’s AI-led design, not an audit of every explanation. “World best” is an ambition, not a verified ranking. “Score 200+ with AI” is a practice goal, not a guarantee.
      </T>
      <Pill testID="series-explainer-close" label="Got it" onPress={onClose} />
    </DSheet>
  );
}

export function useShare() {
  return () =>
    Share.share({ message: "JEELIVE.AI — free JEE Main, BITSAT & COMEDK practice: chapter tests, 62-day All India series and 15-second Rapid Fire formula cards. Free for everyone. https://jeelive.ai" }).catch(() => {});
}
