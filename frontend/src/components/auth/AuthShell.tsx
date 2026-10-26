import React from "react";
import { StyleSheet, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { colors, space } from "@/src/theme";

export function AuthShell({ children, testID }: { children: React.ReactNode; testID: string }) {
  const insets = useSafeAreaInsets();
  return <View testID={testID} style={styles.screen}>
    <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={[styles.scroll, { paddingTop: insets.top + space.lg, paddingBottom: insets.bottom + space.xl }]}>
      <View style={styles.content}>{children}</View>
    </KeyboardAwareScrollView>
  </View>;
}
const styles = StyleSheet.create({ screen: { flex: 1, backgroundColor: colors.surface }, scroll: { flexGrow: 1, paddingHorizontal: space.lg }, content: { width: "100%", maxWidth: 480, alignSelf: "center", gap: space.lg } });