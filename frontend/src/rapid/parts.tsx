import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Icon, T, tap } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena } from "@/src/theme";
import { GEM_LABEL, GEM_ORDER, Gem, PhoenixDiamond, topGem } from "./Art";
import { ArenaBg, OnlineDot, ScreenTop } from "./arena";
import { Jelly, Pop } from "./juice";
import { PlayerCard } from "./social";

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
  return <View testID={testID} style={[styles.row, selected && styles.rowOn]}>
    <Pressable onPress={onPress ? () => { tap(); onPress(); } : undefined} disabled={!onPress} accessibilityRole="button" accessibilityLabel={p.name} accessibilityState={{ selected: !!selected }} style={styles.rowMain}>
      <Face p={p} />
      <View style={styles.flex}>
        <T w="heavy" size={15} color={arena.text} numberOfLines={1}>{p.name || "Player"}</T>
        {sub ? <T w="bold" size={12} color={p.online ? arena.online : arena.muted} numberOfLines={1}>{sub}</T> : null}
      </View>
    </Pressable>
    {right}
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
export function InnerScreen({ title, sub, right, children, testID, footer }: { title: string; sub?: string; right?: React.ReactNode; children: React.ReactNode; testID: string; footer?: React.ReactNode }) {
  const insets = useSafeAreaInsets(), router = useRouter();
  return <ArenaBg testID={testID}>
    <View style={[styles.inner, { paddingTop: insets.top + 6 }]}>
      <ScreenTop title={title} sub={sub} right={right} testID={testID} onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"))} />
      <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 28 }]}>{children}</KeyboardAwareScrollView>
      {footer ? <View style={[styles.footer, { paddingBottom: insets.bottom + 10 }]}>{footer}</View> : null}
    </View>
  </ArenaBg>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, dot: { position: "absolute", right: -1, bottom: -1 }, winged: { alignItems: "center", justifyContent: "center" },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 64, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  rowOn: { borderColor: arena.tealHi, backgroundColor: arena.panelHi }, rowMain: { flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", gap: 12, minHeight: 48 },
  check: { width: 30, height: 30, borderRadius: 10, borderWidth: 2, borderColor: arena.rimHi, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge },
  checkOn: { backgroundColor: arena.teal, borderColor: arena.tealOutline },
  gems: { flexDirection: "row", justifyContent: "space-around", alignItems: "flex-end" }, gem: { alignItems: "center", gap: 2, flex: 1 },
  track: { height: 10, borderRadius: 5, backgroundColor: arena.panelEdge, overflow: "hidden", borderWidth: 1, borderColor: arena.rim }, fill: { height: "100%", borderRadius: 5 },
  note: { textAlign: "center", paddingVertical: 6 },
  inner: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" }, content: { paddingHorizontal: 16, paddingTop: 10, gap: 14 },
  footer: { paddingHorizontal: 16, paddingTop: 10 },
});
