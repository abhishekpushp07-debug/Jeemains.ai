import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Avatar } from "@/src/components/Entry";
import { GameProfile } from "@/src/components/game";
import { rapidColors as colors } from "@/src/theme";
import { Art, ArtKind } from "./Art";
import { Press, T, Icon } from "./ui";

export function PlayerStrip({ profile: p, onAvatar, onCoins }: { profile?: GameProfile | null; onAvatar: () => void; onCoins: () => void }) {
  const pct = p ? Math.max(0, Math.min(1, (p.xp - p.level_floor) / Math.max(1, p.next_level_xp - p.level_floor))) : 0;
  return <View testID="game-hud" style={styles.strip}>
    <Press testID="rf-open-avatar" accessibilityLabel="Choose your avatar" onPress={onAvatar}><Avatar icon={p?.avatar} frame={p?.equipped?.frame} size={48} /></Press>
    <View style={styles.player}><T testID="game-hud-level" w="heavy" size={16}>{p ? `Level ${p.level}` : "Your arena"}</T><View style={styles.track}><View style={[styles.progress, { width: `${pct * 100}%` }]} /></View><T testID="game-hud-xp" size={10} color={colors.muted}>{p ? `${p.xp} / ${p.next_level_xp} XP` : "Loading progress…"}</T></View>
    <Press testID="rf-open-store" accessibilityLabel="Your coins and shop" onPress={onCoins} style={styles.wallet}><Art kind="coins" size={36} /><View><T size={10} color={colors.custom_neonAmber} w="bold">Coins</T><T testID="game-hud-coins" size={17} w="heavy">{p ? p.coins.toLocaleString() : "—"}</T></View><Icon name="plus" size={15} color={colors.custom_neonAmber} /></Press>
  </View>;
}
export function EnergyHero() {
  return <View testID="rf-battle-hero" style={styles.hero}>
    <View style={styles.heroCopy}><T testID="rf-brand" size={11} w="heavy" color={colors.custom_neonCyan} style={styles.eyebrow}>JEECIRCLE</T><T testID="rf-game-title" size={34} w="heavy" style={styles.title}>Rapid{"\n"}Fire.</T><T testID="rf-game-tagline" size={12} color={colors.muted}>Big concepts. Quick wins.</T></View>
    <View style={styles.heroArt}><Art kind="spark" size={184} testID="rf-original-emblem" /></View>
    <View style={styles.rule}><Icon name="cards-outline" color={colors.custom_neonCyan} size={15} /><T testID="rf-game-rules" size={11} w="bold" color={colors.muted}>30 cards <T color={colors.borderStrong}> / </T> 20 seconds each</T></View>
  </View>;
}
export function PlayNow({ onPress, disabled }: { onPress: () => void; disabled: boolean }) {
  return <Press testID="rf-play-now" accessibilityLabel="Play Now" onPress={onPress} disabled={disabled} style={styles.playOuter}>
    <LinearGradient colors={[colors.custom_neonCyan, colors.custom_subjectChemistry]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.play}>
      <Icon name="play" size={25} color={colors.custom_gameBg} /><T w="heavy" size={22} color={colors.custom_gameBg}>Play Now</T><Icon name="arrow-right" size={22} color={colors.custom_gameBg} />
    </LinearGradient>
  </Press>;
}
export function FriendAction({ onPress, disabled }: { onPress: () => void; disabled: boolean }) {
  return <Press testID="rf-duel-invite" onPress={onPress} disabled={disabled} style={styles.friend}><Art kind="friends" size={58} /><View style={styles.flex}><T w="heavy" size={17}>Challenge Friend</T><T size={12} color={colors.muted}>Your friend. Same cards. Game on.</T></View><Icon name="chevron-right" size={24} color={colors.custom_neonViolet} /></Press>;
}
export function Shortcut({ kind, label, onPress, testID }: { kind: ArtKind; label: string; onPress: () => void; testID: string }) {
  return <Press testID={testID} onPress={onPress} style={styles.shortcut}><Art kind={kind} size={48} /><T w="bold" size={12}>{label}</T></Press>;
}
const styles = StyleSheet.create({
  flex: { flex: 1 }, strip: { flexDirection: "row", alignItems: "center", gap: 10 }, player: { flex: 1, gap: 4 }, track: { height: 4, backgroundColor: colors.border, borderRadius: 4, overflow: "hidden" }, progress: { height: "100%", backgroundColor: colors.custom_neonCyan },
  wallet: { flexDirection: "row", alignItems: "center", gap: 7, paddingRight: 10, paddingVertical: 5, borderRadius: 18, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.border },
  hero: { height: 218, justifyContent: "center", position: "relative", overflow: "hidden" }, heroCopy: { gap: 4, zIndex: 1, maxWidth: "60%" }, eyebrow: { letterSpacing: 3 }, title: { lineHeight: 36, letterSpacing: -1.5 }, heroArt: { position: "absolute", right: -15, top: 4 },
  rule: { position: "absolute", bottom: 5, left: 0, flexDirection: "row", alignItems: "center", gap: 8 },
  playOuter: { borderRadius: 20, backgroundColor: colors.brandPrimary, paddingBottom: 4 }, play: { minHeight: 60, paddingHorizontal: 24, borderRadius: 20, flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 10 },
  friend: { minHeight: 78, borderRadius: 21, padding: 10, flexDirection: "row", alignItems: "center", gap: 10, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_neonViolet + "55" },
  shortcut: { flex: 1, alignItems: "center", gap: 6, minHeight: 76, paddingVertical: 5 },
});