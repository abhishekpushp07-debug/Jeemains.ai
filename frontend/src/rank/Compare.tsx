// College compare (Rank tab tile), two ways:
// Colleges: search any college (JEE Main, COMEDK, BITS campus), add it, and read 2–3 colleges side by side (marks for
// the easiest branch, Computer Science and the toughest branch, branches, seats, fee). Each college opens its full branch
// list ("Saari branches dekho"), and any branch there can be added to the branch compare.
// Branches: 2–3 college-branches (added from a College predictor card or a college's branch list) side by side: round-wise
// closing, final and last year's cutoff, seats, fee and the chance. Everything stays text, so it costs nothing in app size.
import React, { useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, useWindowDimensions, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";
import { compareSaved, CompareCol, fmt, JeeProfileIn } from "./api";
import { track } from "@/src/jlTracker";
import { EXAM, TAG } from "./tones";
import { RemoveButton, Strip, Switch, Tag } from "./controls";
import { PdfButton } from "./PdfButton";
import { Saved, savedPdfBody, toCompareItem, toggleSaved, useShortlist } from "./shortlist";
import { FormButton, useAccent } from "./accent";
import { useCompareColleges } from "./colleges";
import { CollegeCompare } from "./CompareColleges";
import { Dash, TableRow, tableStyles } from "./compareKit";

const MAX = 3;
type Mode = "college" | "branch";

export function Compare({ onGoCollege, profile }: { onGoCollege: () => void; profile: JeeProfileIn }) {
  const saved = useShortlist(), colleges = useCompareColleges();
  const [mode, setMode] = useState<Mode | null>(null);
  // Until the student picks a side, branches open first only when they have branches and no colleges yet.
  const shown: Mode = mode ?? (saved.length && !colleges.length ? "branch" : "college");
  return <>
    <Switch prefix="cmp-mode" value={shown} onChange={setMode}
      items={[{ key: "college", label: `Colleges · ${colleges.length}` }, { key: "branch", label: `Branches · ${saved.length}` }]} />
    <View style={[styles.mode, shown !== "college" && styles.hidden]}><CollegeCompare profile={profile} onBranches={() => setMode("branch")} /></View>
    <View style={[styles.mode, shown !== "branch" && styles.hidden]}><BranchCompare onGoCollege={onGoCollege} onColleges={() => setMode("college")} /></View>
  </>;
}

function BranchCompare({ onGoCollege, onColleges }: { onGoCollege: () => void; onColleges: () => void }) {
  const saved = useShortlist();
  const [pick, setPick] = useState<string[]>([]);
  const [hint, setHint] = useState<string | null>(null);
  const [data, setData] = useState<{ items: CompareCol[]; notes: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const touched = useRef(false);
  const a = useAccent();

  // Until the student ticks something, the latest saved (up to 3) stay ticked, so a compare shows straight away.
  useEffect(() => {
    if (!touched.current) setPick(saved.slice(0, MAX).map(s => s.id));
  }, [saved]);
  const chosen = pick.map(id => saved.find(s => s.id === id)).filter((s): s is Saved => !!s);
  const key = chosen.map(s => s.id).join(",");
  useEffect(() => {
    if (chosen.length < 2) { setData(null); return; }
    let live = true;
    setBusy(true); setError(null);
    compareSaved(chosen.map(toCompareItem)).then(d => { if (live) { setData(d); track("college_compare_used", { kind: "branches", count: chosen.length }); } }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; setBusy(false); };
  }, [key, tries]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id: string) => {
    touched.current = true;
    if (pick.includes(id)) { setPick(pick.filter(x => x !== id)); setHint(null); return; }
    if (pick.length >= MAX) { setHint("Ek baar mein 3 branches tak. Pehle kisi ek ka tick hatao."); return; }
    setPick([...pick, id]); setHint(null);
  };

  if (saved.length === 0) return <Strip form title="Branches compare" testID="cmp-empty">
    <T size={13.5} color={colors.custom_softText}>Abhi koi branch nahi judi. College predictor ke kisi bhi card par “Add to Compare” dabao, ya Colleges mein kisi college ki “Saari branches dekho” se jodo. Phir yahan 2–3 branches side by side dekho.</T>
    <FormButton testID="cmp-go-college" label="College predictor kholo" onPress={onGoCollege} />
    <Press testID="cmp-go-colleges" onPress={onColleges} style={styles.link} accessibilityRole="button">
      <Glyph name="magnify" size={16} color={colors.custom_fSky} />
      <T w="bold" size={13.5} color={colors.custom_fSky}>Ya college dhoondo, uski branches jodo</T>
    </Press>
  </Strip>;

  return <>
    <Strip form title="Saved branches" testID="cmp-list" right={<T w="bold" size={12} color={a ? a.on : colors.muted}>{pick.length} / {MAX} chune</T>}>
      {saved.map((s, i) => {
        const on = pick.includes(s.id);
        return <View key={s.id} style={styles.item}>
          <Press testID={`cmp-item-${i}`} onPress={() => toggle(s.id)} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
            accessibilityLabel={`${s.title}, ${s.sub}`} scaleTo={0.99} style={styles.itemMain}>
            <View style={[tableStyles.check, a && { borderColor: a.line }, on && styles.checkOn, on && a && { backgroundColor: a.ink, borderColor: a.ink }]}>
              {on ? <Glyph name="check" size={14} color={a ? a.on : colors.onBrandPrimary} stroke={2.4} /> : null}
            </View>
            <View style={{ flex: 1, gap: 2 }}>
              <View style={styles.line}>
                <Tag label={EXAM[s.exam].label} ink={EXAM[s.exam].ink} soft={EXAM[s.exam].soft} />
                <T w="bold" size={14} numberOfLines={1} style={{ flexShrink: 1 }}>{s.title}</T>
              </View>
              <T size={12.5} color={colors.custom_softText} numberOfLines={1}>{s.sub}</T>
            </View>
          </Press>
          <RemoveButton testID={`cmp-item-${i}-remove`} label={`${s.title}, ${s.sub} compare se hatao`}
            onPress={() => { touched.current = true; setPick(p => p.filter(x => x !== s.id)); toggleSaved(s); }} />
        </View>;
      })}
      {hint ? <T testID="cmp-hint" w="semibold" size={12.5} color={colors.custom_flame}>{hint}</T> : null}
      {pick.length < 2 ? <T testID="cmp-need" size={12.5} color={colors.muted}>Compare ke liye kam se kam 2 branches chuno.</T> : null}
    </Strip>
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="cmp-error" />
    {busy && !data ? <ActivityIndicator testID="cmp-loading" color={colors.muted} /> : null}
    {data && chosen.length >= 2 ? <CompareTable cols={data.items} saved={chosen} notes={data.notes} /> : null}
    <PdfButton testID="cmp-pdf" path="/saved" body={savedPdfBody(saved, chosen.length >= 2 ? chosen.map(s => s.id) : [])}
      label={chosen.length >= 2 ? "Compare + saved list ki PDF" : "Saved list ki PDF"} />
  </>;
}

// Branch vs branch.
function CompareTable({ cols, saved, notes }: { cols: CompareCol[]; saved: Saved[]; notes: string[] }) {
  const tight = useWindowDimensions().width < 360 && cols.length === 3;
  // "Sabse aasaan" only when every closing is the same kind of number (same exam and same rank type).
  const same = cols.every(c => c.exam === cols[0].exam && c.rank_label === cols[0].rank_label && !c.missing && c.final);
  const finals = cols.map(c => c.final?.close ?? 0);
  const easiest = same ? finals.indexOf((cols[0].higher_is_harder ? Math.min : Math.max)(...finals)) : -1;
  const nRounds = Math.max(...cols.map(c => c.rounds?.length ?? 0));
  const feeNotes = [...new Set(cols.filter(c => !c.missing && !c.fee && c.fee_note).map(c => c.fee_note!))];
  const row = (key: string, label: string | null, cell: (c: CompareCol, i: number) => React.ReactNode) =>
    <TableRow key={key} id={`cmp-row-${key}`} label={label} count={cols.length} tight={tight} best={easiest}
      cell={i => cols[i].missing && key !== "head" ? <Dash /> : cell(cols[i], i)} />;
  const tag = (i: number) => { const t = saved[i]?.tag; return t ? <Tag label={TAG[t].label} ink={TAG[t].ink} soft={TAG[t].soft} /> : <Dash />; };
  return <Strip title="Side by side" testID="cmp-table">
    <View style={tableStyles.table}>
      {row("head", null, (c, i) => <View testID={`cmp-col-${i}`} style={{ gap: 3 }}>
        <Tag label={EXAM[c.exam].label} ink={EXAM[c.exam].ink} soft={EXAM[c.exam].soft} />
        {c.missing ? <T size={12} color={colors.error}>Ye seat 2026 ke data mein nahi mili. Isko dobara save karo.</T> : <>
          <T w="bold" size={13.5} numberOfLines={4}>{c.title ?? "—"}</T>
          <T size={12} color={colors.custom_softText} numberOfLines={3}>{c.sub ?? ""}</T>
          <T size={11} color={colors.muted} numberOfLines={2}>{c.path ?? ""}</T>
        </>}
      </View>)}
      {row("final", "Final cutoff", (c, i) => c.final ? <View style={{ gap: 1 }}>
        <T testID={`cmp-final-${i}`} color={colors.custom_rankSilver} style={tableStyles.serif}>{fmt(c.final.close)}</T>
        <T size={11} color={colors.muted}>{c.final.label} · {c.rank_label}</T>
        {i === easiest ? <T testID={`cmp-easiest-${i}`} w="semibold" size={11} color={TAG.safe.ink}>sabse aasaan</T> : null}
      </View> : <Dash />)}
      {Array.from({ length: nRounds }, (_, r) => row(`r${r}`, r === 0 ? (cols.some(c => c.exam === "bitsat") ? "Round / saal-wise" : "Round-wise closing") : null, c => {
        const x = c.rounds?.[r];
        return x ? <View style={tableStyles.cellLine}>
          <T size={11} color={colors.muted}>{x.label}</T>
          <T w="semibold" size={12.5} color={x.close ? colors.onSurface : colors.custom_dim}>{x.close ? fmt(x.close) : "—"}</T>
          {x.close && x.crl ? <T size={10} color={colors.muted}>CRL</T> : null}
        </View> : null;
      }))}
      {row("prev", "Pichhla saal", c => c.prev?.close ? <View>
        <T w="semibold" size={12.5} color={colors.custom_softText}>{fmt(c.prev.close)}</T>
        <T size={10.5} color={colors.muted}>{c.prev.label}</T>
      </View> : <Dash />)}
      {row("seats", "Seats", c => c.seats ? <View>
        <T w="bold" size={13.5}>{c.seats}</T>
        {c.seats_label ? <T size={10.5} color={colors.muted}>{c.seats_label}</T> : null}
      </View> : <Dash />)}
      {row("fee", "Fee / saal", c => c.fee ? <T w="bold" size={13.5}>₹{fmt(c.fee)}</T> : <T size={11} color={colors.custom_dim}>website par *</T>)}
      {row("tag", "Aapka chance", (_c, i) => tag(i))}
    </View>
    {feeNotes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>* {n}</T>)}
    {notes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>{n}</T>)}
  </Strip>;
}

const styles = StyleSheet.create({
  mode: { gap: space.lg },
  hidden: { display: "none" },
  item: { flexDirection: "row", alignItems: "center", gap: space.xs, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  itemMain: { flex: 1, flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 56, paddingVertical: space.sm },
  checkOn: { backgroundColor: colors.custom_rankBlood, borderColor: colors.custom_rankBlood },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  link: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, minHeight: 44 },
});
