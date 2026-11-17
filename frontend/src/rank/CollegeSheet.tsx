// College detail, opened over the Rank tab: top branches x every round's closing rank, seat-path switches and the official link.
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Linking, ScrollView, StyleSheet, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { rankColors as colors, radius, space } from "@/src/theme";
import { CollegeOut, CollegeReq, fmt, fmtRange, getCollege } from "./api";
import { KIND, TAG } from "./tones";
import { Tag, Toggle } from "./controls";

const NAME_W = 132, CELL_W = 76, ROW_H = 54;

export function CollegeSheet({ req, onClose }: { req: CollegeReq; onClose: () => void }) {
  const [path, setPath] = useState({ quota: req.quota, gender: req.gender, seat: req.seat });
  const [all, setAll] = useState(false);
  const [pick, setPick] = useState<number | null>(req.prog ?? null);
  const [data, setData] = useState<CollegeOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);

  useEffect(() => {
    let live = true;
    setError(null);
    getCollege({ ...req, ...path, all }).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [req, path, all, tries]);

  const kind = data ? KIND[data.college.type] : null;
  const chosen = data?.rows.find(r => r.prog === pick) ?? null;
  return <DSheet visible onClose={onClose} title={data?.college.short ?? "College"} testID="rank-college">
    {!data && !error ? <ActivityIndicator testID="rank-college-loading" color={colors.muted} style={{ paddingVertical: space.xl }} /> : null}
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="rank-college-error" />
    {data && kind ? <>
      <View style={{ gap: 4 }}>
        <View style={styles.line}>
          <Tag label={kind.label} ink={kind.ink} soft={kind.soft} />
          <T size={13} color={colors.muted}>{data.college.city}, {data.college.state}</T>
        </View>
        <T w="semibold" size={14}>{data.college.name}</T>
        <T testID="rank-college-yourrank" w="bold" size={14} color={TAG.likely.ink}>Aapki {data.your_rank.label}: {fmtRange(data.your_rank.range)}</T>
      </View>
      <View style={styles.wrap}>
        {data.options.quota.map(q => <Toggle key={q.key} testID={`rank-college-quota-${q.key}`} label={q.label} on={data.path.quota === q.key} onPress={() => setPath(p => ({ ...p, quota: q.key }))} />)}
      </View>
      {data.options.gender.length > 1 || data.options.seat.length > 1 ? <View style={styles.wrap}>
        {data.options.gender.length > 1 ? data.options.gender.map(g => <Toggle key={g} testID={`rank-college-gender-${g}`} label={g === "F" ? "Female-only" : "Gender-neutral"}
          on={data.path.gender === g} onPress={() => setPath(p => ({ ...p, gender: g }))} />) : null}
        {data.options.seat.length > 1 ? data.options.seat.map(s => <Toggle key={s} testID={`rank-college-seat-${s}`} label={s === "open" ? "Open" : data.options.cat_label ?? "Category"}
          on={data.path.seat === s} onPress={() => setPath(p => ({ ...p, seat: s }))} />) : null}
      </View> : null}
      {data.line ? <T testID="rank-college-line" w="semibold" size={13.5} color={data.blocked ? colors.error : colors.custom_softText}>{data.line}</T> : null}
      {chosen ? <View testID="rank-college-branch-detail" style={styles.detail}>
        <T w="bold" size={13.5}>{chosen.branch}</T>
        {data.rounds.map((rd, i) => <View key={rd} style={styles.detailRow}>
          <T size={12.5} color={colors.muted} style={{ width: 70 }}>{rd}</T>
          <T size={12.5} style={{ flex: 1 }}>Opening {chosen.cells[i].open ? fmt(chosen.cells[i].open!) : "—"}</T>
          <T w="semibold" size={12.5}>Closing {chosen.cells[i].close ? fmt(chosen.cells[i].close!) : "—"}</T>
        </View>)}
        {data.y25_label ? <View style={styles.detailRow}>
          <T size={12.5} color={colors.muted} style={{ width: 70 }}>{data.y25_label}</T>
          <T size={12.5} style={{ flex: 1 }}>Pichhle saal ki final</T>
          <T w="semibold" size={12.5}>Closing {chosen.y25 ? fmt(chosen.y25) : "—"}</T>
        </View> : null}
      </View> : null}
      {data.rows.length === 0 ? <T size={13} color={colors.muted}>Is raaste par 2026 mein koi seat nahi thi.</T> : <View style={styles.table} testID="rank-college-table">
        <View style={{ width: NAME_W }}>
          <View style={styles.head}><T w="bold" size={11} color={colors.custom_eyebrow}>BRANCH</T></View>
          {data.rows.map(r => <Press key={r.prog} testID={`rank-college-branch-${r.prog}`} onPress={() => setPick(r.prog === pick ? null : r.prog)} scaleTo={0.99}
            accessibilityState={{ selected: r.prog === pick }} style={[styles.name, r.prog === pick && styles.nameOn]}>
            <T w={r.prog === pick ? "bold" : "medium"} size={12} numberOfLines={3}>{r.branch}{r.degree ? ` (${r.degree})` : ""}</T>
          </Press>)}
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View>
            <View style={styles.rowFlex}>
              {data.rounds.map(rd => <View key={rd} style={[styles.head, styles.cellW]}><T w="bold" size={11} color={colors.custom_eyebrow}>{rd}</T></View>)}
              {data.y25_label ? <View style={[styles.head, styles.cellW, styles.prev]}><T w="bold" size={11} color={colors.custom_eyebrow}>{data.y25_label}</T></View> : null}
            </View>
            {data.rows.map(r => <View key={r.prog} style={styles.rowFlex}>
              {r.cells.map((c, i) => <View key={i} style={[styles.cell, c.in && styles.cellIn]}>
                <T w={c.in ? "bold" : "regular"} size={12.5} color={c.in ? TAG.safe.ink : c.close ? colors.onSurface : colors.custom_dim}>{c.close ? fmt(c.close) : "—"}</T>
              </View>)}
              {data.y25_label ? <View testID={`rank-college-y25-${r.prog}`} style={[styles.cell, styles.prev]}>
                <T size={12.5} color={colors.custom_softText}>{r.y25 ? fmt(r.y25) : "—"}</T>
              </View> : null}
            </View>)}
          </View>
        </ScrollView>
      </View>}
      <T size={11.5} color={colors.muted}>Hara khaana = aapki rank us round ki closing rank ke andar. {data.official_csab ? "CSAB rounds mein CRL dekhi jaati hai." : "Upgrade aur Spot round ki rank JAC ne publish nahi ki."}{data.y25_label ? ` Aakhri column (${data.y25_label}) pichhle saal ki final closing rank hai.` : ""}</T>
      {!all && data.total > data.rows.length ? <Press testID="rank-college-all" onPress={() => setAll(true)} style={styles.outline}>
        <T w="bold" size={14}>Show all branches ({data.total})</T>
      </Press> : null}
      <Press testID="rank-college-official" onPress={() => Linking.openURL(data.official).catch(() => {})} style={styles.link}>
        <T w="bold" size={13.5} color={colors.brandText}>Official page kholo ({data.official_csab ? "JoSAA" : "JAC Delhi"})</T>
      </Press>
      {data.official_csab ? <Press testID="rank-college-official-csab" onPress={() => Linking.openURL(data.official_csab!).catch(() => {})} style={styles.link}>
        <T w="bold" size={13.5} color={colors.brandText}>CSAB Special ka official page</T>
      </Press> : null}
    </> : null}
  </DSheet>;
}

const styles = StyleSheet.create({
  line: { flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  table: { flexDirection: "row", borderWidth: 1, borderColor: colors.custom_cardLine, borderRadius: 14, overflow: "hidden" },
  rowFlex: { flexDirection: "row" },
  head: { height: 34, justifyContent: "center", paddingHorizontal: 8, backgroundColor: colors.custom_cardRaised, borderBottomWidth: 1, borderBottomColor: colors.custom_cardLine },
  cellW: { width: CELL_W },
  name: { height: ROW_H, justifyContent: "center", paddingHorizontal: 8, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine, borderRightWidth: 1, borderRightColor: colors.custom_cardLine },
  nameOn: { backgroundColor: colors.custom_webSavedSoft },
  cell: { width: CELL_W, height: ROW_H, justifyContent: "center", paddingHorizontal: 8, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  cellIn: { backgroundColor: colors.custom_successSoft },
  prev: { backgroundColor: colors.custom_cardRaised, borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
  detail: { gap: 4, padding: space.md, borderRadius: 14, backgroundColor: colors.custom_cardRaised },
  detailRow: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 24 },
  outline: { minHeight: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  link: { minHeight: 44, justifyContent: "center" },
});
