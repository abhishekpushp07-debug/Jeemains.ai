// Target marks (Rank tab tile): pick a college and see, branch by branch, how many marks 2026's closing rank needed —
// JEE Main per paper type and round, COMEDK as the range of the 3 analyses, BITSAT straight from the official cutoff.
import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, StyleSheet, useWindowDimensions, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, radius, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import {
  BitsatTarget, Category, ComedkCollege, ComedkTarget, ComedkTargetRow, fmt, getColleges, JeeCollege, JeeTargetRow,
  targetBitsat, targetComedk, targetJee,
} from "./api";
import { CAMPUS, CATEGORY_LABEL, KIND, LEVEL, SERIF } from "./tones";
import { Picker, Strip, Switch, Tag, Toggle } from "./controls";
import { CollegeSearch } from "./CollegeSearch";
import { feeLine } from "./ComedkSheet";
import { PdfButton } from "./PdfButton";
import { useAccent } from "./accent";

const SAVED = "rank.target.v1";
const CATS: Category[] = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];
type Exam = "jee" | "bitsat" | "comedk";
type Profile = { exam: Exam; category: Category; female: boolean; pwd: boolean; state: string | null; inst: number | null; code: string | null; campus: "all" | "Pilani" | "Goa" | "Hyderabad" };
const DEFAULT: Profile = { exam: "jee", category: "GEN", female: false, pwd: false, state: null, inst: null, code: null, campus: "all" };

/** Loads once per screen and caches through re-renders. */
function useOnce<T>(load: (() => Promise<T>) | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const ready = !!load;
  useEffect(() => {
    if (!load || data) return;
    let live = true;
    setError(null);
    load().then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [ready, tries]); // eslint-disable-line react-hooks/exhaustive-deps
  return { data, error, retry: () => setTries(t => t + 1) };
}

export function TargetMarks({ states }: { states: string[] }) {
  const [p, setP] = useState<Profile>(DEFAULT);
  useEffect(() => {
    storage.getItem<string | null>(SAVED, null).then(raw => {
      if (!raw) return;
      try { setP({ ...DEFAULT, ...JSON.parse(raw) }); } catch { /* keep defaults */ }
    });
  }, []);
  const patch = (x: Partial<Profile>) => setP(prev => { const next = { ...prev, ...x }; storage.setItem(SAVED, JSON.stringify(next)); return next; });
  const lists = useOnce(p.exam === "bitsat" ? null : getColleges);
  return <>
    <Switch prefix="tm-exam" value={p.exam} onChange={exam => patch({ exam })} items={[{ key: "jee", label: "JEE Main" }, { key: "bitsat", label: "BITSAT" }, { key: "comedk", label: "COMEDK" }]} />
    <ErrorBox error={lists.error ?? undefined} retry={lists.retry} testID="tm-colleges-error" />
    {p.exam === "jee" ? <JeePart p={p} patch={patch} states={states} colleges={lists.data?.jee ?? []} />
      : p.exam === "comedk" ? <ComedkPart p={p} patch={patch} colleges={lists.data?.comedk ?? []} />
      : <BitsatPart campus={p.campus} onCampus={campus => patch({ campus })} />}
  </>;
}

function Chooser({ label, onPress, testID }: { label: string | null; onPress: () => void; testID: string }) {
  const a = useAccent();
  return <Press testID={testID} onPress={onPress} scaleTo={0.99} style={[styles.chooser, a && { borderColor: a.line }]} accessibilityLabel={label ?? "College chuno"}>
    <Glyph name="school-outline" size={20} color={a ? a.text : colors.custom_rankSilver} stroke={1.5} />
    <T w="bold" size={15} color={label ? colors.onSurface : colors.custom_softText} numberOfLines={1} style={{ flex: 1 }}>{label ?? "College chuno"}</T>
    <Glyph name="chevron-down" size={16} color={a ? a.text : colors.muted} />
  </Press>;
}

/** Fetches one target answer whenever its request changes. */
function useTarget<Q, R>(q: Q | null, load: (q: Q) => Promise<R>) {
  const [data, setData] = useState<R | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const key = q ? JSON.stringify(q) : null;
  useEffect(() => {
    if (!q) { setData(null); return; }
    let live = true;
    setBusy(true); setError(null);
    load(q).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; setBusy(false); };
  }, [key, tries]); // eslint-disable-line react-hooks/exhaustive-deps
  return { data, busy, error, retry: () => setTries(t => t + 1) };
}

function JeePart({ p, patch, states, colleges }: { p: Profile; patch: (x: Partial<Profile>) => void; states: string[]; colleges: JeeCollege[] }) {
  const [picker, setPicker] = useState<"state" | "college" | null>(null);
  const [openRow, setOpenRow] = useState<number | null>(null);
  const q = p.inst === null ? null : { inst: p.inst, category: p.category, female: p.female, pwd: p.pwd, state: p.state };
  const t = useTarget(q, targetJee);
  const chosen = colleges.find(c => c.inst === p.inst);
  const options = useMemo(() => colleges.map(c => ({ key: String(c.inst), title: c.short, sub: `${KIND[c.type].label} · ${c.city}, ${c.state}`, find: c.name })), [colleges]);
  return <>
    <Strip form title="Aapki details" testID="tm-profile">
      <View style={styles.wrap}>
        {CATS.map(c => <Toggle key={c} testID={`tm-cat-${c}`} label={CATEGORY_LABEL[c]} on={p.category === c} onPress={() => patch({ category: c })} />)}
      </View>
      <View style={styles.wrap}>
        <Toggle testID="tm-female" label="Female" on={p.female} onPress={() => patch({ female: !p.female })} />
        <Toggle testID="tm-pwd" label="PwD" on={p.pwd} onPress={() => patch({ pwd: !p.pwd })} />
        <Toggle testID="tm-state" label={p.state ?? "Home state"} on={!!p.state} caret onPress={() => setPicker("state")} />
      </View>
      <Chooser testID="tm-college" label={chosen?.short ?? null} onPress={() => setPicker("college")} />
      <T size={11.5} color={colors.custom_dim}>Home state se NIT ki Home-state seat aur JAC Delhi ki Delhi seat khulti hai.</T>
    </Strip>
    <ErrorBox error={t.error ?? undefined} retry={t.retry} testID="tm-error" />
    {t.data && q ? <Strip title={t.data.college.short} testID="tm-list" right={t.busy ? <ActivityIndicator size="small" color={colors.muted} /> : <Tag label={KIND[t.data.college.type].label} ink={KIND[t.data.college.type].ink} soft={KIND[t.data.college.type].soft} />}>
      <T size={12.5} color={colors.muted}>{t.data.college.city}, {t.data.college.state} · {t.data.rows.length} branches · tap karo, har round ka target</T>
      {t.data.rows.length ? <PdfButton testID="tm-pdf" path="/target/jee" body={q} label="Is college ki PDF" /> : null}
      {t.data.rows.length === 0 ? <T testID="tm-empty" size={13.5} color={colors.muted}>Aapke category / state / gender ke liye is college mein 2026 ki koi seat nahi thi.</T> : null}
      {t.data.rows.map((r, i) => <JeeRow key={r.prog} r={r} rounds={t.data!.rounds} open={openRow === r.prog} onPress={() => setOpenRow(openRow === r.prog ? null : r.prog)} testID={`tm-row-${i}`} />)}
      {t.data.notes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>{n}</T>)}
    </Strip> : q ? <ActivityIndicator testID="tm-loading" color={colors.muted} /> : <T testID="tm-hint" size={13} color={colors.muted}>College chuno, phir har branch ke liye dikhega ki 2026 ki closing rank ke liye lagbhag kitne marks chahiye the.</T>}
    <Picker visible={picker === "state"} title="Home state" options={states} value={p.state ? [p.state] : []} allLabel="No home state"
      onChange={v => patch({ state: v[0] ?? null })} onClose={() => setPicker(null)} testID="tm-state-picker" />
    <CollegeSearch visible={picker === "college"} title="College chuno" options={options} onPick={k => { patch({ inst: Number(k) }); setOpenRow(null); }}
      onClose={() => setPicker(null)} testID="tm-college-sheet" />
  </>;
}

function JeeRow({ r, rounds, open, onPress, testID }: { r: JeeTargetRow; rounds: string[]; open: boolean; onPress: () => void; testID: string }) {
  const f = r.final;
  return <View style={styles.row}>
    <Press testID={testID} onPress={onPress} scaleTo={0.99} accessibilityState={{ expanded: open }} accessibilityLabel={`${r.branch}: Normal paper ${f.marks.normal} marks`} style={styles.rowMain}>
      <View style={{ flex: 1, gap: 3 }}>
        <T w="bold" size={14} numberOfLines={2}>{r.branch}{r.degree ? ` (${r.degree})` : ""}</T>
        <T size={12} color={colors.muted}>{r.path}</T>
        <T size={12} color={colors.muted}>Closing {fmt(f.close)} {r.rank_type} · {f.label}{r.seats ? ` · ${r.seats} seats` : ""}</T>
      </View>
      <View style={styles.big}>
        <T testID={`${testID}-normal`} color={colors.custom_rankSilver} style={styles.serif}>{f.marks.normal}+</T>
        <T size={10.5} color={colors.muted}>marks · Normal</T>
      </View>
    </Press>
    <T testID={`${testID}-line`} size={12} color={colors.custom_softText}>Tough paper {f.marks.tough}+ · Easy paper {f.marks.easy}+ · {f.pct.toFixed(2)} percentile</T>
    {open ? <RoundTable r={r} rounds={rounds} testID={`${testID}-rounds`} /> : null}
  </View>;
}

const MARK_LEVELS = ["tough", "normal", "easy"] as const;

/** Round-by-round closing and marks; under 360px the headers drop to small title case so every column keeps a gap. */
function RoundTable({ r, rounds, testID }: { r: JeeTargetRow; rounds: string[]; testID: string }) {
  const narrow = useWindowDimensions().width < 360;
  const head = (s: string) => narrow ? s : s.toUpperCase();
  const td = { round: [styles.tdRound, narrow && styles.tdRoundNarrow], mark: [styles.tdMark, narrow && styles.tdMarkNarrow] };
  const csab = rounds.some(x => x.startsWith("CSAB"));
  return <View testID={testID} style={styles.table}>
    <View style={[styles.tr, styles.th]}>
      <T w="bold" size={narrow ? 10.5 : 11} color={colors.custom_eyebrow} style={td.round}>{head("Round")}</T>
      <T w="bold" size={narrow ? 10.5 : 11} color={colors.custom_eyebrow} style={styles.tdClose}>{head("Closing")}</T>
      {MARK_LEVELS.map(l => <T key={l} w="bold" size={narrow ? 10.5 : 11} color={LEVEL[l].ink === colors.onSurface ? colors.custom_eyebrow : LEVEL[l].ink} style={td.mark}>{head(LEVEL[l].label)}</T>)}
    </View>
    {r.cells.map((c, i) => <View key={rounds[i]} style={styles.tr}>
      <T size={12} color={colors.muted} style={td.round}>{c.label}</T>
      <T size={12} color={c.close ? colors.onSurface : colors.custom_dim} style={styles.tdClose}>{c.close ? fmt(c.close) : c.unpublished ? "—*" : "—"}</T>
      {MARK_LEVELS.map(l => <T key={l} w={l === "normal" ? "bold" : "regular"} size={12} color={c.marks ? colors.onSurface : colors.custom_dim} style={td.mark}>{c.marks ? c.marks[l] : "—"}</T>)}
    </View>)}
    <T size={11} color={colors.custom_dim}>Marks = us round ki closing tak pahunchne ke liye.{csab ? " CSAB rounds CRL par band hote hain." : ""}</T>
    {r.cells.some(c => c.unpublished) ? <T size={11} color={colors.custom_dim}>* JAC ne Upgrade / Spot round ki rank publish nahi ki.</T> : null}
  </View>;
}

function ComedkPart({ p, patch, colleges }: { p: Profile; patch: (x: Partial<Profile>) => void; colleges: ComedkCollege[] }) {
  const [picker, setPicker] = useState(false);
  const [openRow, setOpenRow] = useState<string | null>(null);
  const t = useTarget(p.code, targetComedk);
  const chosen = colleges.find(c => c.code === p.code);
  const options = useMemo(() => colleges.map(c => ({ key: c.code, title: c.short, sub: c.city || "Karnataka", find: c.name })), [colleges]);
  return <>
    <Strip form title="College" testID="tm-profile">
      <Chooser testID="tm-college" label={chosen?.short ?? null} onPress={() => setPicker(true)} />
      <T size={11.5} color={colors.custom_dim}>Sirf GM (All India) seats. COMEDK mein category se cutoff nahi badalta.</T>
    </Strip>
    <ErrorBox error={t.error ?? undefined} retry={t.retry} testID="tm-error" />
    {t.data && p.code ? <ComedkList data={t.data} busy={t.busy} openRow={openRow} onRow={cc => setOpenRow(openRow === cc ? null : cc)} />
      : p.code ? <ActivityIndicator testID="tm-loading" color={colors.muted} /> : <T testID="tm-hint" size={13} color={colors.muted}>College chuno, phir har course ke liye dikhega ki 2026 ki closing rank ke liye lagbhag kitne marks chahiye the.</T>}
    <CollegeSearch visible={picker} title="College chuno" options={options} onPick={k => { patch({ code: k }); setOpenRow(null); }} onClose={() => setPicker(false)} testID="tm-college-sheet" />
  </>;
}

function ComedkList({ data, busy, openRow, onRow }: { data: ComedkTarget; busy: boolean; openRow: string | null; onRow: (cc: string) => void }) {
  return <Strip title={data.college.short} testID="tm-list" right={busy ? <ActivityIndicator size="small" color={colors.muted} /> : <Tag label="COMEDK · GM" ink={colors.custom_rankBloodInk} soft={colors.custom_rankBloodSoft} />}>
    <T size={12.5} color={colors.muted}>{data.college.city} · {data.rows.length} courses · tap karo, har round ka target</T>
    <PdfButton testID="tm-pdf" path="/target/comedk" body={{ code: data.college.code }} label="Is college ki PDF" />
    {data.rows.map((r, i) => <ComedkRow key={r.cc} r={r} open={openRow === r.cc} onPress={() => onRow(r.cc)} testID={`tm-row-${i}`} />)}
    {data.notes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>{n}</T>)}
  </Strip>;
}

function ComedkRow({ r, open, onPress, testID }: { r: ComedkTargetRow; open: boolean; onPress: () => void; testID: string }) {
  const f = r.final, money = feeLine(r.fee, r.seats);
  return <View style={styles.row}>
    <Press testID={testID} onPress={onPress} scaleTo={0.99} accessibilityState={{ expanded: open }} accessibilityLabel={`${r.course}: lagbhag ${f.mid} marks`} style={styles.rowMain}>
      <View style={{ flex: 1, gap: 3 }}>
        <T w="bold" size={14} numberOfLines={2}>{r.course}</T>
        <T size={12} color={colors.muted}>Closing {fmt(f.close)} · {f.label} · GM</T>
        {money ? <T size={12} color={colors.muted}>{money}</T> : null}
      </View>
      <View style={styles.big}>
        <T testID={`${testID}-mid`} color={colors.custom_rankSilver} style={styles.serif}>{f.mid}+</T>
        <T size={10.5} color={colors.muted}>marks / 180</T>
      </View>
    </Press>
    <T testID={`${testID}-line`} size={12} color={colors.custom_softText}>3 analyses ki range: {f.marks[0]}–{f.marks[1]} marks</T>
    {open ? <View testID={`${testID}-rounds`} style={styles.table}>
      <View style={[styles.tr, styles.th]}>
        <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.tdRound}>ROUND</T>
        <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.tdClose}>CLOSING</T>
        <T w="bold" size={11} color={colors.custom_eyebrow} style={styles.tdWide}>MARKS</T>
      </View>
      {r.cells.map(c => <View key={c.label} style={styles.tr}>
        <T size={12} color={colors.muted} style={styles.tdRound}>{c.label}</T>
        <T size={12} color={c.close ? colors.onSurface : colors.custom_dim} style={styles.tdClose}>{c.close ? fmt(c.close) : "—"}</T>
        <T w="bold" size={12} color={c.close ? colors.onSurface : colors.custom_dim} style={styles.tdWide}>{c.marks ? `${c.mid} (${c.marks[0]}–${c.marks[1]})` : "allotment nahi"}</T>
      </View>)}
    </View> : null}
  </View>;
}

function BitsatPart({ campus, onCampus }: { campus: Profile["campus"]; onCampus: (c: Profile["campus"]) => void }) {
  const t = useOnce<BitsatTarget>(targetBitsat);
  const rows = (t.data?.rows ?? []).filter(r => campus === "all" || r.campus === campus);
  return <>
    <Strip form title="Campus" testID="tm-campus">
      <View style={styles.wrap}>
        {(["all", "Pilani", "Goa", "Hyderabad"] as const).map(c => <Toggle key={c} testID={`tm-campus-${c}`} label={c === "all" ? "All campuses" : c} on={campus === c} onPress={() => onCampus(c)} />)}
      </View>
    </Strip>
    <ErrorBox error={t.error ?? undefined} retry={t.retry} testID="tm-error" />
    {t.data ? <Strip title="BITSAT target" testID="tm-list" right={<T size={12} color={colors.muted}>score / {t.data.max}</T>}>
      <PdfButton testID="tm-pdf" path="/target/bitsat" body={{ campus }} label="Target list ki PDF" />
      {rows.map((r, i) => <View key={r.id} testID={`tm-row-${i}`} style={[styles.row, styles.rowMain]}>
        <View style={{ flex: 1, gap: 3 }}>
          <View style={styles.line}>
            <Tag label={CAMPUS[r.campus].label} ink={CAMPUS[r.campus].ink} soft={CAMPUS[r.campus].soft} />
            <T w="bold" size={14} numberOfLines={2} style={{ flexShrink: 1 }}>{r.program}</T>
          </View>
          <T size={12} color={colors.muted}>{t.data!.years.map((y, k) => `${y}: ${r.history[k] ?? "—"}`).join(" · ")}</T>
          <T size={12} color={colors.custom_softText}>Safe target {r.safe}+</T>
        </View>
        <View style={styles.big}>
          <T testID={`tm-row-${i}-cutoff`} color={colors.custom_rankSilver} style={styles.serif}>{r.cutoff}+</T>
          <T size={10.5} color={colors.muted}>2026 cutoff</T>
        </View>
      </View>)}
      {t.data.notes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>{n}</T>)}
    </Strip> : <ActivityIndicator testID="tm-loading" color={colors.muted} />}
  </>;
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  chooser: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 52, paddingHorizontal: space.md, borderRadius: radius.pill,
    borderWidth: 1, borderColor: colors.custom_rankSilverLine, backgroundColor: colors.custom_cardRaised },
  row: { gap: 6, paddingVertical: space.md, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  rowMain: { flexDirection: "row", alignItems: "flex-start", gap: space.md },
  big: { alignItems: "flex-end", minWidth: 72 },
  serif: { fontFamily: SERIF, fontSize: 24, lineHeight: 30 },
  table: { gap: 2, padding: space.sm, borderRadius: 12, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine },
  tr: { flexDirection: "row", alignItems: "center", minHeight: 28, gap: 4 },
  th: { borderBottomWidth: 1, borderBottomColor: colors.custom_cardLine },
  tdRound: { width: 56 },
  tdRoundNarrow: { width: 48 },
  tdClose: { flex: 1 },
  tdMark: { width: 54, textAlign: "right" },
  tdMarkNarrow: { width: 42 },
  tdWide: { flex: 1.4, textAlign: "right" },
});
