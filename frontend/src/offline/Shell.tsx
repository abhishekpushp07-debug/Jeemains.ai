// The frame of a screen that works without a line: Rapid Fire's own dark colours, nothing that moves.
import React, { useCallback } from "react";
import { StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { setStatusBarStyle } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { PaletteContext, arena, rapidColors } from "@/src/theme";

export function OfflineShell({ children, testID }: { children: React.ReactNode; testID: string }) {
  const insets = useSafeAreaInsets();
  useFocusEffect(useCallback(() => { setStatusBarStyle("light"); return () => setStatusBarStyle("dark"); }, []));
  return <PaletteContext.Provider value={rapidColors}>
    <View testID={testID} style={[styles.screen, { paddingTop: insets.top + 8, paddingBottom: insets.bottom }]}>{children}</View>
  </PaletteContext.Provider>;
}

const styles = StyleSheet.create({ screen: { flex: 1, backgroundColor: arena.bgDeep } });
