import React from "react";
import Svg, { Circle, Defs, Ellipse, G, LinearGradient as Grad, Path, RadialGradient, Rect, Stop } from "react-native-svg";
import { arena, fx, gemColors } from "@/src/theme";

/** A jewelled royal crown, gold or silver, drawn so it stays sharp at any size. */
export function CrownArt({ size, gold }: { size: number; gold: boolean }) {
  const [hi, mid, low] = gold ? [fx.white, arena.gold, arena.goldDeep] : [fx.white, fx.smoke, arena.faint];
  return <Svg width={size} height={size * 0.8} viewBox="0 0 220 176">
    <Defs>
      <Grad id="metal" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={hi} /><Stop offset="0.35" stopColor={mid} /><Stop offset="1" stopColor={low} /></Grad>
      <Grad id="band" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={mid} /><Stop offset="1" stopColor={low} /></Grad>
      <RadialGradient id="ruby" cx="0.35" cy="0.35" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="0.3" stopColor={gemColors.red} /><Stop offset="1" stopColor={arena.bgDeep} /></RadialGradient>
      <RadialGradient id="sapph" cx="0.35" cy="0.35" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="0.3" stopColor={gemColors.blue} /><Stop offset="1" stopColor={fx.night} /></RadialGradient>
      <RadialGradient id="emer" cx="0.35" cy="0.35" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="0.3" stopColor={gemColors.emerald} /><Stop offset="1" stopColor={arena.tealOutline} /></RadialGradient>
      <RadialGradient id="pearl" cx="0.35" cy="0.3" r="0.7"><Stop offset="0" stopColor={fx.white} /><Stop offset="1" stopColor={low} /></RadialGradient>
    </Defs>
    {/* the five points and the body */}
    <Path d="M30 132 L14 50 L66 96 L82 40 L110 88 L138 40 L154 96 L206 50 L190 132 Z" fill="url(#metal)" stroke={arena.badgeInk} strokeWidth={4} strokeLinejoin="round" />
    <Path d="M40 124 L30 70 L68 104 L84 60 L110 100 L136 60 L152 104 L190 70 L182 124 Z" fill={hi} opacity={0.18} />
    {/* pearls on every point */}
    {[[14, 50, 10], [82, 40, 9], [110, 22, 13], [138, 40, 9], [206, 50, 10]].map(([x, y, r]) => <Circle key={x} cx={x} cy={y} r={r} fill="url(#pearl)" stroke={arena.badgeInk} strokeWidth={3} />)}
    <Path d="M110 34 L110 86" stroke={arena.badgeInk} strokeWidth={4} />
    {/* the band, studded with jewels */}
    <Rect x={24} y={128} width={172} height={36} rx={10} fill="url(#band)" stroke={arena.badgeInk} strokeWidth={4} />
    <Rect x={32} y={133} width={156} height={7} rx={3.5} fill={hi} opacity={0.45} />
    <G stroke={arena.badgeInk} strokeWidth={3}>
      <Ellipse cx={110} cy={146} rx={16} ry={12} fill="url(#ruby)" />
      <Ellipse cx={66} cy={146} rx={11} ry={9} fill="url(#sapph)" />
      <Ellipse cx={154} cy={146} rx={11} ry={9} fill="url(#sapph)" />
      <Circle cx={38} cy={146} r={6} fill="url(#emer)" />
      <Circle cx={182} cy={146} r={6} fill="url(#emer)" />
      <Ellipse cx={110} cy={108} rx={12} ry={14} fill="url(#ruby)" />
      <Circle cx={60} cy={116} r={7} fill="url(#emer)" />
      <Circle cx={160} cy={116} r={7} fill="url(#emer)" />
    </G>
  </Svg>;
}
