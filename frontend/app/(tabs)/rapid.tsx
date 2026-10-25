import React, { useCallback, useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, RefreshControl, ScrollView, TextInput, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { invalidate, useCached } from "@/src/useCached";
import { ErrorBox, Icon, IconName, Press, Sheet, Skeleton, T } from "@/src/components/ui";
import { BADGE_ICON, useGameProfile } from "@/src/components/game";
import { Avatar } from "@/src/components/Entry";
import { BattleHero, OutlineAction, PlayButton } from "@/src/components/BattleHero";
import { ChapterSheet } from "@/src/components/ChapterSheet";
import { DiagramShortcut, WeakRevision } from "@/src/components/ArenaLearning";
import { ExamLeaderboard } from "@/src/components/ExamLeaderboard";
import { playSfx } from "@/src/sfx";
import { colors, fonts, radius, space, subjectColor } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

const pick = { exam: "JEE" as "JEE" | "NEET", subject: "Physics", chapter: "" as string };
// Purchased arena themes (fixed artwork colours, identical in light/dark).
const THEME_BG: Record<string, string> = { theme_inferno: "#1F0707", theme_ocean: "#03202B", theme_gold: "#1F1704" };
const EXAM_SUBJECTS: Record<"JEE" | "NEET", [string, string, IconName][]> = {
  JEE: [["Physics", "Physics", "atom"], ["Chemistry", "Chemistry", "flask-outline"], ["Mathematics", "Maths", "function-variant"]],
  NEET: [["Physics", "Physics", "atom"], ["Chemistry", "Chemistry", "flask-outline"], ["Biology", "Biology", "dna"]],
};
type Pane = "board" | "recent" | "trophies";

const scoreColor = (m: any) => {
  const r = m?.total ? m.score / m.total : 0;
  return r >= 0.8 ? colors.custom_neonGreen : r >= 0.5 ? colors.custom_neonAmber : colors.custom_neonRed;
};


export default function RapidHome() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const [exam, setExam] = useState(pick.exam);
  const [subject, setSubject] = useState(pick.subject);
  const [chapter, setChapter] = useState(pick.chapter);
  Object.assign(pick, { exam, subject, chapter });
  const SUBJECTS = EXAM_SUBJECTS[exam];
  const switchExam = (e: "JEE" | "NEET") => {
    setExam(e);
    if (!EXAM_SUBJECTS[e].some(([s]) => s === subject)) { setSubject(e === "NEET" ? "Biology" : "Mathematics"); setChapter(""); }
  };
  const cat = useCached<any>(`rf.catalog.${exam}`, () => rf(`/catalog?exam=${exam}`, user?.id || "guest-viewer"));
  const hist = useCached<any>(user ? `u.${user.id}.rfhist.${exam}` : null, () => rf(`/history?exam=${exam}`, user!.id));
  const duels = useCached<any>(user ? `u.${user.id}.duels.${exam}` : null, () => rf(`/duels?exam=${exam}`, user!.id));
  const prof = useGameProfile(user?.id);
  const board = useCached<any>(user ? `u.${user.id}.rfboard.${exam}` : null, () => rf(`/leaderboard?exam=${exam}`, user!.id), false);
  const [revisionRefresh, setRevisionRefresh] = useState(0);
  const [claimErr, setClaimErr] = useState("");
  const [code, setCode] = useState("");
  const [sheet, setSheet] = useState<"" | "chapters" | "quests" | "join">("");
  const [pane, setPane] = useState<Pane>("board");
  const sub = cat.data?.subjects?.find((s: any) => s.name === subject);
  const chosen = chapter ? sub?.chapters.find((c: any) => c.name === chapter) : null;
  const available = chosen ? chosen.count : sub?.total ?? 0;
  const tint = subjectColor(subject);
  const p = prof.data;
  const can = !!available && !!user;
  const quests = p?.quests || [];
  const questsDone = quests.filter((q: any) => q.done).length;
  const claimable = quests.filter((q: any) => q.done && !q.claimed).length;
  const reload = () => { cat.reload(); hist.reload(); duels.reload(); prof.reload(); board.reload(); setRevisionRefresh((v) => v + 1); };
  // Refresh XP / streak / history whenever the arena regains focus (e.g. after a sprint or duel).
  const first = useRef(true);
  useFocusEffect(useCallback(() => {
    if (first.current) { first.current = false; return; }
    hist.reload(); duels.reload(); prof.reload(); board.reload(); invalidate(`u.${user?.id}.rfshop`);
  }, [hist.reload, duels.reload, prof.reload, board.reload])); // eslint-disable-line react-hooks/exhaustive-deps
  const pct = p ? Math.min(1, (p.xp - p.level_floor) / Math.max(1, p.next_level_xp - p.level_floor)) : 0;
  const recent = Array.from(new Map((hist.data?.items || []).filter((x: any) => x.chapter).map((x: any) => [x.subject + x.chapter, { subject: x.subject, chapter: x.chapter }])).values()).slice(0, 6) as { subject: string; chapter: string }[];
  const record = duels.data?.items?.length ? `${duels.data.items.filter((x: any) => x.won).length}W · ${duels.data.items.filter((x: any) => x.tie).length}T · ${duels.data.items.filter((x: any) => !x.won && !x.tie).length}L` : "";

  return (
    <View style={{ flex: 1, backgroundColor: THEME_BG[p?.equipped?.theme || ""] || colors.custom_gameBg }}>
      <ScrollView testID="rapid-fire-home" contentContainerStyle={{ paddingTop: insets.top + space.md, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xl, paddingHorizontal: space.lg, gap: space.lg }}
        refreshControl={<RefreshControl refreshing={false} onRefresh={reload} tintColor={colors.custom_neonAmber} />}>

        {/* 1 · Identity bar: who you are, level progress, wallet, store */}
        <View testID="game-hud" style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
          <Press testID="rf-open-avatar" onPress={() => router.push({ pathname: "/rapid/shop", params: { tab: "avatar" } })} accessibilityLabel="Change avatar">
            <Avatar icon={p?.avatar} frame={p?.equipped?.frame} size={52} />
          </Press>
          <View style={{ flex: 1, gap: 6 }}>
            <View style={{ flexDirection: "row", alignItems: "baseline", gap: space.sm }}>
              <T w="heavy" size={17} color={colors.onSurfaceInverse} numberOfLines={1}>Lv {p?.level ?? 1}</T>
              <T w="bold" size={11} color={colors.custom_gameMuted} testID="game-hud-xp" numberOfLines={1} style={{ flexShrink: 1 }}>{p ? `${p.xp} / ${p.next_level_xp} XP` : "— XP"}</T>
            </View>
            <View style={{ height: 6, borderRadius: 3, backgroundColor: colors.custom_gameLine, overflow: "hidden" }}>
              <LinearGradient colors={[colors.custom_neonCyan, colors.custom_neonGreen]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ width: `${pct * 100}%`, height: "100%" }} />
            </View>
          </View>
          <Press testID="rf-open-store" onPress={() => router.push("/rapid/shop")} accessibilityLabel="Arena store" style={{ flexDirection: "row", alignItems: "center", gap: 6, height: 44, paddingHorizontal: space.md, borderRadius: radius.pill, backgroundColor: colors.custom_gameCardHi, borderWidth: 1, borderColor: colors.custom_neonAmber + "66" }}>
            <Icon name="hexagon-multiple" size={16} color={colors.custom_neonAmber} />
            <T testID="game-hud-coins" w="heavy" size={14} color={colors.custom_neonAmber}>{p?.coins ?? 0}</T>
            <Icon name="storefront-outline" size={16} color={colors.custom_neonAmber} />
          </Press>
        </View>

        {/* 2 · The lobby stage + PLAY: the main event */}
        <Animated.View entering={FadeInDown.duration(350)} style={{ gap: space.lg }}>
          <BattleHero me={{ avatar: p?.avatar, frame: p?.equipped?.frame, entry: p?.equipped?.entry }} record={record}
            subjects={
              <View style={{ gap: space.sm }}>
              <View testID="rf-exam-toggle" style={{ flexDirection: "row", alignSelf: "center", gap: space.lg }}>
                {(["JEE", "NEET"] as const).map((e) => (
                  <Press key={e} testID={"rf-exam-" + e.toLowerCase()} onPress={() => switchExam(e)} accessibilityLabel={e === "JEE" ? "JEE Main" : "NEET UG"}
                    style={{ minHeight: 44, minWidth: 64, alignItems: "center", justifyContent: "center", borderBottomWidth: 2, borderBottomColor: exam === e ? colors.custom_neonAmber : "transparent" }}>
                    <T w="heavy" size={13} color={exam === e ? colors.custom_neonAmber : colors.custom_gameMuted} style={{ letterSpacing: 2 }}>{e === "JEE" ? "JEE MAIN" : "NEET UG"}</T>
                  </Press>
                ))}
              </View>
              <View style={{ flexDirection: "row", padding: 4, gap: 4, borderRadius: radius.pill, backgroundColor: colors.custom_gameBg + "D9", borderWidth: 1, borderColor: colors.custom_gameLine }}>
                {SUBJECTS.map(([s, l, ic]) => {
                  const on = subject === s;
                  return (
                    <Press key={s} testID={"rf-subject-" + s.toLowerCase()} onPress={() => { setSubject(s); setChapter(""); }} style={{ flex: 1, height: 44, borderRadius: radius.pill, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, backgroundColor: on ? subjectColor(s) : "transparent", shadowColor: colors.custom_neonCyan, shadowOpacity: on ? 0.6 : 0, shadowRadius: 10 }}>
                      <Icon name={ic} size={16} color={on ? colors.onSurfaceInverse : colors.custom_gameMuted} />
                      <T w="heavy" size={13} color={on ? colors.onSurfaceInverse : colors.custom_gameMuted} numberOfLines={1}>{l}</T>
                    </Press>
                  );
                })}
              </View>
              </View>
            }
            chapterPill={!cat.data && !cat.error ? <Skeleton h={52} /> : (
              <Press testID="rf-chapter-picker" onPress={() => setSheet("chapters")} scaleTo={0.97} style={{ flexDirection: "row", alignItems: "center", gap: space.sm, height: 52, paddingHorizontal: space.md, borderRadius: radius.pill, backgroundColor: colors.custom_gameCardHi, borderWidth: 1.5, borderColor: tint, shadowColor: tint, shadowOpacity: 0.5, shadowRadius: 12, elevation: 8 }}>
                <View style={{ width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center", backgroundColor: tint + "33" }}><Icon name="map-marker-radius" size={18} color={tint} /></View>
                <View style={{ flex: 1 }}>
                  <T w="heavy" size={14} color={colors.onSurfaceInverse} numberOfLines={1}>{chapter || `Mixed ${subject === "Mathematics" ? "Maths" : subject}`}</T>
                  <T size={11} color={colors.custom_gameMuted} testID="rf-session-summary" numberOfLines={1}>{available ? `${available} cards · tap to change` : "No cards yet"}</T>
                </View>
                <Icon name="chevron-down" size={22} color={colors.onSurfaceInverse} />
              </Press>
            )} />
          <ErrorBox error={cat.error && !cat.data ? cat.error : ""} retry={cat.reload} testID="rf-catalog-error" />
          <PlayButton disabled={!can} sub={`${exam} 1v1 · same 30 cards · winner takes the coins`} onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "random", exam, subject, chapter } })} />
          <View style={{ flexDirection: "row", gap: space.md }}>
            <OutlineAction testID="rf-duel-invite" icon="account-multiple-plus" label="Challenge friend" tint={colors.custom_neonViolet} disabled={!can} onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "invite", exam, subject, chapter } })} />
            <OutlineAction testID="rf-open-join" icon="ticket-confirmation-outline" label="Join code" tint={colors.custom_neonCyan} onPress={() => setSheet("join")} />
          </View>
        </Animated.View>

        {/* 3 · Solo practice: a calm secondary row */}
        <Press testID="rf-start-button" onPress={() => router.push({ pathname: "/rapid/session", params: { exam, subject, chapter } })} disabled={!can} scaleTo={0.97}
          style={{ flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 68, paddingHorizontal: space.md, borderRadius: radius.lg, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_neonAmber + "55", opacity: can ? 1 : 0.5 }}>
          <LinearGradient colors={[colors.custom_neonAmber, colors.custom_examBitsat]} style={{ width: 44, height: 44, borderRadius: 14, alignItems: "center", justifyContent: "center" }}>
            <Icon name="lightning-bolt" size={24} color={colors.custom_gameBg} />
          </LinearGradient>
          <View style={{ flex: 1 }}>
            <T w="heavy" size={15} color={colors.onSurfaceInverse}>Solo Sprint</T>
            <T size={12} color={colors.custom_gameMuted}>Practise alone · 30 cards · 20 s each</T>
          </View>
          <Icon name="play-circle" size={30} color={colors.custom_neonAmber} />
        </Press>

        {exam === "NEET" ? <DiagramShortcut count={cat.data?.diagram_count || 0} /> : null}
        {user ? <WeakRevision key={`${user.id}.${exam}.${revisionRefresh}`} uid={user.id} exam={exam} /> : null}

        {/* 2 · Today: streak + quests as two calm tiles */}
        <View style={{ flexDirection: "row", gap: space.md }}>
          <View testID="rf-streak-card" style={{ flex: 1, padding: space.md, gap: 8, borderRadius: radius.lg, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_gameLine }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Icon name="fire" size={22} color={p?.played_today ? colors.custom_examBitsat : colors.custom_gameMuted} />
              <T testID="game-hud-streak" w="heavy" size={20} color={colors.onSurfaceInverse}>{p?.streak ?? 0}</T>
              <T w="bold" size={12} color={colors.custom_gameMuted}>day streak</T>
            </View>
            <View style={{ flexDirection: "row", gap: 4 }}>
              {Array.from({ length: 7 }, (_, i) => <View key={i} style={{ flex: 1, height: 4, borderRadius: 2, backgroundColor: i < Math.min(7, p?.streak ?? 0) ? colors.custom_neonAmber : colors.custom_gameLine }} />)}
            </View>
            <T size={11} color={colors.custom_gameMuted} numberOfLines={1}>{p?.played_today ? "Lit for today" : "Play once today"} · ❄ {p?.freezes ?? 0}</T>
          </View>
          <Press testID="rf-daily-quests" onPress={() => setSheet("quests")} style={{ flex: 1, padding: space.md, gap: 8, borderRadius: radius.lg, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: claimable ? colors.custom_neonGreen : colors.custom_gameLine }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Icon name={claimable ? "gift" : "calendar-check"} size={22} color={claimable ? colors.custom_neonGreen : colors.custom_neonCyan} />
              <T w="heavy" size={20} color={colors.onSurfaceInverse}>{questsDone}/{quests.length || 3}</T>
              <T w="bold" size={12} color={colors.custom_gameMuted}>quests</T>
            </View>
            <View style={{ height: 4, borderRadius: 2, backgroundColor: colors.custom_gameLine, overflow: "hidden" }}>
              <View style={{ width: `${quests.length ? (questsDone / quests.length) * 100 : 0}%`, height: "100%", backgroundColor: colors.custom_neonCyan }} />
            </View>
            <T w={claimable ? "heavy" : "regular"} size={11} color={claimable ? colors.custom_neonGreen : colors.custom_gameMuted} numberOfLines={1}>{claimable ? `${claimable} reward ready · Claim` : "Resets at midnight"}</T>
          </Press>
        </View>

        {/* 5 · One switcher instead of three long lists */}
        <View style={{ gap: space.md }}>
          <View style={{ flexDirection: "row", gap: space.lg, borderBottomWidth: 1, borderBottomColor: colors.custom_gameLine }}>
            {([["board", "Leaderboard"], ["recent", "Recent"], ["trophies", "Trophies"]] as [Pane, string][]).map(([k, l]) => (
              <Press key={k} testID={"rf-pane-" + k} onPress={() => setPane(k)} style={{ minHeight: 44, justifyContent: "center", borderBottomWidth: 2, borderBottomColor: pane === k ? colors.custom_neonAmber : "transparent", marginBottom: -1 }}>
                <T w="heavy" size={14} color={pane === k ? colors.onSurfaceInverse : colors.custom_gameMuted}>{l}</T>
              </Press>
            ))}
          </View>

          {pane === "board" ? (
            <ExamLeaderboard exam={exam} data={board.data} error={board.error} loading={board.loading} retry={board.reload} />
          ) : null}

          {pane === "recent" ? (
            <View style={{ gap: space.sm }}>
              {hist.data?.items?.length ? hist.data.items.slice(0, 5).map((s: any) => (
                <Press key={s.id} testID={"rf-history-" + s.id} onPress={() => router.push({ pathname: "/rapid/session", params: { review: s.id } })} style={{ flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 56, paddingHorizontal: space.md, borderRadius: radius.md, backgroundColor: colors.custom_gameCard }}>
                  <View style={{ width: 42, height: 42, borderRadius: 12, backgroundColor: scoreColor(s.summary), alignItems: "center", justifyContent: "center" }}>
                    <T w="heavy" size={13} color={colors.custom_gameBg}>{s.summary?.score}/{s.summary?.total}</T>
                  </View>
                  <View style={{ flex: 1 }}>
                    <T w="bold" size={14} color={colors.onSurfaceInverse} numberOfLines={1}>{s.chapter || "Mixed " + s.subject}{s.mode === "repeat_missed" ? " · missed repeat" : ""}</T>
                    <T size={12} color={colors.custom_gameMuted}>{s.summary?.incorrect} wrong · {s.summary?.skipped} skipped</T>
                  </View>
                  <Icon name="chevron-right" size={20} color={colors.custom_gameMuted} />
                </Press>
              )) : <T size={13} color={colors.custom_gameMuted}>Your finished sprints will show here.</T>}
            </View>
          ) : null}

          {pane === "trophies" && p ? (
            <View testID="rf-badges" style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
              {p.badges.map((b) => (
                <View key={b.id} testID={"rf-badge-" + b.id} accessibilityLabel={`${b.title}: ${b.body}${b.earned ? ", earned" : ", locked"}`} style={{ width: "31.5%", paddingVertical: space.md, borderRadius: radius.md, alignItems: "center", gap: 4, backgroundColor: colors.custom_gameCard, opacity: b.earned ? 1 : 0.45 }}>
                  <Icon name={b.earned ? BADGE_ICON[b.id] || "medal" : "lock-outline"} size={24} color={b.earned ? colors.custom_neonAmber : colors.custom_gameMuted} />
                  <T w="bold" size={11} color={colors.onSurfaceInverse} numberOfLines={1}>{b.title}</T>
                </View>
              ))}
            </View>
          ) : null}
        </View>

        <T size={10} color={colors.custom_gameMuted} style={{ textAlign: "center" }}>Practice XP only. Never changes mock marks, ranks or the series streak.</T>
      </ScrollView>

      <ChapterSheet visible={sheet === "chapters"} onClose={() => setSheet("")} subjects={(cat.data?.subjects || []).filter((s: any) => SUBJECTS.some(([n]) => n === s.name))} subject={subject} chapter={chapter}
        recent={recent.filter((r) => SUBJECTS.some(([n]) => n === r.subject))} onPick={(sb, ch) => { if (!SUBJECTS.some(([n]) => n === sb)) setExam(sb === "Biology" ? "NEET" : "JEE"); setSubject(sb); setChapter(ch); setSheet(""); }} />

      <Sheet visible={sheet === "quests"} onClose={() => setSheet("")} testID="rf-quests-sheet">
        <T w="heavy" size={18}>Daily quests</T>
        <T size={12} color={colors.muted}>Reset at midnight IST</T>
        {quests.map((q: any) => (
          <View key={q.id} testID={"rf-quest-" + q.id} style={{ gap: 6 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
              <Icon name={q.claimed ? "check-decagram" : q.done ? "gift" : "checkbox-blank-circle-outline"} size={20} color={q.done ? colors.success : colors.muted} />
              <T w="bold" size={14} style={{ flex: 1 }}>{q.title}</T>
              {q.done && !q.claimed ? (
                <Press testID={"rf-quest-claim-" + q.id} onPress={async () => { setClaimErr(""); try { await rf("/quests/claim", user!.id, { method: "POST", body: { id: q.id } }); playSfx("coin"); prof.reload(); } catch (e: any) { setClaimErr(e?.message || "Couldn't claim. Please retry in a moment."); } }} style={{ paddingHorizontal: 16, height: 44, borderRadius: 22, backgroundColor: colors.custom_neonAmber, justifyContent: "center" }}>
                  <T w="heavy" size={13} color={colors.custom_gameBg}>Claim +{q.coins}</T>
                </Press>
              ) : <T w="bold" size={12} color={colors.custom_neonAmber}>{q.claimed ? "Claimed" : `${q.progress}/${q.goal} · +${q.coins}`}</T>}
            </View>
            <View style={{ height: 4, borderRadius: 2, backgroundColor: colors.border, overflow: "hidden" }}>
              <View style={{ width: `${(q.progress / q.goal) * 100}%`, height: "100%", backgroundColor: q.done ? colors.success : colors.brandPrimary }} />
            </View>
          </View>
        ))}
        {claimErr ? <T testID="rf-quest-claim-error" size={12} w="bold" color={colors.error}>{claimErr}</T> : null}
      </Sheet>

      {sheet === "join" ? <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: 0, zIndex: 50 }}>
      <Sheet visible onClose={() => setSheet("")} testID="rf-join-sheet">
        <T w="heavy" size={18}>Join a friend’s duel</T>
        <T size={13} color={colors.muted}>Enter the 6-character code your friend shared.</T>
        <TextInput testID="rf-duel-code-input" value={code} onChangeText={(t) => setCode(t.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6))} placeholder="ABC123" placeholderTextColor={colors.muted} autoCapitalize="characters" autoFocus
          style={{ height: 56, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: space.md, fontFamily: fonts.heavy, fontSize: 22, letterSpacing: 6, textAlign: "center", color: colors.onSurface, backgroundColor: colors.surface }} />
        <Press testID="rf-duel-join" disabled={code.length < 6 || !user} onPress={() => { setSheet(""); router.push({ pathname: "/rapid/duel", params: { mode: "join", exam, code } }); }} style={{ height: 52, borderRadius: radius.md, backgroundColor: colors.custom_neonAmber, alignItems: "center", justifyContent: "center", opacity: code.length < 6 ? 0.5 : 1 }}>
          <T w="heavy" size={16} color={colors.custom_gameBg}>JOIN DUEL</T>
        </Press>
      </Sheet>
      </KeyboardAvoidingView> : null}
    </View>
  );
}
