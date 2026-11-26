// The All India series as one bar on Home. From JEE Main's first published shift the Matched card has the big card's
// place (src/matched/gate.tsx); the series keeps this bar right under it for its remaining days, and the bar goes when
// the series is over (the series and its archive stay under Explore). One tap does what the big card's button did:
// today's test, the running attempt, its result, or the series hub.
import React from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { DayInfo, Series } from "@/src/series";
import { cardState } from "./HomeSeriesCard";

export function HomeSeriesBar({ series, days }: { series: Series; days: DayInfo[] }) {
  const router = useRouter();
  const narrow = useWindowDimensions().width < 360;
  const st = cardState(series, days);
  // "Live today · Start today's test"; a day with nothing to tap into says only how it stands ("Awaiting paper").
  const plain = st.tone === "upcoming" || st.action.to === "/live" && st.action.icon === "arrow-right";
  const line = plain ? st.status : `${st.status} · ${st.action.label}`;
  return (
    <Press testID="home-series-bar" onPress={() => router.push(st.action.to as any)} scaleTo={0.985} style={styles.bar}
      accessibilityLabel={`All India series. ${st.right}. ${line}. Open`}>
      <View style={styles.words}>
        <View style={styles.top}>
          <View style={styles.live} />
          <T w="bold" size={10.5} color={colors.onSurfaceInverse} style={styles.caps} numberOfLines={1}>{narrow ? "ALL INDIA" : "ALL INDIA SERIES"}</T>
          <T testID="home-series-bar-day" w="bold" size={10.5} color={colors.custom_whiteA70} style={[narrow ? styles.tight : styles.caps, styles.day]} numberOfLines={1}>· {st.right}</T>
        </View>
        <T testID="home-series-bar-line" w="heavy" size={15} color={colors.onSurfaceInverse} numberOfLines={2}>{line}</T>
      </View>
      <View style={styles.go}><Glyph name={st.action.icon} size={18} color={colors.onBrandPrimary} stroke={2} /></View>
    </Press>
  );
}

const styles = StyleSheet.create({
  // The series' own onyx, so it is still the All India series at a glance; no shine: it is a bar, not the card.
  bar: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 68, paddingVertical: 12, paddingLeft: 16, paddingRight: 12, borderRadius: 20, backgroundColor: colors.custom_series },
  words: { flex: 1, minWidth: 0, gap: 4 },
  top: { flexDirection: "row", alignItems: "center", gap: 7 },
  live: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.brandPrimary },
  caps: { letterSpacing: 2 },
  tight: { letterSpacing: 1 },
  day: { flexShrink: 1 },
  go: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center" },
});
