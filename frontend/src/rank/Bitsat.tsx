// BITSAT on the Rank tab: score in, BITSAT Rank Card out, then every BITS program with its 2026 cutoff and 5-year trend.
import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, TextInput, View } from "react-native";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { rankColors as colors, fonts, noOutline, radius, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import { bitsat, BitsatItem, BitsatOut, Campus, Degree } from "./api";
import { CAMPUS, TAG } from "./tones";
import { StarButton, Strip, Summary, Tag, Toggle } from "./controls";
import { BlueRule, CardActions, Eyebrow, MetalCard, Serial, SerifBig, SilverCaps } from "./MetalCard";
import { shareBitsat } from "./share";
import { bitsatSaved, toggleSaved, useShortlist } from "./shortlist";

const SAVED = "rank.bitsat.v1";
const CAMPUSES: Campus[] = ["all", "Pilani", "Goa", "Hyderabad"];
const DEGREES: { key: Degree; label: string }[] = [{ key: "all", label: "All degrees" }, { key: "BE", label: "B.E." }, { key: "MSc", label: "M.Sc." }, { key: "BPharm", label: "B.Pharm" }];

export function BitsatPanel({ onShortlist }: { onShortlist: () => void }) {
  const [text, setText] = useState("");
  const [score, setScore] = useState<number | null>(null);
  const [open, setOpen] = useState(true);
  const [campus, setCampus] = useState<Campus>("all");
  const [degree, setDegree] = useState<Degree>("all");
  const [res, setRes] = useState<BitsatOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const saved = useShortlist();

  useEffect(() => { storage.getItem<string | null>(SAVED, null).then(v => { if (v) setText(v); }); }, []);
  useEffect(() => {
    if (score === null) return;
    let live = true;
    setBusy(true); setError(null);
    bitsat({ score, campus, degree }).then(d => { if (live) setRes(d); }).catch(e => { if (live) setError(e.message); })
      .finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [score, campus, degree, tries]);

  const show = () => {
    const v = text.trim(), n = Number(v);
    if (!v || !Number.isInteger(n) || n < -130 || n > 390) { setProblem("BITSAT score −130 se 390 ke beech poore ank mein daalo."); return; }
    setProblem(null); storage.setItem(SAVED, v); setScore(n); setOpen(false);
  };

  return <>
    {open || score === null ? <Strip title="Your BITSAT score" testID="bitsat-input">
      <View style={{ gap: 4 }}>
        <T w="semibold" size={12} color={colors.muted}>Score (out of 390)</T>
        <TextInput testID="bitsat-score-input" value={text} onChangeText={v => setText(v.replace(/[^0-9-]/g, "").slice(0, 4))} keyboardType="numbers-and-punctuation"
          placeholder="e.g. 280" placeholderTextColor={colors.custom_dim} style={styles.input} keyboardAppearance="dark" selectionColor={colors.custom_rankBlue} returnKeyType="done" onSubmitEditing={show} maxLength={4} accessibilityLabel="BITSAT score out of 390" />
      </View>
      <T size={12} color={colors.muted}>BITSAT 2026: 130 sawaal, +3 / −1. Cutoff BITS ki official 2022–2026 list se.</T>
      {problem ? <T testID="bitsat-input-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
      <Pill testID="bitsat-show" size="lg" label="Show" iconRight="arrow-right" busy={busy && !res} onPress={show} bg={colors.brandPrimary} ink={colors.onBrandPrimary} />
    </Strip> : <Summary testID="bitsat-input-collapsed" text={`${score} / 390 · BITSAT 2026`} onEdit={() => setOpen(true)} />}
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="bitsat-error" />
    {res && score !== null ? <>
      <BitsatCard data={res} saved={saved.length} onShortlist={onShortlist} />
      <Strip title="BITS programs" testID="bitsat-list"
        right={busy ? <ActivityIndicator size="small" color={colors.muted} /> : <T size={12} color={colors.muted}>{res.result.cleared} / {res.result.total} clear</T>}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
          {CAMPUSES.map(c => <Toggle key={c} testID={`bitsat-campus-${c}`} label={c === "all" ? "All campus" : CAMPUS[c].label} on={campus === c}
            ink={c === "all" ? colors.onSurface : CAMPUS[c].ink} soft={c === "all" ? undefined : CAMPUS[c].soft} onPress={() => setCampus(c)} />)}
        </ScrollView>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
          {DEGREES.map(d => <Toggle key={d.key} testID={`bitsat-degree-${d.key}`} label={d.label} on={degree === d.key} onPress={() => setDegree(d.key)} />)}
        </ScrollView>
        <BitsatList data={res} saved={new Set(saved.map(s => s.id))} />
      </Strip>
    </> : null}
  </>;
}

function BitsatCard({ data, saved, onShortlist }: { data: BitsatOut; saved: number; onShortlist: () => void }) {
  const reduced = useReducedMotion();
  const r = data.result;
  return <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} style={{ gap: space.md }}>
    <MetalCard testID="bitsat-card" badge="BITSAT 2026" foot={<>
      <View style={{ flex: 1, gap: 3 }}>
        <Eyebrow>BEST PROGRAM</Eyebrow>
        <SilverCaps testID="bitsat-card-best">{r.best ? `${r.best.college} · ${r.best.program}` : "Abhi koi program clear nahi"}</SilverCaps>
      </View>
      <Serial testID="bitsat-card-serial" value={String(r.cleared_all)} of={String(r.total_all)} />
    </>}>
      <View style={{ gap: 2 }}>
        <Eyebrow>YOUR SCORE</Eyebrow>
        <SerifBig testID="bitsat-card-score">{`${r.score} / ${r.max}`}</SerifBig>
      </View>
      <BlueRule testID="bitsat-card-cleared" label={`CLEARS ${r.cleared_all} OF ${r.total_all} BITS PROGRAMS`} />
      <T testID="bitsat-card-target" size={12.5} color={colors.custom_rankSilverMuted}>
        {r.target ? `Agla target: ${r.target.college} · ${r.target.program}, +${r.target.gap} marks aur (cutoff ${r.target.cutoff}).` : "Har BITS program ka 2026 cutoff clear!"}
      </T>
    </MetalCard>
    <CardActions prefix="bitsat" onShare={() => shareBitsat(data)} saved={saved} onShortlist={onShortlist} notes={data.notes} />
  </Animated.View>;
}

function BitsatList({ data, saved }: { data: BitsatOut; saved: Set<string> }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [rest, setRest] = useState(false);
  const row = (b: BitsatItem, testID: string) => <BitsatRow key={b.id} item={b} score={data.result.score} years={data.years} testID={testID}
    open={openId === b.id} onPress={() => setOpenId(openId === b.id ? null : b.id)} saved={saved.has(`bitsat-${b.id}`)} onStar={() => toggleSaved(bitsatSaved(b))} />;
  return <>
    {data.items.length === 0 ? <T testID="bitsat-list-empty" size={13.5} color={colors.muted}>Is score par is filter mein koi program 2026 cutoff ke paas nahi. Campus ya degree badal kar dekho.</T>
      : <View>{data.items.map((b, i) => row(b, `bitsat-item-${i}`))}</View>}
    {data.near.length ? <View testID="bitsat-near" style={{ gap: space.xs, marginTop: space.sm }}>
      <T w="bold" size={11} color={colors.custom_eyebrow} style={{ letterSpacing: 2 }}>BAS THODA SA DOOR</T>
      {data.near.map((b, i) => row(b, `bitsat-near-${i}`))}
    </View> : null}
    {data.rest.length ? rest ? <View testID="bitsat-rest">{data.rest.map((b, i) => row(b, `bitsat-rest-${i}`))}</View>
      : <Press testID="bitsat-rest-show" onPress={() => setRest(true)} style={styles.outline}><T w="bold" size={14}>Baaki programs ({data.rest.length})</T></Press> : null}
  </>;
}

function BitsatRow({ item, score, years, open, onPress, saved, onStar, testID }: {
  item: BitsatItem; score: number; years: number[]; open: boolean; onPress: () => void; saved: boolean; onStar: () => void; testID: string;
}) {
  const k = CAMPUS[item.campus];
  const d = item.last === null ? null : item.cutoff - item.last, same = d !== null && Math.abs(d) <= 2;
  return <View style={styles.row}>
    <Press testID={testID} onPress={onPress} accessibilityState={{ expanded: open }} accessibilityLabel={`${item.college}, ${item.program}`} scaleTo={0.99} style={styles.main}>
      <View style={{ flex: 1, gap: 3 }}>
        <View style={styles.line}>
          <T w="bold" size={14.5} numberOfLines={1} style={{ flexShrink: 1 }}>{item.college}</T>
          <Tag label={k.label} ink={k.ink} soft={k.soft} />
        </View>
        <T size={13.5} color={colors.custom_softText} numberOfLines={2}>{item.program}</T>
        <T size={12} color={colors.muted}>Cutoff 2026: {item.cutoff}{item.last !== null ? ` · 2025: ${item.last}` : " · naya program"}</T>
        {d !== null ? <T testID={`${testID}-trend`} w="semibold" size={12} color={same ? colors.muted : d > 0 ? colors.error : colors.success}>
          {same ? "2025 jitna hi" : d > 0 ? `▲ ${d} marks, 2025 se tough hua` : `▼ ${-d} marks, 2025 se aasaan hua`}
        </T> : null}
        <T w="semibold" size={12} color={item.gap > 0 ? colors.custom_flame : colors.success}>
          {item.gap > 0 ? `+${item.gap} marks aur chahiye` : `Aapka score cutoff se ${score - item.cutoff} upar`}
        </T>
        {open ? <T testID={`${testID}-history`} size={12} color={colors.custom_softText}>
          {years.map((y, i) => `${y}: ${item.history[i] ?? "—"}`).join("  ·  ")}
        </T> : null}
      </View>
      {item.tag ? <Tag testID={`${testID}-tag`} label={TAG[item.tag].label} ink={TAG[item.tag].ink} soft={TAG[item.tag].soft} /> : null}
    </Press>
    <StarButton saved={saved} onPress={onStar} testID={`${testID}-star`} />
  </View>;
}

const styles = StyleSheet.create({
  input: { height: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.bold, fontSize: 18, color: colors.onSurface, ...noOutline },
  chips: { gap: space.sm, paddingRight: space.sm },
  row: { flexDirection: "row", alignItems: "flex-start", borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  main: { flex: 1, flexDirection: "row", gap: space.sm, paddingVertical: space.md, alignItems: "flex-start" },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  outline: { minHeight: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center", marginTop: space.sm },
});
