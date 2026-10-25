import React, { useEffect } from "react";
import { ImageBackground, View } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { Easing, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSequence, withTiming } from "react-native-reanimated";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { Avatar, EFFECTS } from "@/src/components/Entry";
import { AVATAR_IMAGES } from "@/src/avatars";
import { colors, radius, space } from "@/src/theme";

const ARENA = require("../../assets/images/arena_bg.webp");

function useBob(delay = 0) {
  const reduced = useReducedMotion();
  const y = useSharedValue(0);
  useEffect(() => {
    if (!reduced) y.value = withDelay(delay, withRepeat(withSequence(withTiming(-6, { duration: 1100, easing: Easing.inOut(Easing.sin) }), withTiming(0, { duration: 1100, easing: Easing.inOut(Easing.sin) })), -1, false));
  }, [reduced, y, delay]);
  return useAnimatedStyle(() => ({ transform: [{ translateY: y.value }] }));
}

// Opponent seat: a glowing silhouette until the match is found.
function Mystery({ size }: { size: number }) {
  const bob = useBob(550);
  return (
    <Animated.View style={[{ alignItems: "center", gap: 8 }, bob]}>
      <View style={{ width: size, height: size, borderRadius: size / 2, borderWidth: 3, borderColor: colors.custom_neonRed, backgroundColor: colors.custom_gameCardHi, overflow: "hidden", alignItems: "center", justifyContent: "center", shadowColor: colors.custom_neonRed, shadowOpacity: 0.9, shadowRadius: 16, elevation: 10 }}>
        <Image source={AVATAR_IMAGES.av_thunder} style={{ width: "100%", height: "100%", position: "absolute", opacity: 0.28 }} contentFit="cover" />
        <View style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: 0, backgroundColor: colors.custom_gameBg + "66" }} />
        <T w="heavy" size={size * 0.42} color={colors.custom_neonRed}>?</T>
      </View>
      <T w="heavy" size={14} color={colors.onSurfaceInverse}>Opponent</T>
    </Animated.View>
  );
}

// Game-lobby stage: you vs the next opponent, subject switch, chapter pill on the edge.
export function BattleHero({ me, subjects, chapterPill, record }: {
  me?: { avatar?: string | null; frame?: string | null; entry?: string | null };
  subjects: React.ReactNode; chapterPill: React.ReactNode; record?: string;
}) {
  const reduced = useReducedMotion();
  const vs = useSharedValue(1);
  const live = useSharedValue(1);
  useEffect(() => {
    if (reduced) return;
    vs.value = withRepeat(withSequence(withTiming(1.15, { duration: 520 }), withTiming(1, { duration: 520 })), -1, false);
    live.value = withRepeat(withTiming(0.25, { duration: 800 }), -1, true);
  }, [reduced, vs, live]);
  const vsS = useAnimatedStyle(() => ({ transform: [{ scale: vs.value }] }));
  const liveS = useAnimatedStyle(() => ({ opacity: live.value }));
  const bob = useBob();
  const fx = me?.entry ? EFFECTS[me.entry] : null;
  return (
    <View testID="rf-battle-hero">
      <View style={{ borderRadius: radius.lg + 8, overflow: "hidden", borderWidth: 1, borderColor: colors.custom_neonViolet + "55" }}>
        <ImageBackground source={ARENA} resizeMode="cover">
          <LinearGradient colors={[colors.custom_gameBg + "55", colors.custom_gameBg + "CC", colors.custom_gameBg + "F2"]} locations={[0, 0.55, 1]} style={{ padding: space.lg, paddingBottom: space.xl + space.md, gap: space.lg }}>
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 12, height: 28, borderRadius: 14, backgroundColor: colors.custom_gameBg + "B3", borderWidth: 1, borderColor: colors.custom_neonGreen + "66" }}>
                <Animated.View style={[{ width: 8, height: 8, borderRadius: 4, backgroundColor: colors.custom_neonGreen }, liveS]} />
                <T w="heavy" size={11} color={colors.custom_neonGreen} style={{ letterSpacing: 1.5 }}>LIVE 1v1 ARENA</T>
              </View>
              <View style={{ flex: 1 }} />
              {record ? <T w="heavy" size={11} color={colors.custom_gameMuted} testID="rf-duel-record">{record}</T> : null}
            </View>

            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-around" }}>
              <Animated.View style={[{ alignItems: "center", gap: 8 }, bob]}>
                <View style={{ borderRadius: 60, shadowColor: fx?.c1 || colors.custom_neonCyan, shadowOpacity: 0.9, shadowRadius: 16, elevation: 10 }}>
                  <Avatar icon={me?.avatar} frame={me?.frame} size={96} />
                </View>
                <T w="heavy" size={14} color={colors.onSurfaceInverse}>You</T>
              </Animated.View>
              <Animated.View style={vsS}>
                <T w="heavy" size={34} color={colors.custom_neonMagenta} style={{ textShadowColor: colors.custom_neonMagenta, textShadowRadius: 18, letterSpacing: 2 }}>VS</T>
              </Animated.View>
              <Mystery size={96} />
            </View>
            {fx ? (
              <View style={{ alignSelf: "center", flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 12, height: 26, borderRadius: 13, backgroundColor: fx.c1 + "22" }}>
                <Icon name={fx.icon as IconName} size={13} color={fx.c1} />
                <T w="bold" size={11} color={fx.c1}>Entry effect ready</T>
              </View>
            ) : null}
            {subjects}
          </LinearGradient>
        </ImageBackground>
      </View>
      {chapterPill ? <View style={{ marginTop: -24, paddingHorizontal: space.lg }}>{chapterPill}</View> : null}
    </View>
  );
}

// The anchor of the lobby: one huge tactile PLAY button with a light sweep.
export function PlayButton({ onPress, disabled, sub }: { onPress: () => void; disabled?: boolean; sub: string }) {
  const reduced = useReducedMotion();
  const sweep = useSharedValue(-1);
  useEffect(() => {
    if (!reduced) sweep.value = withRepeat(withSequence(withTiming(1.6, { duration: 1500, easing: Easing.inOut(Easing.quad) }), withTiming(1.6, { duration: 900 })), -1, false);
  }, [reduced, sweep]);
  const sweepS = useAnimatedStyle(() => ({ transform: [{ translateX: sweep.value * 220 }, { rotate: "20deg" }] }));
  return (
    <Press testID="rf-duel-random" onPress={onPress} disabled={disabled} scaleTo={0.95}
      style={{ borderRadius: radius.pill, opacity: disabled ? 0.5 : 1, shadowColor: colors.custom_neonAmber, shadowOpacity: 0.7, shadowRadius: 18, shadowOffset: { width: 0, height: 6 }, elevation: 12 }}>
      <LinearGradient colors={[colors.custom_neonAmber, colors.custom_examBitsat]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ height: 76, borderRadius: radius.pill, overflow: "hidden", alignItems: "center", justifyContent: "center", borderBottomWidth: 4, borderBottomColor: colors.custom_amber }}>
        <Animated.View pointerEvents="none" style={[{ position: "absolute", top: -20, bottom: -20, width: 40, backgroundColor: colors.onSurfaceInverse + "40" }, sweepS]} />
        <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
          <Icon name="sword-cross" size={28} color={colors.custom_gameBg} />
          <T w="heavy" size={28} color={colors.custom_gameBg} style={{ letterSpacing: 4 }}>PLAY</T>
        </View>
        <T w="bold" size={11} color={colors.custom_gameBg + "CC"}>{sub}</T>
      </LinearGradient>
    </Press>
  );
}

export function OutlineAction({ testID, icon, label, tint, onPress, disabled }: { testID: string; icon: IconName; label: string; tint: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Press testID={testID} onPress={onPress} disabled={disabled} scaleTo={0.96} style={{ flex: 1, height: 56, borderRadius: radius.lg, borderWidth: 1.5, borderColor: tint, backgroundColor: tint + "14", flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, opacity: disabled ? 0.5 : 1 }}>
      <Icon name={icon} size={20} color={tint} />
      <T w="heavy" size={14} color={colors.onSurfaceInverse} numberOfLines={1}>{label}</T>
    </Press>
  );
}
