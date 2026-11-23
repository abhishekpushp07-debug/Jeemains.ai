// Rank predictor (Rank tab, first tile): pick JEE Main or COMEDK, type marks (JEE: category, PwD, paper type) and get the
// expected rank and percentile only. JEE shows all three paper types side by side; COMEDK shows what each analysis says.
// "Colleges dekho" carries the same score into the College predictor.
import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, TextInput, useWindowDimensions, View } from "react-native";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { rankColors as colors, fonts, noOutline, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import { Category, ComedkEstimate, estimate, EstimateIn, EstimateOut, fmt, fmtPct, fmtRange, JeeEstimate, Level } from "./api";
import { CATEGORY_LABEL, LEVEL, SERIF } from "./tones";
import { Strip, Summary, Switch, Tag, Toggle } from "./controls";
import { CardActions, Eyebrow, Hairline, MetalCard, Serial, SerifBig, SilverCaps, Small } from "./MetalCard";
import { shareEstimate } from "./share";
import { FormButton, useField } from "./accent";
import { SAVED, useProfileSaves } from "./profile";
import { shareCard } from "@/src/shareCard";
import { useShareLink } from "@/src/mission/stats";

const LEVELS: Level[] = ["tough", "normal", "easy"];
const CATS: Category[] = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];
type Exam = "jee" | "comedk";
type Form = { exam: Exam; jee: string; comedk: string; level: Level; category: Category; pwd: boolean };
const DEFAULT: Form = { exam: "jee", jee: "", comedk: "", level: "normal", category: "GEN", pwd: false };
const MAX: Record<Exam, number> = { jee: 300, comedk: 180 };

function toQuery(f: Form): EstimateIn | string {
  const raw = (f.exam === "jee" ? f.jee : f.comedk).trim();
  const n = Number(raw);
  if (!raw) return "Marks daalo.";
  const min = f.exam === "jee" ? -75 : 0;
  if (!Number.isInteger(n) || n < min || n > MAX[f.exam]) return `Marks ${min === 0 ? "0" : "−75"} se ${MAX[f.exam]} ke beech poore ank mein daalo.`;
  return { exam: f.exam, marks: n, level: f.level, category: f.category, pwd: f.pwd };
}

const summaryOf = (q: EstimateIn) => q.exam === "jee"
  ? [`${q.marks} / 300 marks`, `${LEVEL[q.level].label} paper`, CATEGORY_LABEL[q.category], q.pwd ? "PwD" : null, "JEE Main 2026"].filter(Boolean).join(" · ")
  : `${q.marks} / 180 marks · COMEDK 2026`;

export function RankPredictor({ onColleges }: { onColleges: (q: EstimateIn) => void }) {
  const [form, setForm] = useState<Form>(DEFAULT);
  const [open, setOpen] = useState(true);
  // One question and answer per exam, so switching JEE <-> COMEDK never shows the other exam's card.
  const [queries, setQueries] = useState<Partial<Record<Exam, EstimateIn>>>({});
  const [results, setResults] = useState<Partial<Record<Exam, EstimateOut>>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const query = queries[form.exam] ?? null;
  const field = useField();

  // Read when the tool opens and again after "Meri details" is saved (that fills every tool's form).
  const saves = useProfileSaves();
  useEffect(() => {
    storage.getItem<string | null>(SAVED.estimate, null).then(raw => {
      // After a profile save the student stays on the exam they were looking at.
      if (raw) try { const v = JSON.parse(raw); setForm(f => ({ ...DEFAULT, ...v, ...(saves ? { exam: f.exam } : {}) })); } catch { /* keep defaults */ }
      if (saves) setOpen(true);
    });
  }, [saves]);
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError(null);
    estimate(query).then(d => { if (live) setResults(r => ({ ...r, [query.exam]: d })); }).catch(e => { if (live) setError(e.message); })
      .finally(() => { if (live) setBusy(false); });
    return () => { live = false; setBusy(false); };
  }, [query, tries]);

  const patch = (p: Partial<Form>) => { setForm(f => ({ ...f, ...p })); setProblem(null); };
  const run = (f: Form) => {
    const q = toQuery(f);
    if (typeof q === "string") { setProblem(q); return; }
    setProblem(null);
    storage.setItem(SAVED.estimate, JSON.stringify(f));
    setQueries(m => ({ ...m, [q.exam]: q })); setOpen(false);
  };
  // Tapping a paper type in the comparison re-reads the card for that paper.
  const pickLevel = (level: Level) => { const f = { ...form, level }; setForm(f); run(f); };
  const switchExam = (exam: Exam) => { patch({ exam }); setOpen(!queries[exam]); setError(null); };
  const found = results[form.exam];
  const shown = found && query && found.exam === form.exam ? found : null;

  return <>
    <Switch prefix="rp-exam" value={form.exam} onChange={switchExam} items={[{ key: "jee", label: "JEE Main" }, { key: "comedk", label: "COMEDK" }]} />
    {open || !query ? <Strip form title="Your marks" testID="rp-input">
      <View style={{ gap: 4 }}>
        <T w="semibold" size={12} color={colors.muted}>Marks (out of {MAX[form.exam]})</T>
        <TextInput testID="rp-marks-input" value={form.exam === "jee" ? form.jee : form.comedk} keyboardType="numbers-and-punctuation"
          onChangeText={v => patch(form.exam === "jee" ? { jee: v.replace(/[^0-9-]/g, "").slice(0, 4) } : { comedk: v.replace(/[^0-9]/g, "").slice(0, 3) })}
          placeholder={form.exam === "jee" ? "e.g. 180" : "e.g. 110"} placeholderTextColor={colors.custom_dim} style={[styles.input, field.style]} keyboardAppearance="dark"
          selectionColor={field.selectionColor} returnKeyType="done" maxLength={4} accessibilityLabel={`Marks out of ${MAX[form.exam]}`} onSubmitEditing={() => run(form)} />
      </View>
      {form.exam === "jee" ? <>
        <View style={styles.row}>
          <T w="semibold" size={12} color={colors.muted} style={styles.rowLabel}>Paper</T>
          {LEVELS.map(l => <Toggle key={l} testID={`rp-level-${l}`} label={LEVEL[l].label} on={form.level === l} ink={LEVEL[l].ink} soft={LEVEL[l].soft} onPress={() => patch({ level: l })} />)}
        </View>
        <T size={11.5} color={colors.custom_dim}>Paper type = aapki shift ka paper kaisa tha (pata na ho to Normal rakho).</T>
        <View style={styles.wrap}>
          {CATS.map(c => <Toggle key={c} testID={`rp-cat-${c}`} label={CATEGORY_LABEL[c]} on={form.category === c} onPress={() => patch({ category: c })} />)}
          <Toggle testID="rp-pwd" label="PwD" on={form.pwd} onPress={() => patch({ pwd: !form.pwd })} />
        </View>
      </> : <T size={12} color={colors.muted}>COMEDK UGET 2026: 180 sawaal, +1 / 0. Sabki ek hi merit list, isliye category aur paper type nahi lagte.</T>}
      {problem ? <T testID="rp-input-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
      <FormButton testID="rp-show" label="Predict rank" busy={busy && !shown} onPress={() => run(form)} />
    </Strip> : <Summary testID="rp-input-collapsed" text={summaryOf(query)} onEdit={() => setOpen(true)} />}
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="rp-error" />
    {shown && query ? <>
      {shown.exam === "jee" ? <JeeCard data={shown} level={query.level} onLevel={pickLevel} busy={busy} /> : <ComedkCard data={shown} />}
      <Pill testID="rp-colleges" size="lg" label="Is score se colleges dekho" iconRight="arrow-right" onPress={() => onColleges(query)}
        bg={colors.custom_cardRaised} ink={colors.onSurface} style={styles.outline} />
    </> : null}
  </>;
}

function JeeCard({ data, level, onLevel, busy }: { data: JeeEstimate; level: Level; onLevel: (l: Level) => void; busy: boolean }) {
  const reduced = useReducedMotion();
  const narrow = useWindowDimensions().width < 360;
  const card = useRef<React.ComponentRef<typeof View>>(null);
  const link = useShareLink();
  const r = data.result;
  return <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} style={{ gap: space.md }}>
    <MetalCard testID="rp-card" cardRef={card} badge="JEE MAIN 2026" foot={<>
      <View style={{ flexGrow: 1, flexShrink: 1, gap: 3 }}>
        <Eyebrow>YOUR SCORE</Eyebrow>
        <SilverCaps testID="rp-card-summary">{r.summary}</SilverCaps>
      </View>
      <Serial testID="rp-card-serial" value={fmt((r.crl[0] + r.crl[1]) / 2)} of={fmt(data.candidates)} />
    </>}>
      <View style={{ gap: 2 }}>
        <Eyebrow>EXPECTED PERCENTILE</Eyebrow>
        <SerifBig testID="rp-card-percentile">{fmtPct(r.percentile)}</SerifBig>
      </View>
      <Hairline testID="rp-card-crl" label={`RANK (CRL)  ${fmtRange(r.crl)}`} />
      {r.cat_rank || r.pwd_rank ? <View style={styles.smalls}>
        {r.cat_rank ? <Small testID="rp-card-cat" label={r.cat_rank.label} value={fmtRange(r.cat_rank.range)} /> : null}
        {r.pwd_rank ? <Small testID="rp-card-pwd" label={r.pwd_rank.label} value={fmtRange(r.pwd_rank.range)} /> : null}
      </View> : null}
    </MetalCard>
    <Strip title="Paper type ke hisaab se" testID="rp-levels" right={busy ? <T size={12} color={colors.muted}>…</T> : undefined}>
      {data.levels.map(l => {
        const on = l.level === level;
        return <Press key={l.level} testID={`rp-levels-${l.level}`} onPress={() => onLevel(l.level)} accessibilityState={{ selected: on }}
          accessibilityLabel={`${LEVEL[l.level].label} paper: ${fmtPct(l.percentile)} percentile, rank ${fmtRange(l.crl)}`} scaleTo={0.99} style={[styles.level, on && styles.levelOn]}>
          {on ? <View style={styles.levelBar} /> : null}
          <View style={styles.levelHead}>
            <Tag label={LEVEL[l.level].label} ink={LEVEL[l.level].ink} soft={LEVEL[l.level].soft} />
            {on ? <T size={11} w="semibold" color={colors.custom_rankBloodInk}>aapka paper</T> : null}
          </View>
          <View style={styles.levelVals}>
            <View style={{ flex: 1, gap: 2 }}>
              <T color={on ? colors.custom_rankSilver : colors.onSurface} style={[styles.serif, narrow && styles.serifNarrow]}>{fmtPct(l.percentile)}</T>
              <T size={11} color={colors.muted}>percentile</T>
            </View>
            <View style={{ flex: 1, gap: 2, alignItems: "flex-end" }}>
              <T color={on ? colors.custom_rankSilver : colors.onSurface} style={[styles.serif, narrow && styles.serifNarrow]}>{fmtRange(l.crl)}</T>
              <T size={11} color={colors.muted}>rank (CRL)</T>
            </View>
          </View>
          {[l.cat_rank, l.pwd_rank].map(x => x ? <T key={x.label} size={11.5} color={colors.custom_softText}>
            {x.label.replace(/-/g, "\u2011")}: {fmtRange(x.range).replace(" – ", "\u00A0–\u00A0")}
          </T> : null)}
        </Press>;
      })}
      <T size={11.5} color={colors.custom_dim}>Same marks par shift ka paper tough tha to percentile zyada aata hai. Kisi bhi row par tap karo, card us paper ke hisaab se badal jayega.</T>
    </Strip>
    <CardActions prefix="rp" onShare={() => shareCard(card, shareEstimate(data, link))} notes={[r.spread, ...data.notes]} />
  </Animated.View>;
}

function ComedkCard({ data }: { data: ComedkEstimate }) {
  const reduced = useReducedMotion();
  const card = useRef<React.ComponentRef<typeof View>>(null);
  const link = useShareLink();
  return <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} style={{ gap: space.md }}>
    <MetalCard testID="rp-card" cardRef={card} badge="COMEDK 2026" foot={<>
      <View style={{ flexGrow: 1, flexShrink: 1, gap: 3 }}>
        <Eyebrow>YOUR SCORE</Eyebrow>
        <SilverCaps testID="rp-card-summary">{data.summary}</SilverCaps>
      </View>
      <Serial testID="rp-card-serial" value={fmt(data.mid)} of={fmt(data.candidates)} />
    </>}>
      <View style={{ gap: 2 }}>
        <Eyebrow>EXPECTED RANK</Eyebrow>
        <SerifBig testID="rp-card-rank">{fmtRange(data.rank)}</SerifBig>
      </View>
      <Hairline testID="rp-card-percentile" label={`PERCENTILE  ${fmtPct(data.percentile)}`} />
    </MetalCard>
    <Strip title="3 analyses kya kehte hain" testID="rp-sources">
      {data.sources.map((s, i) => <View key={s.label} testID={`rp-sources-${i}`} style={styles.source}>
        <T size={12.5} color={colors.custom_softText} style={{ flex: 1 }} numberOfLines={2}>{s.label}</T>
        <T color={colors.custom_rankSilver} style={styles.serif}>{fmt(s.rank)}</T>
      </View>)}
      <T size={11.5} color={colors.custom_dim}>Beech wala andaaza (№ {fmt(data.mid)}) card par hai; range = sabse achha se sabse kharab andaaza.</T>
    </Strip>
    <CardActions prefix="rp" onShare={() => shareCard(card, shareEstimate(data, link))} notes={data.notes} />
  </Animated.View>;
}

const styles = StyleSheet.create({
  input: { height: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.bold, fontSize: 18, color: colors.onSurface, ...noOutline },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" },
  rowLabel: { width: 44 },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  outline: { borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  smalls: { flexDirection: "row", flexWrap: "wrap", gap: space.md },
  level: { gap: space.sm, paddingVertical: space.md, paddingHorizontal: space.md, borderRadius: 14, overflow: "hidden" },
  levelOn: { backgroundColor: colors.custom_rankBloodSoft },
  levelBar: { position: "absolute", left: 0, top: 10, bottom: 10, width: 2, borderRadius: 1, backgroundColor: colors.custom_rankBlood },
  levelHead: { flexDirection: "row", alignItems: "center", gap: space.sm },
  levelVals: { flexDirection: "row", alignItems: "flex-start", gap: space.md },
  serif: { fontFamily: SERIF, fontSize: 16, lineHeight: 21 },
  serifNarrow: { fontSize: 14.5, lineHeight: 19 },
  source: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 44, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
});
