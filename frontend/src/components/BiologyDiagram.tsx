import React from "react";
import { StyleSheet, View } from "react-native";
import Svg, { Circle, Ellipse, G, Line, Path, Text as SvgText } from "react-native-svg";
import { T } from "./ui";
import { colors, radius, space } from "@/src/theme";

type Shape = { type: string; d?: string; cx?: number; cy?: number; rx?: number; ry?: number; fill?: string; stroke?: string; strokeWidth?: number };
export type Diagram = { kind: string; target: string; title: string; note: string; shapes: Shape[]; labels: { letter: string; x: number; y: number; toX: number; toY: number }[] };
const ink = (token?: string) => token ? colors[token as keyof typeof colors] || colors.onSurface : "none";

// Native vector drawing, not a downloaded image: readable offline and portable with the card JSON.
export function BiologyDiagram({ diagram, testID = "biology-diagram" }: { diagram?: Diagram | null; testID?: string }) {
  if (!diagram) return null;
  return <View testID={testID} style={styles.panel} accessibilityLabel={`${diagram.title}. Identify highlighted label ${diagram.target}. ${diagram.note}`}>
    <View style={styles.heading}>
      <T testID={`${testID}-title`} size={10} w="bold" color={colors.muted} style={styles.title}>{diagram.title}</T>
      <T testID={`${testID}-target`} size={11} w="heavy" color={colors.custom_neonAmber}>LABEL {diagram.target}</T>
    </View>
    <Svg testID={`${testID}-drawing`} width="100%" height={166} viewBox="0 0 320 194">
      {diagram.shapes.map((shape, i) => {
        const props = { fill: ink(shape.fill), stroke: ink(shape.stroke), strokeWidth: shape.strokeWidth || 0, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
        return shape.type === "ellipse" ? <Ellipse key={i} {...props} cx={shape.cx} cy={shape.cy} rx={shape.rx} ry={shape.ry} /> : <Path key={i} {...props} d={shape.d} />;
      })}
      {diagram.labels.map((label) => {
        const active = label.letter === diagram.target;
        const color = active ? colors.custom_neonAmber : colors.muted;
        return <G key={label.letter}>
          <Line x1={label.x} y1={label.y} x2={label.toX} y2={label.toY} stroke={color} strokeWidth={active ? 2 : 1} />
          <Circle cx={label.toX} cy={label.toY} r={active ? 3 : 2} fill={color} />
          <Circle cx={label.x} cy={label.y} r={10} fill={active ? colors.custom_neonAmber : colors.surfaceSecondary} stroke={color} />
          <SvgText testID={`${testID}-label-${label.letter.toLowerCase()}`} x={label.x} y={label.y + 4} textAnchor="middle" fontSize={12} fontWeight="bold" fill={active ? colors.custom_gameBg : colors.onSurface}>{label.letter}</SvgText>
        </G>;
      })}
    </Svg>
    <T testID={`${testID}-note`} size={10} color={colors.muted}>{diagram.note}</T>
  </View>;
}

const styles = StyleSheet.create({
  panel: { backgroundColor: colors.surface, borderRadius: radius.md, padding: space.sm, borderWidth: 1, borderColor: colors.border, gap: 2 },
  heading: { flexDirection: "row", alignItems: "center", gap: space.sm },
  title: { flex: 1 },
});