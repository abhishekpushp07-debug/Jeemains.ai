import React, { useCallback, useEffect } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Easing, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import Svg, { Path } from "react-native-svg";
import { T } from "@/src/components/ui";
import { arena, fx } from "@/src/theme";
import { Alive, GameIcon } from "./Art";
import { GoldTitle, Panel, RaisedButton } from "./arena";
import { Pop, Twinkles } from "./juice";
import { Crown, Face } from "./parts";
import { CrownArt } from "./CrownArt";
import { Champion, go, useChampions } from "./social";

/** One champion on the wall: their crown over their face, the cup they won, and the Cheer button. */
function ChampCard({ c, i, onCheer }: { c: Champion; i: number; onCheer: () => void }) {
  const gold = (c.crown?.real || 0) > 0;
  return <Pop delay={i * 70}>
    <View testID={`rf-champ-${c.pid}`} style={[styles.card, c.you && styles.cardYou]}>
      <Alive kind="float" delay={i * 300}><CrownArt size={44} gold={gold} /></Alive>
      <Face p={c} size={58} />
      <T w="heavy" size={13} color={arena.text} numberOfLines={1} style={styles.center}>{c.you ? "You!" : c.name}</T>
      <View style={styles.inline}><Crown c={c.crown} /><T w="bold" size={10.5} color={arena.muted} numberOfLines={1}>Cup {c.no} · {c.size}</T></View>
      <RaisedButton testID={`rf-champ-${c.pid}-cheer`} glyph="party-popper" height={40} label="CHEER" onPress={onCheer} style={styles.stretch} />
    </View>
  </Pop>;
}

/** Golden light turning slowly behind the top champion. */
function SpotRays({ size }: { size: number }) {
  const reduced = !!useReducedMotion();
  const t = useSharedValue(0);
  useEffect(() => {
    if (reduced) return;
    t.value = withRepeat(withTiming(1, { duration: 14000, easing: Easing.linear }), -1, false);
    return () => cancelAnimation(t);
  }, [reduced]); // eslint-disable-line react-hooks/exhaustive-deps
  const spin = useAnimatedStyle(() => ({ transform: [{ rotate: `${t.value * 360}deg` }] }));
  const c = size / 2, rays = Array.from({ length: 12 }, (_, i) => (i / 12) * Math.PI * 2);
  return <Animated.View pointerEvents="none" style={[styles.rays, { width: size, height: size, marginLeft: -c, marginTop: -c }, spin]}>
    <Svg width={size} height={size}>{rays.map((a) => <Path key={a} fill={arena.gold} opacity={0.14}
      d={`M${c} ${c} L${c + Math.cos(a - 0.11) * c} ${c + Math.sin(a - 0.11) * c} L${c + Math.cos(a + 0.11) * c} ${c + Math.sin(a + 0.11) * c} Z`} />)}</Svg>
  </Animated.View>;
}

/** The top champion of the night (most crowns overall): a golden spotlight card above the rest of the wall. */
function Spotlight({ c, onCheer }: { c: Champion; onCheer: () => void }) {
  const gold = (c.crown?.real || 0) > 0;
  return <Pop>
    <View testID="rf-champ-spotlight" style={styles.spot}>
      <LinearGradient pointerEvents="none" colors={[arena.gold, arena.goldDeep, arena.panel]} locations={[0, 0.45, 1]} style={StyleSheet.absoluteFill} />
      <View style={styles.raysAt}><SpotRays size={300} /></View>
      <Twinkles spots={[[8, 18, 14], [92, 14, 12], [70, 8, 10], [20, 80, 10], [88, 76, 12]]} />
      <View style={styles.spotRow}>
        <View style={styles.spotFace}>
          <Alive kind="float"><CrownArt size={56} gold={gold} /></Alive>
          <Face p={c} size={76} />
        </View>
        <View style={styles.flex}>
          <T w="heavy" size={10.5} color={arena.badgeInk} style={styles.spaced} numberOfLines={1}>★ TOP CHAMPION ★</T>
          <T testID="rf-champ-spotlight-name" w="heavy" size={22} color={fx.white} numberOfLines={1} style={styles.glow}>{c.you ? "You!" : c.name}</T>
          <View style={styles.inline}><Crown c={c.crown} size="lg" /><T w="heavy" size={12} color={fx.white} numberOfLines={1}>{c.crown?.won || 1} crown{(c.crown?.won || 1) === 1 ? "" : "s"} · Cup {c.no} · {c.size}</T></View>
        </View>
      </View>
      <RaisedButton testID="rf-champ-spotlight-cheer" glyph="party-popper" height={52} streak label="CHEER THE TOP CHAMPION" onPress={onCheer} style={styles.stretch} />
    </View>
  </Pop>;
}

/**
 * Champions Wall in the lobby: the last Cup Night's champions, from the moment they are crowned until the next night's
 * doors open. The one with the most crowns gets the golden spotlight. Cheer one and their cheer squad dances in their trophy cabinet.
 */
export function ChampionsWall({ uid }: { uid: string }) {
  const router = useRouter();
  const q = useChampions(uid), reload = q.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const d = q.data, items = d?.items || [];
  if (!d?.day || !items.length) return null;
  const top = [...items].sort((x, y) => (y.crown?.won || 0) - (x.crown?.won || 0) || x.no - y.no)[0], rest = items.filter((c) => c !== top);
  return <Panel gold testID="rf-champions-wall" style={styles.wall}>
    <LinearGradient pointerEvents="none" colors={[arena.goldSoft, arena.clear]} style={StyleSheet.absoluteFill} />
    <View style={styles.head}>
      <Alive kind="breathe"><GameIcon name="trophy" size={44} /></Alive>
      <View style={styles.flex}>
        <T w="heavy" size={10.5} color={arena.aqua} style={styles.spaced} numberOfLines={1}>CHAMPIONS WALL · CUP NIGHT</T>
        <GoldTitle size={20} testID="rf-champions-title">{d.tonight ? "Tonight’s champions" : "Last night’s champions"}</GoldTitle>
      </View>
      <View style={styles.count}><T testID="rf-champions-count" w="heavy" size={13} color={arena.badgeInk}>{items.length}</T></View>
    </View>
    <Spotlight c={top} onCheer={() => router.push(go.cheer(top.pid))} />
    {rest.length ? <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row} testID="rf-champions-list">
      {rest.map((c, i) => <ChampCard key={c.cup_id} c={c} i={i} onCheer={() => router.push(go.cheer(c.pid))} />)}
    </ScrollView> : null}
    <T w="bold" size={11} color={arena.muted} style={styles.center}>Tap Cheer and their cheer squad dances in the trophy cabinet. Next Cup Night at {d.time_label}.</T>
  </Panel>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 1.5 }, stretch: { alignSelf: "stretch" },
  inline: { flexDirection: "row", alignItems: "center", gap: 4 },
  wall: { padding: 12, gap: 10, overflow: "hidden" },
  head: { flexDirection: "row", alignItems: "center", gap: 10 },
  count: { minWidth: 30, height: 30, paddingHorizontal: 8, borderRadius: 15, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
  row: { gap: 10, paddingRight: 4 },
  card: { width: 124, alignItems: "center", gap: 4, paddingHorizontal: 8, paddingTop: 4, paddingBottom: 10, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.goldDeep },
  cardYou: { borderColor: arena.gold, backgroundColor: arena.panelHi },
  spot: { borderRadius: 20, borderWidth: 2.5, borderColor: arena.gold, borderBottomWidth: 5, borderBottomColor: arena.goldDeep, padding: 12, gap: 10, overflow: "hidden" },
  spotRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  spotFace: { alignItems: "center", marginTop: -6 },
  raysAt: { position: "absolute", left: 60, top: 50 },
  rays: { position: "absolute" },
  glow: { textShadowColor: arena.black, textShadowRadius: 6, textShadowOffset: { width: 0, height: 1 } },
});
