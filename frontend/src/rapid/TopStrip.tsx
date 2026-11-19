import React from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { T } from "@/src/components/ui";
import { useAuth } from "@/src/auth";
import { Avatar } from "@/src/components/Entry";
import { useGameProfile } from "@/src/components/game";
import { arena } from "@/src/theme";
import { GameIcon, Gem } from "./Art";
import { Jelly } from "./juice";
import { Bar } from "./parts";
import { go, setArenaTab } from "./social";
import { SettingsButton } from "./SoundSettings";

/** Top of every arena tab: you (opens your profile), your diamonds (opens the Vault) and your coins (opens the Store). */
export function TopStrip() {
  const router = useRouter(), { user } = useAuth();
  const p = useGameProfile(user?.id).data;
  const diamonds = Object.values(p?.diamonds || {}).reduce((a, b) => a + b, 0);
  const progress = p ? (p.xp - p.level_floor) / Math.max(1, p.next_level_xp - p.level_floor) : 0;
  return <View testID="arena-top-strip" style={styles.row}>
    <Jelly testID="arena-top-profile" accessibilityLabel="Your profile" onPress={() => { if (p?.pid) router.push(go.player(p.pid)); }} style={styles.me}>
      <View>
        <Avatar icon={p?.avatar} frame={p?.equipped?.frame} size={44} />
        <View style={styles.level}><T testID="arena-top-level" w="heavy" size={10} color={arena.badgeInk}>{p?.level ?? 1}</T></View>
      </View>
      <View style={styles.flex}>
        <T testID="arena-top-name" w="heavy" size={14} color={arena.text} numberOfLines={1}>{p?.name || user?.name || "Player"}</T>
        <Bar value={progress} color={arena.gold} />
      </View>
    </Jelly>
    <SettingsButton />
    <Jelly testID="arena-top-diamonds" accessibilityLabel={`${diamonds} diamonds. Open Diamond Vault`} onPress={() => router.push("/rapid/vault" as any)} style={styles.pill}>
      <Gem color="red" size={26} /><T testID="arena-top-diamond-count" w="heavy" size={14} color={arena.text}>{diamonds}</T>
    </Jelly>
    <Jelly testID="arena-top-coins" accessibilityLabel={`${p?.coins ?? 0} coins. Open Store`} onPress={() => setArenaTab("store")} style={styles.pill}>
      <GameIcon name="coin" size={26} /><T testID="game-hud-coins" w="heavy" size={14} color={arena.gold}>{p?.coins ?? "—"}</T>
      <View style={styles.plus}><T w="heavy" size={14} color={arena.text}>+</T></View>
    </Jelly>
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 12, minHeight: 56 }, flex: { flex: 1, minWidth: 0, gap: 4 },
  me: { flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", gap: 8, minHeight: 48 },
  level: { position: "absolute", right: -4, bottom: -4, minWidth: 20, height: 20, borderRadius: 10, paddingHorizontal: 4, alignItems: "center", justifyContent: "center", backgroundColor: arena.badge, borderWidth: 1.5, borderColor: arena.badgeInk },
  pill: { flexDirection: "row", alignItems: "center", gap: 4, height: 44, paddingHorizontal: 8, borderRadius: 22, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  plus: { width: 22, height: 22, borderRadius: 11, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline, marginLeft: 2 },
});
