// Percentile se rank (Rank tab tile): NTA JEE Main percentile + category + PwD -> CRL, category / PwD rank, and the marks
// that percentile took on each paper type. "Colleges dekho" carries the percentile into the College predictor.
import React, { useEffect, useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { ErrorBox, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { rankColors as colors, fonts, noOutline, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import { Category, fmt, fmtRange, Handover, percentileRank, PercentileOut } from "./api";
import { CATEGORY_LABEL, LEVEL, SERIF } from "./tones";
import { Strip, Summary, Tag, Toggle } from "./controls";
import { CardActions, Eyebrow, Hairline, MetalCard, Serial, SerifBig, SilverCaps, Small } from "./MetalCard";
import { sharePercentile } from "./share";

const SAVED = "rank.pct.v1";
const CATS: Category[] = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];
type Query = { percentile: number; category: Category; pwd: boolean };

export function PercentileRank({ onColleges }: { onColleges: (h: Handover) => void }) {
  const [pct, setPct] = useState("");
  const [category, setCategory] = useState<Category>("GEN");
  const [pwd, setPwd] = useState(false);
  const [open, setOpen] = useState(true);
  const [query, setQuery] = useState<Query | null>(null);
  const [res, setRes] = useState<PercentileOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [tries, setTries] = useState(0);

  useEffect(() => {
    storage.getItem<string | null>(SAVED, null).then(raw => {
      if (!raw) return;
      try { const v = JSON.parse(raw); setPct(v.pct ?? ""); setCategory(v.category ?? "GEN"); setPwd(!!v.pwd); } catch { /* keep empty */ }
    });
  }, []);
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError(null);
    percentileRank(query).then(d => { if (live) setRes(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; setBusy(false); };
  }, [query, tries]);

  const show = () => {
    const n = Number(pct.trim());
    if (!pct.trim() || !Number.isFinite(n) || n < 0 || n > 100) { setProblem("Percentile 0 se 100 ke beech daalo (jaise 97.4567)."); return; }
    setProblem(null);
    storage.setItem(SAVED, JSON.stringify({ pct, category, pwd }));
    setQuery({ percentile: n, category, pwd }); setOpen(false);
  };
  const summary = query ? [`${query.percentile} percentile`, CATEGORY_LABEL[query.category], query.pwd ? "PwD" : null, "JEE Main 2026"].filter(Boolean).join(" · ") : "";

  return <>
    {open || !query ? <Strip title="Your NTA percentile" testID="pr-input">
      <View style={{ gap: 4 }}>
        <T w="semibold" size={12} color={colors.muted}>JEE Main percentile (scorecard se)</T>
        <TextInput testID="pr-percentile-input" value={pct} onChangeText={v => { setPct(v.replace(/[^0-9.]/g, "").slice(0, 10)); setProblem(null); }}
          keyboardType="decimal-pad" placeholder="e.g. 97.4567" placeholderTextColor={colors.custom_dim} style={styles.input} keyboardAppearance="dark"
          selectionColor={colors.custom_rankBloodInk} returnKeyType="done" maxLength={10} accessibilityLabel="JEE Main percentile" onSubmitEditing={show} />
      </View>
      <View style={styles.wrap}>
        {CATS.map(c => <Toggle key={c} testID={`pr-cat-${c}`} label={CATEGORY_LABEL[c]} on={category === c} onPress={() => setCategory(c)} />)}
        <Toggle testID="pr-pwd" label="PwD" on={pwd} onPress={() => setPwd(p => !p)} />
      </View>
      <T size={11.5} color={colors.custom_dim}>Percentile paper type par nahi badalta, isliye yahan Tough / Easy nahi chahiye.</T>
      {problem ? <T testID="pr-input-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
      <Pill testID="pr-show" size="lg" label="Rank dekho" iconRight="arrow-right" busy={busy && !res} onPress={show} bg={colors.brandPrimary} ink={colors.onBrandPrimary} />
    </Strip> : <Summary testID="pr-input-collapsed" text={summary} onEdit={() => setOpen(true)} />}
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="pr-error" />
    {res && query ? <>
      <PercentileCard data={res} typed={query.percentile} />
      <Pill testID="pr-colleges" size="lg" label="Is percentile se colleges dekho" iconRight="arrow-right" bg={colors.custom_cardRaised} ink={colors.onSurface}
        style={styles.outline} onPress={() => onColleges({ exam: "jee", percentile: query.percentile, category: query.category, pwd: query.pwd })} />
    </> : null}
  </>;
}

function PercentileCard({ data, typed }: { data: PercentileOut; typed: number }) {
  const reduced = useReducedMotion();
  const r = data.result;
  return <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} style={{ gap: space.md }}>
    <MetalCard testID="pr-card" badge="JEE MAIN 2026" foot={<>
      <View style={{ flexGrow: 1, flexShrink: 1, gap: 3 }}>
        <Eyebrow>YOUR SCORE</Eyebrow>
        <SilverCaps testID="pr-card-summary">{r.summary}</SilverCaps>
      </View>
      <Serial testID="pr-card-serial" value={fmt((r.crl[0] + r.crl[1]) / 2)} of={fmt(data.candidates)} />
    </>}>
      <View style={{ gap: 2 }}>
        <Eyebrow>EXPECTED RANK · CRL</Eyebrow>
        <SerifBig testID="pr-card-crl">{fmtRange(r.crl)}</SerifBig>
      </View>
      <Hairline testID="pr-card-percentile" label={`PERCENTILE  ${typed}`} />
      {r.cat_rank || r.pwd_rank ? <View style={styles.smalls}>
        {r.cat_rank ? <Small testID="pr-card-cat" label={r.cat_rank.label} value={fmtRange(r.cat_rank.range)} /> : null}
        {r.pwd_rank ? <Small testID="pr-card-pwd" label={r.pwd_rank.label} value={fmtRange(r.pwd_rank.range)} /> : null}
      </View> : null}
    </MetalCard>
    <Strip title="Is percentile ke liye marks" testID="pr-marks">
      <View style={styles.marks}>
        {data.marks.map(m => <View key={m.level} testID={`pr-marks-${m.level}`} style={styles.markBox}>
          <Tag label={LEVEL[m.level].label} ink={LEVEL[m.level].ink} soft={LEVEL[m.level].soft} />
          <T color={colors.custom_rankSilver} style={styles.serif}>{m.marks}</T>
          <T size={11} color={colors.muted}>/ 300</T>
        </View>)}
      </View>
      <T size={11.5} color={colors.custom_dim}>Tough shift mein kam marks par hi ye percentile aa jaata hai, Easy shift mein zyada marks lagte hain.</T>
    </Strip>
    <CardActions prefix="pr" onShare={() => sharePercentile(data)} notes={data.notes} />
  </Animated.View>;
}

const styles = StyleSheet.create({
  input: { height: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.bold, fontSize: 18, color: colors.onSurface, ...noOutline },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  outline: { borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  smalls: { flexDirection: "row", flexWrap: "wrap", gap: space.md },
  marks: { flexDirection: "row", gap: space.sm },
  markBox: { flex: 1, alignItems: "center", gap: 6, paddingVertical: space.md, borderRadius: 14, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine },
  serif: { fontFamily: SERIF, fontSize: 26, lineHeight: 32 },
});
