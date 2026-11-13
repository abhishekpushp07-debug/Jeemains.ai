import React, { useCallback } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena } from "@/src/theme";
import { SectionTitle } from "./arena";
import { Jelly, LiveDot } from "./juice";
import { go, useLiveMatches } from "./social";

/** "Live now": matches your friends and gang mates are playing this minute. One tap to watch. Hidden when nobody is playing. */
export function LiveStrip({ uid }: { uid: string }) {
  const router = useRouter();
  const live = useLiveMatches(uid), reload = live.reload;
  useFocusEffect(useCallback(() => {
    reload();
    const iv = setInterval(reload, 8000);
    return () => clearInterval(iv);
  }, [reload]));
  const items = live.data?.items || [];
  if (!items.length) return null;
  return <View testID="rf-live-strip" style={styles.wrap}>
    <SectionTitle title={`Live now (${items.length})`} />
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {items.map((m) => {
        const [a, b] = m.players, group = m.players.length > 2;
        return <Jelly key={m.id} testID={`rf-live-${m.id}`} accessibilityLabel={`Watch ${m.teams ? m.teams.join(" vs ") : m.players.map((p) => p.name).join(" vs ")}`} onPress={() => router.push(go.watch(m.id))} style={styles.card}>
          <View style={styles.head}><LiveDot /><T w="heavy" size={10} color={arena.danger}>{m.started ? "LIVE" : "STARTING"}</T>{m.cup ? <T w="heavy" size={10} color={arena.gold}> · CUP</T> : null}</View>
          <View style={styles.faces}>
            <Avatar icon={a?.avatar} frame={a?.frame} size={34} />
            <T w="heavy" size={14} color={arena.gold}>{group ? `${m.players.length}P` : `${a?.score ?? 0}–${b?.score ?? 0}`}</T>
            {group ? null : <Avatar icon={b?.avatar} frame={b?.frame} size={34} />}
          </View>
          <T w="heavy" size={11} color={arena.text} numberOfLines={1}>{m.teams ? m.teams.join(" vs ") : group ? m.players.map((p) => p.name).join(", ") : `${a?.name} vs ${b?.name}`}</T>
          <T w="bold" size={10} color={arena.aqua} numberOfLines={1}>{m.label} · Watch</T>
        </Jelly>;
      })}
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  wrap: { gap: 8 }, row: { gap: 8, paddingRight: 8 },
  card: { width: 168, gap: 4, padding: 10, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim, borderBottomWidth: 4, borderBottomColor: arena.panelEdge },
  head: { flexDirection: "row", alignItems: "center", gap: 5 },
  faces: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
});
