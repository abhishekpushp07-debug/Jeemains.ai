// A dotted edge for a Shine face (Home's Misfire card, the Rank tab's details bar). The rim between the outer edge and
// the face is painted in one colour with a row of round holes along its middle, so the colours that run round behind it
// show only through the holes, like a string of lights. It is one still shape: nothing here moves.
import React, { useMemo } from "react";
import { StyleSheet } from "react-native";
import Svg, { Path } from "react-native-svg";

const PITCH = 9; // from the centre of one light to the centre of the next
const QUARTER = Math.PI / 2;
const n1 = (n: number) => +n.toFixed(1);

/** A rounded rectangle, clockwise from the start of its top side. */
const rounded = (x: number, y: number, w: number, h: number, r: number) =>
  `M${n1(x + r)} ${n1(y)}H${n1(x + w - r)}A${n1(r)} ${n1(r)} 0 0 1 ${n1(x + w)} ${n1(y + r)}V${n1(y + h - r)}A${n1(r)} ${n1(r)} 0 0 1 ${n1(x + w - r)} ${n1(y + h)}`
  + `H${n1(x + r)}A${n1(r)} ${n1(r)} 0 0 1 ${n1(x)} ${n1(y + h - r)}V${n1(y + r)}A${n1(r)} ${n1(r)} 0 0 1 ${n1(x + r)} ${n1(y)}Z`;

/** Everything from the outer edge in to the face, as one even-odd shape: the face and every light are holes in it. */
function rimPath(w: number, h: number, radius: number, ring: number) {
  const m = ring / 2, W = w - ring, H = h - ring, r = Math.max(0.1, Math.min(radius - m, W / 2, H / 2));
  const sx = W - 2 * r, sy = H - 2 * r, turn = QUARTER * r, total = 2 * (sx + sy) + 4 * turn;
  const count = Math.max(4, Math.round(total / PITCH)), step = total / count, dot = Math.max(1, m - 1);
  const on = (cx: number, cy: number, from: number, d: number) => [cx + r * Math.cos(from + d / r), cy + r * Math.sin(from + d / r)];
  // The middle line of the rim, clockwise from the start of the top side: four sides and four quarter turns.
  const legs: [number, (d: number) => number[]][] = [
    [sx, d => [m + r + d, m]], [turn, d => on(m + W - r, m + r, -QUARTER, d)],
    [sy, d => [m + W, m + r + d]], [turn, d => on(m + W - r, m + H - r, 0, d)],
    [sx, d => [m + W - r - d, m + H]], [turn, d => on(m + r, m + H - r, QUARTER, d)],
    [sy, d => [m, m + H - r - d]], [turn, d => on(m + r, m + r, 2 * QUARTER, d)],
  ];
  let holes = "", leg = 0, start = 0;
  for (let i = 0; i < count; i++) {
    const s = (i + 0.5) * step;
    while (leg < legs.length - 1 && s > start + legs[leg][0]) start += legs[leg++][0];
    const [x, y] = legs[leg][1](s - start);
    holes += `M${n1(x - dot)} ${n1(y)}a${dot} ${dot} 0 1 0 ${dot * 2} 0a${dot} ${dot} 0 1 0 ${-dot * 2} 0Z`;
  }
  // The rim reaches half a point under the face, so no line of the running colours shows between the two.
  const inset = ring - 0.5, iw = w - inset * 2, ih = h - inset * 2;
  return `M-2 -2H${n1(w + 2)}V${n1(h + 2)}H-2Z` + rounded(inset, inset, iw, ih, Math.max(0.1, Math.min(radius - inset, iw / 2, ih / 2))) + holes;
}

/** `w`, `h`, `radius`, `ring` = the Shine face's own box, corner and edge width; `color` = the rim between the lights. */
export function DotRim({ w, h, radius, ring, color }: { w: number; h: number; radius: number; ring: number; color: string }) {
  const d = useMemo(() => rimPath(w, h, radius, ring), [w, h, radius, ring]);
  return <Svg pointerEvents="none" width={w} height={h} style={StyleSheet.absoluteFill}><Path d={d} fill={color} fillRule="evenodd" /></Svg>;
}
