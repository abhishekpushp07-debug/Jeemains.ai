import React, { useEffect, useState } from "react";
import { View } from "react-native";
import Animated, { Easing, FadeInDown, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withTiming, ZoomIn } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

export type GameProfile = { xp: number; level: number; level_floor: number; next_level_xp: number; coins: number; streak: number; best_streak: number; played_today: boolean; sessions: number; duels: number; wins: number; cards_correct: number; badges: { id: string; title: string; body: string; earned: boolean }[]; avatar?: string; equipped?: Record<string, string | null>; owned?: string[]; freezes?: number; quests?: any[] };
export type Reward = { xp: number; coins: number; streak: number; level_before: number; level_after: number; level_up: boolean; new_badges: { id: string; title: string; body: string }[] };

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

export function RewardPanel({ reward, title, testID = "reward-panel" }: { reward?: Reward | null; title: string; testID?: string }) {
  if (!reward) return null;
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
