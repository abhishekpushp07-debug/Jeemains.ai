import React, { useEffect, useState } from "react";
import { Modal, Pressable, View } from "react-native";
import { useRouter } from "expo-router";
import { playSfx } from "@/src/sfx";
import Animated, { Easing, FadeInDown, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withTiming, ZoomIn } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

export type GameProfile = { xp: number; level: number; level_floor: number; next_level_xp: number; coins: number; streak: number; best_streak: number; played_today: boolean; sessions: number; duels: number; wins: number; cards_correct: number; badges: { id: string; title: string; body: string; earned: boolean }[]; avatar?: string; equipped?: Record<string, string | null>; owned?: string[]; freezes?: number; quests?: any[] };
export type Reward = { xp: number; coins: number; streak: number; level_before: number; level_after: number; level_up: boolean; new_badges: { id: string; title: string; body: string }[];
  xp_total?: number; coins_total?: number; level_floor?: number; next_level_xp?: number; played?: boolean; quest_ready?: boolean };

export const BADGE_ICON: Record<string, any> = { first_sprint: "flag-checkered", first_win: "sword", streak_3: "fire", streak_7: "fire-circle", streak_30: "crown", sharpshooter: "target", perfect: "star-shooting", duelist_10: "sword-cross", champion_10: "trophy-award" };

export function useGameProfile(uid?: string) {
  return useCached<GameProfile>(uid ? `u.${uid}.rfprofile` : null, () => rf("/profile", uid!));
}

export function LevelGem({ level, size = 46 }: { level: number; size?: number }) {
  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <LinearGradient colors={[colors.custom_neonAmber, colors.custom_amber]} style={{ position: "absolute", width: size * 0.78, height: size * 0.78, borderRadius: 10, transform: [{ rotate: "45deg" }], borderWidth: 2, borderColor: colors.custom_whiteA70 }} />
      <T w="heavy" size={size * 0.36} color={colors.custom_gameBg}>{level}</T>
    </View>
  );
}

export function GameHUD({ p, testID = "game-hud" }: { p?: GameProfile | null; testID?: string }) {
  const pct = p ? Math.min(1, (p.xp - p.level_floor) / Math.max(1, p.next_level_xp - p.level_floor)) : 0;
  return (
    <View testID={testID} style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderRadius: radius.lg, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_gameLine }}>
      <LevelGem level={p?.level ?? 1} />
      <View style={{ flex: 1, gap: 4 }}>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <T w="heavy" size={13} color={colors.onSurfaceInverse}>Level {p?.level ?? 1}</T>
          <T w="bold" size={11} color={colors.custom_gameMuted} testID="game-hud-xp">{p ? `${p.xp} / ${p.next_level_xp} XP` : "— XP"}</T>
        </View>
        <View style={{ height: 8, borderRadius: 4, backgroundColor: colors.custom_gameLine, overflow: "hidden" }}>
          <LinearGradient colors={[colors.custom_neonCyan, colors.custom_neonGreen]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ width: `${pct * 100}%`, height: "100%" }} />
        </View>
      </View>
      <View testID="game-hud-coins" style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, height: 30, borderRadius: radius.pill, backgroundColor: colors.custom_gameCardHi }}>
        <Icon name="hexagon-multiple" size={15} color={colors.custom_neonAmber} />
        <T w="heavy" size={13} color={colors.custom_neonAmber}>{p?.coins ?? 0}</T>
      </View>
      <View testID="game-hud-streak" style={{ flexDirection: "row", alignItems: "center", gap: 2, paddingHorizontal: 8, height: 30, borderRadius: radius.pill, backgroundColor: colors.custom_gameCardHi }}>
        <Icon name="fire" size={16} color={p?.played_today ? colors.custom_examBitsat : colors.custom_gameMuted} />
        <T w="heavy" size={13} color={colors.onSurfaceInverse}>{p?.streak ?? 0}</T>
      </View>
    </View>
  );
}

function Particle({ i }: { i: number }) {
  const t = useSharedValue(0);
  const angle = (i / 16) * Math.PI * 2;
  const dist = 90 + (i % 4) * 22;
  useEffect(() => {
    t.value = withDelay(i * 15, withTiming(1, { duration: 900, easing: Easing.out(Easing.cubic) }));
  }, [t, i]);
  const s = useAnimatedStyle(() => ({ opacity: 1 - t.value, transform: [{ translateX: Math.cos(angle) * dist * t.value }, { translateY: Math.sin(angle) * dist * t.value }, { scale: 1 - t.value * 0.5 }] }));
  const c = [colors.custom_neonAmber, colors.custom_neonCyan, colors.custom_neonGreen, colors.custom_neonRed][i % 4];
  return <Animated.View style={[{ position: "absolute", width: 10, height: 10, borderRadius: i % 2 ? 5 : 2, backgroundColor: c }, s]} />;
}

// One-shot celebration burst (never loops; skipped when Reduce Motion is on).
export function Burst() {
  const reduced = useReducedMotion();
  if (reduced) return null;
  return (
    <View pointerEvents="none" style={{ position: "absolute", top: 60, left: 0, right: 0, alignItems: "center" }}>
      {Array.from({ length: 16 }, (_, i) => <Particle key={i} i={i} />)}
    </View>
  );
}

function CountUp({ to, color, size = 26, prefix = "+" }: { to: number; color: string; size?: number; prefix?: string }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    let k = 0;
    const steps = 20;
    const iv = setInterval(() => {
      k += 1;
      setV(Math.round((to * k) / steps));
      if (k >= steps) clearInterval(iv);
    }, 35);
    return () => clearInterval(iv);
  }, [to]);
  return <T w="heavy" size={size} color={color}>{prefix}{v}</T>;
}

function XpBar({ r }: { r: Reward }) {
  const reduced = useReducedMotion();
  const span = Math.max(1, (r.next_level_xp ?? 1) - (r.level_floor ?? 0));
  const to = Math.min(1, ((r.xp_total ?? 0) - (r.level_floor ?? 0)) / span);
  const from = r.level_up ? 0 : Math.max(0, to - r.xp / span);
  const w = useSharedValue(from);
  useEffect(() => { w.value = reduced ? to : withDelay(400, withTiming(to, { duration: 900, easing: Easing.out(Easing.cubic) })); }, [to]); // eslint-disable-line react-hooks/exhaustive-deps
  const st = useAnimatedStyle(() => ({ width: `${w.value * 100}%` }));
  return (
    <View style={{ alignSelf: "stretch", gap: 6 }} testID="reward-xp-bar">
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        <T w="heavy" size={12} color={colors.onSurfaceInverse}>Level {r.level_after}</T>
        <T w="bold" size={12} color={colors.custom_gameMuted}>{(r.next_level_xp ?? 0) - (r.xp_total ?? 0)} XP to Level {r.level_after + 1}</T>
      </View>
      <View style={{ height: 10, borderRadius: 5, backgroundColor: colors.custom_gameLine, overflow: "hidden" }}>
        <Animated.View style={[{ height: "100%", borderRadius: 5, overflow: "hidden" }, st]}>
          <LinearGradient colors={[colors.custom_neonCyan, colors.custom_neonGreen]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ flex: 1 }} />
        </Animated.View>
      </View>
    </View>
  );
}

// Full-screen level-up moment (tap anywhere to continue).
function LevelUpOverlay({ level, onClose }: { level: number; onClose: () => void }) {
  useEffect(() => { playSfx("levelup"); const t = setTimeout(onClose, 2600); return () => clearTimeout(t); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <Modal transparent animationType="fade" visible onRequestClose={onClose}>
      <Pressable testID="level-up-overlay" onPress={onClose} style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_gameBg + "F2", gap: space.lg }}>
        <Burst />
        <Animated.View entering={ZoomIn.springify().damping(8)}><LevelGem level={level} size={150} /></Animated.View>
        <Animated.View entering={FadeInDown.delay(250)} style={{ alignItems: "center", gap: 4 }}>
          <T w="heavy" size={40} color={colors.custom_neonAmber} style={{ letterSpacing: 3 }}>LEVEL UP!</T>
          <T w="bold" size={16} color={colors.onSurfaceInverse}>You reached Level {level}</T>
          <T size={12} color={colors.custom_gameMuted}>Tap to continue</T>
        </Animated.View>
      </Pressable>
    </Modal>
  );
}

export function RewardPanel({ reward, title, testID = "reward-panel" }: { reward?: Reward | null; title: string; testID?: string }) {
  const router = useRouter();
  const [closed, setClosed] = useState<number | null>(null);
  const lvl = !!reward?.level_up && closed !== reward.level_after;
  useEffect(() => {
    if (reward && !reward.level_up && reward.coins > 0) playSfx("coin", 0.7);
  }, [reward?.level_after, reward?.coins]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!reward) return null;
  if (reward.played === false) {
    return (
      <View testID={testID} style={{ borderRadius: radius.lg, padding: space.lg, gap: space.sm, alignItems: "center", backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_gameLine }}>
        <Icon name="treasure-chest" size={40} color={colors.custom_gameMuted} />
        <T w="heavy" size={17} color={colors.onSurfaceInverse}>{title}</T>
        <T size={13} color={colors.custom_gameMuted} style={{ textAlign: "center" }}>Answer at least one card to earn XP, coins and keep your streak alive.</T>
      </View>
    );
  }
  return (
    <View testID={testID} style={{ borderRadius: radius.lg, overflow: "hidden" }}>
      <LinearGradient colors={[colors.custom_gameCardHi, colors.custom_gameBg]} style={{ padding: space.lg, gap: space.md, alignItems: "center" }}>
        <Burst />
        <Animated.View entering={ZoomIn.duration(350)}><Icon name="treasure-chest" size={54} color={colors.custom_neonAmber} /></Animated.View>
        <T w="heavy" size={20} color={colors.onSurfaceInverse} style={{ textAlign: "center" }}>{title}</T>
        <View style={{ flexDirection: "row", gap: space.md }}>
          <View style={{ alignItems: "center", flex: 1, padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_gameCard }} testID="reward-xp">
            <CountUp to={reward.xp} color={colors.custom_neonCyan} />
            <T size={11} w="bold" color={colors.custom_gameMuted}>XP</T>
          </View>
          <View style={{ alignItems: "center", flex: 1, padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_gameCard }} testID="reward-coins">
            <CountUp to={reward.coins} color={colors.custom_neonAmber} />
            <T size={11} w="bold" color={colors.custom_gameMuted}>COINS</T>
          </View>
          <View style={{ alignItems: "center", flex: 1, padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_gameCard }} testID="reward-streak">
            <View style={{ flexDirection: "row", alignItems: "center" }}><Icon name="fire" size={22} color={colors.custom_examBitsat} /><T w="heavy" size={26} color={colors.onSurfaceInverse}>{reward.streak}</T></View>
            <T size={11} w="bold" color={colors.custom_gameMuted}>DAY STREAK</T>
          </View>
        </View>
        {reward.level_up ? (
          <Animated.View entering={FadeInDown.delay(300)} testID="reward-level-up" style={{ flexDirection: "row", alignItems: "center", gap: space.sm, paddingHorizontal: space.lg, paddingVertical: space.sm, borderRadius: radius.pill, backgroundColor: colors.custom_neonAmber }}>
            <Icon name="arrow-up-bold-circle" size={20} color={colors.custom_gameBg} />
            <T w="heavy" size={14} color={colors.custom_gameBg}>LEVEL UP! You reached Level {reward.level_after}</T>
          </Animated.View>
        ) : null}
        <XpBar r={reward} />
        {reward.coins_total != null ? (
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }} testID="reward-coin-balance">
            <Icon name="hexagon-multiple" size={16} color={colors.custom_neonAmber} />
            <T w="bold" size={13} color={colors.custom_gameMuted}>Balance <T w="heavy" size={13} color={colors.custom_neonAmber}>{reward.coins_total}</T> coins</T>
          </View>
        ) : null}
        {reward.quest_ready ? (
          <Pressable testID="reward-quest-ready" onPress={() => router.push("/(tabs)/rapid")} style={{ flexDirection: "row", alignItems: "center", gap: space.sm, alignSelf: "stretch", minHeight: 44, paddingHorizontal: space.md, borderRadius: radius.md, backgroundColor: colors.custom_neonGreen }}>
            <Icon name="gift" size={20} color={colors.custom_gameBg} />
            <T w="heavy" size={13} color={colors.custom_gameBg} style={{ flex: 1 }}>Daily quest complete — claim your coins!</T>
            <Icon name="chevron-right" size={20} color={colors.custom_gameBg} />
          </Pressable>
        ) : null}
        {lvl ? <LevelUpOverlay level={reward.level_after} onClose={() => setClosed(reward.level_after)} /> : null}
        {reward.new_badges.map((b, i) => (
          <Animated.View key={b.id} entering={FadeInDown.delay(450 + i * 150)} testID={"reward-badge-" + b.id} style={{ flexDirection: "row", alignItems: "center", gap: space.md, alignSelf: "stretch", padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_neonAmber }}>
            <Icon name={BADGE_ICON[b.id] || "medal"} size={28} color={colors.custom_neonAmber} />
            <View style={{ flex: 1 }}>
              <T w="heavy" size={14} color={colors.custom_neonAmber}>New badge · {b.title}</T>
              <T size={12} color={colors.custom_gameMuted}>{b.body}</T>
            </View>
          </Animated.View>
        ))}
      </LinearGradient>
    </View>
  );
}
