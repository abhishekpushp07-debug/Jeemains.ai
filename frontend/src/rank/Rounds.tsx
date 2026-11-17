// Round-wise closing ranks of one college-course: a ladder (R1 to the last round, then last year's final) and the
// branches x rounds grid of the college sheet. Shared by JEE (JoSAA / CSAB / JAC) and COMEDK.
import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";
import { Cell, fmt } from "./api";
import { SERIF, TAG } from "./tones";

const silver = colors.custom_rankSilver;
const LABEL_W = 52;

/** Every round's closing rank as a blood-red bar; the silver line and soft band are the student's rank (best to worst estimate). */
export function RoundLadder({ title, sub, rounds, cells, prev, quiet, testID }: {
  title: string; sub?: string; rounds: string[]; cells: Cell[]; prev?: { label: string; close: number | null } | null; quiet?: boolean; testID: string;
}) {
  const closes = [...cells.map(c => c.close), prev?.close].filter((c): c is number => !!c);
  const yours = quiet ? [] : cells.map(c => c.hi ?? c.mine ?? 0);
  const top = Math.max(1, ...closes, ...yours) * 1.04; // the scale always holds the student's own rank too
  const first = quiet ? null : cells.find(c => c.mine) ?? null;
  return <View testID={testID} style={styles.ladder}>
    <LinearGradient colors={[colors.custom_rankBloodSoft, colors.custom_clear]} start={{ x: 0, y: 0 }} end={{ x: 0.8, y: 0.5 }} style={StyleSheet.absoluteFill} />
    <View style={{ gap: 2 }}>
      <T w="bold" size={10.5} color={colors.custom_rankBloodInk} style={styles.caps}>ROUND-WISE CLOSING RANK</T>
      <T w="bold" size={14.5} numberOfLines={2}>{title}</T>
      {sub ? <T size={12} color={colors.muted}>{sub}</T> : null}
    </View>
    {rounds.map((rd, i) => <Rung key={rd} label={rd} cell={cells[i] ?? { close: null, in: false }} top={top} quiet={quiet} testID={`${testID}-${i}`} />)}
    {prev ? <>
      <View style={styles.divider} />
      <Rung label={prev.label} cell={{ close: prev.close, in: false, mine: first?.mine, hi: first?.hi }} top={top} past testID={`${testID}-prev`} />
    </> : null}
    {quiet ? null : <View style={styles.legend}>
      <View style={styles.legendItem}><View style={styles.legendMark} /><T size={11} color={colors.muted}>silver = aapki rank</T></View>
      <View style={styles.legendItem}><View style={styles.legendBar} /><T size={11} color={colors.muted}>laal patti = closing rank</T></View>
    </View>}
  </View>;
}

/** One line for the tapped course: the first round the student is surely in, else the first borderline round. */
export function ladderLine(name: string, rounds: string[], cells: Cell[]) {
  const sure = cells.findIndex(c => !!c.close && (c.hi != null ? c.close >= c.hi : c.in));
  const maybe = cells.findIndex(c => c.in);
  if (sure >= 0) return `${name}: aapki rank ${rounds[sure]} se andar aati hai.`;
  if (maybe >= 0) return `${name}: ${rounds[maybe]} se borderline, aapki range ke andar par pakka nahi.`;
  return `${name}: aapki rank kisi round ki closing rank tak nahi pahunchi.`;
}

function Rung({ label, cell, top, past, quiet, testID }: { label: string; cell: Cell; top: number; past?: boolean; quiet?: boolean; testID: string }) {
  const has = !!cell.close;
  const fill = has ? Math.max(0.04, cell.close! / top) : 0;
  const mark = !quiet && cell.mine ? Math.min(1, cell.mine / top) : null;
  const band = mark !== null && cell.hi && cell.hi > cell.mine! ? Math.min(1, cell.hi / top) - mark : 0;
  const state = !has || past || quiet ? null : (cell.hi != null ? cell.close! >= cell.hi : cell.in) ? "in" : cell.in ? "maybe" : "out";
  const empty = past ? "2025 mein is seat ka data nahi" : cell.unpublished ? "JAC ne ye rank publish nahi ki" : "is round mein allotment nahi";
  const said = { in: ", aapki rank andar", maybe: ", borderline", out: ", aapki rank bahar" };
  const note = !has ? <T size={11.5} color={colors.custom_dim} style={styles.italic}>{empty}</T>
    : state === "in" ? <><Glyph name="check" size={12} color={silver} stroke={2.4} /><T testID={`${testID}-in`} w="semibold" size={11.5} color={TAG.safe.ink}>aapki rank andar</T></>
    : state === "maybe" ? <T testID={`${testID}-maybe`} w="semibold" size={11.5} color={TAG.borderline.ink}>borderline · aapki range ke andar</T>
    : state === "out" ? <T size={11.5} color={colors.custom_dim}>aapki rank bahar</T> : null;
  return <View testID={testID} style={styles.rung} accessibilityLabel={`${label}: ${has ? `closing ${fmt(cell.close!)}` : empty}${state ? said[state] : ""}`}>
    <View style={styles.rungTop}>
      <T w="semibold" size={12} color={past ? colors.custom_dim : colors.muted} style={styles.label} numberOfLines={2}>{label}</T>
      <View style={styles.trackBox}>
        <View style={[styles.track, !has && styles.trackEmpty]}>
          {has ? <LinearGradient colors={past ? [colors.custom_rankTrack, colors.custom_rankSilverMuted] : [colors.custom_rankBloodSoft, colors.custom_rankBlood]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[styles.fill, { width: `${fill * 100}%` }]} /> : null}
        </View>
        {has && band > 0 ? <View style={[styles.band, { left: `${mark! * 100}%`, width: `${band * 100}%` }]} /> : null}
        {has && mark !== null ? <View testID={`${testID}-mine`} style={[styles.marker, { left: `${mark * 100}%` }]} /> : null}
      </View>
      <View style={styles.value}>
        <T testID={`${testID}-close`} color={has ? (past ? colors.custom_softText : silver) : colors.custom_dim} style={styles.serif}>{has ? fmt(cell.close!) : "—"}</T>
        {cell.open ? <T size={10.5} color={colors.custom_dim}>open {fmt(cell.open)}</T> : null}
      </View>
    </View>
    {note ? <View style={styles.note}>{note}</View> : null}
  </View>;
}

export type GridRow = { key: string | number; name: string; cells: Cell[]; prev?: number | null };
const NAME_W = 140, CELL_W = 76, ROW_H = 62;

/** Branches x rounds: green = the student's whole rank range is inside that round's closing rank, amber = only part of it. */
export function RoundTable({ rounds, rows, prevLabel, pick, onPick, prefix }: {
  rounds: string[]; rows: GridRow[]; prevLabel: string | null; pick: string | number | null; onPick: (k: string | number | null) => void; prefix: string;
}) {
  return <View style={styles.table} testID={`${prefix}-table`}>
    <View style={{ width: NAME_W }}>
      <View style={styles.head}><T w="bold" size={11} color={colors.custom_eyebrow}>BRANCH</T></View>
      {rows.map(r => <Press key={r.key} testID={`${prefix}-branch-${r.key}`} onPress={() => onPick(r.key === pick ? null : r.key)} scaleTo={0.99}
        accessibilityState={{ selected: r.key === pick }} accessibilityLabel={r.name} style={[styles.name, r.key === pick && styles.nameOn]}>
        {r.key === pick ? <View style={styles.pickBar} /> : null}
        <T w={r.key === pick ? "bold" : "medium"} size={11.5} numberOfLines={4}>{r.name}</T>
      </Press>)}
    </View>
    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
      <View>
        <View style={styles.rowFlex}>
          {rounds.map(rd => <View key={rd} style={[styles.head, styles.cellW]}><T w="bold" size={11} color={colors.custom_eyebrow}>{rd}</T></View>)}
          {prevLabel ? <View style={[styles.head, styles.cellW, styles.prev]}><T w="bold" size={11} color={colors.custom_eyebrow}>{prevLabel}</T></View> : null}
        </View>
        {rows.map(r => <View key={r.key} style={styles.rowFlex}>
          {r.cells.map((c, i) => {
            const part = c.in && c.hi != null && !!c.close && c.close < c.hi;
            return <View key={i} style={[styles.cell, c.in && (part ? styles.cellPart : styles.cellIn)]}>
              <T w={c.in ? "bold" : "regular"} size={12.5} color={c.in ? (part ? TAG.borderline.ink : TAG.safe.ink) : c.close ? colors.onSurface : colors.custom_dim}>{c.close ? fmt(c.close) : "—"}</T>
            </View>;
          })}
          {prevLabel ? <View testID={`${prefix}-y25-${r.key}`} style={[styles.cell, styles.prev]}>
            <T size={12.5} color={colors.custom_softText}>{r.prev ? fmt(r.prev) : "—"}</T>
          </View> : null}
        </View>)}
      </View>
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  ladder: { gap: space.sm, padding: space.lg, borderRadius: 18, overflow: "hidden", backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine },
  caps: { letterSpacing: 2.4 },
  rung: { gap: 4, minHeight: 44, justifyContent: "center" },
  rungTop: { flexDirection: "row", alignItems: "center", gap: space.md },
  label: { width: LABEL_W },
  trackBox: { flex: 1, height: 16, justifyContent: "center" },
  track: { height: 4, borderRadius: 2, backgroundColor: colors.custom_rankTrack, overflow: "hidden" },
  trackEmpty: { opacity: 0.4 },
  note: { marginLeft: LABEL_W + space.md, flexDirection: "row", alignItems: "center", gap: 4 },
  fill: { position: "absolute", left: 0, top: 0, bottom: 0, borderRadius: 2 },
  marker: { position: "absolute", top: 0, width: 1.5, height: 16, marginLeft: -0.75, backgroundColor: colors.custom_rankShimmer, borderRadius: 1 },
  band: { position: "absolute", top: 5, height: 6, borderRadius: 3, backgroundColor: colors.custom_rankSilverLine },
  italic: { fontStyle: "italic" },
  value: { width: 72, alignItems: "flex-end" },
  serif: { fontFamily: SERIF, fontSize: 15.5, lineHeight: 20 },
  divider: { height: 1, backgroundColor: colors.custom_cardLine, marginVertical: 2 },
  legend: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", columnGap: space.md, rowGap: 4, paddingTop: 2 },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 6 },
  legendMark: { width: 1.5, height: 12, backgroundColor: colors.custom_rankShimmer },
  legendBar: { width: 16, height: 4, borderRadius: 2, backgroundColor: colors.custom_rankBlood },
  table: { flexDirection: "row", borderWidth: 1, borderColor: colors.custom_cardLine, borderRadius: 14, overflow: "hidden" },
  rowFlex: { flexDirection: "row" },
  head: { height: 34, justifyContent: "center", paddingHorizontal: 8, backgroundColor: colors.custom_cardRaised, borderBottomWidth: 1, borderBottomColor: colors.custom_cardLine },
  cellW: { width: CELL_W },
  name: { height: ROW_H, justifyContent: "center", paddingHorizontal: 8, borderBottomWidth: 1, borderBottomColor: colors.custom_cardLine, borderRightWidth: 1, borderRightColor: colors.custom_cardLine },
  nameOn: { backgroundColor: colors.custom_rankBloodSoft },
  pickBar: { position: "absolute", left: 0, top: 8, bottom: 8, width: 2, borderRadius: 1, backgroundColor: colors.custom_rankBlood },
  cell: { width: CELL_W, height: ROW_H, justifyContent: "center", paddingHorizontal: 8, borderBottomWidth: 1, borderBottomColor: colors.custom_cardLine },
  cellIn: { backgroundColor: colors.custom_successSoft },
  cellPart: { backgroundColor: colors.custom_flameSoft },
  prev: { backgroundColor: colors.custom_cardRaised, borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
});
