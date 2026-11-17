// BITSAT on the Rank tab: score in, BITSAT Rank Card out, then every BITS program with its 2026 cutoff and 5-year trend.
import React, { useEffect, useRef, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, TextInput, View } from "react-native";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { rankColors as colors, fonts, noOutline, radius, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import { bitsat, BitsatItem, BitsatOut, Campus, Degree } from "./api";
import { CAMPUS, TAG } from "./tones";
import { Strip, Summary, Tag, Toggle } from "./controls";
import { CardActions, Eyebrow, Hairline, MetalCard, Serial, SerifBig, SilverCaps } from "./MetalCard";
import { shareBitsat } from "./share";
import { CardsHeading, CollegeCard, TapHint, cardStyles, useCardViews } from "./CollegeCard";
import { edgeOf } from "./SeatList";
import { PdfButton } from "./PdfButton";
import { bitsatSaved, toggleSaved, useShortlist } from "./shortlist";
import { FormButton, useField } from "./accent";
import { CardRef, shareCard } from "@/src/shareCard";
import { useShareLink } from "@/src/mission/stats";
import { useDreamToggle } from "@/src/dream/useDreamToggle";
import { bitsatDream } from "@/src/dream/need";

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
  const field = useField();
  const card = useRef<React.ComponentRef<typeof View>>(null); // the BITSAT card: shared as a photo, and with the PDF

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
    {open || score === null ? <Strip form title="Your BITSAT score" testID="bitsat-input">
      <View style={{ gap: 4 }}>
        <T w="semibold" size={12} color={colors.muted}>Score (out of 390)</T>
        <TextInput testID="bitsat-score-input" value={text} onChangeText={v => setText(v.replace(/[^0-9-]/g, "").slice(0, 4))} keyboardType="numbers-and-punctuation"
          placeholder="e.g. 280" placeholderTextColor={colors.custom_dim} style={[styles.input, field.style]} keyboardAppearance="dark" selectionColor={field.selectionColor} returnKeyType="done" onSubmitEditing={show} maxLength={4} accessibilityLabel="BITSAT score out of 390" />
      </View>
      <T size={12} color={colors.muted}>BITSAT 2026: 130 sawaal, +3 / −1. Cutoff BITS ki official 2022–2026 list se.</T>
      {problem ? <T testID="bitsat-input-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
      <FormButton testID="bitsat-show" label="Show" busy={busy && !res} onPress={show} />
    </Strip> : <Summary testID="bitsat-input-collapsed" text={`${score} / 390 · BITSAT 2026`} onEdit={() => setOpen(true)} />}
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="bitsat-error" />
    {res && score !== null ? <>
      <BitsatCard data={res} saved={saved.length} onShortlist={onShortlist} cardRef={card} />
      <View testID="bitsat-list" style={cardStyles.list}>
        <Strip title="BITS programs" testID="bitsat-list-head"
          right={busy ? <ActivityIndicator size="small" color={colors.muted} /> : <T size={12} color={colors.muted}>{res.result.cleared} / {res.result.total} clear</T>}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            {CAMPUSES.map(c => <Toggle key={c} testID={`bitsat-campus-${c}`} label={c === "all" ? "All campus" : CAMPUS[c].label} on={campus === c}
              ink={c === "all" ? colors.onSurface : CAMPUS[c].ink} soft={c === "all" ? undefined : CAMPUS[c].soft} onPress={() => setCampus(c)} />)}
          </ScrollView>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            {DEGREES.map(d => <Toggle key={d.key} testID={`bitsat-degree-${d.key}`} label={d.label} on={degree === d.key} onPress={() => setDegree(d.key)} />)}
          </ScrollView>
          <PdfButton testID="bitsat-pdf" path="/bitsat" body={{ score, campus, degree }} label="Programs list ki PDF" card={card} />
        </Strip>
        <BitsatList data={res} saved={new Set(saved.map(s => s.id))} />
      </View>
    </> : null}
  </>;
}

function BitsatCard({ data, saved, onShortlist, cardRef }: { data: BitsatOut; saved: number; onShortlist: () => void; cardRef: CardRef }) {
  const reduced = useReducedMotion();
  const link = useShareLink();
  const r = data.result;
  return <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} style={{ gap: space.md }}>
    <MetalCard testID="bitsat-card" cardRef={cardRef} badge="BITSAT 2026" foot={<>
      <View style={{ flexGrow: 1, flexShrink: 1, gap: 3 }}>
        <Eyebrow>BEST PROGRAM</Eyebrow>
        <SilverCaps testID="bitsat-card-best">{r.best ? `${r.best.college} · ${r.best.program}` : "Abhi koi program clear nahi"}</SilverCaps>
      </View>
      <Serial testID="bitsat-card-serial" value={String(r.cleared_all)} of={String(r.total_all)} />
    </>}>
      <View style={{ gap: 2 }}>
        <Eyebrow>YOUR SCORE</Eyebrow>
        <SerifBig testID="bitsat-card-score">{`${r.score} / ${r.max}`}</SerifBig>
      </View>
      <Hairline testID="bitsat-card-cleared" label={`CLEARS ${r.cleared_all} OF ${r.total_all} BITS PROGRAMS`} />
      <T testID="bitsat-card-target" size={12.5} color={colors.custom_rankSilverMuted}>
        {r.target ? `Agla target: ${r.target.college} · ${r.target.program}, +${r.target.gap} marks aur (cutoff ${r.target.cutoff}).` : "Har BITS program ka 2026 cutoff clear!"}
      </T>
    </MetalCard>
    <CardActions prefix="bitsat" onShare={() => shareCard(cardRef, shareBitsat(data, link))} saved={saved} onShortlist={onShortlist} notes={data.notes} />
  </Animated.View>;
}

function BitsatList({ data, saved }: { data: BitsatOut; saved: Set<string> }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [rest, setRest] = useState(false);
  const views = useCardViews();
  const tap = (id: string) => { if (openId !== id) views.mark(id); setOpenId(openId === id ? null : id); };
  const row = (b: BitsatItem, testID: string, rank?: number, first?: boolean) => <BitsatRow key={`${testID}-${b.id}`} item={b} score={data.result.score} years={data.years} testID={testID} rank={rank}
    open={openId === b.id} viewed={views.viewed.has(b.id)} pulse={first && views.pulse} onPress={() => tap(b.id)} saved={saved.has(`bitsat-${b.id}`)} onStar={() => toggleSaved(bitsatSaved(b))} />;
  return <>
    {data.items.length === 0 ? <T testID="bitsat-list-empty" size={13.5} color={colors.muted}>Is score par is filter mein koi program 2026 cutoff ke paas nahi. Campus ya degree badal kar dekho.</T>
      : <>
        <TapHint testID="bitsat-tap-hint" viewed={views.viewed.size} what="program" />
        {data.items.map((b, i) => row(b, `bitsat-item-${i}`, i + 1, i === 0))}
      </>}
    {data.near.length ? <View testID="bitsat-near" style={cardStyles.list}>
      <CardsHeading icon="flag-checkered" title="BAS THODA SA DOOR" sub="Thode aur marks, aur ye programs bhi aapke" ink={colors.custom_flame} />
      {data.near.map((b, i) => row(b, `bitsat-near-${i}`))}
    </View> : null}
    {data.rest.length ? rest ? <View testID="bitsat-rest" style={cardStyles.list}>
      <CardsHeading icon="format-list-bulleted" title="BAAKI PROGRAMS" />
      {data.rest.map((b, i) => row(b, `bitsat-rest-${i}`))}
    </View>
      : <Press testID="bitsat-rest-show" onPress={() => setRest(true)} style={styles.outline}><T w="bold" size={14}>Baaki programs ({data.rest.length})</T></Press> : null}
  </>;
}

function BitsatRow({ item, score, years, open, onPress, saved, onStar, testID, rank, viewed, pulse }: {
  item: BitsatItem; score: number; years: number[]; open: boolean; onPress: () => void; saved: boolean; onStar: () => void; testID: string; rank?: number;
  viewed?: boolean; pulse?: boolean;
}) {
  const k = CAMPUS[item.campus];
  const d = item.last === null ? null : item.cutoff - item.last, same = d !== null && Math.abs(d) <= 2;
  const dream = useDreamToggle(`bitsat-${item.id}`, "bitsat", () => bitsatDream(item));
  return <CollegeCard testID={testID} rank={rank} edge={edgeOf(item.tag, item.gap > 0)} title={item.college} a11y={`${item.college}, ${item.program}`} open={open} dream={dream}
    tags={<>
      <Tag label={k.label} ink={k.ink} soft={k.soft} />
      {item.tag ? <Tag testID={`${testID}-tag`} label={TAG[item.tag].label} ink={TAG[item.tag].ink} soft={TAG[item.tag].soft} /> : null}
    </>}
    sub={item.program}
    stats={[
      { label: "CUTOFF", value: String(item.cutoff), sub: "2026 · / 390" },
      d === null ? { label: "2025 SE", value: "Naya", sub: "naya program", ink: colors.custom_softText, testID: `${testID}-trend` }
        : { label: "2025 SE", value: same ? "≈ Same" : d > 0 ? `▲ ${d} tough` : `▼ ${-d} aasaan`, sub: `2025: ${item.last}`,
          ink: same ? colors.custom_softText : d > 0 ? colors.error : colors.success, testID: `${testID}-trend` },
      item.gap > 0 ? { label: "AAPKA", value: `+${item.gap} chahiye`, sub: `score ${score}`, ink: colors.custom_flame }
        : { label: "AAPKA", value: `${score - item.cutoff} upar`, sub: `score ${score}`, ink: colors.success },
    ]}
    teaser="2022 se 2026 tak, 5 saal ke cutoff" viewed={viewed} pulse={pulse} onPress={onPress} saved={saved} onStar={onStar}>
    {open ? <View testID={`${testID}-history`} style={styles.years}>
      {years.map((y, i) => <View key={y} style={[styles.year, i === years.length - 1 && styles.yearNow]}>
        <T w="bold" size={10.5} color={colors.custom_eyebrow}>{y}</T>
        <T w="heavy" size={14} color={item.history[i] == null ? colors.custom_dim : colors.onSurface}>{item.history[i] ?? "—"}</T>
      </View>)}
    </View> : null}
  </CollegeCard>;
}

const styles = StyleSheet.create({
  input: { height: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.bold, fontSize: 18, color: colors.onSurface, ...noOutline },
  chips: { gap: space.sm, paddingRight: space.sm },
  years: { flexDirection: "row", gap: 6 },
  year: { flex: 1, minWidth: 0, alignItems: "center", gap: 2, paddingVertical: 8, borderRadius: 10, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_cardRaised },
  yearNow: { borderColor: colors.custom_rankSilverLine },
  outline: { minHeight: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center", marginTop: space.sm },
});
