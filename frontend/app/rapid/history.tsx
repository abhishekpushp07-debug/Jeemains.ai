import React, { useCallback, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Art } from "@/src/rapid/Art";
import { Button, ErrorBox, Icon, Press, Skeleton, T } from "@/src/rapid/ui";
import { rapidColors as colors } from "@/src/theme";

const dateLabel = (iso: string) => new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
export default function History() {
  const router = useRouter(), insets = useSafeAreaInsets(), { user } = useAuth();
  const params = useLocalSearchParams<{ tab?: string }>();
  const [tab, setTab] = useState(params.tab === "solo" ? "solo" : "friends");
  const history = useCached<any>(user ? `u.${user.id}.rf-private-history.${tab}.v2` : null, () => rf(tab === "friends" ? "/duels?exam=JEE&friends_only=true" : "/history?exam=JEE", user!.id), false);
  useFocusEffect(useCallback(() => { history.reload(); }, [history.reload]));
  const items = history.data?.items || [];
  return <View testID="rf-history-screen" style={[styles.root, { paddingTop: insets.top + 12 }]}>
    <View style={styles.header}><Press testID="rf-history-back" accessibilityLabel="Back to arena" onPress={() => router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid")} style={styles.back}><Icon name="arrow-left" size={22} color={colors.onSurface} /></Press><View style={styles.flex}><T testID="rf-history-eyebrow" size={10} color={colors.custom_neonViolet} w="heavy">YOUR RIVALRIES</T><T testID="rf-history-title" size={25} w="heavy">Friends Fight</T></View><Art kind="friends" size={54} /></View>
    <View style={styles.tabs}>{[["friends", "Friend duels"], ["solo", "Solo sprints"]].map(([key, label]) => <Press key={key} testID={`rf-history-tab-${key}`} accessibilityState={{ selected: tab === key }} onPress={() => setTab(key)} style={[styles.tab, tab === key && styles.active]}><T size={14} w="bold" color={tab === key ? colors.custom_neonCyan : colors.muted}>{label}</T></Press>)}</View>
    <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 24 }]} refreshControl={<RefreshControl refreshing={history.loading && !!history.data} onRefresh={history.reload} tintColor={colors.custom_neonCyan} />}>
      <ErrorBox testID="rf-history-error" error={history.error} retry={history.reload} />
      {!history.data && history.loading ? <Skeleton h={200} /> : null}
      {history.data && !items.length ? <View testID="rf-friends-empty" style={styles.empty}><Art kind={tab === "friends" ? "friends" : "spark"} size={150} /><T testID="rf-empty-history-title" w="heavy" size={24} style={styles.center}>{tab === "friends" ? "A fresh rivalry awaits" : "Your first sprint awaits"}</T><T testID="rf-empty-history-body" color={colors.muted} size={15} style={styles.center}>{tab === "friends" ? "No completed friend duels yet. Share a challenge and your first result will land here." : "Finish a Solo Sprint to see your scores here."}</T><Button testID="rf-history-challenge" label={tab === "friends" ? "Choose a friend challenge" : "Back to Play"} onPress={() => router.dismissTo("/(tabs)/rapid")} /></View> : null}
      {items.map((m: any) => {
        const mine = m.scores?.find((p: any) => p.you), opponent = m.scores?.find((p: any) => !p.you);
        const solo = tab === "solo", color = m.tie ? colors.custom_neonAmber : m.won ? colors.success : colors.custom_gameMuted;
        return <Press key={m.id} testID={`rf-history-match-${m.id}`} onPress={() => router.push({ pathname: solo ? "/rapid/session" : "/rapid/duel", params: { review: m.id } })} style={styles.match}>
          <View style={styles.row}><T testID={`rf-history-outcome-${m.id}`} w="heavy" size={11} color={solo ? colors.custom_neonCyan : color}>{solo ? "SOLO SPRINT" : m.tie ? "DRAW" : m.won ? "VICTORY" : "GOOD FIGHT"}</T><T testID={`rf-history-date-${m.id}`} size={10} color={colors.muted}>{dateLabel(solo ? m.completed_at : m.finished_at)}</T></View>
          <View style={styles.row}><View style={styles.flex}><T testID={`rf-history-opponent-${m.id}`} w="heavy" size={18} numberOfLines={1}>{solo ? m.chapter || m.subject : `vs ${opponent?.name || "Friend"}`}</T><T size={12} color={colors.muted}>{solo ? "Concept recall" : `${m.subject} · ${m.chapter || "Mixed chapters"}`}</T></View><T testID={`rf-history-scores-${m.id}`} w="heavy" size={23}>{solo ? `${m.summary?.score}/${m.summary?.total}` : `${mine?.score} : ${opponent?.score}`}</T><Icon name="chevron-right" size={22} color={colors.muted} /></View>
          {!solo ? <T testID={`rf-history-score-key-${m.id}`} size={10} color={colors.muted}>You : Friend · Tap to review, not to rematch</T> : null}
        </Press>;
      })}
      {items.length ? <Button testID="rf-history-new-challenge" kind="secondary" icon="sword-cross" label="Choose a new challenge" onPress={() => router.dismissTo("/(tabs)/rapid")} /> : null}
    </ScrollView>
  </View>;
}
const styles = StyleSheet.create({ root: { flex: 1, backgroundColor: colors.custom_gameBg }, header: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 20, paddingBottom: 20 }, back: { width: 44, height: 44, borderRadius: 16, backgroundColor: colors.custom_gameCard, alignItems: "center", justifyContent: "center" }, flex: { flex: 1 }, tabs: { marginHorizontal: 20, padding: 4, borderRadius: 16, backgroundColor: colors.surfaceAlt, flexDirection: "row", gap: 6 }, tab: { flex: 1, minHeight: 46, alignItems: "center", justifyContent: "center", borderRadius: 12 }, active: { backgroundColor: colors.custom_gameCardHi }, content: { padding: 20, gap: 16 }, empty: { alignItems: "center", paddingVertical: 36, gap: 20 }, center: { textAlign: "center" }, match: { padding: 18, borderRadius: 22, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.border, gap: 14 }, row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 10 } });