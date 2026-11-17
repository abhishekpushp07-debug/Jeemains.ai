// Shared pieces of the Mission share card. The card is 4:5 and drawn in units of its own width (u = width / 320),
// so it looks the same on every phone and in the shared picture.
import React, { useId } from "react";
import { StyleSheet, useWindowDimensions } from "react-native";
import Svg, { Defs, RadialGradient, Rect, Stop } from "react-native-svg";
import { T } from "@/src/components/ui";

export const useCardWidth = () => Math.min(340, useWindowDimensions().width - 32);

/** Card text never grows with the phone's font setting, so the fixed 4:5 layout (and the shared picture) never overflows. */
export const CT = (p: React.ComponentProps<typeof T>) => <T allowFontScaling={false} {...p} />;

const useUid = () => useId().replace(/[^a-zA-Z0-9]/g, "");

/** A soft round light. cx / cy / r are percentages of the card. Explicit stopOpacity: native SVG ignores alpha in stopColor. */
export function Glow({ color, cx, cy, r, opacity }: { color: string; cx: string; cy: string; r: string; opacity: number }) {
  const id = "mg" + useUid();
  return <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" pointerEvents="none">
    <Defs>
      <RadialGradient id={id} cx={cx} cy={cy} r={r}>
        <Stop offset="0" stopColor={color} stopOpacity={opacity} />
        <Stop offset="1" stopColor={color} stopOpacity={0} />
      </RadialGradient>
    </Defs>
    <Rect x="0" y="0" width="100%" height="100%" fill={`url(#${id})`} />
  </Svg>;
}
