import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Icon, T, tap } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena, fx } from "@/src/theme";
import { GEM_LABEL, GEM_ORDER, Gem, PhoenixDiamond, topGem } from "./Art";
import { ArenaBg, OnlineDot, ScreenTop } from "./arena";
import { Jelly, Pop } from "./juice";
import { Glitter } from "./Glitter";
import { Crown as CrownT, PlayerCard } from "./social";

type Person = Partial<Omit<PlayerCard, "pid">> & { pid?: string | null; name?: string };

/** A player's portrait with the green online dot. Tapping it opens their profile when `onPress` is given. */
export function Face({ p, size = 46, onPress, testID }: { p: Person; size?: number; onPress?: () => void; testID?: string }) {
  const body = <View><Avatar icon={p.avatar} frame={p.frame} size={size} />{p.online ? <View style={styles.dot}><OnlineDot size={Math.max(12, size * 0.26)} /></View> : null}</View>;
  return onPress ? <Jelly testID={testID} onPress={onPress} accessibilityLabel={`${p.name || "Player"}, open profile`}>{body}</Jelly> : body;
}

/** A player's portrait between Phoenix wings in the colour of the rarest diamond they have won. */
export function WingedFace({ p, diamonds, size = 104, testID }: { p: Person; diamonds?: Record<string, number> | null; size?: number; testID?: string }) {
  const tier = topGem(diamonds);
  return <View testID={testID} accessibilityLabel={`${GEM_LABEL[tier]} Phoenix wings`} style={styles.winged}>
    <PhoenixDiamond width={size * 2.5} color={tier} breathe wingsOnly testID={testID ? `${testID}-${tier}` : undefined} />
    <View style={[StyleSheet.absoluteFill, styles.winged]}><Face p={p} size={size} /></View>
  </View>;
}

export function PersonRow({ p, sub, right, onPress, testID, selected }: { p: Person; sub?: string; right?: React.ReactNode; onPress?: () => void; testID?: string; selected?: boolean }) {
  return <Glitter testID={testID} radius={18} sparkles={1} inner={[styles.row, selected && styles.rowOn]}>
    <Pressable onPress={onPress ? () => { tap(); onPress(); } : undefined} disabled={!onPress} accessibilityRole="button" accessibilityLabel={`${p.name || "Player"}${crownText(p.crown)}`} accessibilityState={{ selected: !!selected }} style={styles.rowMain}>
      <Face p={p} />
      <View style={styles.flex}>
        <NameLine name={p.name || "Player"} crown={p.crown} testID={testID ? `${testID}-crown` : undefined} />
        {sub ? <T w="bold" size={12} color={p.online ? arena.online : arena.muted} numberOfLines={1}>{sub}</T> : null}
      </View>
    </Pressable>
    {right}
  </Glitter>;
}

/** Read out after a name in a row's label: ", Cup Champion ×3". Empty when the player has no crown. */
export const crownText = (c?: CrownT | null) => (c?.won ? `, Cup Champion${c.won > 1 ? ` ×${c.won}` : ""}` : "");

/**
 * The Cup Champion crown: gold once a Knockout Cup is won against real players, silver while every title came from
 * practice-rival cups. Shows ×N for more than one cup.
 */
export function Crown({ c, size = "sm", testID }: { c?: CrownT | null; size?: "sm" | "lg"; testID?: string }) {
  if (!c?.won) return null;
  const gold = c.real > 0, big = size === "lg", ink = gold ? arena.badgeInk : arena.panelEdge;
  return <View testID={testID} accessible accessibilityLabel={`Cup Champion, ${c.won} cup${c.won === 1 ? "" : "s"} won${c.real ? `, ${c.real} against real players` : ", practice cups"}`}
    style={[styles.crown, big && styles.crownBig, gold ? styles.crownGold : styles.crownSilver]}>
    <Icon name="crown" size={big ? 20 : 13} color={ink} />
    {c.won > 1 ? <T w="heavy" size={big ? 14 : 10} color={ink}>×{c.won}</T> : null}
  </View>;
}

/** A player's name with their champion crown right after it. */
export function NameLine({ name, crown, size = 15, color = arena.text, testID }: { name: string; crown?: CrownT | null; size?: number; color?: string; testID?: string }) {
  return <View style={styles.nameLine}>
    <T w="heavy" size={size} color={color} numberOfLines={1} style={styles.shrink}>{name}</T>
    <Crown c={crown} testID={testID} />
  </View>;
}

/** Tick box used when picking several friends. */
export function Check({ on }: { on: boolean }) {
  return <View style={[styles.check, on && styles.checkOn]}>{on ? <Icon name="check-bold" size={16} color={arena.text} /> : null}</View>;
}

/** The five streak diamonds with how many the player owns. Colours never won stay as a dark shape. */
export function GemStrip({ diamonds, size = 40, labels, pop, wings }: { diamonds?: Record<string, number> | null; size?: number; labels?: boolean; pop?: boolean; wings?: boolean }) {
  return <View style={styles.gems}>{GEM_ORDER.map((c, i) => {
    const n = diamonds?.[c] || 0;
    // `wings`: a diamond you own shows as the full Phoenix, with wings in that diamond's own colour.
    const cell = <>{wings && n ? <PhoenixDiamond width={size * 1.7} color={c} testID={`gem-${c}`} /> : <Gem color={c} size={size} locked={!n} testID={`gem-${c}`} />}
      <T testID={`gem-count-${c}`} w="heavy" size={size > 44 ? 18 : 13} color={n ? arena.text : arena.faint}>{n}</T>
      {labels ? <T w="bold" size={10} color={n ? arena.aqua : arena.faint}>{GEM_LABEL[c]}</T> : null}</>;
    return pop ? <Pop key={c} delay={i * 90} style={styles.gem}>{cell}</Pop> : <View key={c} style={styles.gem}>{cell}</View>;
  })}</View>;
}

export function Bar({ value, color = arena.teal }: { value: number; color?: string }) {
  return <View style={styles.track}><View style={[styles.fill, { width: `${Math.max(0, Math.min(1, value)) * 100}%`, backgroundColor: color }]} /></View>;
}

export function Note({ children, testID }: { children: React.ReactNode; testID?: string }) {
  return <T testID={testID} size={13} color={arena.muted} style={styles.note}>{children}</T>;
}

/** Inner arena screen: crimson stage, raised Back button and a scrolling body. `footer` stays above the keyboardless bottom edge. */
export function InnerScreen({ title, sub, right, children, testID, footer, onScroll }: { title: string; sub?: string; right?: React.ReactNode; children: React.ReactNode; testID: string; footer?: React.ReactNode; onScroll?: (y: number, height: number) => void }) {
  const insets = useSafeAreaInsets(), router = useRouter();
  return <ArenaBg testID={testID}>
    <View style={[styles.inner, { paddingTop: insets.top + 6 }]}>
      <ScreenTop title={title} sub={sub} right={right} testID={testID} onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"))} />
      <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} scrollEventThrottle={100}
        onScroll={onScroll ? (e) => onScroll(e.nativeEvent.contentOffset.y, e.nativeEvent.layoutMeasurement.height) : undefined} contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 28 }]}>{children}</KeyboardAwareScrollView>
      {footer ? <View style={[styles.footer, { paddingBottom: insets.bottom + 10 }]}>{footer}</View> : null}
    </View>
  </ArenaBg>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, dot: { position: "absolute", right: -1, bottom: -1 }, winged: { alignItems: "center", justifyContent: "center" },
  nameLine: { flexDirection: "row", alignItems: "center", gap: 6, minWidth: 0 }, shrink: { flexShrink: 1 },
  crown: { flexDirection: "row", alignItems: "center", gap: 2, height: 20, paddingHorizontal: 5, borderRadius: 10, borderWidth: 1.5 },
  crownBig: { height: 32, paddingHorizontal: 9, borderRadius: 16, gap: 4 },
  crownGold: { backgroundColor: arena.gold, borderColor: arena.goldDeep }, crownSilver: { backgroundColor: fx.smoke, borderColor: fx.white },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 64, paddingHorizontal: 12, paddingVertical: 8, backgroundColor: arena.panel },
  rowOn: { backgroundColor: arena.panelHi, borderLeftWidth: 4, borderLeftColor: arena.tealHi }, rowMain: { flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", gap: 12, minHeight: 48 },
  check: { width: 30, height: 30, borderRadius: 10, borderWidth: 2, borderColor: arena.rimHi, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge },
  checkOn: { backgroundColor: arena.teal, borderColor: arena.tealOutline },
  gems: { flexDirection: "row", justifyContent: "space-around", alignItems: "flex-end" }, gem: { alignItems: "center", gap: 2, flex: 1 },
  track: { height: 10, borderRadius: 5, backgroundColor: arena.panelEdge, overflow: "hidden", borderWidth: 1, borderColor: arena.rim }, fill: { height: "100%", borderRadius: 5 },
  note: { textAlign: "center", paddingVertical: 6 },
  inner: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" }, content: { paddingHorizontal: 16, paddingTop: 10, gap: 14 },
  footer: { paddingHorizontal: 16, paddingTop: 10 },
});
