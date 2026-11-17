// College detail, opened over the Rank tab: the tapped branch's closing rank in every round (R1 to the last CSAB / JAC round)
// as a ladder, then top branches x every round, seat-path switches and the official link.
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Linking, StyleSheet, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { rankColors as colors, radius, space } from "@/src/theme";
import { CollegeOut, CollegeReq, fmtRange, getCollege } from "./api";
import { KIND } from "./tones";
import { Tag, Toggle } from "./controls";
import { RoundLadder, RoundTable, ladderLine } from "./Rounds";

export function CollegeSheet({ req, onClose }: { req: CollegeReq; onClose: () => void }) {
  const [path, setPath] = useState({ quota: req.quota, gender: req.gender, seat: req.seat });
  const [all, setAll] = useState(false);
  const [pick, setPick] = useState<string | number | null>(req.prog ?? null);
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
        <T testID="rank-college-yourrank" w="bold" size={14} color={colors.custom_rankSilver}>Aapki {data.your_rank.label}: {fmtRange(data.your_rank.range)}</T>
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
      {data.line ? <T testID="rank-college-line" w="semibold" size={13.5} color={data.blocked ? colors.error : colors.custom_softText}>
        {chosen && !data.blocked ? ladderLine(chosen.branch, data.rounds, chosen.cells) : data.line}
      </T> : null}
      {chosen ? <View testID="rank-college-branch-detail">
        <RoundLadder testID="rank-college-ladder" title={`${chosen.branch}${chosen.degree ? ` (${chosen.degree})` : ""}`}
          rounds={data.rounds} cells={chosen.cells} quiet={!!data.blocked} prev={data.y25_label ? { label: data.y25_label, close: chosen.y25 } : null} />
      </View> : null}
      {data.rows.length === 0 ? <T size={13} color={colors.muted}>Is raaste par 2026 mein koi seat nahi thi.</T>
        : <RoundTable prefix="rank-college" rounds={data.rounds} prevLabel={data.y25_label} pick={pick} onPick={setPick}
          rows={data.rows.map(r => ({ key: r.prog, name: `${r.branch}${r.degree ? ` (${r.degree})` : ""}`, cells: r.cells, prev: r.y25 }))} />}
      <T size={11.5} color={colors.muted}>Kisi bhi branch par tap karo, uska har round upar dikhega. Hara khaana = aapki poori rank range andar, peela = range ka sirf kuch hissa. {data.official_csab ? "CSAB rounds mein CRL dekhi jaati hai." : "Upgrade aur Spot round ki rank JAC ne publish nahi ki."}{data.y25_label ? ` Aakhri column (${data.y25_label}) pichhle saal ki final closing rank hai.` : ""}</T>
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
  outline: { minHeight: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  link: { minHeight: 44, justifyContent: "center" },
});
