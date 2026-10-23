import React, { useCallback, useRef, useState } from "react";
import { RefreshControl, ScrollView, TextInput, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { invalidate, useCached } from "@/src/useCached";
import { ErrorBox, Icon, IconName, Press, Skeleton, T } from "@/src/components/ui";
import { BADGE_ICON, GameHUD, useGameProfile } from "@/src/components/game";
import { Avatar } from "@/src/components/Entry";
import { playSfx } from "@/src/sfx";
import { colors, fonts, radius, space, subjectColor } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

const pick = { subject: "Physics", chapter: "" as string };
// Purchased arena themes (fixed artwork colours, identical in light/dark).
const THEME_BG: Record<string, string> = { theme_inferno: "#1F0707", theme_ocean: "#03202B", theme_gold: "#1F1704" };
const SUBJECTS: [string, string, IconName][] = [["Physics", "Physics", "atom"], ["Chemistry", "Chemistry", "flask-outline"], ["Mathematics", "Maths", "function-variant"]];

function GChip({ label, active, count, onPress, testID, tint }: { label: string; active: boolean; count?: number; onPress: () => void; testID: string; tint: string }) {
  return (
    <Press testID={testID} onPress={onPress} style={{ height: 44, flexShrink: 0, paddingHorizontal: space.md, borderRadius: radius.pill, flexDirection: "row", alignItems: "center", gap: 6, borderWidth: 1, borderColor: active ? tint : colors.custom_gameLine, backgroundColor: active ? tint : colors.custom_gameCard }}>
      <T w="bold" size={13} color={colors.onSurfaceInverse}>{label}</T>
      {count !== undefined ? <T w="bold" size={11} color={active ? colors.onSurfaceInverse : colors.custom_gameMuted}>{count}</T> : null}
    </Press>
  );
}

function Mode({ testID, icon, title, sub, grad, onPress, disabled, tag }: { testID: string; icon: IconName; title: string; sub: string; grad: [string, string]; onPress: () => void; disabled?: boolean; tag?: string }) {
  return (
    <Press testID={testID} onPress={onPress} disabled={disabled} scaleTo={0.96} style={{ borderRadius: radius.lg, overflow: "hidden" }}>
      <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ padding: space.lg, flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 84 }}>
        <View style={{ position: "absolute", right: -18, top: -18, width: 90, height: 90, borderRadius: 45, backgroundColor: colors.custom_whiteA15 }} />
        <View style={{ width: 52, height: 52, borderRadius: 16, backgroundColor: colors.custom_whiteA15, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: colors.custom_whiteA70 }}>
          <Icon name={icon} size={28} color={colors.onSurfaceInverse} />
        </View>
        <View style={{ flex: 1 }}>
          <T w="heavy" size={17} color={colors.onSurfaceInverse} style={{ letterSpacing: 0.5 }}>{title}</T>
          <T size={12} color={colors.custom_whiteA70}>{sub}</T>
        </View>
        {tag ? <View style={{ paddingHorizontal: 8, height: 22, borderRadius: radius.pill, backgroundColor: colors.custom_gameBg, justifyContent: "center" }}><T w="heavy" size={10} color={colors.custom_neonAmber}>{tag}</T></View> : <Icon name="play-circle" size={30} color={colors.onSurfaceInverse} />}
      </LinearGradient>
    </Press>
  );
}

const scoreColor = (m: any) => {
  const r = m?.total ? m.score / m.total : 0;
  return r >= 0.8 ? colors.custom_neonGreen : r >= 0.5 ? colors.custom_neonAmber : colors.custom_neonRed;
};

export default function RapidHome() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const [subject, setSubject] = useState(pick.subject);
  const [chapter, setChapter] = useState(pick.chapter);
  Object.assign(pick, { subject, chapter });
  const cat = useCached<any>("rf.catalog", () => rf("/catalog", user?.id || "guest-viewer"));
  const hist = useCached<any>(user ? `u.${user.id}.rfhist` : null, () => rf("/history", user!.id));
  const duels = useCached<any>(user ? `u.${user.id}.duels` : null, () => rf("/duels", user!.id));
  const prof = useGameProfile(user?.id);
  const [claimErr, setClaimErr] = useState("");
  const board = useCached<any>(user ? `u.${user.id}.rfboard` : null, () => rf("/leaderboard", user!.id));
  const [code, setCode] = useState("");
  const sub = cat.data?.subjects?.find((s: any) => s.name === subject);
  const chosen = chapter ? sub?.chapters.find((c: any) => c.name === chapter) : null;
  const available = chosen ? chosen.count : sub?.total ?? 0;
  const tint = subjectColor(subject);
  const p = prof.data;
  const can = !!available && !!user;
  const reload = () => { cat.reload(); hist.reload(); duels.reload(); prof.reload(); board.reload(); };
  // Refresh XP / streak / history whenever the arena regains focus (e.g. after a sprint or duel).
  const first = useRef(true);
  useFocusEffect(useCallback(() => {
    if (first.current) { first.current = false; return; }
    hist.reload(); duels.reload(); prof.reload(); board.reload(); invalidate(`u.${user?.id}.rfshop`);
  }, [hist.reload, duels.reload, prof.reload, board.reload])); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <ScrollView testID="rapid-fire-home" style={{ flex: 1, backgroundColor: THEME_BG[p?.equipped?.theme || ""] || colors.custom_gameBg }} contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xl, paddingHorizontal: space.lg, gap: space.lg }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={reload} tintColor={colors.custom_neonAmber} />}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
        <Icon name="lightning-bolt" size={26} color={colors.custom_neonAmber} />
        <View style={{ flex: 1 }}>
          <T w="heavy" size={11} color={colors.custom_neonAmber} style={{ letterSpacing: 2 }}>RAPID FIRE ARENA</T>
          <T w="heavy" size={24} color={colors.onSurfaceInverse}>Recall. Race. Rise.</T>
        </View>
        <Press testID="rf-open-store" onPress={() => router.push("/rapid/shop")} accessibilityLabel="Arena store" style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: space.md, height: 44, borderRadius: radius.pill, backgroundColor: colors.custom_neonAmber }}>
          <Icon name="storefront" size={18} color={colors.custom_gameBg} />
          <T w="heavy" size={13} color={colors.custom_gameBg}>Store</T>
        </Press>
        <Press testID="rf-open-avatar" onPress={() => router.push({ pathname: "/rapid/shop", params: { tab: "avatar" } })} accessibilityLabel="Change avatar">
          <Avatar icon={p?.avatar} frame={p?.equipped?.frame} size={44} />
        </Press>
      </View>
      <GameHUD p={p} />

      {p?.quests ? (
        <View testID="rf-daily-quests" style={{ gap: space.sm, padding: space.lg, borderRadius: radius.lg, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_gameLine }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <Icon name="calendar-star" size={20} color={colors.custom_neonCyan} />
            <T w="heavy" size={15} color={colors.onSurfaceInverse} style={{ flex: 1 }}>Daily Quests</T>
            <T size={11} color={colors.custom_gameMuted}>Reset at midnight IST</T>
          </View>
          {p.quests.map((q: any) => (
            <View key={q.id} testID={"rf-quest-" + q.id} style={{ gap: 4 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
                <Icon name={q.claimed ? "check-decagram" : q.done ? "gift" : "checkbox-blank-circle-outline"} size={18} color={q.done ? colors.custom_neonGreen : colors.custom_gameMuted} />
                <T w="bold" size={13} color={colors.onSurfaceInverse} style={{ flex: 1 }}>{q.title}</T>
                {q.done && !q.claimed ? (
                  <Press testID={"rf-quest-claim-" + q.id} onPress={async () => { setClaimErr(""); try { await rf("/quests/claim", user!.id, { method: "POST", body: { id: q.id } }); playSfx("coin"); prof.reload(); } catch (e: any) { setClaimErr(e?.message || "Couldn't claim. Please retry in a moment."); } }} style={{ paddingHorizontal: 14, height: 44, borderRadius: 22, backgroundColor: colors.custom_neonAmber, justifyContent: "center" }}>
                    <T w="heavy" size={12} color={colors.custom_gameBg}>Claim +{q.coins}</T>
                  </Press>
                ) : <T w="bold" size={12} color={colors.custom_neonAmber}>{q.claimed ? "Claimed" : `${q.progress}/${q.goal} · +${q.coins}`}</T>}
              </View>
              <View style={{ height: 5, borderRadius: 3, backgroundColor: colors.custom_gameLine, overflow: "hidden" }}>
                <View style={{ width: `${(q.progress / q.goal) * 100}%`, height: "100%", backgroundColor: q.done ? colors.custom_neonGreen : colors.custom_neonCyan }} />
              </View>
            </View>
          ))}
          {claimErr ? <T testID="rf-quest-claim-error" size={12} w="bold" color={colors.custom_neonRed}>{claimErr}</T> : null}
        </View>
      ) : null}

      <Animated.View entering={FadeInDown.duration(350)}>
        <LinearGradient testID="rf-streak-card" colors={[colors.custom_examBitsatDeep, colors.custom_gameCard]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ borderRadius: radius.lg, padding: space.lg, gap: space.md, borderWidth: 1, borderColor: colors.custom_gameLine }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
            <Icon name="fire" size={44} color={p?.played_today ? colors.custom_neonAmber : colors.custom_gameMuted} />
            <View style={{ flex: 1 }}>
              <T w="heavy" size={20} color={colors.onSurfaceInverse}>{p?.streak ?? 0}-day streak</T>
              <T size={12} color={colors.custom_whiteA70}>{p?.played_today ? "Today’s fire is lit. Come back tomorrow!" : "Finish one sprint or duel today to keep it burning."} Best: {p?.best_streak ?? 0} · ❄ {p?.freezes ?? 0} freezes</T>
            </View>
          </View>
          <View style={{ flexDirection: "row", gap: 6 }}>
            {Array.from({ length: 7 }, (_, i) => {
              const lit = i < Math.min(7, p?.streak ?? 0);
              return <View key={i} style={{ flex: 1, height: 8, borderRadius: 4, backgroundColor: lit ? colors.custom_neonAmber : colors.custom_gameLine }} />;
            })}
          </View>
          <T size={10} color={colors.custom_gameMuted}>Rapid Fire streak is separate from the All India series streak.</T>
        </LinearGradient>
      </Animated.View>

      <View style={{ gap: space.sm }}>
        <T w="heavy" size={13} color={colors.custom_gameMuted} style={{ letterSpacing: 1.5 }}>CHOOSE YOUR ARENA</T>
        <View style={{ flexDirection: "row", gap: space.sm }}>
          {SUBJECTS.map(([s, l, ic]) => {
            const on = subject === s;
            return (
              <Press key={s} testID={"rf-subject-" + s.toLowerCase()} onPress={() => { setSubject(s); setChapter(""); }} style={{ flex: 1, height: 84, borderRadius: radius.lg, alignItems: "center", justifyContent: "center", gap: 4, backgroundColor: on ? subjectColor(s) : colors.custom_gameCard, borderWidth: 2, borderColor: on ? colors.custom_whiteA70 : colors.custom_gameLine, shadowColor: subjectColor(s), shadowOpacity: on ? 0.6 : 0, shadowRadius: 14, elevation: on ? 8 : 0 }}>
                <Icon name={ic} size={28} color={on ? colors.onSurfaceInverse : subjectColor(s)} />
                <T w="heavy" size={13} color={colors.onSurfaceInverse}>{l}</T>
              </Press>
            );
          })}
        </View>
        <ErrorBox error={cat.error && !cat.data ? cat.error : ""} retry={cat.reload} testID="rf-catalog-error" />
        {!cat.data && !cat.error ? <Skeleton h={36} /> : null}
        {sub ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ height: 56, flexGrow: 0, marginHorizontal: -space.lg }} contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}>
            <GChip testID="rf-chapter-mixed" label={`Mixed ${subject === "Mathematics" ? "Maths" : subject}`} active={!chapter} tint={tint} count={sub.total} onPress={() => setChapter("")} />
            {sub.chapters.map((c: any) => (
              <GChip key={c.name} testID={"rf-chapter-" + c.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")} label={c.name} active={chapter === c.name} tint={tint} count={c.count} onPress={() => c.count && setChapter(c.name)} />
            ))}
          </ScrollView>
        ) : null}
        <T size={12} color={colors.custom_gameMuted} testID="rf-session-summary">{chapter || `Mixed ${subject}`} · {available ? `${Math.min(30, available)} cards · 20 s each · auto-next` : "No cards here yet"}</T>
      </View>

      <View style={{ gap: space.md }}>
        <T w="heavy" size={13} color={colors.custom_gameMuted} style={{ letterSpacing: 1.5 }}>GAME MODES</T>
        <Mode testID="rf-start-button" icon="lightning-bolt" title="SOLO SPRINT" sub="30 cards · beat your best · earn XP & coins" grad={[colors.custom_amber, colors.custom_examBitsatDeep]} disabled={!can} onPress={() => router.push({ pathname: "/rapid/session", params: { subject, chapter } })} />
        <Mode testID="rf-duel-random" icon="sword-cross" title="RANDOM DUEL" sub="Auto-match a live student · winner takes +50 coins" grad={[colors.custom_examJee, colors.custom_examJeeDeep]} disabled={!can} tag="PvP" onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "random", subject, chapter } })} />
        <Mode testID="rf-duel-invite" icon="whatsapp" title="CHALLENGE A FRIEND" sub="Send a duel code on WhatsApp" grad={[colors.success, colors.custom_subjectChemistry]} disabled={!can} onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "invite", subject, chapter } })} />
        <View style={{ flexDirection: "row", gap: space.sm, alignItems: "center" }}>
          <TextInput testID="rf-duel-code-input" value={code} onChangeText={(t) => setCode(t.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6))} placeholder="Got a code? Enter it" placeholderTextColor={colors.custom_gameMuted} autoCapitalize="characters"
            style={{ flex: 1, height: 52, borderRadius: radius.md, borderWidth: 1, borderColor: colors.custom_gameLine, paddingHorizontal: space.md, fontFamily: fonts.heavy, fontSize: 16, letterSpacing: 3, color: colors.onSurfaceInverse, backgroundColor: colors.custom_gameCard }} />
          <Press testID="rf-duel-join" disabled={code.length < 6 || !user} onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "join", code } })} style={{ height: 52, paddingHorizontal: space.xl, borderRadius: radius.md, backgroundColor: colors.custom_neonAmber, alignItems: "center", justifyContent: "center" }}>
            <T w="heavy" size={15} color={colors.custom_gameBg}>JOIN</T>
          </Press>
        </View>
        {duels.data?.items?.length ? (
          <T size={12} color={colors.custom_gameMuted} testID="rf-duel-record">Duel record (last {duels.data.items.length}): {duels.data.items.filter((x: any) => x.won).length}W · {duels.data.items.filter((x: any) => x.tie).length}T · {duels.data.items.filter((x: any) => !x.won && !x.tie).length}L</T>
        ) : null}
      </View>

      {p ? (
        <View style={{ gap: space.sm }} testID="rf-badges">
          <T w="heavy" size={13} color={colors.custom_gameMuted} style={{ letterSpacing: 1.5 }}>TROPHY CABINET · {p.badges.filter((b) => b.earned).length}/{p.badges.length}</T>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm }}>
            {p.badges.map((b) => (
              <View key={b.id} testID={"rf-badge-" + b.id} accessibilityLabel={`${b.title}: ${b.body}${b.earned ? ", earned" : ", locked"}`} style={{ width: "31.5%", padding: space.sm, borderRadius: radius.md, alignItems: "center", gap: 4, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: b.earned ? colors.custom_neonAmber : colors.custom_gameLine, opacity: b.earned ? 1 : 0.55 }}>
                <Icon name={b.earned ? BADGE_ICON[b.id] || "medal" : "lock"} size={24} color={b.earned ? colors.custom_neonAmber : colors.custom_gameMuted} />
                <T w="bold" size={11} color={colors.onSurfaceInverse} numberOfLines={1}>{b.title}</T>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {board.data?.items?.length ? (
        <View style={{ gap: space.sm }} testID="rf-leaderboard">
          <T w="heavy" size={13} color={colors.custom_gameMuted} style={{ letterSpacing: 1.5 }}>TOP PLAYERS · PRACTICE XP</T>
          {board.data.items.slice(0, 5).map((r: any) => (
            <View key={r.rank} style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderRadius: radius.md, backgroundColor: r.you ? colors.custom_gameCardHi : colors.custom_gameCard, borderWidth: 1, borderColor: r.you ? colors.custom_neonCyan : colors.custom_gameLine }}>
              <T w="heavy" size={16} color={r.rank === 1 ? colors.custom_neonAmber : colors.custom_gameMuted} style={{ width: 24 }}>#{r.rank}</T>
              <T w="bold" size={14} color={colors.onSurfaceInverse} style={{ flex: 1 }} numberOfLines={1}>{r.name}{r.you ? " (you)" : ""}</T>
              <T w="bold" size={12} color={colors.custom_neonCyan}>Lv {r.level} · {r.xp} XP</T>
            </View>
          ))}
          <T size={10} color={colors.custom_gameMuted}>Practice game XP only — not JEE marks, AIR or eligibility.</T>
        </View>
      ) : null}

      {hist.data?.items?.length ? (
        <View style={{ gap: space.sm }}>
          <T w="heavy" size={13} color={colors.custom_gameMuted} style={{ letterSpacing: 1.5 }}>RECENT SPRINTS · {hist.data.totals.sessions} played</T>
          {hist.data.items.slice(0, 5).map((s: any) => (
            <Press key={s.id} testID={"rf-history-" + s.id} onPress={() => router.push({ pathname: "/rapid/session", params: { review: s.id } })} style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_gameLine }}>
              <View style={{ width: 46, height: 46, borderRadius: 12, backgroundColor: scoreColor(s.summary), alignItems: "center", justifyContent: "center" }}>
                <T w="heavy" size={14} color={colors.custom_gameBg}>{s.summary?.score}/{s.summary?.total}</T>
              </View>
              <View style={{ flex: 1 }}>
                <T w="bold" size={14} color={colors.onSurfaceInverse} numberOfLines={1}>{s.chapter || "Mixed " + s.subject}{s.mode === "repeat_missed" ? " · missed repeat" : ""}</T>
                <T size={12} color={colors.custom_gameMuted}>{s.summary?.incorrect} wrong · {s.summary?.skipped} skipped · {s.summary?.timed_out} timed out</T>
              </View>
              <Icon name="chevron-right" size={22} color={colors.custom_gameMuted} />
            </Press>
          ))}
        </View>
      ) : null}
      <T size={10} color={colors.custom_gameMuted}>{cat.data?.note} Rapid Fire never changes mock marks, ranks or the series streak.</T>
    </ScrollView>
  );
}
