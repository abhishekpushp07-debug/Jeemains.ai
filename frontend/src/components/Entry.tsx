import React, { useEffect } from "react";
import { View } from "react-native";
import Animated, { Easing, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSequence, withSpring, withTiming } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, T } from "@/src/components/ui";
import { colors } from "@/src/theme";

export const FRAME_COLORS: Record<string, [string, string]> = {
  frame_gold: [colors.custom_neonAmber, colors.custom_amber],
  frame_neon: [colors.custom_neonCyan, colors.brandPrimary],
  frame_fire: [colors.custom_examBitsat, colors.custom_examJee],
  frame_diamond: [colors.custom_neonCyan, colors.custom_neonAmber],
};

// Avatar with an optional purchased frame (animated pulse for neon/diamond frames).
export function Avatar({ icon, frame, size = 56, testID }: { icon?: string | null; frame?: string | null; size?: number; testID?: string }) {
  const reduced = useReducedMotion();
  const pulse = useSharedValue(1);
  useEffect(() => {
    if (!reduced && (frame === "frame_neon" || frame === "frame_diamond" || frame === "frame_fire")) pulse.value = withRepeat(withTiming(1.08, { duration: 900 }), -1, true);
  }, [frame, reduced, pulse]);
  const a = useAnimatedStyle(() => ({ transform: [{ scale: pulse.value }] }));
  const ring = frame ? FRAME_COLORS[frame] : [colors.custom_gameLine, colors.custom_gameLine];
  return (
    <Animated.View testID={testID} style={[{ width: size, height: size }, a]}>
      <LinearGradient colors={ring as [string, string]} style={{ flex: 1, borderRadius: size / 2, padding: frame ? 3 : 2 }}>
        <View style={{ flex: 1, borderRadius: size / 2, backgroundColor: colors.custom_gameCardHi, alignItems: "center", justifyContent: "center" }}>
          <Icon name={(icon || "robot-happy") as any} size={size * 0.55} color={colors.onSurfaceInverse} />
        </View>
      </LinearGradient>
      {frame === "frame_diamond" ? <View style={{ position: "absolute", top: -8, alignSelf: "center" }}><Icon name="crown" size={size * 0.34} color={colors.custom_neonAmber} /></View> : null}
    </Animated.View>
  );
}

const ENTRY_ICON: Record<string, string> = { entry_rocket: "rocket-launch", entry_lightning: "lightning-bolt", entry_supercar: "car-sports", entry_crown: "crown" };

// Animated entry effect played once when a player enters the duel (or as a shop preview).
export function EntryEffect({ effect, fromRight = false, children, play = 0 }: { effect?: string | null; fromRight?: boolean; children: React.ReactNode; play?: number }) {
  const reduced = useReducedMotion();
  const x = useSharedValue(reduced ? 0 : fromRight ? 260 : -260);
  const y = useSharedValue(reduced ? 0 : effect === "entry_crown" ? -160 : 0);
  const s = useSharedValue(reduced ? 1 : 0.4);
  const fx = useSharedValue(0);
  useEffect(() => {
    if (reduced) return;
    x.value = fromRight ? 260 : -260;
    y.value = effect === "entry_crown" ? -160 : effect === "entry_rocket" ? 120 : 0;
    s.value = 0.4;
    fx.value = 0;
    const ease = Easing.out(Easing.back(1.4));
    x.value = withTiming(0, { duration: effect === "entry_supercar" ? 520 : 700, easing: ease });
    y.value = withTiming(0, { duration: 700, easing: ease });
    s.value = withDelay(200, withSpring(1, { damping: 9 }));
    fx.value = effect ? withSequence(withTiming(1, { duration: 450 }), withDelay(500, withTiming(0, { duration: 500 }))) : 0;
  }, [effect, fromRight, reduced, play]); // eslint-disable-line react-hooks/exhaustive-deps
  const body = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }, { translateY: y.value }, { scale: s.value }] }));
  const glow = useAnimatedStyle(() => ({ opacity: fx.value, transform: [{ scale: 0.6 + fx.value * 0.8 }] }));
  const tint = effect === "entry_lightning" ? colors.custom_neonCyan : effect === "entry_supercar" ? colors.custom_examBitsat : effect === "entry_crown" ? colors.custom_neonAmber : colors.custom_neonRed;
  return (
    <View style={{ alignItems: "center", justifyContent: "center" }}>
      {effect ? (
        <Animated.View pointerEvents="none" style={[{ position: "absolute", width: 130, height: 130, borderRadius: 65, alignItems: "center", justifyContent: "center", backgroundColor: tint + "33" }, glow]}>
          <Icon name={ENTRY_ICON[effect] as any} size={64} color={tint} />
          {effect === "entry_supercar" || effect === "entry_rocket" ? (
            <View style={{ position: "absolute", [fromRight ? "right" : "left"]: -30, gap: 6 }}>
              {[40, 60, 30].map((w, i) => <View key={i} style={{ width: w, height: 3, borderRadius: 2, backgroundColor: tint }} />)}
            </View>
          ) : null}
        </Animated.View>
      ) : null}
      <Animated.View style={body}>{children}</Animated.View>
    </View>
  );
}

export function RivalTag() {
  return (
    <View testID="duel-ai-rival-tag" style={{ flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: 6, height: 20, borderRadius: 10, backgroundColor: colors.custom_neonCyan }}>
      <Icon name="robot" size={11} color={colors.custom_gameBg} />
      <T w="heavy" size={11} color={colors.custom_gameBg}>AI RIVAL</T>
    </View>
  );
}
