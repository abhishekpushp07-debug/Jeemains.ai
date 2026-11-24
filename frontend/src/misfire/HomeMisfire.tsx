// Home's Misfire card, as on jeelive.ai: how many wrong or skipped questions wait to be solved again, by subject.
import React from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { MisfireSummary, getSummary, misfireKey } from "./api";
import { slugOf } from "./parts";

export function HomeMisfire() {
  const router = useRouter();
  const { user } = useAuth();
  const res = useCached<MisfireSummary>(user ? `${misfireKey(user.id)}.summary` : null, getSummary);
  useListFocus(res.revalidate);
  const d = res.data;
  // Nothing is shown before a first graded paper: there is nothing to solve again yet.
  if (!d || !(d.open + d.fixed)) return null;
  const subjects = d.subjects.filter(s => s.open > 0);
  return <Press testID="home-misfire" onPress={() => router.push("/misfire" as any)} scaleTo={0.985}
    accessibilityLabel={d.open ? `Misfire. ${d.open} sawaal dobara solve karne hain` : "Misfire. Saari galtiyan samajh li"}>
    <LinearGradient colors={[colors.custom_chipFrom, colors.custom_chipTo]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.card}>
      <View style={styles.icon}><Glyph name="crosshairs" size={26} color={colors.custom_royalMaroon} stroke={1.5} /></View>
      <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
        <View style={styles.top}>
          <T testID="home-misfire-title" w="heavy" size={17} color={colors.custom_royalMaroon} style={{ letterSpacing: 1 }}>MISFIRE</T>
          {d.open ? <View style={styles.badge}><T testID="home-misfire-open" w="bold" size={10} color={colors.brandText} style={{ letterSpacing: 1.2 }}>{d.open} OPEN</T></View> : null}
        </View>
        <T testID="home-misfire-line" size={13.5} w="semibold" color={colors.muted} numberOfLines={2}>{d.open ? `${d.open} sawaal dobara solve karne hain` : "Saari galtiyan samajh li. Shabash!"}</T>
        {subjects.length ? <View style={styles.chips}>
          {subjects.map(s => <View key={s.name} testID={"home-misfire-subject-" + slugOf(s.name)} style={styles.chip}><T w="bold" size={11.5} color={colors.custom_royalMaroon}>{s.name} {s.open}</T></View>)}
        </View> : null}
      </View>
      <Glyph name="chevron-right" size={18} color={colors.muted} />
    </LinearGradient>
  </Press>;
}

const styles = StyleSheet.create({
  card: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.lg, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  icon: { width: 50, height: 50, borderRadius: 25, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  top: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  badge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4, backgroundColor: colors.brandTertiary },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 2 },
  chip: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4, backgroundColor: colors.brandTertiary },
});
