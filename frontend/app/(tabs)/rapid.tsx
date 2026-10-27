import React, { useCallback, useState } from "react";
import { KeyboardAvoidingView, Platform, RefreshControl, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Button, ErrorBox, Icon, Press, Sheet, T } from "@/src/rapid/ui";
import { BADGE_ICON, useGameProfile } from "@/src/components/game";
import { ChapterSheet } from "@/src/components/ChapterSheet";
import { WeakRevision } from "@/src/components/ArenaLearning";
import { EnergyHero, FriendAction, PlayerStrip, PlayNow, Shortcut } from "@/src/rapid/Lobby";
import { playSfx } from "@/src/sfx";
import { rapidColors as colors, fonts, rapidSubjectColor as subjectColor } from "@/src/theme";

const selection = { subject: "Physics", chapter: "" };
const SUBJECTS = ["Physics", "Chemistry", "Mathematics"];
type Panel = "" | "play" | "chapters" | "join" | "quests" | "trophies";
export default function RapidHome() {
  const insets = useSafeAreaInsets(), router = useRouter(), { user } = useAuth();
  const uid = user?.id || "";
  const [subject, setSubject] = useState(selection.subject), [chapter, setChapter] = useState(selection.chapter);
  const [sheet, setSheet] = useState<Panel>(""), [code, setCode] = useState(""), [claimError, setClaimError] = useState("");
  const [claimBusy, setClaimBusy] = useState("");
  const cat = useCached<any>("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
  const prof = useGameProfile(uid), p = prof.data;
  const refreshProfile = prof.revalidate, refreshCatalog = cat.revalidate;
  useFocusEffect(useCallback(() => { refreshProfile(); refreshCatalog(); }, [refreshProfile, refreshCatalog]));
  const pick = (s: string, ch: string) => { setSubject(s); setChapter(ch); Object.assign(selection, { subject: s, chapter: ch }); };
  const sub = cat.data?.subjects?.find((s: any) => s.name === subject);
  const available = chapter ? sub?.chapters?.find((c: any) => c.name === chapter)?.count || 0 : sub?.total || 0;
  const can = available >= 30 && !!uid;
  const route = (mode: "random" | "invite" | "solo" | "ai") => {
    setSheet("");
    router.push({ pathname: mode === "solo" ? "/rapid/session" : "/rapid/duel", params: { mode, exam: "JEE", subject, chapter } });
  };
  const quests = p?.quests || [], ready = quests.filter((q: any) => q.done && !q.claimed).length;
  return <View style={styles.root}>
    <ScrollView testID="rapid-fire-home" showsVerticalScrollIndicator={false} contentContainerStyle={[styles.content, { paddingTop: insets.top + 14, paddingBottom: 28 }]}
      refreshControl={<RefreshControl refreshing={prof.loading && !!p} tintColor={colors.custom_neonCyan} onRefresh={() => { prof.reload(); cat.reload(); }} />}>
      <PlayerStrip profile={p} onAvatar={() => router.push({ pathname: "/rapid/shop", params: { tab: "avatar" } })} onCoins={() => router.push("/rapid/shop")} />
      <ErrorBox testID="rf-profile-error" error={prof.error} retry={prof.reload} />
      <EnergyHero />
      <View style={styles.subjects}>{SUBJECTS.map(s => <Press testID={`rf-subject-${s.toLowerCase()}`} accessibilityState={{ selected: subject === s }} key={s} onPress={() => pick(s, "")} style={[styles.subject, subject === s && { backgroundColor: colors.custom_gameCardHi, borderColor: subjectColor(s) + "88" }]}><T w="heavy" size={13} color={subject === s ? subjectColor(s) : colors.muted}>{s === "Mathematics" ? "Maths" : s}</T></Press>)}</View>
      <Press testID="rf-chapter-picker" onPress={() => setSheet("chapters")} style={styles.chapter}><Icon name="layers-outline" size={18} color={subjectColor(subject)} /><View style={styles.flex}><T testID="rf-selected-chapter" w="bold" size={13} numberOfLines={1}>{chapter || `Mixed ${subject === "Mathematics" ? "Maths" : subject}`}</T><T testID="rf-session-summary" size={11} color={colors.muted}>{cat.loading && !cat.data ? "Loading your cards…" : `${available} quick-recall cards`}</T></View><Icon name="chevron-down" size={20} color={colors.muted} /></Press>
      <ErrorBox testID="rf-catalog-error" error={cat.error} retry={cat.reload} />
      <PlayNow disabled={!can} onPress={() => setSheet("play")} />
      <FriendAction disabled={!can} onPress={() => route("invite")} />
      <View style={styles.links}><Press testID="rf-friends-history" onPress={() => router.push("/rapid/history")} style={styles.history}><Icon name="history" color={colors.custom_neonViolet} size={19} /><T w="bold" size={12}>Friends Fight history</T></Press><Press testID="rf-open-join" onPress={() => setSheet("join")} style={styles.join}><Icon name="ticket-outline" size={18} color={colors.custom_neonCyan} /><T w="bold" size={12} color={colors.custom_neonCyan}>Join code</T></Press></View>
      <View style={styles.shortcuts}><Shortcut kind="trophy" label="Leaderboard" testID="rf-open-leaderboard" onPress={() => router.push("/rapid/leaderboard")} /><Shortcut kind="coins" label="Coin shop" testID="rf-shop-shortcut" onPress={() => router.push("/rapid/shop")} /><Shortcut kind="spark" label="Trophies" testID="rf-open-trophies" onPress={() => setSheet("trophies")} /></View>
      <Press testID="rf-daily-quests" onPress={() => setSheet("quests")} style={styles.today}><Icon name="fire" color={colors.custom_neonAmber} size={20} /><T testID="game-hud-streak" w="bold" size={13} style={styles.flex}>{p?.streak ?? "—"} day streak</T><T testID="rf-quest-status" w="bold" size={12} color={colors.custom_neonCyan}>{ready ? `${ready} reward ready` : "Daily quests"}</T><Icon name="chevron-right" color={colors.custom_neonCyan} size={18} /></Press>
      {uid ? <WeakRevision uid={uid} exam="JEE" /> : null}
      <Press testID="rf-solo-history" onPress={() => router.push({ pathname: "/rapid/history", params: { tab: "solo" } })} style={styles.soloLink}><T size={13} color={colors.muted}>Your solo sprints</T><Icon name="chevron-right" color={colors.muted} size={20} /></Press>
      <T testID="rf-practice-note" size={10} color={colors.muted} style={styles.center}>Practice, not exam marks. Earn coins through play.</T>
    </ScrollView>
    <ChapterSheet visible={sheet === "chapters"} onClose={() => setSheet("")} subjects={cat.data?.subjects || []} subject={subject} chapter={chapter} recent={[]} onPick={(s, ch) => { if (SUBJECTS.includes(s)) pick(s, ch); setSheet(""); }} />
    <Sheet visible={sheet === "play"} onClose={() => setSheet("")} testID="rf-play-sheet"><T testID="rf-mode-heading" w="heavy" size={25}>How will you play?</T><T testID="rf-mode-rules" color={colors.muted}>30 cards · 20 seconds each{"\n"}+1 score and +2 Coins per correct answer</T><Button testID="rf-duel-random" icon="sword-cross" label="Quick Match" onPress={() => route("random")} /><Button testID="rf-start-button" kind="secondary" icon="lightning-bolt" label="Solo Sprint" onPress={() => route("solo")} /><Button testID="rf-duel-ai" kind="secondary" icon="robot-outline" label="Practice Rival" onPress={() => route("ai")} /><T testID="rf-practice-rival-note" size={12} color={colors.muted}>Practice Rival is computer-controlled, with no queue.</T></Sheet>
    <Sheet visible={sheet === "join"} onClose={() => setSheet("")} testID="rf-join-sheet"><KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.form}><T w="heavy" size={24}>Join your friend</T><T testID="rf-join-help" color={colors.muted}>Enter the 6-character code they shared.</T><TextInput testID="rf-duel-code-input" accessibilityLabel="Duel code" value={code} onChangeText={t => setCode(t.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6))} placeholder="ABC123" placeholderTextColor={colors.muted} autoCapitalize="characters" style={styles.input} /><Button testID="rf-duel-join" label="Join Duel" disabled={code.length !== 6 || !uid} onPress={() => { setSheet(""); router.push({ pathname: "/rapid/duel", params: { mode: "join", exam: "JEE", code } }); }} /></KeyboardAvoidingView></Sheet>
    <Sheet visible={sheet === "quests"} onClose={() => setSheet("")} testID="rf-quests-sheet"><T w="heavy" size={24}>A little daily momentum</T><T testID="rf-quests-reset" color={colors.muted} size={12}>Resets at midnight IST · {p?.freezes ?? 0} streak freezes</T>{quests.map((q: any) => <View key={q.id} testID={`rf-quest-${q.id}`} style={styles.quest}><View style={styles.flex}><T w="bold">{q.title}</T><T size={12} color={colors.muted}>{q.progress}/{q.goal} · {q.coins} coins</T></View>{q.done && !q.claimed ? <Button testID={`rf-quest-claim-${q.id}`} label="Claim" busy={claimBusy === q.id} disabled={!!claimBusy} onPress={async () => { setClaimBusy(q.id); setClaimError(""); try { await rf("/quests/claim", uid, { method: "POST", body: { id: q.id } }); playSfx("coin"); prof.reload(); } catch (e: any) { setClaimError(e.message); } finally { setClaimBusy(""); } }} /> : <T testID={`rf-quest-state-${q.id}`} size={12} color={colors.custom_neonCyan}>{q.claimed ? "Claimed" : "In progress"}</T>}</View>)}<ErrorBox testID="rf-quest-claim-error" error={claimError} /></Sheet>
    <Sheet visible={sheet === "trophies"} onClose={() => setSheet("")} testID="rf-trophies-sheet"><T w="heavy" size={24}>Your trophy shelf</T>{p?.badges.map(b => <View key={b.id} testID={`rf-badge-${b.id}`} style={styles.quest}><Icon name={b.earned ? BADGE_ICON[b.id] : "lock-outline"} color={b.earned ? colors.custom_neonAmber : colors.muted} size={28} /><View style={styles.flex}><T w="bold">{b.title}</T><T size={12} color={colors.muted}>{b.body}</T></View><T size={11} color={colors.muted}>{b.earned ? "Earned" : "Locked"}</T></View>)}</Sheet>
  </View>;
}
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.custom_gameBg }, content: { paddingHorizontal: 20, gap: 12, maxWidth: 560, width: "100%", alignSelf: "center" }, flex: { flex: 1 },
  subjects: { flexDirection: "row", padding: 4, gap: 4, borderRadius: 17, backgroundColor: colors.surfaceAlt }, subject: { flex: 1, minHeight: 44, alignItems: "center", justifyContent: "center", borderRadius: 13, borderWidth: 1, borderColor: "transparent" },
  chapter: { flexDirection: "row", alignItems: "center", minHeight: 48, gap: 10, paddingHorizontal: 10 }, links: { flexDirection: "row", justifyContent: "space-between", gap: 8 }, history: { flex: 1, minHeight: 48, flexDirection: "row", alignItems: "center", gap: 6 }, join: { minHeight: 48, flexDirection: "row", alignItems: "center", gap: 5 },
  shortcuts: { flexDirection: "row", borderTopWidth: 1, borderBottomWidth: 1, borderColor: colors.border, paddingVertical: 12 }, today: { flexDirection: "row", alignItems: "center", minHeight: 52, gap: 8 }, soloLink: { minHeight: 44, flexDirection: "row", alignItems: "center", justifyContent: "space-between" }, center: { textAlign: "center" },
  form: { gap: 16 }, input: { height: 60, paddingHorizontal: 14, borderRadius: 16, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, color: colors.onSurface, fontFamily: fonts.heavy, fontSize: 24, letterSpacing: 7, textAlign: "center" }, quest: { minHeight: 66, flexDirection: "row", alignItems: "center", gap: 12 },
});