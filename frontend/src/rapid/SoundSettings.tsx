import React, { useState } from "react";
import { Pressable, StyleSheet, Switch, View } from "react-native";
import { Icon, IconName, T, tap } from "@/src/components/ui";
import { setSoundPrefs, useSoundPrefs } from "@/src/sfx";
import { arena } from "@/src/theme";
import { GoldTitle } from "./arena";
import { Jelly } from "./juice";
import { Sheet } from "./ui";

function Row({ icon, title, sub, value, onChange, testID }: { icon: IconName; title: string; sub: string; value: boolean; onChange: (v: boolean) => void; testID: string }) {
  return <Pressable testID={testID} accessibilityRole="switch" accessibilityState={{ checked: value }} accessibilityLabel={`${title}. ${value ? "On" : "Off"}`}
    onPress={() => { tap(); onChange(!value); }} style={styles.row}>
    <View style={[styles.icon, value && styles.iconOn]}><Icon name={icon} size={20} color={value ? arena.badgeInk : arena.muted} /></View>
    <View style={styles.flex}>
      <T w="heavy" size={15} color={arena.text}>{title}</T>
      <T w="bold" size={11.5} color={arena.muted}>{sub}</T>
    </View>
    <Switch testID={`${testID}-switch`} value={value} onValueChange={(v) => { tap(); onChange(v); }} trackColor={{ false: arena.panelEdge, true: arena.teal }} thumbColor={arena.text} ios_backgroundColor={arena.panelEdge} />
  </Pressable>;
}

/** The gear on the arena's top strip: Rapid Fire settings (card sounds and game sounds on or off, kept on this phone). */
export function SettingsButton() {
  const [open, setOpen] = useState(false), s = useSoundPrefs(), quiet = !s.card && !s.game;
  return <>
    <Jelly testID="arena-top-settings" accessibilityLabel={`Rapid Fire settings${quiet ? ". Sounds off" : ""}`} onPress={() => setOpen(true)} style={styles.btn}>
      <Icon name={quiet ? "volume-off" : "cog"} size={22} color={arena.text} />
    </Jelly>
    <Sheet visible={open} onClose={() => setOpen(false)} testID="rf-settings-sheet">
      <GoldTitle size={20}>Rapid Fire settings</GoldTitle>
      <Row testID="rf-settings-card-sound" icon="volume-high" title="Card sounds" sub="Roar, rocket launch, war horn, gallop and arrow on the All India card" value={s.card} onChange={(v) => setSoundPrefs({ card: v })} />
      <Row testID="rf-settings-game-sound" icon="music-note" title="Game sounds" sub="Right and wrong, the clock ticking, wins and coins" value={s.game} onChange={(v) => setSoundPrefs({ game: v })} />
      <T size={11} color={arena.muted}>The phone’s silent switch always wins. Saved on this phone.</T>
    </Sheet>
  </>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0, gap: 2 },
  btn: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  row: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 64, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  icon: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge },
  iconOn: { backgroundColor: arena.gold },
});
