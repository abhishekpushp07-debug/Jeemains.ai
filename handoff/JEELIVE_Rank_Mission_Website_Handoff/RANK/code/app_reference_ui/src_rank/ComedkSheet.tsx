// COMEDK college detail over the Rank tab: the tapped course's closing rank in every round (R1 to R4) and 2025's final,
// then every GM course of the college x rounds, fee and the official link.
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Linking, StyleSheet, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { rankColors as colors, radius, space } from "@/src/theme";
import { ComedkCollegeOut, ComedkCollegeReq, fmt, fmtRange, getComedkCollege } from "./api";
import { TAG } from "./tones";
import { Tag } from "./controls";
import { RoundLadder, RoundTable, ladderLine } from "./Rounds";

export const feeLine = (fee: number | null, seats: number | null) =>
  [fee ? `₹${fmt(fee)} / saal` : null, seats ? `${seats} GM seats` : null].filter(Boolean).join(" · ");

export function ComedkSheet({ req, onClose }: { req: ComedkCollegeReq; onClose: () => void }) {
  const [all, setAll] = useState(false);
  const [pick, setPick] = useState<string | number | null>(req.course ?? null);
  const [data, setData] = useState<ComedkCollegeOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);

  useEffect(() => {
    let live = true;
    setError(null);
    getComedkCollege({ ...req, all }).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [req, all, tries]);

  const chosen = data?.rows.find(r => r.cc === pick) ?? null;
  return <DSheet visible onClose={onClose} title={data?.college.short ?? "College"} testID="comedk-college">
    {!data && !error ? <ActivityIndicator testID="comedk-college-loading" color={colors.muted} style={{ paddingVertical: space.xl }} /> : null}
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="comedk-college-error" />
    {data ? <>
      <View style={{ gap: 4 }}>
        <View style={styles.line}>
          <Tag label="COMEDK · GM" ink={colors.custom_rankBloodInk} soft={colors.custom_rankBloodSoft} />
          {data.college.city ? <T size={13} color={colors.muted}>{data.college.city}</T> : null}
        </View>
        <T w="semibold" size={14}>{data.college.name}</T>
        <T testID="comedk-college-yourrank" w="bold" size={14} color={colors.custom_rankSilver}>Aapki {data.your_rank.label}: {fmtRange(data.your_rank.range)}</T>
      </View>
      <T testID="comedk-college-line" w="semibold" size={13.5} color={colors.custom_softText}>{chosen ? ladderLine(chosen.course, data.rounds, chosen.cells) : data.line}</T>
      {chosen ? <RoundLadder testID="comedk-college-ladder" title={chosen.course} sub={[feeLine(chosen.fee, chosen.seats), chosen.tag ? TAG[chosen.tag].label : null].filter(Boolean).join(" · ")}
        rounds={data.rounds} cells={chosen.cells} prev={{ label: data.y25_label, close: chosen.y25 }} /> : null}
      <RoundTable prefix="comedk-college" rounds={data.rounds} prevLabel={data.y25_label} pick={pick} onPick={setPick}
        rows={data.rows.map(r => ({ key: r.cc, name: r.course, cells: r.cells, prev: r.y25 }))} />
      <T size={11.5} color={colors.muted}>Kisi bhi course par tap karo, uska har round upar dikhega. Hara khaana = aapki poori rank range andar, peela = range ka sirf kuch hissa. — = us round mein GM seat par allotment nahi hua. Aakhri column COMEDK 2025 ki final closing rank hai.</T>
      {!all && data.total > data.rows.length ? <Press testID="comedk-college-all" onPress={() => setAll(true)} style={styles.outline}>
        <T w="bold" size={14}>Show all courses ({data.total})</T>
      </Press> : null}
      <Press testID="comedk-college-official" onPress={() => Linking.openURL(data.official).catch(() => {})} style={styles.link}>
        <T w="bold" size={13.5} color={colors.brandText}>Official page kholo (COMEDK)</T>
      </Press>
    </> : null}
  </DSheet>;
}

const styles = StyleSheet.create({
  line: { flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" },
  outline: { minHeight: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  link: { minHeight: 44, justifyContent: "center" },
});
