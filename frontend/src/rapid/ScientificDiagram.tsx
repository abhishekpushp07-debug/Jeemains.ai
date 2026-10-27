import React from "react";
import { StyleSheet, View } from "react-native";
import Svg, { Circle, Ellipse, Line, Path, Rect, Text as Label } from "react-native-svg";
import { rapidColors as colors } from "@/src/theme";
import { T } from "./ui";

export type ScientificDiagramSpec = { kind: "ydse" | "ellipse" | "charged_ring"; caption: string; medium?: boolean };
const ink = colors.onSurface, muted = colors.muted, teal = colors.custom_neonCyan, blue = colors.custom_subjectChemistry;
const label = { fill: ink, fontSize: 15, fontWeight: "600" as const };

function Slits({ medium }: { medium?: boolean }) {
  return <>{medium ? <Rect x={65} y={14} width={214} height={143} rx={8} fill={colors.custom_gameCardHi} /> : null}
    <Path d="M65 16V53M65 64V106M65 117V158" stroke={muted} strokeWidth={5} />
    <Line x1={278} y1={16} x2={278} y2={158} stroke={blue} strokeWidth={4} />
    <Line x1={65} y1={58} x2={278} y2={60} stroke={teal} strokeWidth={1.5} /><Line x1={65} y1={112} x2={278} y2={60} stroke={teal} strokeWidth={1.5} />
    <Line x1={65} y1={85} x2={278} y2={85} stroke={muted} strokeDasharray="4 4" />
    <Line x1={45} y1={58} x2={45} y2={112} stroke={ink} /><Line x1={41} y1={58} x2={49} y2={58} stroke={ink} /><Line x1={41} y1={112} x2={49} y2={112} stroke={ink} />
    <Label {...label} x={12} y={91}>d</Label><Label {...label} x={69} y={48}>S₁</Label><Label {...label} x={69} y={133}>S₂</Label><Label {...label} x={286} y={65}>P</Label><Label {...label} x={286} y={92}>O</Label>
    <Line x1={70} y1={151} x2={272} y2={151} stroke={muted} /><Label {...label} x={165} y={146}>D</Label>{medium ? <Label {...label} x={170} y={35}>μ</Label> : null}<Label {...label} fontSize={12} x={248} y={177}>screen</Label>
  </>;
}
function Conic() {
  return <><Line x1={22} y1={95} x2={298} y2={95} stroke={muted} /><Line x1={160} y1={12} x2={160} y2={177} stroke={muted} />
    <Ellipse cx={160} cy={95} rx={112} ry={60} fill="none" stroke={teal} strokeWidth={2.5} />
    <Line x1={160} y1={95} x2={272} y2={95} stroke={blue} strokeWidth={3} /><Line x1={160} y1={95} x2={160} y2={35} stroke={colors.custom_neonViolet} strokeWidth={3} />
    <Label {...label} x={208} y={87}>a</Label><Label {...label} x={169} y={67}>b</Label><Label {...label} x={144} y={113}>O</Label><Label {...label} x={300} y={100}>x</Label><Label {...label} x={167} y={18}>y</Label><Label {...label} fontSize={12} x={233} y={166}>a &gt; b</Label>
  </>;
}
function ChargedRing() {
  return <><Ellipse cx={105} cy={91} rx={36} ry={65} fill="none" stroke={teal} strokeWidth={3} /><Line x1={55} y1={91} x2={296} y2={91} stroke={muted} strokeDasharray="4 4" /><Circle cx={270} cy={91} r={4} fill={ink} />
    <Line x1={105} y1={91} x2={105} y2={26} stroke={blue} strokeWidth={2} /><Label {...label} x={115} y={64}>R</Label><Label {...label} x={268} y={80}>P</Label><Label {...label} x={91} y={110}>O</Label><Label {...label} x={60} y={25}>Q</Label><Line x1={105} y1={125} x2={270} y2={125} stroke={muted} /><Label {...label} x={183} y={146}>x</Label>
  </>;
}
export function ScientificDiagram({ spec, testID }: { spec: ScientificDiagramSpec; testID: string }) {
  return <View testID={testID} accessibilityRole="image" accessibilityLabel={spec.caption} style={styles.frame}><Svg width="100%" height={176} viewBox="0 0 320 185">{spec.kind === "ydse" ? <Slits medium={spec.medium} /> : spec.kind === "ellipse" ? <Conic /> : <ChargedRing />}</Svg><T testID={`${testID}-caption`} size={10} color={muted} style={styles.caption}>{spec.caption} · not to scale</T></View>;
}
const styles = StyleSheet.create({ frame: { backgroundColor: colors.surface, borderRadius: 15, borderWidth: 1, borderColor: colors.border, padding: 8 }, caption: { textAlign: "center", paddingBottom: 3 } });