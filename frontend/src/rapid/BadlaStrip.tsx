import React, { useCallback } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { T } from "@/src/components/ui";
import { arena, fx } from "@/src/theme";
import { Alive, GameIcon } from "./Art";
import { SectionTitle } from "./arena";
import { useBadla } from "./HeadToHead";
import { Jelly } from "./juice";
import { Face } from "./parts";
import { ErrorBox } from "./ui";
import { useBadlaPending } from "./social";

/**
 * "Badla pending": friends who beat you in your latest 1 v 1s. One tap picks the battleground and sends the revenge
 * challenge. A friend leaves the strip when you win one back, or after 5 losses in a row. Hidden when you owe nobody.
 */
export function BadlaStrip({ uid }: { uid: string }) {
  const q = useBadlaPending(uid), reload = q.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const { badla, busy, error, sheet } = useBadla(uid);
  const items = q.data?.items || [], max = q.data?.max || 5;
  if (!items.length) return null;
  return <View testID="rf-badla-strip" style={styles.wrap}>
    <SectionTitle title={`Badla pending (${items.length})`} />
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {items.map((f) => <Jelly key={f.pid} testID={`rf-badla-${f.pid}`} disabled={!!busy} onPress={() => badla(f.match_id, f.picks, f.name)}
        accessibilityLabel={`Badla pending against ${f.name}. You lost ${f.streak} in a row. Take your revenge`} style={styles.card}>
        <LinearGradient colors={[arena.panelHi, arena.panel]} style={styles.face}>
          <View style={styles.chip}><Alive kind="breathe"><GameIcon name="flame" size={15} /></Alive><T w="heavy" size={9} color={arena.badgeInk} style={styles.spaced} numberOfLines={1}>BADLA PENDING</T></View>
          <Face p={f} size={56} />
          <T w="heavy" size={13} color={arena.text} numberOfLines={1}>{f.name}</T>
          <T testID={`rf-badla-${f.pid}-streak`} w="bold" size={11} color={arena.danger} numberOfLines={1}>Lost {f.streak} in a row</T>
          {/* One dot a loss: at the fifth the Badla is dropped. */}
          <View style={styles.dots}>{Array.from({ length: max }, (_, i) => <View key={i} style={[styles.dot, i < f.streak && styles.dotLost, i === max - 1 && styles.dotLast]} />)}</View>
          <View style={styles.go}><T w="heavy" size={12} color={arena.text}>{busy === f.match_id ? "SENDING…" : "BADLA LO"}</T></View>
        </LinearGradient>
      </Jelly>)}
    </ScrollView>
    <ErrorBox testID="rf-badla-strip-error" error={error} />
    {sheet}
  </View>;
}

const styles = StyleSheet.create({
  wrap: { gap: 8 }, row: { gap: 10, paddingRight: 8, paddingTop: 6 }, spaced: { letterSpacing: 0.8 },
  card: { width: 150, borderRadius: 20, borderWidth: 1.5, borderColor: fx.fire, borderBottomWidth: 4, borderBottomColor: arena.panelEdge, overflow: "hidden" },
  face: { alignItems: "center", gap: 4, paddingHorizontal: 8, paddingTop: 10, paddingBottom: 10 },
  chip: { flexDirection: "row", alignItems: "center", gap: 3, height: 22, paddingHorizontal: 7, borderRadius: 11, backgroundColor: fx.ember, borderWidth: 1, borderColor: fx.fire, marginBottom: 2 },
  dots: { flexDirection: "row", gap: 4, marginVertical: 2 },
  dot: { width: 9, height: 9, borderRadius: 5, backgroundColor: arena.panelEdge, borderWidth: 1, borderColor: arena.rim },
  dotLost: { backgroundColor: fx.crimson, borderColor: arena.danger }, dotLast: { borderStyle: "dashed" },
  go: { alignSelf: "stretch", height: 36, borderRadius: 12, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline, borderBottomWidth: 3, borderBottomColor: arena.tealDeep },
});
