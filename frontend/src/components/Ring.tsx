import React from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";
import { T } from "@/src/components/ui";
import { colors } from "@/src/theme";

const LIMIT = 20000;

export function Ring({ left, color }: { left: number; color: string }) {
  const r = 22, c = 2 * Math.PI * r, frac = Math.max(0, left / LIMIT);
  const urgent = left < 5000;
  return (
    <View testID="rf-timer" accessibilityLabel={`${Math.ceil(left / 1000)} seconds left`} style={{ width: 56, height: 56, alignItems: "center", justifyContent: "center" }}>
      <Svg width={56} height={56} style={{ position: "absolute", transform: [{ rotate: "-90deg" }] }}>
        <Circle cx={28} cy={28} r={r} stroke={colors.border} strokeWidth={5} fill="none" />
        <Circle cx={28} cy={28} r={r} stroke={urgent ? colors.error : color} strokeWidth={5} fill="none" strokeDasharray={`${c}`} strokeDashoffset={c * (1 - frac)} strokeLinecap="round" />
      </Svg>
      <T w="heavy" size={16} color={urgent ? colors.error : colors.onSurface}>{Math.ceil(left / 1000)}</T>
    </View>
  );
}

