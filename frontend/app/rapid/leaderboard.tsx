import React, { useCallback } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { ExamLeaderboard } from "@/src/components/ExamLeaderboard";
import { Art } from "@/src/rapid/Art";
import { Icon, Press, T } from "@/src/rapid/ui";
import { rapidColors as colors } from "@/src/theme";

export default function Leaderboard() {
  const router = useRouter(), insets = useSafeAreaInsets(), { user } = useAuth();
  const board = useCached<any>(user ? `u.${user.id}.rfboard.JEE` : null, () => rf("/leaderboard?exam=JEE", user!.id), false);
  useFocusEffect(useCallback(() => { board.reload(); }, [board.reload]));
  return <View testID="rf-leaderboard-screen" style={[styles.root, { paddingTop: insets.top + 12 }]}><View style={styles.header}><Press testID="rf-leaderboard-back" accessibilityLabel="Back" onPress={() => router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid")} style={styles.back}><Icon name="arrow-left" color={colors.onSurface} size={22} /></Press><T testID="rf-leaderboard-page-title" w="heavy" size={25}>The leaderboard</T></View><ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 24 }]}><View style={styles.hero}><Art kind="trophy" size={140} /><T testID="rf-leaderboard-tagline" size={16} color={colors.muted}>Keep showing up. Keep climbing.</T></View><ExamLeaderboard exam="JEE" data={board.data} error={board.error} loading={board.loading} retry={board.reload} /></ScrollView></View>;
}
const styles = StyleSheet.create({ root: { flex: 1, backgroundColor: colors.custom_gameBg }, header: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 20 }, back: { width: 44, height: 44, alignItems: "center", justifyContent: "center", borderRadius: 16, backgroundColor: colors.custom_gameCard }, content: { padding: 20, gap: 24 }, hero: { alignItems: "center", gap: 8 } });