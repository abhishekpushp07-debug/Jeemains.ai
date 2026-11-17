// COMEDK on the Rank tab: marks or rank in, COMEDK Rank Card out, then GM (All India) college-courses with every round's
// closing rank, the 2025 trend, fee and seats. All data comes from our server (/api/rank/comedk).
import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, TextInput, View } from "react-native";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { rankColors as colors, fonts, noOutline, radius, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import { comedk, ComedkArea, ComedkCollegeReq, ComedkItem, ComedkOut, ComedkQuery, fmt, fmtRange } from "./api";
import { TAG } from "./tones";
import { Picker, Strip, Summary, Tag, Toggle } from "./controls";
import { CardActions, Eyebrow, Hairline, MetalCard, Serial, SerifBig, SilverCaps } from "./MetalCard";
import { branchLabel } from "./InputCard";
import { edgeOf, trendStat } from "./SeatList";
import { ComedkSheet } from "./ComedkSheet";
import { shareComedk } from "./share";
import { CardsHeading, CollegeCard, TapHint, cardStyles, useCardViews } from "./CollegeCard";
import { PdfButton } from "./PdfButton";
import { comedkSaved, toggleSaved, useShortlist } from "./shortlist";
import { FormButton, useField } from "./accent";

const SAVED = "rank.comedk.v1";
const AREAS: { key: ComedkArea; label: string }[] = [{ key: "all", label: "All" }, { key: "blr", label: "Bengaluru" }, { key: "other", label: "Other cities" }];

/** Typed values -> request, or what to fix. A rank card rank wins over marks when both are filled. */
function toQuery(marks: string, rank: string): ComedkQuery | string {
  const m = marks.trim(), r = rank.trim();
  if (!m && !r) return "Marks ya rank mein se koi ek daalo.";
  if (r) {
    const n = Number(r);
    return Number.isInteger(n) && n >= 1 && n <= 200000 ? { rank: n } : "Rank 1 se 2,00,000 ke beech poore ank mein daalo.";
  }
  const n = Number(m);
  return Number.isInteger(n) && n >= 0 && n <= 180 ? { marks: n } : "Marks 0 se 180 ke beech poore ank mein daalo.";
}

export function ComedkPanel({ groups, onShortlist, seed, onSeedUsed }: {
  groups: string[]; onShortlist: () => void; seed?: { marks: number; at: number } | null; onSeedUsed?: () => void;
}) {
  const [marks, setMarks] = useState("");
  const [rank, setRank] = useState("");
  const [branches, setBranches] = useState<string[]>([]);
  const [open, setOpen] = useState(true);
  const [query, setQuery] = useState<ComedkQuery | null>(null);
  const [area, setArea] = useState<ComedkArea>("all");
  const [page, setPage] = useState(1);
  const [res, setRes] = useState<ComedkOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [picker, setPicker] = useState(false);
  const [tries, setTries] = useState(0);
  const [detail, setDetail] = useState<ComedkCollegeReq | null>(null);
  const saved = useShortlist();
  const field = useField();

  useEffect(() => {
    if (seed) return; // a score handed over from the Rank predictor wins over the last saved one
    storage.getItem<string | null>(SAVED, null).then(raw => {
      if (!raw) return;
      try {
        const v = JSON.parse(raw);
        setMarks(v.marks ?? ""); setRank(v.rank ?? ""); setBranches(Array.isArray(v.branches) ? v.branches : []);
      } catch { /* keep empty */ }
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!seed) return;
    setMarks(String(seed.marks)); setRank(""); setProblem(null);
    setPage(1); setQuery({ marks: seed.marks }); setOpen(false);
    // Save the handed-over score (keeping saved branches) so a later visit opens with it, then let the parent forget it.
    storage.getItem<string | null>(SAVED, null).then(raw => {
      let kept: string[] = [];
      try { const v = raw ? JSON.parse(raw) : null; kept = Array.isArray(v?.branches) ? v.branches : []; } catch { /* none */ }
      setBranches(kept);
      storage.setItem(SAVED, JSON.stringify({ marks: String(seed.marks), rank: "", branches: kept }));
    });
    onSeedUsed?.();
  }, [seed]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError(null);
    comedk({ ...query, branches, area, page }).then(d => { if (live) setRes(d); }).catch(e => { if (live) setError(e.message); })
      .finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [query, branches, area, page, tries]);

  const show = () => {
    const q = toQuery(marks, rank);
    if (typeof q === "string") { setProblem(q); return; }
    setProblem(null);
    storage.setItem(SAVED, JSON.stringify({ marks, rank, branches }));
    setPage(1); setQuery(q); setOpen(false);
  };
  const pickBranches = (b: string[]) => { setBranches(b); setPage(1); };
  const summary = query ? [query.rank ? `Rank ${fmt(query.rank)}` : `${query.marks} / 180 marks`, "COMEDK 2026 · GM", branches.length ? branchLabel(branches) : null].filter(Boolean).join(" · ") : "";

  return <>
    {open || !query ? <Strip form title="Your COMEDK score" testID="comedk-input">
      <View style={styles.inputs}>
        <View style={{ flex: 1, gap: 4 }}>
          <T w="semibold" size={12} color={colors.muted}>Marks (out of 180)</T>
          <TextInput testID="comedk-marks-input" value={marks} onChangeText={v => setMarks(v.replace(/[^0-9]/g, "").slice(0, 3))} keyboardType="number-pad"
            placeholder="e.g. 110" placeholderTextColor={colors.custom_dim} style={[styles.input, field.style]} keyboardAppearance="dark" selectionColor={field.selectionColor}
            returnKeyType="done" maxLength={3} accessibilityLabel="COMEDK marks out of 180" />
        </View>
        <View style={{ flex: 1, gap: 4 }}>
          <T w="semibold" size={12} color={colors.muted}>Rank (rank card se)</T>
          <TextInput testID="comedk-rank-input" value={rank} onChangeText={v => setRank(v.replace(/[^0-9]/g, "").slice(0, 6))} keyboardType="number-pad"
            placeholder="e.g. 4500" placeholderTextColor={colors.custom_dim} style={[styles.input, field.style]} keyboardAppearance="dark" selectionColor={field.selectionColor}
            returnKeyType="done" maxLength={6} accessibilityLabel="COMEDK rank" />
        </View>
      </View>
      <T size={12} color={colors.muted}>COMEDK UGET 2026: 180 sawaal, +1 / 0 (negative marking nahi). Sirf GM (All India) seats.{marks.trim() && rank.trim() ? " Dono bhare hain, to Rank se dikhayenge." : ""}</T>
      <View style={styles.wrap}>
        <Toggle testID="comedk-branch" label={branchLabel(branches)} on={branches.length > 0} caret onPress={() => setPicker(true)} />
      </View>
      {problem ? <T testID="comedk-input-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
      <FormButton testID="comedk-show" label="Show" busy={busy && !res} onPress={show} />
    </Strip> : <Summary testID="comedk-input-collapsed" text={summary} onEdit={() => setOpen(true)} />}
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="comedk-error" />
    {res && query ? <>
      <ComedkCard data={res} saved={saved.length} onShortlist={onShortlist} />
      <ComedkList data={res} area={area} onArea={a => { setArea(a); setPage(1); }} page={page} onPage={setPage} busy={busy}
        branchText={branchLabel(branches)} onBranch={() => setPicker(true)} saved={new Set(saved.map(s => s.id))}
        onOpen={i => setDetail({ ...query, branches, code: i.code, course: i.cc })}
        tools={<PdfButton testID="comedk-pdf" path="/comedk" body={{ ...query, branches, area }} label="Top 50 ki PDF" />} />
    </> : null}
    <View style={{ gap: 4 }}>
      {(res?.notes ?? []).map(n => <T key={n} size={12} color={colors.muted}>{n}</T>)}
      <T size={11.5} color={colors.custom_dim}>Data: COMEDK 2026 Round 1–4 cut-off ranks, 2025 final cut-off, 2026 seat matrix & fee (comedk.org). Marks se rank: 3 public analyses (2024–2026).</T>
    </View>
    <Picker visible={picker} title="Branch" options={groups} value={branches} multi allLabel="All branches"
      onChange={pickBranches} onClose={() => setPicker(false)} testID="comedk-branch-picker" />
    {detail ? <ComedkSheet key={`${detail.code}-${detail.course}`} req={detail} onClose={() => setDetail(null)} /> : null}
  </>;
}

function ComedkCard({ data, saved, onShortlist }: { data: ComedkOut; saved: number; onShortlist: () => void }) {
  const reduced = useReducedMotion();
  const r = data.result;
  return <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} style={{ gap: space.md }}>
    <MetalCard testID="comedk-card" badge="COMEDK 2026" foot={<>
      <View style={{ flexGrow: 1, flexShrink: 1, gap: 3 }}>
        <Eyebrow>YOUR SCORE</Eyebrow>
        <SilverCaps testID="comedk-card-summary">{r.summary}</SilverCaps>
      </View>
      <Serial testID="comedk-card-serial" value={fmt(r.mid)} of={fmt(r.candidates)} />
    </>}>
      <View style={{ gap: 2 }}>
        <Eyebrow>{r.from_marks ? "EXPECTED RANK · GM" : "YOUR RANK · GM"}</Eyebrow>
        <SerifBig testID="comedk-card-rank">{fmtRange(r.rank)}</SerifBig>
      </View>
      <Hairline testID="comedk-card-reach" label={`${r.in_reach} OF ${r.total} GM SEATS IN REACH`} />
    </MetalCard>
    <CardActions prefix="comedk" onShare={() => shareComedk(data)} saved={saved} onShortlist={onShortlist}
      notes={[r.spread, r.check, "In reach = Safe + Likely + Borderline seats (Borderline pakki nahi)."]} />
  </Animated.View>;
}

function ComedkList({ data, area, onArea, page, onPage, branchText, onBranch, onOpen, busy, saved, tools }: {
  data: ComedkOut; area: ComedkArea; onArea: (a: ComedkArea) => void; page: number; onPage: (p: number) => void;
  branchText: string; onBranch: () => void; onOpen: (i: ComedkItem) => void; busy: boolean; saved: Set<string>; tools: React.ReactNode;
}) {
  const views = useCardViews();
  const row = (it: ComedkItem, testID: string, rank?: number, first?: boolean) => <ComedkRow key={`${testID}-${it.id}`} item={it} testID={testID} rank={rank}
    viewed={views.viewed.has(it.id)} pulse={first && views.pulse} onPress={() => { views.mark(it.id); onOpen(it); }} saved={saved.has(`comedk-${it.id}`)} />;
  return <View testID="comedk-list" style={cardStyles.list}>
    <Strip title="Top college-course" testID="comedk-list-head"
      right={busy ? <ActivityIndicator size="small" color={colors.muted} /> : <T size={12} color={colors.muted}>Top {data.total}</T>}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
        {AREAS.map(a => <Toggle key={a.key} testID={`comedk-area-${a.key}`} label={`${a.label} ${data.reach[a.key] ?? 0}`} on={area === a.key} onPress={() => onArea(a.key)} />)}
      </ScrollView>
      <View style={styles.wrap}>
        <Toggle testID="comedk-list-branch" label={branchText} caret on={branchText !== "All branches"} onPress={onBranch} />
      </View>
      {data.items.length ? tools : null}
    </Strip>
    {data.items.length === 0 ? <T testID="comedk-list-empty" size={13.5} color={colors.muted}>
      Is filter mein 2026 ki koi GM seat aapki rank tak nahi gayi. Branch ya shehar badal kar dekho.
    </T> : <>
      <TapHint testID="comedk-tap-hint" viewed={views.viewed.size} />
      {data.items.map((it, i) => row(it, `comedk-seat-${(page - 1) * 25 + i}`, (page - 1) * 25 + i + 1, i === 0 && page === 1))}
    </>}
    {data.pages > 1 ? <View style={styles.pager}>
      {Array.from({ length: data.pages }, (_, i) => i + 1).map(p => (
        <Press key={p} testID={`comedk-page-${p}`} onPress={() => onPage(p)} accessibilityState={{ selected: p === page }} style={[styles.pageBtn, p === page && styles.pageOn]}>
          <T w="bold" size={13.5} color={p === page ? colors.onSurfaceInverse : colors.onSurface}>Page {p}</T>
        </Press>
      ))}
    </View> : null}
    {data.near.length ? <View testID="comedk-near" style={cardStyles.list}>
      <CardsHeading icon="flag-checkered" title="BAS THODA SA DOOR" sub="Thode aur marks, aur ye seats bhi aapki" ink={colors.custom_flame} />
      {data.near.map((it, i) => row(it, `comedk-near-${i}`))}
    </View> : null}
  </View>;
}

/** ₹2,85,000 → "₹2.85 L" so the fee fits its stat box. */
const lakh = (fee: number) => fee >= 100000 ? `₹${(fee / 100000).toFixed(2)} L` : `₹${fmt(fee)}`;

function ComedkRow({ item, onPress, saved, testID, rank, viewed, pulse }: { item: ComedkItem; onPress: () => void; saved: boolean; testID: string; rank?: number; viewed?: boolean; pulse?: boolean }) {
  return <CollegeCard testID={testID} rank={rank} edge={edgeOf(item.tag, !!item.gap)} title={item.college} a11y={`${item.college}, ${item.course}`}
    tags={item.tag ? <Tag testID={`${testID}-tag`} label={TAG[item.tag].label} ink={TAG[item.tag].ink} soft={TAG[item.tag].soft} /> : undefined}
    sub={item.course} line={`${item.city ? `${item.city} · ` : ""}GM (All India)`}
    stats={[
      { label: "CLOSING", value: fmt(item.close), sub: `${item.round} · 2026` },
      trendStat(item.y25, item.close, `${testID}-trend`),
      { label: "FEE / SAAL", value: item.fee ? lakh(item.fee) : "—", sub: item.seats ? `${item.seats} GM seats` : "seats —" },
    ]}
    note={item.gap ? <T w="semibold" size={12} color={colors.custom_flame}>{item.gap}</T> : null}
    teaser="Har round ka cutoff · fee · seats" viewed={viewed} pulse={pulse} onPress={onPress}
    saved={saved} onStar={() => toggleSaved(comedkSaved(item))} />;
}

const styles = StyleSheet.create({
  inputs: { flexDirection: "row", gap: space.md },
  input: { height: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.bold, fontSize: 18, color: colors.onSurface, ...noOutline },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  chips: { gap: space.sm, paddingRight: space.sm },
  pager: { flexDirection: "row", gap: space.sm, justifyContent: "center", paddingTop: space.sm },
  pageBtn: { minHeight: 44, minWidth: 96, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center", paddingHorizontal: space.lg },
  pageOn: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
});
