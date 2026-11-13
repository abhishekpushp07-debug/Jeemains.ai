import React, { useCallback, useId } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { setStatusBarStyle } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useReducedMotion } from "react-native-reanimated";
import * as Base from "@/src/components/ui";
import { PaletteContext, rapidColors as colors } from "@/src/theme";
import { RaisedButton } from "./arena";
import { ChallengeBanner } from "./ChallengeBanner";

export { Icon, tap, buzz, ErrorBox, Stat } from "@/src/components/ui";
export type { IconName } from "@/src/components/ui";

// Rapid Fire keeps its own dark identity on top of the light app: shared primitives read
// this palette and the status bar turns light while any RF screen is focused.
let rapidFocus = 0;
export function withRapid<P extends object>(Screen: React.ComponentType<P>, opts: { banner?: boolean } = {}) {
  function RapidScreen(props: P) {
    useFocusEffect(useCallback(() => {
      rapidFocus++; setStatusBarStyle("light");
      return () => { rapidFocus = Math.max(0, rapidFocus - 1); if (!rapidFocus) setStatusBarStyle("dark"); };
    }, []));
    // A challenge can arrive on any arena screen, except in a match or Match Room (banner: false there).
    return <PaletteContext.Provider value={colors}><View style={styles.screen}><Screen {...props} />{opts.banner === false ? null : <ChallengeBanner floating />}</View></PaletteContext.Provider>;
  }
  return RapidScreen;
}
export function T(props: React.ComponentProps<typeof Base.T>) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  return <Base.T testID={`rf-text-${id}`} color={colors.onSurface} {...props} />;
}
export function Press(props: React.ComponentProps<typeof Base.Press>) {
  const reduced = useReducedMotion();
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  return <Base.Press testID={`rf-control-${id}`} {...props} scaleTo={reduced ? 1 : props.scaleTo ?? 0.97} />;
}
// Every arena button is a raised key: teal for the action, wine for the quiet choice.
export function Button({ kind = "primary", style, label, icon, busy, disabled, testID, onPress }: React.ComponentProps<typeof Base.Button>) {
  return <RaisedButton testID={testID} label={label} glyph={icon} busy={busy} disabled={disabled} onPress={onPress} tone={kind === "primary" ? "teal" : kind === "danger" ? "danger" : "wine"} style={style} />;
}
export function Card({ style, ...props }: React.ComponentProps<typeof Base.Card>) { return <Base.Card {...props} style={[styles.card, style]} />; }
export function Skeleton({ h = 80 }: { h?: number }) { return <View style={[styles.card, { height: h, justifyContent: "center" }]}><ActivityIndicator color={colors.custom_neonCyan} /></View>; }
export function Empty({ title, body, action, testID }: React.ComponentProps<typeof Base.Empty>) {
  return <View testID={testID} style={styles.empty}><T size={20} w="heavy" style={styles.center}>{title}</T><T size={14} color={colors.muted} style={styles.center}>{body}</T>{action}</View>;
}
export function Sheet({ visible, onClose, children, testID = "rf-sheet" }: React.ComponentProps<typeof Base.Sheet>) {
  const insets = useSafeAreaInsets();
  const reduced = useReducedMotion();
  return <Modal transparent visible={visible} onRequestClose={onClose} animationType={reduced ? "none" : "fade"}>
    <View style={styles.modal}><Pressable accessibilityLabel="Close" testID={`${testID}-backdrop`} onPress={onClose} style={styles.backdrop} />
      <View testID={testID} style={[styles.sheet, { paddingBottom: insets.bottom + 20 }]}>
        <View style={styles.sheetHeader}><View style={styles.handle} /><Press testID={`${testID}-close`} accessibilityLabel="Close" onPress={onClose} style={styles.close}><Base.Icon name="close" size={22} color={colors.muted} /></Press></View>
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.sheetContent}>{children}</ScrollView>
      </View>
    </View>
  </Modal>;
}
const styles = StyleSheet.create({
  screen: { flex: 1 }, card: { backgroundColor: colors.custom_gameCard, borderColor: colors.border, shadowColor: colors.custom_gameBg },
  empty: { padding: 24, alignItems: "center", gap: 14 }, center: { textAlign: "center" },
  modal: { flex: 1, justifyContent: "flex-end", backgroundColor: colors.custom_overlay }, backdrop: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  sheet: { maxHeight: "86%", backgroundColor: colors.surfaceSecondary, borderTopLeftRadius: 28, borderTopRightRadius: 28, borderWidth: 1, borderColor: colors.border, paddingHorizontal: 20 },
  sheetHeader: { height: 48, alignItems: "center", justifyContent: "center" }, handle: { width: 38, height: 4, borderRadius: 4, backgroundColor: colors.borderStrong }, close: { position: "absolute", right: -4, height: 44, width: 44, alignItems: "center", justifyContent: "center" },
  sheetContent: { gap: 16, paddingBottom: 8 },
});