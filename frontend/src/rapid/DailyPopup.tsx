import React from "react";
import { Modal, Pressable, StyleSheet, View, useWindowDimensions } from "react-native";
import { useReducedMotion } from "react-native-reanimated";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { GoldTitle, RaisedButton } from "./arena";
import { AllIndiaCard } from "./AllIndiaCard";
import { DailyLook, DailyStatus } from "./daily";

/** Opening Rapid Fire: today's All India round first. ENTER goes straight to the cards, EXIT stays on the Rapid Fire home. */
export function DailyPopup({ visible, d, look, onEnter, onExit }: { visible: boolean; d?: DailyStatus | null; look: DailyLook; onEnter: () => void; onExit: () => void }) {
  const reduced = useReducedMotion(), { width, height } = useWindowDimensions();
  const size = Math.min(width - 48, 380, height - 260);
  const playing = d?.you.status === "playing";
  return <Modal visible={visible} transparent animationType={reduced ? "none" : "fade"} onRequestClose={onExit} statusBarTranslucent>
    <View style={styles.wrap} testID="rf-daily-popup">
      <Pressable style={StyleSheet.absoluteFill} onPress={onExit} accessibilityLabel="Close" testID="rf-daily-popup-backdrop" />
      <T w="heavy" size={11} color={arena.aqua} style={styles.kicker}>TODAY’S BIG MATCH</T>
      <GoldTitle size={24} center>{playing ? "Finish what you started!" : "All India Rapid is live!"}</GoldTitle>
      <AllIndiaCard d={d} look={look} size={size} testID="rf-daily-popup-card" onPress={onEnter} />
      <View style={[styles.buttons, { width: size }]}>
        <RaisedButton testID="rf-daily-popup-exit" label="EXIT" tone="wine" height={54} onPress={onExit} style={styles.exit} />
        <RaisedButton testID="rf-daily-popup-enter" label={playing ? "CONTINUE" : "ENTER"} icon="bolt" height={54} streak onPress={onEnter} style={styles.enter} />
      </View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  wrap: { flex: 1, alignItems: "center", justifyContent: "center", gap: 10, backgroundColor: arena.scrim, paddingHorizontal: 24 },
  kicker: { letterSpacing: 2 },
  buttons: { flexDirection: "row", gap: 10, marginTop: 6 }, exit: { flex: 1 }, enter: { flex: 1.6 },
});
