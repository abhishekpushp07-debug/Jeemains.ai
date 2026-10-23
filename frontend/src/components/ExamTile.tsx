import React from "react";
import { Platform, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Circle, Defs, G, Line, LinearGradient as SvgLinear, Path, Polygon, RadialGradient, Rect, Stop } from "react-native-svg";
import { Card, Icon, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

// Illustration palette: fixed artwork colours that must stay identical in light and dark.
const ART = {
  white: "#FFFFFF",
  ice: "#DFF1FF",
  sky: "#8CCBFF",
  blue: "#2F7BFF",
  navy: "#123A9C",
  gold: "#FFD966",
  goldMid: "#F2B632",
  goldDeep: "#A86C08",
  ruby: "#E0314B",
  sapphire: "#3B82F6",
  flameY: "#FFE066",
  flameO: "#FF8A1F",
  steel: "#C9D3E0",
  red: "#FF5A6E",
  redDeep: "#9E0B22",
};

export type TileKind = "jee" | "live" | "bitsat" | "comedk";

function TargetArt() {
  return (
    <Svg width={50} height={50} viewBox="0 0 48 48">
      <Defs>
        <RadialGradient id="tCore" cx="40%" cy="35%" r="65%">
          <Stop offset="0" stopColor={ART.white} />
          <Stop offset="0.35" stopColor={ART.red} />
          <Stop offset="1" stopColor={ART.redDeep} />
        </RadialGradient>
      </Defs>
      <Circle cx={24} cy={24} r={21} stroke={ART.white} strokeOpacity={0.45} strokeWidth={1} strokeDasharray="2 3" fill="none" />
      <Circle cx={24} cy={24} r={16} stroke={ART.white} strokeOpacity={0.85} strokeWidth={1.6} fill="none" />
      <Circle cx={24} cy={24} r={11} stroke={ART.white} strokeOpacity={0.6} strokeWidth={1.2} fill="none" />
      <Line x1={24} y1={1} x2={24} y2={9} stroke={ART.white} strokeWidth={1.4} strokeOpacity={0.9} />
      <Line x1={24} y1={39} x2={24} y2={47} stroke={ART.white} strokeWidth={1.4} strokeOpacity={0.9} />
      <Line x1={1} y1={24} x2={9} y2={24} stroke={ART.white} strokeWidth={1.4} strokeOpacity={0.9} />
      <Line x1={39} y1={24} x2={47} y2={24} stroke={ART.white} strokeWidth={1.4} strokeOpacity={0.9} />
      <Circle cx={24} cy={24} r={7} fill="url(#tCore)" />
      <Circle cx={21.8} cy={21.6} r={2.2} fill={ART.white} fillOpacity={0.9} />
      {[[24, 8], [40, 24], [24, 40], [8, 24]].map(([x, y]) => <Circle key={`${x}${y}`} cx={x} cy={y} r={1.6} fill={ART.white} />)}
    </Svg>
  );
}

function DiamondArt() {
  return (
    <Svg width={50} height={50} viewBox="0 0 48 48">
      <Defs>
        <SvgLinear id="dTop" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor={ART.white} />
          <Stop offset="1" stopColor={ART.sky} />
        </SvgLinear>
        <SvgLinear id="dBot" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={ART.sky} />
          <Stop offset="1" stopColor={ART.blue} />
        </SvgLinear>
      </Defs>
      <Polygon points="9,17 16,8 32,8 39,17" fill="url(#dTop)" />
      <Polygon points="9,17 24,42 39,17" fill="url(#dBot)" />
      <Polygon points="16,8 20,17 24,8" fill={ART.white} fillOpacity={0.85} />
      <Polygon points="24,8 28,17 32,8" fill={ART.ice} />
      <Polygon points="20,17 24,42 28,17" fill={ART.sky} fillOpacity={0.75} />
      <Path d="M9 17 H39 M20 17 L24 42 L28 17 M16 8 L20 17 L24 8 L28 17 L32 8" stroke={ART.white} strokeOpacity={0.85} strokeWidth={0.9} fill="none" />
      <Polygon points="9,17 24,42 14,17" fill={ART.navy} fillOpacity={0.25} />
      <Circle cx={15} cy={11} r={1.3} fill={ART.white} />
    </Svg>
  );
}

function RocketArt() {
  return (
    <Svg width={58} height={58} viewBox="0 0 48 48">
      <Defs>
        <SvgLinear id="rBody" x1="0" y1="0" x2="1" y2="0">
          <Stop offset="0" stopColor={ART.white} />
          <Stop offset="1" stopColor={ART.steel} />
        </SvgLinear>
        <SvgLinear id="rFlame" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={ART.flameY} />
          <Stop offset="1" stopColor={ART.flameO} stopOpacity={0} />
        </SvgLinear>
      </Defs>
      <G transform="rotate(40 24 24)">
        <Path d="M20 34 Q24 48 28 34 Z" fill="url(#rFlame)" />
        <Path d="M18 26 L12 34 L18 33 Z" fill={ART.flameO} />
        <Path d="M30 26 L36 34 L30 33 Z" fill={ART.flameO} />
        <Path d="M24 3 C31 9 32 22 30 33 H18 C16 22 17 9 24 3 Z" fill="url(#rBody)" />
        <Path d="M24 3 C27.5 6 29.2 9.5 30 13 H18 C18.8 9.5 20.5 6 24 3 Z" fill={ART.flameO} />
        <Circle cx={24} cy={19} r={4} fill={ART.sapphire} stroke={ART.white} strokeWidth={1.6} />
        <Circle cx={22.8} cy={17.8} r={1.2} fill={ART.white} fillOpacity={0.9} />
        <Rect x={22} y={33} width={4} height={3} rx={1} fill={ART.steel} />
      </G>
      <Path d="M8 10 l1.2 2.6 2.6 1.2 -2.6 1.2 -1.2 2.6 -1.2 -2.6 -2.6 -1.2 2.6 -1.2z" fill={ART.white} />
      <Path d="M40 34 l0.9 1.9 1.9 0.9 -1.9 0.9 -0.9 1.9 -0.9 -1.9 -1.9 -0.9 1.9 -0.9z" fill={ART.white} />
    </Svg>
  );
}

function CrownArt() {
  return (
    <Svg width={52} height={52} viewBox="0 0 48 48">
      <Defs>
        <SvgLinear id="cGold" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={ART.gold} />
          <Stop offset="0.55" stopColor={ART.goldMid} />
          <Stop offset="1" stopColor={ART.goldDeep} />
        </SvgLinear>
      </Defs>
      <Path d="M6 16 L15 25 L24 9 L33 25 L42 16 L38 36 H10 Z" fill="url(#cGold)" stroke={ART.goldDeep} strokeWidth={0.8} />
      <Rect x={9} y={35} width={30} height={6} rx={2} fill="url(#cGold)" stroke={ART.goldDeep} strokeWidth={0.8} />
      <Path d="M12 30 H36" stroke={ART.white} strokeOpacity={0.45} strokeWidth={1} />
      <Circle cx={24} cy={9} r={2.6} fill={ART.gold} stroke={ART.goldDeep} strokeWidth={0.6} />
      <Circle cx={6} cy={16} r={2.2} fill={ART.gold} stroke={ART.goldDeep} strokeWidth={0.6} />
      <Circle cx={42} cy={16} r={2.2} fill={ART.gold} stroke={ART.goldDeep} strokeWidth={0.6} />
      <Circle cx={24} cy={28} r={3} fill={ART.ruby} stroke={ART.white} strokeOpacity={0.6} strokeWidth={0.8} />
      <Circle cx={16} cy={31} r={2} fill={ART.sapphire} />
      <Circle cx={32} cy={31} r={2} fill={ART.sapphire} />
      <Path d="M15 25 L19 18" stroke={ART.white} strokeOpacity={0.6} strokeWidth={1.2} strokeLinecap="round" />
    </Svg>
  );
}

const ICON: Record<TileKind, () => React.ReactElement> = { jee: TargetArt, live: DiamondArt, bitsat: RocketArt, comedk: CrownArt };

// Background texture: soft blurred orbs, dot grid and thin tech lines.
function Pattern({ kind }: { kind: TileKind }) {
  const accent = kind === "comedk" ? ART.gold : ART.white;
  return (
    <Svg width="100%" height="100%" viewBox="0 0 200 140" preserveAspectRatio="xMidYMid slice" style={{ position: "absolute" }}>
      <Defs>
        <RadialGradient id={`orb-${kind}`} cx="50%" cy="50%" r="50%">
          <Stop offset="0" stopColor={ART.white} stopOpacity={0.32} />
          <Stop offset="1" stopColor={ART.white} stopOpacity={0} />
        </RadialGradient>
        <RadialGradient id={`glow-${kind}`} cx="50%" cy="50%" r="50%">
          <Stop offset="0" stopColor={kind === "comedk" ? ART.gold : ART.white} stopOpacity={kind === "comedk" ? 0.3 : 0.4} />
          <Stop offset="1" stopColor={ART.white} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Circle cx={185} cy={10} r={55} fill={`url(#orb-${kind})`} />
      <Circle cx={10} cy={135} r={48} fill={`url(#orb-${kind})`} />
      <Circle cx={100} cy={68} r={58} fill={`url(#glow-${kind})`} />
      <Circle cx={22} cy={22} r={4} fill={ART.white} fillOpacity={0.35} />
      <Circle cx={172} cy={98} r={3} fill={ART.white} fillOpacity={0.4} />
      {[0, 1, 2].map((c) => [0, 1].map((r) => <Circle key={`d${c}${r}`} cx={14 + c * 6} cy={112 + r * 6} r={1.2} fill={accent} fillOpacity={0.55} />))}
      {[0, 1, 2, 3, 4, 5].map((c) => <Circle key={`l${c}`} cx={150 + c * 6} cy={124} r={0.9} fill={accent} fillOpacity={0.6} />)}
      <Path d="M8 96 H34 L42 88 H58" stroke={ART.white} strokeOpacity={0.28} strokeWidth={1} fill="none" />
      <Circle cx={58} cy={88} r={1.8} fill={ART.white} fillOpacity={0.5} />
      <Path d="M192 74 H168 L160 66 H146" stroke={ART.white} strokeOpacity={0.22} strokeWidth={1} fill="none" />
      <Circle cx={146} cy={66} r={1.6} fill={ART.white} fillOpacity={0.45} />
      {kind === "comedk" ? (
        <>
          <Path d="M28 28 l1.5 3.4 3.4 1.5 -3.4 1.5 -1.5 3.4 -1.5 -3.4 -3.4 -1.5 3.4 -1.5z" fill={ART.gold} fillOpacity={0.85} />
          <Path d="M174 50 l1.1 2.5 2.5 1.1 -2.5 1.1 -1.1 2.5 -1.1 -2.5 -2.5 -1.1 2.5 -1.1z" fill={ART.gold} fillOpacity={0.75} />
        </>
      ) : null}
    </Svg>
  );
}

export function ExamTile({ kind, title, sub, grad, badge, onPress, testID }: { kind: TileKind; title: string; sub: string; grad: [string, string]; badge?: string; onPress: () => void; testID: string }) {
  const Art = ICON[kind];
  return (
    <Press testID={testID} onPress={onPress} accessibilityLabel={`${title}. ${sub}`} scaleTo={0.95}
      style={{ borderRadius: 24, backgroundColor: colors.surfaceSecondary, shadowColor: grad[1], shadowOpacity: 0.22, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 6 }}>
      <Card style={{ padding: 0, overflow: "hidden", borderRadius: 24, borderWidth: 0 }}>
        <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ height: 136, alignItems: "center", justifyContent: "center" }}>
          <Pattern kind={kind} />
          {/* Glassmorphism icon tile with soft glow */}
          <View style={{ borderRadius: 22, shadowColor: kind === "comedk" ? ART.gold : ART.white, shadowOpacity: Platform.OS === "web" ? 0 : 0.5, shadowRadius: 16, shadowOffset: { width: 0, height: 0 } }}>
            <LinearGradient colors={[colors.custom_whiteA70, colors.custom_whiteA15]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={{ width: 76, height: 76, borderRadius: 22, padding: 1.2 }}>
              <LinearGradient colors={kind === "comedk" ? [colors.custom_darkCard, colors.custom_examComedk] : [colors.custom_whiteA15, grad[1]]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                style={{ flex: 1, borderRadius: 21, alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
                <View style={{ position: "absolute", top: 0, left: 0, right: 0, height: "48%", backgroundColor: colors.custom_whiteA15, borderBottomLeftRadius: 40, borderBottomRightRadius: 40 }} />
                <Art />
              </LinearGradient>
            </LinearGradient>
          </View>
          {badge ? (
            <View testID={testID + "-badge"} style={{ position: "absolute", top: 10, right: 10, flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: 8, height: 22, borderRadius: radius.pill, backgroundColor: kind === "jee" ? colors.custom_burgundy : colors.custom_seriesBright, borderWidth: 1, borderColor: colors.custom_whiteA70 }}>
              <T w="heavy" size={10} color={colors.onBrandPrimary} style={{ letterSpacing: 0.4 }}>{badge}</T>
              <Icon name="star-four-points" size={9} color={colors.onBrandPrimary} />
            </View>
          ) : null}
        </LinearGradient>
        <View style={{ paddingHorizontal: space.lg, paddingVertical: space.md, gap: 2 }}>
          <T w="heavy" size={16} numberOfLines={1}>{title}</T>
          <T size={12} color={colors.muted} numberOfLines={1}>{sub}</T>
        </View>
      </Card>
    </Press>
  );
}
