// College compare (Rank tab tile): pick 2–3 saved colleges (any exam) and read them side by side — round-wise closing,
// final and last year's cutoff, seats, fee and the saved chance. Everything stays text, so it costs nothing in app size.
import React, { useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, useWindowDimensions, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";
import { compareSaved, CompareCol, fmt } from "./api";
import { EXAM, SERIF, TAG } from "./tones";
import { Strip, Tag } from "./controls";
import { PdfButton } from "./PdfButton";
import { Saved, savedPdfBody, toCompareItem, useShortlist } from "./shortlist";

const MAX = 3;

export function Compare({ onGoCollege }: { onGoCollege: () => void }) {
  const saved = useShortlist();
  const [pick, setPick] = useState<string[]>([]);
  const [hint, setHint] = useState<string | null>(null);
  const [data, setData] = useState<{ items: CompareCol[]; notes: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const touched = useRef(false);

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
    compareSaved(chosen.map(toCompareItem)).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; setBusy(false); };
  }, [key, tries]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id: string) => {
    touched.current = true;
    if (pick.includes(id)) { setPick(pick.filter(x => x !== id)); setHint(null); return; }
    if (pick.length >= MAX) { setHint("Ek baar mein 3 colleges tak. Pehle kisi ek ka tick hatao."); return; }
    setPick([...pick, id]); setHint(null);
  };

  if (saved.length === 0) return <Strip title="College compare" testID="cmp-empty">
    <T size={13.5} color={colors.custom_softText}>Abhi koi college save nahi hai. College predictor mein kisi bhi college ke ☆ par tap karo, phir yahan 2–3 colleges side by side dekho.</T>
    <Pill testID="cmp-go-college" size="lg" label="College predictor kholo" iconRight="arrow-right" onPress={onGoCollege} bg={colors.brandPrimary} ink={colors.onBrandPrimary} />
  </Strip>;

  return <>
    <Strip title="Saved colleges" testID="cmp-list" right={<T size={12} color={colors.muted}>{pick.length} / {MAX} chune</T>}>
      {saved.map((s, i) => {
        const on = pick.includes(s.id);
        return <Press key={s.id} testID={`cmp-item-${i}`} onPress={() => toggle(s.id)} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
          accessibilityLabel={`${s.title}, ${s.sub}`} scaleTo={0.99} style={styles.item}>
          <View style={[styles.check, on && styles.checkOn]}>{on ? <Glyph name="check" size={14} color={colors.onBrandPrimary} stroke={2.4} /> : null}</View>
          <View style={{ flex: 1, gap: 2 }}>
            <View style={styles.line}>
              <Tag label={EXAM[s.exam].label} ink={EXAM[s.exam].ink} soft={EXAM[s.exam].soft} />
              <T w="bold" size={14} numberOfLines={1} style={{ flexShrink: 1 }}>{s.title}</T>
            </View>
            <T size={12.5} color={colors.custom_softText} numberOfLines={1}>{s.sub}</T>
          </View>
        </Press>;
      })}
      {hint ? <T testID="cmp-hint" w="semibold" size={12.5} color={colors.custom_flame}>{hint}</T> : null}
      {pick.length < 2 ? <T testID="cmp-need" size={12.5} color={colors.muted}>Compare ke liye kam se kam 2 colleges chuno.</T> : null}
    </Strip>
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="cmp-error" />
    {busy && !data ? <ActivityIndicator testID="cmp-loading" color={colors.muted} /> : null}
    {data && chosen.length >= 2 ? <CompareTable cols={data.items} saved={chosen} notes={data.notes} /> : null}
    <PdfButton testID="cmp-pdf" path="/saved" body={savedPdfBody(saved, chosen.length >= 2 ? chosen.map(s => s.id) : [])}
      label={chosen.length >= 2 ? "Compare + saved list ki PDF" : "Saved list ki PDF"} />
  </>;
}

const Dash = () => <T size={12} color={colors.custom_dim}>—</T>;

// Every column fits on the phone (no sideways scroll): a full-width label line, then one row of 2–3 equal cells,
// so each row grows to its tallest cell and the columns always stay level.
function CompareTable({ cols, saved, notes }: { cols: CompareCol[]; saved: Saved[]; notes: string[] }) {
  const tight = useWindowDimensions().width < 360 && cols.length === 3;
  // "Sabse aasaan" only when every closing is the same kind of number (same exam and same rank type).
  const same = cols.every(c => c.exam === cols[0].exam && c.rank_label === cols[0].rank_label && !c.missing && c.final);
  const finals = cols.map(c => c.final?.close ?? 0);
  const easiest = same ? finals.indexOf((cols[0].higher_is_harder ? Math.min : Math.max)(...finals)) : -1;
  const nRounds = Math.max(...cols.map(c => c.rounds?.length ?? 0));
  const feeNotes = [...new Set(cols.filter(c => !c.missing && !c.fee && c.fee_note).map(c => c.fee_note!))];
  const row = (key: string, label: string | null, cell: (c: CompareCol, i: number) => React.ReactNode) => <View key={key}>
    {label ? <T w="bold" size={10.5} color={colors.custom_eyebrow} style={styles.section}>{label.toUpperCase()}</T> : null}
    <View testID={`cmp-row-${key}`} style={styles.tr}>
      {cols.map((c, i) => <View key={i} style={[styles.td, tight && styles.tdTight, i > 0 && styles.tdLine, i === easiest && styles.best]}>
        {c.missing && key !== "head" ? <Dash /> : cell(c, i)}
      </View>)}
    </View>
  </View>;
  const tag = (i: number) => { const t = saved[i]?.tag; return t ? <Tag label={TAG[t].label} ink={TAG[t].ink} soft={TAG[t].soft} /> : <Dash />; };
  return <Strip title="Side by side" testID="cmp-table">
    <View style={styles.table}>
      {row("head", null, (c, i) => <View testID={`cmp-col-${i}`} style={{ gap: 3 }}>
        <Tag label={EXAM[c.exam].label} ink={EXAM[c.exam].ink} soft={EXAM[c.exam].soft} />
        {c.missing ? <T size={12} color={colors.error}>Ye seat 2026 ke data mein nahi mili. Isko dobara save karo.</T> : <>
          <T w="bold" size={13.5} numberOfLines={4}>{c.title ?? "—"}</T>
          <T size={12} color={colors.custom_softText} numberOfLines={3}>{c.sub ?? ""}</T>
          <T size={11} color={colors.muted} numberOfLines={2}>{c.path ?? ""}</T>
        </>}
      </View>)}
      {row("final", "Final cutoff", (c, i) => c.final ? <View style={{ gap: 1 }}>
        <T testID={`cmp-final-${i}`} color={colors.custom_rankSilver} style={styles.serif}>{fmt(c.final.close)}</T>
        <T size={11} color={colors.muted}>{c.final.label} · {c.rank_label}</T>
        {i === easiest ? <T testID={`cmp-easiest-${i}`} w="semibold" size={11} color={TAG.safe.ink}>sabse aasaan</T> : null}
      </View> : <Dash />)}
      {Array.from({ length: nRounds }, (_, r) => row(`r${r}`, r === 0 ? (cols.some(c => c.exam === "bitsat") ? "Round / saal-wise" : "Round-wise closing") : null, c => {
        const x = c.rounds?.[r];
        return x ? <View style={styles.cellLine}>
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
  item: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 56, paddingVertical: space.sm, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  check: { width: 24, height: 24, borderRadius: 7, borderWidth: 1.5, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  checkOn: { backgroundColor: colors.custom_rankBlood, borderColor: colors.custom_rankBlood },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  table: { borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLine, overflow: "hidden" },
  section: { letterSpacing: 1, paddingHorizontal: 8, paddingTop: 7, paddingBottom: 5, backgroundColor: colors.custom_cardRaised,
    borderTopWidth: 1, borderTopColor: colors.custom_cardLine },
  tr: { flexDirection: "row" },
  td: { flex: 1, minWidth: 0, justifyContent: "center", paddingHorizontal: 8, paddingVertical: 7 },
  tdTight: { paddingHorizontal: 6 },
  tdLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
  best: { backgroundColor: colors.custom_rankBloodSoft },
  cellLine: { flexDirection: "row", flexWrap: "wrap", alignItems: "baseline", columnGap: 6 },
  serif: { fontFamily: SERIF, fontSize: 18, lineHeight: 23 },
});
