// Home's Misfire card, as on jeelive.ai: how many wrong or skipped questions wait to be solved again, by subject.
// Blood red with white words and its name in glossy yellow; a soft gloss, a glass glint from corner to corner, and a row
// of lights (sun yellow, white, aqua) running round its rim.
import React from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { GlossWord } from "@/src/components/GlossWord";
import { Shine } from "@/src/analysis/Shine";
import { ScreenMotion } from "@/src/motion";
import { colors, dotEdges, space } from "@/src/theme";
import { MisfireSummary, getSummary, misfireKey } from "./api";
import { slugOf } from "./parts";

const WHITE = colors.custom_chipBloodInk;

export function HomeMisfire() {
  const router = useRouter();
  const { user } = useAuth();
  const res = useCached<MisfireSummary>(user ? `${misfireKey(user.id)}.summary` : null, getSummary);
  useListFocus(res.revalidate);
  const d = res.data;
  // Nothing is shown before a first graded paper: there is nothing to solve again yet.
  if (!d || !(d.open + d.fixed)) return null;
  const subjects = d.subjects.filter(s => s.open > 0);
  // The card's shine rests while another tab or screen is in front.
  return <ScreenMotion>
    <Press testID="home-misfire" onPress={() => router.push("/misfire" as any)} scaleTo={0.985} style={styles.press}
      accessibilityLabel={d.open ? `Misfire. ${d.open} sawaal dobara solve karne hain` : "Misfire. Saari galtiyan samajh li"}>
      <Shine radius={24} ring={6} dots={colors.custom_misfireRim} edge={dotEdges.misfire} gloss={colors.custom_fireGloss} glint={colors.custom_fireGlint} band={84} part={46} corner face={styles.card}
        backdrop={<LinearGradient pointerEvents="none" colors={[colors.custom_chipBlood, colors.custom_chipBloodDeep]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />}>
        <View style={styles.icon}><Glyph name="crosshairs" size={26} color={WHITE} stroke={1.5} /></View>
        <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
          <View style={styles.top}>
            <GlossWord testID="home-misfire-title">MISFIRE</GlossWord>
            {d.open ? <View style={styles.badge}><T testID="home-misfire-open" w="bold" size={10} color={WHITE} style={{ letterSpacing: 1.2 }}>{d.open} OPEN</T></View> : null}
          </View>
          <T testID="home-misfire-line" size={13.5} w="semibold" color={WHITE} numberOfLines={2}>{d.open ? `${d.open} sawaal dobara solve karne hain` : "Saari galtiyan samajh li. Shabash!"}</T>
          {subjects.length ? <View style={styles.chips}>
            {subjects.map(s => <View key={s.name} testID={"home-misfire-subject-" + slugOf(s.name)} style={styles.chip}><T w="bold" size={11.5} color={WHITE}>{s.name} {s.open}</T></View>)}
          </View> : null}
        </View>
        <Glyph name="chevron-right" size={18} color={WHITE} />
      </Shine>
    </Press>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  press: { borderRadius: 24 },
  // 11 inside the 6-point rim of lights: the card is the size it was with its 1-point line and 16 of padding.
  card: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.lg - 5 },
  // Clear glass on the red: the icon circle and the subject chips; the count sits on a darker shade.
  icon: { width: 50, height: 50, borderRadius: 25, backgroundColor: colors.custom_fireGlass, borderWidth: 1, borderColor: colors.custom_fireLine, alignItems: "center", justifyContent: "center" },
  top: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  badge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4, backgroundColor: colors.custom_fireShade },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 2 },
  chip: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3, backgroundColor: colors.custom_fireGlass, borderWidth: 1, borderColor: colors.custom_fireLine },
});
