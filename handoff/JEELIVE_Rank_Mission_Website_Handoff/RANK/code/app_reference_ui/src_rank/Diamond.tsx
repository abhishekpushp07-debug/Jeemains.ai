// A brilliant-cut diamond in side view (crown, girdle, pavilion) drawn as faceted SVG: silver-white facets with a few
// catching the card's own colour, and optional sparkles at the tips. DiamondLine is the same stone seen from above,
// drawn in hairlines only, for the quiet watermark on the Rank Card. No image, so it costs nothing in app size.
import React from "react";
import { StyleProp, View, ViewStyle } from "react-native";
import Svg, { Circle, Path, Polygon } from "react-native-svg";
import { rankColors as colors } from "@/src/theme";

// viewBox 0 0 100 80: table y=8 (x 30–70), girdle y=30 (x 2–98), culet (50, 78). t = facet takes the card's tint.
const FACETS: { p: string; o: number; t?: boolean }[] = [
  { p: "2,30 30,8 18,30", o: 0.5 }, { p: "30,8 34,30 18,30", o: 0.9 }, { p: "30,8 43.3,8 34,30", o: 0.35, t: true },
  { p: "43.3,8 50,30 34,30", o: 0.75 }, { p: "43.3,8 56.7,8 50,30", o: 0.95 }, { p: "56.7,8 66,30 50,30", o: 0.4, t: true },
  { p: "56.7,8 70,8 66,30", o: 0.8 }, { p: "70,8 82,30 66,30", o: 0.3 }, { p: "70,8 98,30 82,30", o: 0.6, t: true },
  { p: "2,30 18,30 50,78", o: 0.3 }, { p: "18,30 34,30 50,78", o: 0.7, t: true }, { p: "34,30 50,30 50,78", o: 0.95 },
  { p: "50,30 66,30 50,78", o: 0.5 }, { p: "66,30 82,30 50,78", o: 0.85, t: true }, { p: "82,30 98,30 50,78", o: 0.4 },
];
const star = (x: number, y: number, r: number) => `M${x} ${y - r}Q${x} ${y} ${x + r} ${y}Q${x} ${y} ${x} ${y + r}Q${x} ${y} ${x - r} ${y}Q${x} ${y} ${x} ${y - r}Z`;

export function Diamond({ width, tint, sparkle, opacity = 1, style }: { width: number; tint: string; sparkle?: boolean; opacity?: number; style?: StyleProp<ViewStyle> }) {
  const white = colors.custom_rankSparkle;
  return <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={[{ width, height: width * 0.8, opacity }, style]}>
    <Svg width={width} height={width * 0.8} viewBox="-8 -8 116 96">
      {FACETS.map(f => <Polygon key={f.p} points={f.p} fill={f.t ? tint : white} fillOpacity={f.o} stroke={white} strokeOpacity={0.75} strokeWidth={0.7} strokeLinejoin="round" />)}
      {sparkle ? <>
        <Path d={star(2, 30, 10)} fill={white} />
        <Path d={star(86, 11, 6)} fill={white} />
      </> : null}
    </Svg>
  </View>;
}

// Top view in a 200 × 200 box: octagon table, the 8-point star around it, bezel and upper-girdle lines, the round girdle.
const at = (r: number, deg: number) => {
  const a = ((deg - 90) * Math.PI) / 180;
  return `${(100 + r * Math.cos(a)).toFixed(1)},${(100 + r * Math.sin(a)).toFixed(1)}`;
};
const TABLE = Array.from({ length: 8 }, (_, k) => at(46, 22.5 + 45 * k)).join(" ");
const STAR = Array.from({ length: 16 }, (_, k) => at(k % 2 ? 46 : 72, 22.5 * k)).join(" ");
const RAYS = [
  ...Array.from({ length: 8 }, (_, k) => `M${at(46, 22.5 + 45 * k)}L${at(96, 22.5 + 45 * k)}`),
  ...Array.from({ length: 8 }, (_, k) => `M${at(72, 45 * k)}L${at(96, 45 * k - 14)}M${at(72, 45 * k)}L${at(96, 45 * k + 14)}`),
].join("");

/** Hairline brilliant seen from above (the watermark of a black metal card). `size` is its width and height. */
export function DiamondLine({ size, style }: { size: number; style?: StyleProp<ViewStyle> }) {
  const line = { fill: "none", stroke: colors.custom_rankSparkle, strokeOpacity: 0.09, strokeWidth: 0.8 } as const;
  return <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 200 200">
      <Circle cx={100} cy={100} r={96} {...line} />
      <Polygon points={STAR} {...line} />
      <Polygon points={TABLE} {...line} />
      <Path d={RAYS} {...line} />
    </Svg>
  </View>;
}

/** Small hairline diamond in side view, like the mark in the corner of a metal card. */
export function DiamondMark({ width }: { width: number }) {
  const line = { fill: "none", stroke: colors.custom_rankSilver, strokeOpacity: 0.85, strokeWidth: 4, strokeLinejoin: "round" } as const;
  return <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={{ width, height: width * 0.8 }}>
    <Svg width={width} height={width * 0.8} viewBox="-6 -6 112 92">
      <Polygon points="30,8 70,8 98,30 50,78 2,30" {...line} />
      <Path d="M2 30H98M30 8L18 30L50 78L34 30L43.3 8M70 8L82 30L50 78L66 30L56.7 8M34 30L50 8L66 30" {...line} />
    </Svg>
  </View>;
}
